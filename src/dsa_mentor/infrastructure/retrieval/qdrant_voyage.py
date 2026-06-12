import voyageai
from qdrant_client import QdrantClient

from dsa_mentor.infrastructure.config import Settings


class NullKnowledgeRetriever:
    def search(self, query: str, limit: int = 4) -> str:
        return ""


class QdrantVoyageRetriever:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.voyage = voyageai.Client(api_key=settings.voyage_api_key)
        self.qdrant = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )

    def search(self, query: str, limit: int = 4) -> str:
        vector = self.voyage.embed(
            [query],
            model=self.settings.voyage_model,
            input_type="query",
        ).embeddings[0]
        result = self.qdrant.query_points(
            collection_name=self.settings.qdrant_collection,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return "\n\n---\n\n".join(
            str(point.payload["text"])
            for point in result.points
            if point.payload and point.payload.get("text")
        )
