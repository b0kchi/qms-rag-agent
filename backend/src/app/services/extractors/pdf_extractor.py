# PDF파일에서 텍스트만 추출하는 유틸함수

from pypdf import PdfReader # PdfReader는 PDF 파일을 읽고 분석하는 객체
import io # 파일처럼 다룰 수 있는 메모리 스트림 객체를 만드는 데 사용

def extract_text_from_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data)) # 메모리에 있는 bytes데이터를 파일 객체처럼 동작하는 스트림 객체로 감싸서 반환
    parts = [] # 각 페이지에서 추출한 텍스트를 저장할 리스트
    for page in reader.pages: # pdf의 모든 페이지 순회
        parts.append(page.extract_text() or "") # 해당 페이지의 텍스트 추출. 실패 시 빈 문자열로 대체
    return "\n".join(parts).strip()