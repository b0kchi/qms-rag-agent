from sqlmodel import Session
from app.agents.strategies.base import Strategy
from app.agents.state import AgentState, RetrievalResult
from app.com.repositories.vector_repo import VectorRepo
from app.com.services.embedding_service import EmbeddingService
from app.com.config.settings import settings
from app.com.utils.text import extract_keywords, overlap_score


class HybridStrategy(Strategy):
    key = "hybrid"

    def __init__(self):
        self.embedder = EmbeddingService()

    def run(self, session: Session, state: AgentState, **kwargs) -> RetrievalResult:
        """
        Hybrid MVP:
        - 벡터 검색을 top_k의 3배로 넓게 뽑고
        - 질의 키워드 overlap로 rerank하여 상위 top_k만 반환
        """
        repo = VectorRepo(session)
        qvec = self.embedder.embed_query(state.query_normalized)
        document_id = kwargs.get("document_id")

        wide_k = max(settings.VECTOR_TOP_K * 3, settings.VECTOR_TOP_K)
        hits = repo.vector_search(qvec, top_k=wide_k, document_id=document_id, include_distance=True)

        keywords = extract_keywords(state.query_normalized, max_n=12)

        enriched = []
        for item in hits:
            ch = item["chunk"]
            vec_sim = float(item["similarity"])
            kw = overlap_score(keywords, ch.text)
            # 가중치: 키워드 0.35 + 벡터 0.65 (초기값)
            final = 0.65 * vec_sim + 0.35 * kw
            enriched.append((final, vec_sim, kw, ch, item.get("distance")))

        enriched.sort(key=lambda x: x[0], reverse=True)
        top = enriched[: settings.VECTOR_TOP_K]

        payload = []
        citations = []
        for final, vec_sim, kw, ch, dist in top:
            payload.append({
                "chunk_id": ch.id,
                "document_id": ch.document_id,
                "text": ch.text,
                "score": round(final, 6),
                "vec_similarity": round(vec_sim, 6),
                "kw_overlap": round(kw, 6),
                "distance": None if dist is None else float(dist),
            })
            citations.append({"document_id": ch.document_id, "chunk_id": ch.id})

        return RetrievalResult(kind="chunks", payload=payload, citations=citations)
    

    