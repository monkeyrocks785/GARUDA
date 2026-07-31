"""Create intelligence engine tables in production database."""
# Import main to get all models registered
from main import app
from database.connection import Base, engine

intelligence_tables = [t for t in Base.metadata.tables if 'registered' in t or 'analysis_job' in t or 'detection' in t or 'analysis_history' in t]
print(f"Intelligence tables to create: {intelligence_tables}")

# Create only intelligence tables
for table_name in intelligence_tables:
    table = Base.metadata.tables[table_name]
    table.create(bind=engine, checkfirst=True)
    print(f"Created/verified: {table_name}")

print("All intelligence tables created successfully")
