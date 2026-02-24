from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class GraphNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(index=True)      # 예: "LOT", "EQUIP", "DEFECT", "MATERIAL"
    name: str = Field(index=True)       # 예: "LOT_A", "ETCH-01"
    props_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GraphEdge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    src_node_id: int = Field(index=True)
    dst_node_id: int = Field(index=True)
    relation: str = Field(index=True)   # 예: "CAUSES", "ASSOCIATED_WITH", "PRODUCED_ON"
    weight: float = 1.0
    evidence_chunk_id: Optional[int] = None  # 문서 근거 chunk 연결
    created_at: datetime = Field(default_factory=datetime.utcnow)