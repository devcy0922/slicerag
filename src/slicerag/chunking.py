from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str


def chunk_text(content: str, *, max_chars: int = 1200, overlap_chars: int = 160) -> list[TextChunk]:
    normalized = "\n".join(line.rstrip() for line in content.strip().splitlines())
    if not normalized:
        return []

    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        current = paragraph

        while len(current) > max_chars:
            chunks.append(current[:max_chars].strip())
            current = current[max(0, max_chars - overlap_chars) :].strip()

    if current:
        chunks.append(current)

    return [TextChunk(index=index, text=text) for index, text in enumerate(chunks)]

