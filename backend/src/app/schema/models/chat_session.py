from datetime import datetime

from sqlmodel import SQLModel, Field


class ChatSessionModel(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: str = Field(primary_key=True, index=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
