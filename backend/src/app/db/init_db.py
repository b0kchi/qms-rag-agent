from sqlalchemy import text
from sqlmodel import SQLModel
from app.db.engine import engine

def init_db():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(engine)