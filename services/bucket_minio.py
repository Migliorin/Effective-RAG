import io
import json
from minio import Minio
from tempfile import NamedTemporaryFile

class BucketMinio:
    def __init__(self,endpoint:str,access_key:str,secret_key:str,secure:bool):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def download_pdf(self,bucket_name:str,object_name:str,delete=False) -> str:
        with NamedTemporaryFile("w+",suffix=".pdf",delete=delete) as tf:
            self.client.fget_object(bucket_name,object_name,tf.name)

        return tf.name
    
    def verify_folder(self,bucket_name:str,prefix:str) -> bool:
        prefix = prefix.strip("/") + "/"
        objects = self.client.list_objects(
            bucket_name,
            prefix=prefix,
            recursive=True
        )
        return any(True for _ in objects)
    
    def get_pages(self,bucket_name:str,prefix:str) -> list[int]:
        prefix = prefix.strip("/") + "/"
        objects = self.client.list_objects(
            bucket_name,
            prefix=prefix,
            recursive=True
        )
        list_pages = list()
        for obj in objects:
            if obj.object_name.endswith(".json"):
                response = self.client.get_object(bucket_name, obj.object_name)
                conteudo:dict = json.loads(response.read().decode("utf-8"))
                if "page" in conteudo.keys():
                    list_pages.append(conteudo.get("page"))

        list_pages.sort()

        return list_pages


    def put_json(self,bucket_name:str,object_name:str,data:dict) -> str | None:
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        result = self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=io.BytesIO(json_bytes),
            length=len(json_bytes),
            content_type="application/json"
        )
        if result:
            return result.object_name
        else:
            return None


