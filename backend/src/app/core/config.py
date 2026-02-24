from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "QMS RAG Agent"
    ENV: str = "dev"

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    DATABASE_URL: str

    VECTOR_TOP_K: int = 8
    CHUNK_SIZE: int = 900
    CHUNK_OVERLAP: int = 120

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()