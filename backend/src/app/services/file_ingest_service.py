from typing import Tuple
from io import BytesIO

from sqlmodel import Session
from pypdf import PdfReader

from app.models.vector_models import File, Chunk
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService


class FileIngestService:
    def __init__(self):
        self.chunker = ChunkingService()
        self.embedder = EmbeddingService()

    def ingest_pdf(self, session: Session, filename: str, pdf_bytes: bytes) -> Tuple[int, int]:
        # 1) file metadata 저장
        file = File(filename=filename, content_type="application/pdf")
        session.add(file)
        session.commit()
        session.refresh(file)

        # 2) PdfReader는 seek 가능한 stream이 필요함 -> BytesIO로 감싸기
        reader = PdfReader(BytesIO(pdf_bytes))

        all_text_pages = []
        for p in range(len(reader.pages)):
            txt = reader.pages[p].extract_text() or ""
            all_text_pages.append((p, txt))

        # 3) 페이지 단위 chunk
        chunk_rows = []
        chunk_index = 0
        for page_no, page_text in all_text_pages:
            if not page_text.strip():
                continue
            for c in self.chunker.chunk_text(page_text):
                chunk_rows.append(
                    Chunk(
                        file_id=file.id,
                        chunk_index=chunk_index,
                        text=c,
                        source_page=page_no,
                    )
                )
                chunk_index += 1

        # 페이지에서 추출된 텍스트가 전혀 없을 수도 있음(스캔 PDF 등)
        if not chunk_rows:
            # 그래도 file record는 남기고, chunk는 0으로 리턴
            return (file.id, 0)

        # 4) 임베딩 생성 후 저장
        vectors = self.embedder.embed_documents([c.text for c in chunk_rows])
        for row, vec in zip(chunk_rows, vectors):
            row.embedding = vec

        session.add_all(chunk_rows)
        session.commit()

        return (file.id, len(chunk_rows))