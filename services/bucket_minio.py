import io
import json
from tempfile import NamedTemporaryFile

from minio import Minio


class BucketMinio:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def download_pdf(self, bucket_name: str, object_name: str, delete=False) -> str:
        with NamedTemporaryFile("w+", suffix=".pdf", delete=delete) as tf:
            self.client.fget_object(bucket_name, object_name, tf.name)

        return tf.name

    def verify_folder(self, bucket_name: str, prefix: str) -> bool:
        prefix = prefix.strip("/") + "/"
        objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
        return any(True for _ in objects)

    def get_pages(self, bucket_name: str, prefix: str) -> list[list[int], list[str]]:
        prefix = prefix.strip("/") + "/"
        objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)

        list_pages = []
        list_paths = []

        temp_items = []

        for obj in objects:
            if obj.object_name.endswith(".json"):
                response = self.client.get_object(bucket_name, obj.object_name)
                conteudo: dict = json.loads(response.read().decode("utf-8"))

                page = conteudo.get("page")
                object_name = conteudo.get("object_name")

                if page is not None and object_name is not None:
                    temp_items.append((page, object_name))

        temp_items.sort(key=lambda x: x[0])

        list_pages = [page for page, _ in temp_items]
        list_paths = [path for _, path in temp_items]

        return list_pages, list_paths

    def get_json_object(self, bucket_name: str, object_name: str) -> dict:
        try:
            response = self.client.get_object(bucket_name, object_name=object_name)
            conteudo: dict = json.loads(response.read().decode("utf-8"))
            return conteudo
        except:
            return {}

    def put_json(self, bucket_name: str, object_name: str, data: dict) -> str | None:
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        result = self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=io.BytesIO(json_bytes),
            length=len(json_bytes),
            content_type="application/json",
        )
        if result:
            return result.object_name
        else:
            return None
