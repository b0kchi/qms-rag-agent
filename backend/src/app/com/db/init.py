from sqlmodel import SQLModel
from app.com.db.session import engine

# 모델 import (테이블 생성에 필요)
from app.schema.models.document import Document  # noqa: F401
from app.schema.models.chunk import Chunk  # noqa: F401
from app.schema.models.sql_template import SqlTemplate  # noqa: F401
from app.schema.models.graph_node import GraphNode  # noqa: F401
from app.schema.models.graph_edge import GraphEdge  # noqa: F401
from app.schema.models.chat_session import ChatSessionModel  # noqa: F401
from app.schema.models.chat_message import ChatMessageModel  # noqa: F401


def init_db():
    SQLModel.metadata.create_all(engine)
