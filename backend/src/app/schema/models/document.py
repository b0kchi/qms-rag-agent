from datetime import datetime
from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    file_name: str
    source_type: str  # "pdf" | "excel"
    created_at: datetime = Field(default_factory=datetime.utcnow)