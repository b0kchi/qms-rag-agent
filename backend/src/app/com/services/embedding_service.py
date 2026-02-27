import hashlib
import numpy as np
from app.com.config.settings import settings


class EmbeddingService:
    """
    스켈레톤: 외부 API 없이도 동작하도록 'deterministic pseudo-embedding' 사용.
    운영에서는 OpenAI/로컬 임베딩 모델로 교체.
    """

    def __init__(self, dim: int | None = None):
        self.dim = dim or settings.EMBEDDING_DIM

    def _hash_to_vec(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], "little", signed=False)
        rng = np.random.default_rng(seed)
        v = rng.normal(0, 1, size=self.dim).astype("float32")
        # normalize
        norm = float(np.linalg.norm(v)) or 1.0
        v = v / norm
        return v.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._hash_to_vec(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vec(t) for t in texts]