#  사전 정의된 SQL 템플릿을 조회하고 실행하는 서비스 레이어 함수 
from typing import Any, Dict, List, Optional
from sqlalchemy import text # text: Raw SQL 문자열을 실행 가능하게 만들어주는 래퍼
from sqlmodel import Session, select
from src.app.db.models import SQLTemplate

def list_active_templates(session: Session, phase: Optional[int] = None) -> List[SQLTemplate]:
    stmt = select(SQLTemplate).where(SQLTemplate.is_active == True)
    if phase is not None:
        stmt = stmt.where(SQLTemplate.phase == phase)
    return session.exec(stmt).all()

def run_template(session: Session, template_id: int, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    tpl = session.get(SQLTemplate, template_id)
    if not tpl or not tpl.is_active:
        return {"template_id": template_id, "error": "template_not_found_or_inactive"}

    try:
        rows = session.exec(text(tpl.sql_text), params or {}).all()
        # rows는 Row 객체일 수 있어 dict로 변환
        out_rows = []
        for r in rows[:200]:  # 안전 상한
            try:
                out_rows.append(dict(r._mapping))
            except Exception:
                out_rows.append({"value": str(r)})
        return {"template_id": tpl.id, "name": tpl.name, "phase": tpl.phase, "rows": out_rows, "row_count": len(rows)}
    except Exception as e:
        return {"template_id": tpl.id, "name": tpl.name, "phase": tpl.phase, "error": str(e)}