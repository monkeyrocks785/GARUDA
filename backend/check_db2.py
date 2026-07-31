import sys, os
os.chdir(r'F:\Mayank Garg\PROJECTS\Personal Projects\GARUDA\backend')
sys.path.insert(0, '.')

# Remove old test.db
if os.path.exists('test.db'):
    os.remove('test.db')

from database.connection import Base, engine, init_db
import knowledge_engine.database.models
import intelligence_engine.database.models

# This is what the app lifespan does
init_db()

# Now check if entities table exists
import sqlite3
conn = sqlite3.connect('test.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'")
result = cursor.fetchone()
print(f'entities table exists: {result is not None}')
conn.close()
