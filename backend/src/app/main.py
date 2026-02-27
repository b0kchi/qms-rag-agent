from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.rest.routers.chat import router as chat_router
from app.rest.routers.ingest import router as ingest_router
from app.com.db.init import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    init_db()
    yield
    # shutdown (필요 시 정리)


app = FastAPI(
    title="Hybrid RAG + Multi-Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])