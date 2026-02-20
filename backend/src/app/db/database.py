# 데이터베이스 연결 및 세션 관리 모듈

from sqlmodel import SQLModel, create_engine, Session # SQLModel은 데이터베이스 테이블을 정의하기 위한 모델들의 부모 클래스, 
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False) # create_engine은 DB에 접속하기 위한 엔진 객체를 만드는 함수 

def init_db() -> None:
    SQLModel.metadata.create_all(engine) # create_all(engine) 메타데이터에 등록된 테이블들을 DB에 실제 생성하라는 명령, 테이블변경은 자동 반영 안 됨.

def get_session():
    with Session(engine) as session:
        yield session