from app.core.config import settings

class ChunkingService:
    def chunk_text(self, text: str) -> list[str]:
        size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP

        chunks = []
        start = 0
        n = len(text)

        while start < n:
            end = min(start + size, n)
            chunks.append(text[start:end])
            if end == n:
                break
            start = max(0, end - overlap)

        return chunks