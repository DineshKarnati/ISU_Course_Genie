full_text = """CREATE FULLTEXT INDEX entityIndex IF NOT EXISTS
FOR (n:Program | Course)
ON EACH [n.name, n.code];
"""