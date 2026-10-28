
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DB = ROOT / "ecommerce.db"
SQL_FILE = ROOT / "sql" / "analytics.sql"

sql_text = SQL_FILE.read_text(encoding="utf-8")

with sqlite3.connect(DB) as conn:
    queries = [q.strip() for q in sql_text.split(";") if q.strip()]

    for index, query in enumerate(queries, start=1):
        print(f"\n--- Query {index} ---")
        cursor = conn.execute(query)

        if cursor.description:
            columns = [item[0] for item in cursor.description]
            print(" | ".join(columns))

            for row in cursor.fetchall():
                print(" | ".join(str(value) for value in row))
