from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    meta: dict


class ChunkingService:
    def chunk(self, text: str, *, chunk_size: int = 1000, overlap: int = 150, meta: dict | None = None):
        meta = meta or {}
        if not text:
            return []

        out: list[TextChunk] = []
        i = 0
        n = len(text)
        while i < n:
            j = min(i + chunk_size, n)
            out.append(TextChunk(text=text[i:j], meta=meta))
            if j == n:
                break
            i = max(0, j - overlap)
        return out