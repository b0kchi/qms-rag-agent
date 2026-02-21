'''
    LangGraph의 전체 워크플로우를 관통하는 공유 상태 객체
'''

from typing import TypedDict, Optional, List, Any, Dict 
# TypedDict: 딕셔너리지만 키와 타입을 명시적으로 정의할 수 있는 타입
# Optional: 값이 있을 수도 없을 수도 있음

class AgentState(TypedDict, total=False): # total=False : 이 딕셔너리의 모든 키를 선택(optional)으로 만든다는 의미, 기본값은 True
    # inputs
    request_text: str # 사용자가 입력한 질문
    user_email: Optional[str] # 보고서 발송용 이메일
    uploaded_filename: Optional[str] # 업로드한 파일 이름
    uploaded_mime: Optional[str]
    uploaded_bytes: Optional[bytes] # 업로드 파일 원본 바이트

    # extracted evidence
    evidence_text: Optional[str] # RAG 검색 결과 텍스트

    # agentic decisions
    action: Optional[str]  # "db_lookup" | "ask_user" | "reject": SQL 실행, 추가 질문 필요, 요청 거부
    selected_template_ids: List[int] # 선택된 SQL 템플릿 ID 목록
    params: Dict[str, Any] # SQL 실행에 필요한 파라미터

    # execution results
    phase1_results: List[Any]
    phase2_results: List[Any]

    # adaptive controls
    quality_score: float
    retry_count: int
    max_retry: int
    next_fix: Optional[str]  # 다음 수정 전략 "add_queries" | "refine_params" | "ask_user" | "finalize"

    # outputs / persistence
    run_id: Optional[int]
    final_answer: Optional[str]
    report_pdf_path: Optional[str]
    email_sent: bool