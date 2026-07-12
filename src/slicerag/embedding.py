import hashlib
import math
import re
from collections.abc import Iterable

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[가-힣]+", re.UNICODE)


class HashEmbeddingProvider:
    """MVP용 결정론적 임베딩.

    운영 단계에서는 Gateway 정책을 경유하는 embedding 모델 호출 구현으로 교체한다.
    테스트와 로컬 개발에서는 외부 모델 없이 project RAG 흐름을 검증할 수 있다.
    """

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[bucket] += 1.0
        return _normalize(vector)


class OpenAIEmbeddingProvider:
    """vLLM / MLX / OpenAI API 호환 임베딩 프로바이더."""

    def __init__(self, model: str | None = None, dimensions: int | None = None) -> None:
        from slicerag.config import settings
        import openai

        self.model = model or settings.embedding_model
        self.dimensions = dimensions or settings.embedding_dimensions
        
        api_key = settings.openai_api_key
        base_url = settings.openai_base_url or None
        
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self.dimensions

        params = {
            "input": text,
            "model": self.model,
        }
        
        # text-embedding-3 모델 계열은 dimensions를 받아 차원 축소를 기본 제공
        if "text-embedding-3" in self.model:
            params["dimensions"] = self.dimensions

        response = self.client.embeddings.create(**params)
        vector = response.data[0].embedding

        if len(vector) != self.dimensions:
            if len(vector) > self.dimensions:
                vector = vector[:self.dimensions]
            else:
                vector = vector + [0.0] * (self.dimensions - len(vector))

        return _normalize(vector)


def get_embedding_provider():
    from slicerag.config import settings
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider()
    return HashEmbeddingProvider(dimensions=settings.embedding_dimensions)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


def _tokens(text: str) -> Iterable[str]:
    for match in TOKEN_PATTERN.finditer(text):
        token = match.group(0).lower()
        yield token
        if _is_korean(token) and len(token) > 1:
            for size in (2, 3):
                for index in range(0, max(0, len(token) - size + 1)):
                    yield token[index : index + size]


def _is_korean(token: str) -> bool:
    return all("가" <= char <= "힣" for char in token)


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
