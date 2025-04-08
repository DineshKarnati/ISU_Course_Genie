import os
import pandas as pd
from neo4j import GraphDatabase

# === Config ===
DIRECTORY_PATH = "./program_files"  # Replace with your folder path
NEO4J_URI="neo4j+s://5ba1c10e.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="jbqO7pkaBdxiDnQC8lTED24a77xSBlRYgtgV0_ZbzQk"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def update_course_attributes(tx, code, name, attributes):
    set_clauses = []
    params = {"code": code}

    for key, value in attributes.items():
        if value != 'nan':  # Only update if value is non-empty
            clause = f"c.{key} = ${key}"
            set_clauses.append(clause)
            params[key] = value

    if not set_clauses:
        return  # Nothing to update

    query = f"""
    MATCH (c:Course {{code: $code}})
    SET {', '.join(set_clauses)}
    """
    tx.run(query, params)


def process_excel(file_path):
    df = pd.read_excel(file_path)

    for _, row in df.iterrows():
        course_code = str(row.get("Course Code", "")).strip()
        course_name = str(row.get("Course Name", "")).strip()

        if not course_code or not course_name:
            continue  # Skip invalid entries

        # Collect only non-empty fields
        attributes = {
            "credits": str(row.get("Credits", "")).strip(),
            "description": str(row.get("Description", "")).strip(),
            "note": str(row.get("Note", "")).strip(),
            "prerequisites": str(row.get("Prerequisites", "")).strip(),
            "additional_info": str(row.get("Additional Information", "")).strip(),
            "corequisites": str(row.get("Co-requisites", "")).strip(),
            "course_fee": str(row.get("Course Fee", "")).strip()
        }

        with driver.session() as session:
            session.write_transaction(update_course_attributes, course_code, course_name, attributes)


# === Loop through all Excel files in folder ===
for filename in os.listdir(DIRECTORY_PATH):
    if filename.endswith(".xlsx") :
        file_path = os.path.join(DIRECTORY_PATH, filename)
        print(f"📘 Processing: {filename}")
        process_excel(file_path)

driver.close()
print("✅ All course nodes updated successfully.")
