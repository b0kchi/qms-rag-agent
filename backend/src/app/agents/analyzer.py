import re
from dataclasses import dataclass
from app.agents.state import ProposedStrategy

@dataclass
class ProposedTemplate:
    template_id: str
    score: float
    reason: str


class QueryAnalyzer:
    def propose_strategies(self, query: str) -> list[ProposedStrategy]:
        q = query.lower()

        candidates: list[ProposedStrategy] = []

        looks_like_report = any(k in q for k in ["수율", "불량", "top", "trend", "추이", "통계", "현황"]) or bool(re.search(r"\d{4}[-/.]\d{1,2}", q))
        looks_like_definition = any(k in q for k in ["뭐야", "정의", "설명", "기준", "절차", "가이드", "규정"])
        looks_like_relation = any(k in q for k in ["원인", "영향", "관계", "연관", "왜", "때문"])

        if looks_like_report:
            candidates.append(ProposedStrategy("sql_template", "SQL 템플릿 조회", "정형 리포트/지표 질문으로 보여서, 미리 정의된 SQL 템플릿이 적합합니다."))
        if looks_like_relation:
            candidates.append(ProposedStrategy("hybrid", "혼합형 검색(Hybrid)", "키워드+의미 기반으로 근거를 넓게 확보하는 게 유리해 보입니다."))
            candidates.append(ProposedStrategy("graph", "그래프 검색(Graph)", "엔터티/관계 기반 탐색이 도움이 될 가능성이 있습니다."))
        if looks_like_definition:
            candidates.append(ProposedStrategy("vector", "벡터 검색(Vector RAG)", "문서 기반 설명/정의형 질문으로 보여 벡터 검색이 적합합니다."))

        if not candidates:
            candidates.append(ProposedStrategy("vector", "벡터 검색(Vector RAG)", "일반 질의이므로 우선 벡터 검색으로 근거를 찾습니다."))
            candidates.append(ProposedStrategy("hybrid", "혼합형 검색(Hybrid)", "벡터 검색이 약하면 혼합형으로 보강할 수 있습니다."))

        uniq = []
        seen = set()
        for c in candidates:
            if c.key not in seen:
                uniq.append(c)
                seen.add(c.key)
        return uniq

    def match_sql_templates(self, query: str, templates: list[dict]) -> list[ProposedTemplate]:
        """
        templates: [{"id","name","description","required_params":[...]}]
        간단 키워드 매칭 + 점수
        """
        q = query.lower()
        scored: list[ProposedTemplate] = []

        def kw_score(text: str) -> float:
            s = 0.0
            for kw in ["수율", "yield", "불량", "defect", "top", "추이", "trend", "현황", "통계"]:
                if kw in text:
                    s += 1.0
            return s

        for t in templates:
            base = 0.0
            name = (t.get("name") or "").lower()
            desc = (t.get("description") or "").lower()
            base += kw_score(q) * 0.1
            if any(k in q for k in name.split()):
                base += 0.3
            if any(k in q for k in desc.split()):
                base += 0.2
            # “수율” 같은 핵심 키워드가 템플릿 설명에 있으면 +0.5
            if ("수율" in q and ("수율" in name or "수율" in desc)):
                base += 0.5
            if ("불량" in q and ("불량" in name or "불량" in desc)):
                base += 0.5

            if base > 0.25:
                scored.append(ProposedTemplate(template_id=t["id"], score=base, reason="질의 키워드와 템플릿 설명이 매칭됩니다."))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:5]