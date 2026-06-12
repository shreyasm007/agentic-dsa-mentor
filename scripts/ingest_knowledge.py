from pathlib import Path
from uuid import uuid4

import voyageai
from qdrant_client import QdrantClient, models

from dsa_mentor.infrastructure.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
SOURCES = sorted((ROOT / "knowledge").glob("*.md"))


def chunk_text(text: str, max_chars: int = 1600) -> list[str]:
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if current and len(current) + len(paragraph) > max_chars:
            chunks.append(current.strip())
            current = ""
        current += paragraph + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def main() -> None:
    settings = get_settings()
    voyage = voyageai.Client(api_key=settings.voyage_api_key)
    qdrant = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    documents = [
        (source, chunk)
        for source in SOURCES
        for chunk in chunk_text(source.read_text(encoding="utf-8"))
    ]
    vectors = voyage.embed(
        [text for _, text in documents],
        model=settings.voyage_model,
        input_type="document",
    ).embeddings

    if qdrant.collection_exists(settings.qdrant_collection):
        qdrant.delete_collection(settings.qdrant_collection)
    qdrant.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=models.VectorParams(
            size=len(vectors[0]),
            distance=models.Distance.COSINE,
        ),
    )
    qdrant.upsert(
        collection_name=settings.qdrant_collection,
        points=[
            models.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={"source": str(source.relative_to(ROOT)), "text": text},
            )
            for (source, text), vector in zip(documents, vectors, strict=True)
        ],
    )
    print(f"Ingested {len(documents)} chunks.")


if __name__ == "__main__":
    main()
