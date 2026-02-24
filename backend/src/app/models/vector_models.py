from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from pgvector.sqlalchemy import Vector

class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    content_type: str = "application/pdf"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: int = Field(index=True)
    chunk_index: int
    text: str

    # pgvector embedding: dimensions는 사용하는 모델에 맞춰주세요
    # text-embedding-3-small: 1536
    embedding: Optional[list[float]] = Field(
        sa_type=Vector(1536),
        default=None
    )

    # citations 용
    source_page: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)