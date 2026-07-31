import sys
sys.path.insert(0, '.')
from database.connection import Base
import knowledge_engine.database.models
print('Tables in metadata:')
for t in sorted(Base.metadata.tables.keys()):
    print(f'  {t}')
has_entities = 'entities' in Base.metadata.tables
print(f'entities in metadata: {has_entities}')
