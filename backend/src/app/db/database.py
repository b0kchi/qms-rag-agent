from sqlmodel import SQLModel, create_engine, Session
from ..core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True) # DATABASE_URL을 기반으로 PostgreSQL(DB) 연결을 관리하는 엔진 생성

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
