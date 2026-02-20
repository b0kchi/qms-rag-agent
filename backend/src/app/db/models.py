# 데이터베이스 스키마 정의 파일

from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class SQLTemplate(SQLModel, table=True):
    __tablename__ = "sql_templates"
    id: Optional[int] = Field(default=None, primary_key=True) # 객체 생성시 id가 없을 수 있으므로 Optional, 그러나 실제 db에서는 null을 허용하지 않는다. primary_key=True는 db에서 not null + auto increment.
    name: str
    phase: int  # 1 or 2, 쿼리 실행 단계를 나누는 용도로 사용 예정. 
    sql_text: str
    description: Optional[str] = None
    is_active: bool = Field(default=True)

class AnalysisRun(SQLModel, table=True):
    __tablename__ = "analysis_runs"
    id: Optional[int] = Field(default=None, primary_key=True)
    request_text: str # 사용자가 입력한 질문
    evidence_text: Optional[str] = None # RAG로 검색된 근거 텍스트 또는 LLM이 추출한 근거 요약
    action: Optional[str] = None # 어떤 행동을 했는지
    selected_template_ids: Optional[str] = None  # 실행에 사용된 SQL 템플릿 ID 목록
    quality_score: Optional[float] = None # 결과 품질 점수
    final_answer: Optional[str] = None # LLM 최종 응답
    report_pdf_path: Optional[str] = None # 생성된 PDF 보고서 경로
    email_sent: bool = Field(default=False) # 이메일 발송 여부
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc)) # default_factory는 기본값을 만드는 함수를 지정, 객체가 생성될 때마다 함수호출하여 새 값을 넣음 