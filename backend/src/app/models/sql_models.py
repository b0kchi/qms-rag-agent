from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class SQLTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str
    sql_text: str
    phase: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)