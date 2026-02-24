from typing import List, Optional
from sqlmodel import Session, select
from app.models.sql_models import SQLTemplate

class TemplateRepo:
    def __init__(self, session: Session):
        self.session = session

    def list_active(self) -> List[SQLTemplate]:
        stmt = select(SQLTemplate).where(SQLTemplate.is_active == True)
        return list(self.session.exec(stmt))

    def get_by_name(self, name: str) -> Optional[SQLTemplate]:
        stmt = select(SQLTemplate).where(SQLTemplate.name == name)
        return self.session.exec(stmt).first()