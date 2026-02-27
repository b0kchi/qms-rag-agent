import re

STOPWORDS = {
    "은","는","이","가","을","를","에","의","와","과","로","으로","및","등","좀","더","해줘","알려줘",
    "어떻게","왜","무엇","뭐","정리","설명","관련","대해","대한"
}

def normalize_query(q: str) -> str:
    q = q.strip()
    q = re.sub(r"\s+", " ", q)
    return q

def extract_keywords(text: str, *, min_len: int = 2, max_n: int = 10) -> list[str]:
    t = normalize_query(text).lower()
    # 한글/영문/숫자 토큰
    tokens = re.findall(r"[0-9a-zA-Z가-힣_]+", t)
    toks = []
    for x in tokens:
        if len(x) < min_len:
            continue
        if x in STOPWORDS:
            continue
        toks.append(x)
    # 중복 제거 + 길이/빈도 기반 간단 정렬
    uniq = list(dict.fromkeys(toks))
    return uniq[:max_n]

def overlap_score(keywords: list[str], text: str) -> float:
    if not keywords:
        return 0.0
    t = (text or "").lower()
    hit = sum(1 for k in keywords if k in t)
    return hit / max(1, len(keywords))