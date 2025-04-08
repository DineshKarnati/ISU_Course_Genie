import openai
from pinecone import Pinecone
from typing import List, Tuple
import os
from dotenv import load_dotenv
load_dotenv() # Load environment variables
openai.api_key= os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY= os.getenv('PINECONE_API_KEY')
INDEX_NAME= os.getenv('INDEX_NAME')
NAMESPACE= os.getenv('NAMESPACE')


# client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


def rephrase_query(query: str, chat_history: str = "") -> str:
    prompt = (
        "You are an academic query rephraser. Rephrase the following query to be structured and detailed, "
        "keeping in mind the previous question for resolving pronouns or vague references.\n\n"
        f"Previous Query: {chat_history}\n"
        f"Current Query: {query}\n\n"
        "Only rephrase the current query, but use the previous query to resolve coreferences or ambiguity."
    )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that rewrites academic queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()



def generate_embedding(text: str) -> List[float]:
    return openai.embeddings.create(
        input=text, model="text-embedding-3-small"
    ).data[0].embedding


# --- Block 1 Function ---
def initial_program_matches(user_query: str, top_k: int = 10, chat_history: str = "") -> Tuple[str, List[str]]:
    """Returns rephrased query and list of matching programs."""
    try:
        rephrased = rephrase_query(user_query, chat_history=chat_history)
        embedding = generate_embedding(rephrased)
        print("🧪 Rephrased inside initial_program_matches:", rephrased)  # <--- ADD THIS
        results = index.query(vector=embedding, top_k=top_k, namespace=NAMESPACE, include_metadata=True)

        programs = list(
            {match["metadata"].get("program") for match in results["matches"] if "program" in match["metadata"]})

        return rephrased, programs

    except Exception as e:
        return f"Error during initial search: {e}", []


# def final_response_from_selection(user_query: str, rephrased_query: str, selected_program: str, top_k: int = 10) -> str:
#     """Performs refined search and generates GPT-4 response based on selected program."""
#     try:
#         # Step 1: Refine the query to be program-specific
#         refined_query = f"Retrieve information about {rephrased_query} specifically in the {selected_program} program."
#
#         # Step 2: Generate new embedding
#         embedding = generate_embedding(refined_query)
#
#         # Step 3: Query Pinecone again
#         results = index.query(vector=embedding, top_k=top_k, namespace=NAMESPACE, include_metadata=True)
#
#         context = " ".join([match["metadata"]["text"] for match in results["matches"] if "text" in match["metadata"]])
#
#         # Step 4: Final GPT-4 prompt
#         prompt = (
#             f"Context: {context}\n\n"
#             f"User Query: {user_query}\n\n"
#             f"Selected Program: {selected_program}\n\n"
#             "Provide a clear, structured, academic response using the context above."
#         )
#
#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a helpful academic advisor."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )
#
#         return response.choices[0].message.content.strip()
#
#     except Exception as e:
#         return f"Error during final response generation: {e}"


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts using OpenAI's embedding model."""
    embeddings = []
    try:
        for text in texts:
            response = openai.embeddings.create(
                input=text, model="text-embedding-3-small"
            ).data[0].embedding
            embedding = response

            # Ensure the embedding has the correct dimensionality (1536 dimensions)
            if len(embedding) == 1536:
                embeddings.append(embedding)
            else:
                print(f"Unexpected embedding dimensions: {len(embedding)} for text: {text[:50]}...")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
    return embeddings


def final_response_from_selection(user_query: str, rephrased_query: str, selected_program: str) -> str:
    try:
        refined_query = f"{rephrased_query} specifically in the {selected_program} program."

        refined_embedding = generate_embeddings([refined_query])[0]

        results = index.query(vector=refined_embedding, top_k=10, namespace=NAMESPACE, include_metadata=True)

        context = " ".join([match["metadata"]["text"] for match in results["matches"]])

        prompt = f"""
        Context: {context}

        Original Query: {user_query}
        Selected Program: {selected_program}

        Please provide a detailed, concise, structured academic response based on the context above.
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful academic advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I encountered an error while generating the final response. Error: {e}"
