from typing import Any, Dict, List
from sqlmodel import Session
from sqlalchemy import text

class SQLRepo:
    def __init__(self, session: Session):
        self.session = session

    def run(self, sql_text_str: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        q = text(sql_text_str)
        rows = self.session.exec(q, params).mappings().all()
        return [dict(r) for r in rows]