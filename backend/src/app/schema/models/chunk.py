from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Index
from app.com.config.settings import settings

# pgvector 타입
from pgvector.sqlalchemy import Vector


class Chunk(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    document_id: str = Field(index=True)

    text: str
    meta_json: Optional[str] = Field(default=None)  # page/sheet 등 JSON 문자열로 저장(간단 스켈레톤)

    # SQLModel이 pgvector를 직접 모르니 SQLAlchemy Column로 심기
    embedding: list[float] = Field(sa_column=Column(Vector(settings.EMBEDDING_DIM), nullable=False))


# 벡터 인덱스(IVFFLAT 등은 운영에서 추가 권장, 스켈레톤은 선언만)
Index("ix_chunks_document_id", Chunk.document_id)