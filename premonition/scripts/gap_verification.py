import io, sys, sqlite3, os, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

base_dir = Path("C:/Users/S. SANJAYKUMAR/Desktop/PROJECTS/Internship_Project/premonition")
logs_dir = base_dir / "logs"
db_path = logs_dir / "agent_memory.db"
memory_sqlite = base_dir / "premonition_memory.sqlite"

print("--- OUTCOME MEMORY ---")
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM outcome_memory")
    count = c.fetchone()[0]
    print(f"OutcomeMemory Row Count: {count}")
    
    if count > 0:
        c.execute("SELECT * FROM outcome_memory ORDER BY rowid DESC LIMIT 3")
        for row in c.fetchall():
            print(f"Example Verified Action: {row}")
            
    conn.close()
except Exception as e:
    print(f"Error reading DB: {e}")

print("\n--- OLLAMA SUMMARIES ---")
try:
    conn = sqlite3.connect(memory_sqlite)
    c = conn.cursor()
    c.execute("SELECT data FROM memory WHERE collection='decision_memory' ORDER BY updated_at DESC LIMIT 200")
    found = False
    for row in c.fetchall():
        try:
            data = json.loads(row[0])
            decision = data.get("decision", {})
            if "autonomous_summary" in decision:
                print("Found Autonomous Ollama Summary:")
                print(decision["autonomous_summary"])
                found = True
                break
        except Exception:
            pass
    if not found:
        print("No autonomous Ollama summary found yet.")
    conn.close()
except Exception as e:
    print(f"Error reading memory sqlite: {e}")
