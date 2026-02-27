import re
from datetime import datetime

DATE_PATTERNS = [
    r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})",   # 2026-02-25
    r"(\d{4})(\d{2})(\d{2})",                 # 20260225
]

RANGE_PATTERNS = [
    r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\s*~\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})",
    r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\s*-\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})",
]

def _normalize_date(s: str) -> str | None:
    s = s.strip()
    # yyyy-mm-dd
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    # yyyymmdd
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return None

def extract_date_range(text: str) -> tuple[str | None, str | None]:
    t = text.strip()
    for p in RANGE_PATTERNS:
        m = re.search(p, t)
        if m:
            a = _normalize_date(m.group(1))
            b = _normalize_date(m.group(2))
            return a, b

    # 단일 날짜가 하나만 있으면 from=to로 채우는 건 위험하니 None 처리(요청 시에만 사용)
    return None, None

def extract_lot(text: str) -> str | None:
    # LOT123, lot_abc, LOT-2026...
    m = re.search(r"\bLOT[-_ ]?([0-9A-Za-z\-]+)\b", text, re.IGNORECASE)
    if m:
        return f"LOT{m.group(1)}"
    return None

def extract_line(text: str) -> str | None:
    # LINE1, line-02, 라인3 등 매우 단순
    m = re.search(r"\bLINE[-_ ]?(\d{1,3})\b", text, re.IGNORECASE)
    if m:
        return f"LINE{m.group(1)}"
    m = re.search(r"라인\s*(\d{1,3})", text)
    if m:
        return f"LINE{m.group(1)}"
    return None

def autofill_params(required: list[str], query: str, given: dict | None) -> dict:
    given = dict(given or {})
    from_date, to_date = extract_date_range(query)
    lot = extract_lot(query)
    line = extract_line(query)

    for r in required:
        if r in given and given[r] not in (None, ""):
            continue
        if r in ("from_date", "start_date") and from_date:
            given[r] = from_date
        if r in ("to_date", "end_date") and to_date:
            given[r] = to_date
        if r == "lot" and lot:
            given[r] = lot
        if r in ("line", "line_id") and line:
            given[r] = line

    return given

def missing_params(required: list[str], params: dict | None) -> list[str]:
    params = params or {}
    miss = []
    for r in required:
        v = params.get(r)
        if v is None or (isinstance(v, str) and v.strip() == ""):
            miss.append(r)
    return miss