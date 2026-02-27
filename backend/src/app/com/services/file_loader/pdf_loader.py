from typing import Iterable

def load_pdf_text(file_bytes: bytes) -> Iterable[tuple[int, str]]:
    """
    return: (page_no, text)
    의존성: pypdf
    """
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            yield i + 1, txt
    except Exception:
        # 라이브러리 미설치/파싱 실패 시 빈 텍스트 반환
        yield 1, ""