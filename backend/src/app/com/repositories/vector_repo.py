from sqlmodel import Session, select
from sqlalchemy import func
from app.schema.models.chunk import Chunk


class VectorRepo:
    def __init__(self, session: Session):
        self.session = session

    def vector_search(
        self,
        qvec: list[float],
        top_k: int = 6,
        document_id: str | None = None,
        include_distance: bool = True,
    ):
        """
        returns:
          include_distance=True:
            [{"chunk": Chunk, "distance": float, "similarity": float}, ...]
          include_distance=False:
            [{"chunk": Chunk, "similarity": float}, ...]
        """
        dist_expr = Chunk.embedding.cosine_distance(qvec).label("distance")
        stmt = select(Chunk, dist_expr)

        if document_id:
            stmt = stmt.where(Chunk.document_id == document_id)

        stmt = stmt.order_by(dist_expr).limit(top_k)

        rows = self.session.exec(stmt).all()

        out = []
        for ch, dist in rows:
            dist_f = float(dist) if dist is not None else 1.0
            sim = 1.0 - dist_f  # cosine_distance 범위 대략 [0,2]일 수 있어 clamp 권장
            if sim < -1.0:
                sim = -1.0
            if sim > 1.0:
                sim = 1.0
            item = {"chunk": ch, "similarity": sim}
            if include_distance:
                item["distance"] = dist_f
            out.append(item)
        return out