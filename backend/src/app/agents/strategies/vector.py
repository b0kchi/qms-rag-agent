import json
from sqlmodel import Session
from app.agents.strategies.base import Strategy
from app.agents.state import AgentState, RetrievalResult
from app.com.services.embedding_service import EmbeddingService
from app.com.repositories.vector_repo import VectorRepo
from app.com.config.settings import settings


class VectorStrategy(Strategy):
    key = "vector"

    def __init__(self):
        self.embedder = EmbeddingService()

    def run(self, session: Session, state: AgentState, **kwargs) -> RetrievalResult:
        repo = VectorRepo(session)
        qvec = self.embedder.embed_query(state.query_normalized)

        document_id = kwargs.get("document_id")
        hits = repo.vector_search(qvec, top_k=settings.VECTOR_TOP_K, document_id=document_id, include_distance=True)

        payload = []
        citations = []
        for item in hits:
            ch = item["chunk"]
            sim = float(item["similarity"])
            dist = float(item["distance"])
            payload.append(
                {
                    "chunk_id": ch.id,
                    "text": ch.text,
                    "score": round(sim, 6),
                    "distance": round(dist, 6),
                    "document_id": ch.document_id,
                }
            )
            meta = json.loads(ch.meta_json) if ch.meta_json else {}
            citations.append({"document_id": ch.document_id, "chunk_id": ch.id, **meta})

        return RetrievalResult(kind="chunks", payload=payload, citations=citations)