from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_PATH = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/rag"
    EMBEDDING_DIM: int = 384

    VECTOR_TOP_K: int = 6
    MIN_RELEVANCE: float = 0.20  # similarity (1 - cosine_distance) 기준
    MAX_LOOPS: int = 3

    # (나중) 실제 LLM 연결 시 사용
    LLM_PROVIDER: str = "stub"  # "openai" 등으로 확장
    OPENAI_API_KEY: str | None = None


settings = Settings()
