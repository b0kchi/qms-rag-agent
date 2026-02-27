# graph_node.py
from sqlmodel import SQLModel, Field


class GraphNode(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    label: str
    props_json: str | None = None