import json
from sqlmodel import Session
from app.com.db.session import engine
from app.schema.models.sql_template import SqlTemplate

def seed():
    with Session(engine) as s:
        existing = s.get(SqlTemplate, "yield_summary")
        if not existing:
            t = SqlTemplate(
                id="yield_summary",
                name="수율 요약",
                description="기간별 수율을 요약합니다.",
                sql_text="""
                    -- 예시: 실제 테이블/컬럼에 맞게 수정
                    SELECT day, yield
                    FROM yield_daily
                    WHERE day BETWEEN :from_date AND :to_date
                    ORDER BY day
                """,
                params_json=json.dumps({"required": ["from_date", "to_date"]}, ensure_ascii=False),
            )
            s.add(t)

        s.commit()

if __name__ == "__main__":
    seed()