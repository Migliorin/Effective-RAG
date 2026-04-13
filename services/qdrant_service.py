from uuid import uuid4

from qdrant_client import QdrantClient, models
from sentence_transformers import CrossEncoder, SentenceTransformer


class QdrantService:
    def __init__(self, values: dict):
        self.client = QdrantClient(url=values.get("QDRANT_URL"))
        self.collection_name = values.get("QDRANT_COLLECTION")

        self.embedder = SentenceTransformer(values.get("EMBEDDING_MODEL"))
        self.reranker = CrossEncoder(values.get("RERANK_MODEL"))

        self.vector_size = self.embedder.get_embedding_dimension()
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    def _embed(self, text: str) -> list[float]:
        return self.embedder.encode(text).tolist()

    def add_chunks(self, document_id: str, chunks: list[dict]):
        points = []

        for chunk in chunks:
            vector = self._embed(chunk["contextualized_text"])

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "chunk_id": chunk["id"],
                        "text": chunk["text"],
                        "contextualized_text": chunk["contextualized_text"],
                        "meta": chunk["meta"],
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(self, query: str, document_id: str, limit: int = 50) -> list[dict]:
        query_vector = self._embed(query)

        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            ),
            limit=100,
        )

        candidates = [
            {
                "point_id": point.id,
                "score": point.score,
                "document_id": point.payload["document_id"],
                "chunk_id": point.payload["chunk_id"],
                "text": point.payload["text"],
                "contextualized_text": point.payload["contextualized_text"],
                "meta": point.payload["meta"],
            }
            for point in result.points
        ]

        if not candidates:
            return []

        pairs = [(query, item["contextualized_text"]) for item in candidates]
        rerank_scores = self.reranker.predict(pairs)

        for item, rerank_score in zip(candidates, rerank_scores):
            item["rerank_score"] = float(rerank_score)

        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        return candidates[:limit]