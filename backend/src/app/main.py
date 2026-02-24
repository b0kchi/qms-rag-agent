from fastapi import FastAPI
from app.core.config import settings
from app.db.init_db import init_db
from app.api.routes_chat import router as chat_router
from app.api.routes_files import router as files_router

def create_app():
    app = FastAPI(title=settings.PROJECT_NAME)

    @app.on_event("startup")
    def on_startup():
        init_db()

    app.include_router(files_router)
    app.include_router(chat_router)
    return app

app = create_app()