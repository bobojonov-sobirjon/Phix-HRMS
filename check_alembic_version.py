from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    versions = [row[0] for row in result]
    print("Current alembic versions in database:", versions)

