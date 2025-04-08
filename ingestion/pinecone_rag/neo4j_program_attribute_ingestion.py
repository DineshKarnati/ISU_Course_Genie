import os
import pandas as pd
from neo4j import GraphDatabase

# === Config ===
DIRECTORY_PATH = os.getcwd() + "/short_data"  # Path to your directory of Excel files
NEO4J_URI="neo4j+s://5ba1c10e.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="jbqO7pkaBdxiDnQC8lTED24a77xSBlRYgtgV0_ZbzQk"

# === Neo4j Setup ===
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def update_program_attributes(tx, program_name, learning_outcomes, total_credits):
    total_credits = "Total credits for the program " + program_name + " is " + str(total_credits).strip()
    tx.run("""
        MATCH (p:Program {name: $program_name})
        SET p.learning_outcomes = $learning_outcomes,
            p.total_credits = $total_credits
    """, {
        "program_name": program_name,
        "learning_outcomes": learning_outcomes,
        "total_credits": total_credits
    })


def process_metadata_file(file_path):
    df = pd.read_excel(file_path)

    for _, row in df.iterrows():
        program_name = str(row["Program"]).strip()
        learning_outcomes = str(row["Learningoutcomes"]).strip()
        learning_outcomes = learning_outcomes.replace(str(row["Total_Credits"]), "").replace("For more information click here.", "").strip()
        total_credits = str(row["Total_Credits"]).replace("(", "").replace(")", "").strip()

        with driver.session() as session:
            session.write_transaction(
                update_program_attributes,
                program_name,
                learning_outcomes,
                total_credits
            )
        print(f"✅ Updated: {program_name}")


# === Loop Through Metadata Files ===
for filename in os.listdir(DIRECTORY_PATH):
    if filename.endswith(".xlsx"):
        file_path = os.path.join(DIRECTORY_PATH, filename)
        process_metadata_file(file_path)

driver.close()
print("🚀 All program attributes updated in Neo4j.")
