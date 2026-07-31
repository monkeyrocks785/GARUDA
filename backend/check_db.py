import sqlite3
db = sqlite3.connect('storage/garuda.db')
c = db.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Has registered_models:", 'registered_models' in tables)
print("Has analysis_jobs:", 'analysis_jobs' in tables)
print("Has detections:", 'detections' in tables)
print("Has analysis_history:", 'analysis_history' in tables)
db.close()
