from typing import Iterable

def load_excel_text(file_bytes: bytes) -> Iterable[tuple[str, str]]:
    """
    return: (sheet_name, text)
    의존성: pandas + openpyxl
    """
    try:
        import pandas as pd
        import io
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            # 간단하게 행을 문자열로 합침(운영에서는 더 정교하게)
            text = df.astype(str).fillna("").apply(lambda r: " | ".join(r.values.tolist()), axis=1).tolist()
            yield sheet, "\n".join(text)
    except Exception:
        yield "Sheet1", ""