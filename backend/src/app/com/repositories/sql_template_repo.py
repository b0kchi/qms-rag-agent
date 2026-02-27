from sqlmodel import Session, select
from app.schema.models.sql_template import SqlTemplate


class SqlTemplateRepo:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self):
        return self.session.exec(select(SqlTemplate)).all()

    def get(self, template_id: str) -> SqlTemplate | None:
        return self.session.get(SqlTemplate, template_id)