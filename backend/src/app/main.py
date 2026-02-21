from fastapi import FastAPI
from src.app.core.config import PROJECT_NAME
from src.app.db.database import init_db
from src.app.api.routes import router

app = FastAPI(title=PROJECT_NAME) # 웹 애플리케이션 인스턴스 생성

@app.on_event("startup") # FastAPI가 서버 시작할 때 실행할 이벤트 등록
def on_startup():
    init_db()

app.include_router(router) # routes.py에서 정의한 API 엔드포인트들을 이 앱에 붙인다.