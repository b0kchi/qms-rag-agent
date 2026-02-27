from app.agents.state import RetrievalResult


class LLMAnswerer:
    def answer(self, query: str, retrieval: RetrievalResult) -> str:
        # 운영: LLM 호출 + citations 기반 근거 답변 생성
        if retrieval.kind == "chunks":
            snippets = [c["text"][:200] for c in (retrieval.payload or [])][:3]
            joined = "\n\n".join(f"- {s}" for s in snippets)
            return f"[STUB ANSWER]\n질문: {query}\n\n근거(상위 3개):\n{joined}"
        if retrieval.kind == "sql_rows":
            return f"[STUB ANSWER]\n질문: {query}\n\nSQL 결과(상위 일부): {str(retrieval.payload)[:500]}"
        return f"[STUB ANSWER]\n질문: {query}\n\n근거가 부족합니다."