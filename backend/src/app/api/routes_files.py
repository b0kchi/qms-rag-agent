from fastapi import APIRouter, UploadFile, File as F, Depends
from sqlmodel import Session

from app.db.engine import engine
from app.services.file_ingest_service import FileIngestService
from app.services.graph_build_service import GraphBuildService

router = APIRouter(prefix="/files", tags=["files"])

def get_session():
    from sqlmodel import Session
    return Session(engine)

@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = F(...)):
    data = await file.read()
    ingest = FileIngestService()

    with get_session() as session:
        file_id, chunk_count = ingest.ingest_pdf(session, file.filename, data)

        # 업로드 후 그래프 빌드(초기 버전: 일부 chunk만)
        gb = GraphBuildService()
        gb.build_from_file(session, file_id=file_id, max_chunks=120)

    return {"file_id": file_id, "chunks": chunk_count, "graph_built": True}