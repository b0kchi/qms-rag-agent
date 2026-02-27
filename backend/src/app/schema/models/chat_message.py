from datetime import datetime

from sqlmodel import SQLModel, Field


class ChatMessageModel(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(foreign_key="chat_sessions.id", index=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
