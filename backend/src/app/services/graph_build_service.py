import re
import json
from sqlmodel import Session, select
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.models.graph_models import GraphNode, GraphEdge
from app.models.vector_models import Chunk

ENTITY_PATTERNS = {
    "LOT": r"\bLOT[_-]?[A-Z0-9]+\b",
    "EQUIP": r"\b(EQP|EQUIP)[_-]?[A-Z0-9]+\b",
    "DEFECT": r"\bDEFECT[_-]?[A-Z0-9]+\b",
    "LINE": r"\bLINE[_-]?[A-Z0-9]+\b",
}

class GraphBuildService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )

        # ⚠️ ChatPromptTemplate은 str.format 기반이므로
        # JSON 예시의 { } 는 반드시 {{ }} 로 이스케이프해야 함.
        self.rel_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You extract entity relations from manufacturing/QMS text.\n"
             "Return JSON array ONLY.\n"
             "Each item schema:\n"
             "{{\"src\":{{\"label\":\"LOT|EQUIP|DEFECT|LINE|MATERIAL|PROCESS|PARAM\",\"name\":\"...\"}},"
             "\"relation\":\"CAUSES|ASSOCIATED_WITH|PRODUCED_ON|AFFECTS\","
             "\"dst\":{{\"label\":\"LOT|EQUIP|DEFECT|LINE|MATERIAL|PROCESS|PARAM\",\"name\":\"...\"}},"
             "\"confidence\":0.0}}\n"
             "If none, return []."),
            ("human", "TEXT:\n{chunk}\n")
        ])

    def _upsert_node(self, session: Session, label: str, name: str) -> GraphNode:
        stmt = select(GraphNode).where(GraphNode.label == label, GraphNode.name == name)
        node = session.exec(stmt).first()
        if node:
            return node
        node = GraphNode(label=label, name=name)
        session.add(node)
        session.commit()
        session.refresh(node)
        return node

    def build_from_file(self, session: Session, file_id: int, max_chunks: int = 120):
        stmt = select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.chunk_index).limit(max_chunks)
        chunks = list(session.exec(stmt))

        # 1) regex 엔터티 node 생성
        for ch in chunks:
            for label, pat in ENTITY_PATTERNS.items():
                for m in re.findall(pat, ch.text):
                    self._upsert_node(session, label, m)

        # 2) LLM으로 관계 추출 → edge 생성
        for ch in chunks:
            # 텍스트가 너무 짧으면 스킵(잡음 방지)
            if not (ch.text or "").strip():
                continue

            msg = self.rel_prompt.format_messages(chunk=ch.text[:4000])  # 너무 길면 제한
            res = self.llm.invoke(msg).content

            try:
                items = json.loads(res)
            except Exception:
                continue

            if not isinstance(items, list):
                continue

            for it in items:
                try:
                    s = it["src"]; d = it["dst"]
                    rel = it["relation"]
                    conf = float(it.get("confidence", 0.6))

                    src_node = self._upsert_node(session, s["label"], s["name"])
                    dst_node = self._upsert_node(session, d["label"], d["name"])

                    edge = GraphEdge(
                        src_node_id=src_node.id,
                        dst_node_id=dst_node.id,
                        relation=rel,
                        weight=conf,
                        evidence_chunk_id=ch.id
                    )
                    session.add(edge)
                except Exception:
                    continue

        session.commit()