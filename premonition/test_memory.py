import sqlite3

db_path = r'C:\Users\S. SANJAYKUMAR\Desktop\PROJECTS\Internship_Project\premonition\logs\agent_memory.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

agents = set()
for t in tables:
    table_name = t[0]
    cursor.execute(f"PRAGMA table_info({table_name});")
    cols = [col[1] for col in cursor.fetchall()]
    if 'agent_name' in cols:
        cursor.execute(f"SELECT DISTINCT agent_name FROM {table_name}")
        for row in cursor.fetchall():
            agents.add(row[0])
            
print("=== COMPLETE AGENT EXECUTION TRACE ===")
for a in agents:
    print(a)
    
conn.close()
