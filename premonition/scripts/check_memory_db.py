#!/usr/bin/env python3
"""Check agent memory DB for real runtime decisions."""
import io, sys, sqlite3, glob, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

base = r"C:\Users\S. SANJAYKUMAR\Desktop\PROJECTS\Internship_Project\premonition"
dbs = glob.glob(f"{base}/**/*.db", recursive=True) + glob.glob(f"{base}/**/*.sqlite", recursive=True)
print("=== SQLite Databases Found ===")
for d in dbs:
    print(f"  {d}")

print()
for db in dbs:
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        print(f"DB: {db}")
        print(f"  Tables: {tables}")
        for t in tables:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            n = c.fetchone()[0]
            print(f"  [{t}]: {n} rows")
            if n > 0 and t in ("decision_memory", "alert_memory", "patient_memory", "memory"):
                c.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 3")
                rows = c.fetchall()
                for r in rows:
                    row_str = str(r)[:200]
                    print(f"    {row_str}")
        conn.close()
    except Exception as e:
        print(f"  Error reading {db}: {e}")
    print()
