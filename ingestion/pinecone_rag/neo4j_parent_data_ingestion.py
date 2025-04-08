import os
import pandas as pd
from neo4j import GraphDatabase
from collections import defaultdict
import uuid

# === Config ===
DIRECTORY_PATH = "./data"  # Folder containing Excel files
NEO4J_URI = "neo4j+s://5ba1c10e.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "jbqO7pkaBdxiDnQC8lTED24a77xSBlRYgtgV0_ZbzQk"

# === Neo4j Setup ===
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def insert_data(tx, query, params=None):
    tx.run(query, params or {})


def insert_courses_and_years(session, course_nodes, section_to_courses, course_year_edges, program_name,
                             main_to_sections):
    for main, section_set in main_to_sections.items():
        if "degree map" not in main.lower():
            for section in section_set:
                for code in section_to_courses[section]:
                    course = course_nodes[code]
                    session.write_transaction(insert_data, """
                        MATCH (p:Program {name: $program_name})
                        MATCH (p)-[:HAS_MAIN]->(m:MainGroup {title: $main})
                        MATCH (m)-[:HAS_SECTION]->(s:Section {name: $section})
                        MERGE (c:Course {code: $code, name: $name, credits: $credits})
                        MERGE (s)-[:HAS_COURSE]->(c)
                    """, {
                        "program_name": program_name,
                        "main": main.strip(),
                        "section": section.strip(),
                        "code": course["code"].strip(),
                        "name": course["name"].strip(),
                        "credits": course["credits"].strip()
                    })

    # for main, section_set in main_to_sections.items():
    #     for section in section_set:
    #         for code in section_to_courses[section]:
    for c_code, year, course_name, credits in course_year_edges:
        if course_name and credits and year:
            session.write_transaction(insert_data, """
                MATCH (p:Program {name: $program_name})
                MERGE (p)-[:HAS_MAIN]->(m:MainGroup {title: "Degree Map"})
                MERGE (m)-[:HAS_SECTION]->(s:Section {name: "Degree overview"})
                MERGE (c:Course {code: $code, name: $course_name, credits: $credits})
                MERGE (s)-[:HAS_COURSE]->(c)
                MERGE (y:Year {name: $year})
                MERGE (c)-[:HAS_YEAR]->(y)
            """, {
                "program_name": program_name.strip(),
                "code": c_code.strip(),
                "year": year.lower().strip(),
                "credits": credits.strip(),
                "course_name": course_name.strip()
            })


def process_excel(file_path, program_name):
    df = pd.read_excel(file_path)

    course_nodes = {}
    year_nodes = set()
    main_groups = {}
    sections = {}
    section_attributes = defaultdict(list)
    main_to_sections = defaultdict(set)
    section_to_courses = defaultdict(set)
    course_year_edges = []

    current_term = None
    current_main = None
    current_section = None
    for _, row in df.iterrows():
        main = str(row['Main']).strip() if pd.notna(row['Main']) else ""
        section = str(row['Section']).strip() if pd.notna(row['Section']) else ""
        course_code = str(row['course_code']).strip() if pd.notna(row['course_code']) else ""
        course_name = str(row['course_name']).strip() if pd.notna(row['course_name']) else ""
        credits = str(row['credits']).strip() if pd.notna(row['credits']) else "NA"
        content = str(row['Content']).strip() if pd.notna(row['Content']) else ""

        if course_name and not course_code:
            course_code = "NA"

        if main and 'degree map' not in main.lower():
            current_main = main
            degrre_course = True
            main_groups[main] = True
        else:
            current_main = "Degree Map"
            degrre_course = False
            main_groups[main] = True

        if section and 'degree map' not in (main.lower() if main else ""):
            current_section = section
            sections[section] = True
            main_to_sections[current_main].add(section)
        elif 'degree map' in (main.lower()):
            current_section = "Degree overview"
            sections[current_section] = True
            main_to_sections[current_main].add(current_section)

        elif not section:
            current_section = None  # Prevent section leakage

        if course_code and course_name:
            course_nodes[course_code] = {
                "code": course_code,
                "name": course_name,
                "credits": credits
            }
            # Only add course to section if section is valid in mapping
            if current_section and current_main and current_section in main_to_sections[current_main]:
                if degrre_course:
                    section_to_courses[current_section].add(course_code)
            else:
                print(f"⚠️ Skipping course {course_code} ({course_name}) due to invalid or missing section linkage.")

        if not course_code and not course_name and content and current_section and len(content) >= 11:
            if "Program Description and Career Resources:" not in content and 'For more information on 15 to' not in content \
                    and 'Indiana State University’s priority date for' not in content:
                section_attributes[current_section].append(content)

        if main and 'degree map' in main.lower():
            if section and not course_code and not course_name:
                if "fall" in section.lower() or 'spring' in section.lower():
                    current_term = section
                # year_nodes.add(current_term)
            elif course_code and course_name:
                current_term = section
                course_nodes[course_code] = {
                    "code": course_code,
                    "name": course_name,
                    "credits": credits
                }
                course_year_edges.append((course_code, current_term, course_name, credits))

    with driver.session() as session:
        # session.write_transaction(insert_data, "MERGE (:Program {name: $name})", {"name": program_name.strip()})

        # for main in main_groups:
        #     # session.write_transaction(insert_data, "MERGE (:MainGroup {title: $title})", {"title": main})
        #     session.write_transaction(insert_data, """
        #         MATCH (p:Program {name: $pname})
        #         MERGE (p)-[:HAS_MAIN]->(m:MainGroup {title: $mtitle})
        #     """, {"pname": program_name.strip(), "mtitle": main.strip()})

        for main, section_set in main_to_sections.items():
            for section in section_set:
                combined_content = "\n".join(section_attributes[section]).strip()
                # query = "MERGE (s:Section {name: $name}) SET s.content = $content"
                # attr_dict = {"name": section, "content": combined_content}

                # session.write_transaction(insert_data, query, attr_dict)
                session.write_transaction(insert_data, """
                    MERGE (p:Program {name: $pname})
                    MERGE (p)-[:HAS_MAIN]->(m:MainGroup {title: $main}) 
                    MERGE (m)-[:HAS_SECTION]->(s:Section {name: $section, content: $content})
                """, {"main": main.strip(), "section": section.strip(), "content": combined_content.strip(),
                      "pname": program_name.strip()})

        insert_courses_and_years(session, course_nodes, section_to_courses, course_year_edges, program_name,
                                 main_to_sections)

    print(f"✅ Imported: {program_name}")


# === Loop Through Excel Files ===
for filename in os.listdir(DIRECTORY_PATH):
    if filename.endswith(".xlsx"):
        file_path = os.path.join(DIRECTORY_PATH, filename)
        program_name = os.path.splitext(filename)[0]
        process_excel(file_path, program_name)

driver.close()
print("🚀 All Excel files imported into Neo4j.")
