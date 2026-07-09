from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from uuid import uuid5, NAMESPACE_URL
from tempfile import NamedTemporaryFile

from minio import Minio

class StorageDataQdrant():
    def __init__(self,url:str,api_key:str):
        self.qdrant = QdrantClient(
            url=url,
            api_key=api_key,
        )

    def _deterministic_point_id(self,file_name: str, chunk_idx: int) -> str:
        return str(uuid5(NAMESPACE_URL, f"{file_name}:{chunk_idx}"))

    def _ensure_collection_name(self,collection_name:str,size:int):
        existing = [c.name for c in self.qdrant.get_collections().collections]

        if collection_name not in existing:
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=size,
                    distance=Distance.COSINE,
                ),
            )

    def insert_data(self,md_pdf_name:str,chunks:list[str],embedding:list[list[float]],collection_name:str,size:int):
        self._ensure_collection_name(collection_name,size)

        points = list()
        idx = 0
        for chunk_, embe_ in zip(chunks,embedding):
            points.append(
                PointStruct(
                    id=self._deterministic_point_id(md_pdf_name, idx),
                    vector=embe_,
                    payload={
                        "doc_id": md_pdf_name,
                        "chunk_index": idx,
                        "text": chunk_,
                    },
                )
            )
            idx += 1

        self.qdrant.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )

class StorageDataMinio:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def download_file(self, bucket_name: str, object_name: str, suffix=".pdf", delete=False) -> str:
        with NamedTemporaryFile("w+", suffix=suffix, delete=delete) as tf:
            self.client.fget_object(bucket_name, object_name, tf.name)

        return tf.name

    def put_md_file(self, bucket_name: str, object_name: str, local_file_path:str) -> str | None:

        result = self.client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=local_file_path,
            content_type="text/markdown",
        )
        if result:
            return result.object_name
        else:
            return None


