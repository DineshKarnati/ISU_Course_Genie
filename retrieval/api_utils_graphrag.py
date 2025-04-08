import json
from openai import OpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
load_dotenv() # Load environment variables
OPENAI_API_KEY= os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY= os.getenv('PINECONE_API_KEY')
INDEX_NAME= os.getenv('INDEX_NAME')
NAMESPACE= os.getenv('NAMESPACE')

NEO_URI= os.getenv('NEO_URI')
NEO_USERNAME= os.getenv('NEO_USERNAME')
NEO4J_PASSWORD= os.getenv('NEO4J_PASSWORD')

client = OpenAI(api_key=OPENAI_API_KEY)
neo4j_driver = GraphDatabase.driver(NEO_URI,
                                    auth=(NEO_USERNAME, NEO4J_PASSWORD))


# --- Embedding + Rephrasing ---
def rephrase_query(query: str, previous_query: str = "") -> str:
    prompt = (
        "Rephrase the following user question to be detailed and unambiguous. "
        "Preserve the original intent, and resolve any pronouns or references using the previous query.\n\n"
    )
    if previous_query:
        prompt += f"Previous Rephrased Query: {previous_query}\n\n"
    prompt += f"Current Query: {query}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that refines queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


def extract_entities_and_intent(query: str) -> dict:
    # Use GPT to extract intent + entities
    system_prompt = """Extract the user's intent and key academic entities from their query. 
    Intent must be one of: list_program_courses, course_details, semester_plan, program_overview.
    Return as JSON: {"intent": "...", "program": "...", "coursecode": "...", "coursename": "...","year": "..."} (some fields may be null)"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )
    try:
        result = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        result = {"program": None, "intent": None}
    return result


def generate_cypher(intent: str, entities: dict) -> str:
    program = entities.get("program")
    coursecode = entities.get("coursecode")
    coursename = entities.get("coursename")
    year = entities.get("year")

    if intent == "list_program_courses":
        return f"""
            MATCH (p:Program {{name: "{program}"}})
            MATCH (p)-[:HAS_MAIN]->(m:MainGroup)-[:HAS_SECTION]->(s:Section)-[:HAS_COURSE]->(c:Course)
            RETURN properties(p) AS program_attrs,
                   properties(m) AS maingroup_attrs,
                   properties(s) AS section_attrs,
                   properties(c) AS course_attrs
        """

    elif intent == "course_details":
        course_filter = f'c.code = "{coursecode}"' if coursecode else f'c.name = "{coursename}"'
        return f"""
            MATCH (p:Program {{name: "{program}"}})
            MATCH (p)-[:HAS_MAIN]->(m:MainGroup)-[:HAS_SECTION]->(s:Section)-[:HAS_COURSE]->(c:Course)
            WHERE {course_filter}
            OPTIONAL MATCH (c)-[:HAS_YEAR]->(y:Year)
            RETURN properties(p) AS program_attrs,
                   properties(m) AS maingroup_attrs,
                   properties(s) AS section_attrs,
                   properties(c) AS course_attrs,
                   properties(y) AS year_attrs
        """

    elif intent == "semester_plan":
        return f"""
            MATCH (p:Program {{name: "{program}"}})
            MATCH (p)-[:HAS_MAIN]->(m:MainGroup)
            MATCH (m)-[:HAS_SECTION]->(s:Section)-[:HAS_COURSE]->(c:Course)-[:HAS_YEAR]->(y:Year)
            RETURN properties(p) AS program_attrs,
                   properties(m) AS maingroup_attrs,
                   properties(s) AS section_attrs,
                   properties(c) AS course_attrs,
                   properties(y) AS year_attrs
        """

    elif intent == "program_overview":
        return f"""
            MATCH (p:Program {{name: "{program}"}})
            MATCH (p)-[:HAS_MAIN]->(m:MainGroup)-[:HAS_SECTION]->(s:Section)
            RETURN properties(p) AS program_attrs,
                   properties(m) AS maingroup_attrs,
                   properties(s) AS section_attrs
        """

    else:
        return ""


def run_cypher_query(cypher: str):
    with neo4j_driver.session() as session:
        result = session.run(cypher)
        return [dict(record) for record in result]


def format_response(intent: str, result: list) -> str:
    if not result:
        return "No matching data found."

    def render_attributes(title: str, attrs: dict) -> str:
        if not attrs:
            return ""
        lines = [f"**{title}**"]
        for k, v in attrs.items():
            lines.append(f"- **{k.capitalize()}:** {v}")
        return "\n".join(lines)

    response_blocks = []

    if intent in ["list_program_courses"]:
        for r in result:
            blocks = []
            blocks.append(render_attributes("📘 Course", r.get("course_attrs", {})))
            blocks.append(render_attributes("📗 Year", r.get("year_attrs", {})))
            blocks.append(render_attributes("📙 Section", r.get("section_attrs", {})))
            blocks.append(render_attributes("📒 Main Group", r.get("maingroup_attrs", {})))
            blocks.append(render_attributes("📕 Program", r.get("program_attrs", {})))
            response_blocks.append("\n".join(blocks))

        return "\n---\n".join(response_blocks)
    elif intent in ["semester_plan"]:
        for r in result:
            blocks = []
            blocks.append(render_attributes("📘 Course", r.get("course_attrs", {})))
            blocks.append(render_attributes("📗 Year", r.get("year_attrs", {})))
            # blocks.append(render_attributes("📙 Section", r.get("section_attrs", {})))
            # blocks.append(render_attributes("📒 Main Group", r.get("maingroup_attrs", {})))
            blocks.append(render_attributes("📕 Program", r.get("program_attrs", {})))
            response_blocks.append("\n".join(blocks))

        return "\n---\n".join(response_blocks)
    elif intent == "course_details":
        # r = result[0]
        blocks = []
        for r in result:
            blocks.append(render_attributes("📘 Course", r.get("course_attrs", {})))
            blocks.append(render_attributes("📗 Year", r.get("year_attrs", {})))
            blocks.append(render_attributes("📙 Section", r.get("section_attrs", {})))
            blocks.append(render_attributes("📒 Main Group", r.get("maingroup_attrs", {})))
            blocks.append(render_attributes("📕 Program", r.get("program_attrs", {})))
        return "\n".join(blocks)

    elif intent == "program_overview":
        # grouped = {}
        # for r in result:
        #     pg_attrs = r.get("program_attrs", {})
        #     mg_attrs = r.get("maingroup_attrs", {})
        #     sec_attrs = r.get("section_attrs", {})
        #     mg_title = mg_attrs.get("title", "MainGroup")
        #     sec_name = sec_attrs.get("name", "Section")
        #     sec_content = sec_attrs.get("content", "")
        #     key = f"📘 {mg_title} > {sec_name}"
        #     grouped[key] = sec_content
        #
        # return "\n\n".join([f"### {k}\n{v}" for k, v in grouped.items()])
        blocks = []
        for r in result:
            blocks.append(render_attributes("📙 Section", r.get("section_attrs", {})))
            blocks.append(render_attributes("📒 Main Group", r.get("maingroup_attrs", {})))
            blocks.append(render_attributes("📕 Program", r.get("program_attrs", {})))
        return "\n".join(blocks)


    else:
        return json.dumps(result, indent=2)


def find_best_matching_programs(entities: dict) -> list:
    program_matches = []

    # Try fuzzy search on Program name
    program_term = entities.get("program")
    if program_term and program_term.strip():
        with neo4j_driver.session() as session:
            query = """
            CALL db.index.fulltext.queryNodes("entityIndex", $term + "~") YIELD node, score
            WHERE "Program" IN labels(node)
            RETURN DISTINCT node.name AS program, score
            ORDER BY score DESC
            LIMIT 3
            """
            results = session.run(query, term=program_term.strip())
            program_matches = [record["program"] for record in results]
            if program_matches:
                return program_matches

    # Fallback to course name/code → backtrack to programs
    for key in ["coursename", "coursecode"]:
        term = entities.get(key)
        if term and term.strip():
            with neo4j_driver.session() as session:
                query = """
                CALL db.index.fulltext.queryNodes("entityIndex", $term + "~") YIELD node, score
                WHERE "Course" IN labels(node)
                MATCH (p:Program)-[:HAS_MAIN]->()-[:HAS_SECTION]->()-[:HAS_COURSE]->(node)
                RETURN DISTINCT p.name AS program, score
                ORDER BY score DESC
                LIMIT 3
                """
                results = session.run(query, term=term.strip())
                fallback_matches = [record["program"] for record in results]
                if fallback_matches:
                    return fallback_matches

    return []


def generate_response_from_context(rephrased_query: str, context: str) -> str:
    system_prompt = (
        "You are an academic advisor assistant. Given the user's rephrased question and structured academic data, "
        "respond in a helpful and concise way using the graph-based context."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User query: {rephrased_query}\n\nGraph data:\n{context}"}
        ]
    )

    return response.choices[0].message.content.strip()


def graphrag_query_response(user_input: str) -> str:
    rephrased_query = rephrase_query(user_input)
    entities = extract_entities_and_intent(rephrased_query)
    print("🧠 Extracted:", entities)

    # 👇 Enhanced program identification
    if entities['program'] or entities['coursecode'] or entities['coursename']:
        best_program = find_best_matching_programs(entities)
        if best_program:
            entities["program"] = best_program
        else:
            return "Sorry, I couldn't match your query to any known academic program."
    print("best_program", entities["program"])

    cypher = generate_cypher(entities["intent"], entities)
    print("cypher query", cypher)
    result = run_cypher_query(cypher)
    rstructured_context = format_response(entities["intent"], result)

    final_response = generate_response_from_context(rephrased_query, rstructured_context)
    print(final_response)
    return final_response