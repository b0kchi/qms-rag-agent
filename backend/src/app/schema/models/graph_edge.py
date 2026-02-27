# graph_edge.py
from sqlmodel import SQLModel, Field


class GraphEdge(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    src_id: str = Field(index=True)
    dst_id: str = Field(index=True)
    rel: str
    props_json: str | None = None