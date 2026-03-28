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


