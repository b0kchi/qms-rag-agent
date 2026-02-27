from sqlmodel import Session, select
from app.schema.models.chunk import Chunk


class ChunkRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, chunks: list[Chunk]) -> None:
        self.session.add_all(chunks)
        self.session.commit()

    def get(self, chunk_id: str) -> Chunk | None:
        return self.session.get(Chunk, chunk_id)

    def list_by_document(self, document_id: str, limit: int = 100):
        stmt = select(Chunk).where(Chunk.document_id == document_id).limit(limit)
        return self.session.exec(stmt).all()