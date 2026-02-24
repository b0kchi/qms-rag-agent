from typing import List, Optional, Tuple
from sqlmodel import Session, select
from sqlalchemy import text
from app.models.vector_models import Chunk

class VectorRepo:
    def __init__(self, session: Session):
        self.session = session

    def list_chunks_by_file(self, file_id: int) -> List[Chunk]:
        stmt = select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.chunk_index)
        return list(self.session.exec(stmt))

    def get_chunk(self, chunk_id: int) -> Optional[Chunk]:
        return self.session.get(Chunk, chunk_id)

    def _to_vector_literal(self, vec: list[float]) -> str:
        # pgvector vector literal: '[0.1,0.2,...]'
        # float -> str 변환 시 과도한 자리수는 성능에만 영향. 8~10자리면 충분
        return "[" + ",".join(f"{x:.10f}" for x in vec) + "]"

    def vector_search(self, query_vec: list[float], top_k: int = 8) -> List[Tuple[int, float]]:
        qvec_str = self._to_vector_literal(query_vec)

        sql = text("""
            SELECT id, (1 - (embedding <=> (:qvec)::vector)) AS score
            FROM chunk
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> (:qvec)::vector
            LIMIT :k;
        """)

        rows = self.session.exec(sql, params={"qvec": qvec_str, "k": top_k}).all()
        return [(int(r[0]), float(r[1])) for r in rows]