from dataclasses import dataclass
from app.agents.state import RetrievalResult
from app.com.config.settings import settings

@dataclass
class ValidationDecision:
    ok: bool
    issues: list[str]
    should_retry: bool
    retry_with_strategy: str | None = None
    ask_user: str | None = None

class RetrievalValidator:
    def validate(self, result: RetrievalResult) -> ValidationDecision:
        issues: list[str] = []

        if result.kind == "chunks":
            chunks = result.payload or []
            if len(chunks) == 0:
                issues.append("검색 결과가 비어 있습니다.")
            else:
                sims = [float(c.get("score", 0.0)) for c in chunks]
                best = max(sims) if sims else 0.0
                if best < settings.MIN_RELEVANCE:
                    issues.append(f"관련성이 낮은 근거만 검색되었습니다. (best={best:.3f} < min={settings.MIN_RELEVANCE:.3f})")

        elif result.kind == "sql_rows":
            rows = result.payload or []
            if len(rows) == 0:
                issues.append("SQL 결과가 비어 있습니다.")

        elif result.kind == "graph":
            g = result.payload
            if not g:
                issues.append("그래프 결과가 비어 있습니다.")

        if not issues:
            return ValidationDecision(ok=True, issues=[], should_retry=False)

        issue_text = " / ".join(issues)

        if "검색 결과가 비어" in issue_text or "관련성이 낮은 근거" in issue_text:
            return ValidationDecision(
                ok=False,
                issues=issues,
                should_retry=True,
                retry_with_strategy="hybrid",
                ask_user=None,
            )

        if "SQL 결과가 비어" in issue_text:
            return ValidationDecision(
                ok=False,
                issues=issues,
                should_retry=False,
                retry_with_strategy=None,
                ask_user="SQL 조회 조건이 부족하거나 기간/대상이 맞지 않을 수 있어요. 조회 기간(예: 2026-02-01~2026-02-25)과 대상(LOT/라인/제품)을 알려줄래요?",
            )

        return ValidationDecision(
            ok=False,
            issues=issues,
            should_retry=False,
            retry_with_strategy=None,
            ask_user="근거가 부족해요. 문서/기간/대상(LOT/라인/제품) 중 무엇을 기준으로 찾아야 할지 조금만 더 알려줄래요?",
        )