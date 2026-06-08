import sqlite3
import json

db_path = "premonition_memory.sqlite"

def analyze_loop():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r["name"] for r in cursor.fetchall()]
    print("Tables found:", tables)
    
    if 'memory' in tables:
        print("\n--- AGENTIC LOOP MEMORY ---")
        cursor.execute("SELECT * FROM memory")
        for row in cursor.fetchall()[:5]:
            print(dict(row))
            print("-" * 40)

    conn.close()

if __name__ == "__main__":
    analyze_loop()
