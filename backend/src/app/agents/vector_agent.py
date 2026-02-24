from sqlmodel import Session
from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repo import VectorRepo
from app.core.config import settings
from app.agents.state import AgentState


class VectorRetrievalAgent:
    def __init__(self):
        self.embedder = EmbeddingService()

    def run(self, session: Session, state: AgentState) -> AgentState:
        q = state["query"]
        repo = VectorRepo(session)

        qvec = self.embedder.embed_query(q)
        hits = repo.vector_search(qvec, top_k=settings.VECTOR_TOP_K)

        packed = []
        for chunk_id, score in hits:
            ch = repo.get_chunk(chunk_id)
            if not ch:
                continue
            packed.append({
                "chunk_id": ch.id,
                "file_id": ch.file_id,
                "score": score,
                "source_page": ch.source_page,
                "text": ch.text[:1200],
            })

        state["vector_hits"] = packed
        return state