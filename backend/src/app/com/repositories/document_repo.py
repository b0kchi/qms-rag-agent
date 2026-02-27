from sqlmodel import Session
from app.schema.models.document import Document


class DocumentRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, doc: Document) -> None:
        self.session.add(doc)
        self.session.commit()

    def get(self, doc_id: str) -> Document | None:
        return self.session.get(Document, doc_id)