from langchain_openai import OpenAIEmbeddings
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.emb = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )

    def embed_query(self, text: str) -> list[float]:
        return self.emb.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.emb.embed_documents(texts)