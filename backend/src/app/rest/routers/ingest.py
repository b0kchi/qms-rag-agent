import json
from fastapi import APIRouter, UploadFile, File, Depends
from sqlmodel import Session

from app.com.db.session import get_session
from app.com.utils.ids import new_id
from app.schema.models.document import Document
from app.schema.models.chunk import Chunk
from app.com.repositories.document_repo import DocumentRepo
from app.com.repositories.chunk_repo import ChunkRepo
from app.com.services.embedding_service import EmbeddingService
from app.com.services.chunking_service import ChunkingService
from app.com.services.file_loader.pdf_loader import load_pdf_text
from app.com.services.file_loader.excel_loader import load_excel_text

router = APIRouter()


@router.post("/pdf")
async def ingest_pdf(file: UploadFile = File(...), session: Session = Depends(get_session)):
    b = await file.read()

    doc_id = new_id("doc")
    DocumentRepo(session).add(Document(id=doc_id, file_name=file.filename, source_type="pdf"))

    chunker = ChunkingService()
    embedder = EmbeddingService()

    all_chunks: list[Chunk] = []
    for page_no, text in load_pdf_text(b):
        for ch in chunker.chunk(text, meta={"page_no": page_no, "file_name": file.filename}):
            vec = embedder.embed_query(ch.text)
            all_chunks.append(
                Chunk(
                    id=new_id("chunk"),
                    document_id=doc_id,
                    text=ch.text,
                    meta_json=json.dumps(ch.meta, ensure_ascii=False),
                    embedding=vec,
                )
            )

    ChunkRepo(session).add_many(all_chunks)
    return {"document_id": doc_id, "chunks": len(all_chunks)}


@router.post("/excel")
async def ingest_excel(file: UploadFile = File(...), session: Session = Depends(get_session)):
    b = await file.read()

    doc_id = new_id("doc")
    DocumentRepo(session).add(Document(id=doc_id, file_name=file.filename, source_type="excel"))

    chunker = ChunkingService()
    embedder = EmbeddingService()

    all_chunks: list[Chunk] = []
    for sheet, text in load_excel_text(b):
        for ch in chunker.chunk(text, meta={"sheet": sheet, "file_name": file.filename}):
            vec = embedder.embed_query(ch.text)
            all_chunks.append(
                Chunk(
                    id=new_id("chunk"),
                    document_id=doc_id,
                    text=ch.text,
                    meta_json=json.dumps(ch.meta, ensure_ascii=False),
                    embedding=vec,
                )
            )

    ChunkRepo(session).add_many(all_chunks)
    return {"document_id": doc_id, "chunks": len(all_chunks)}