import logging
import os

from effective_rag import EffectiveRag, StorageDataMinio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

class TestProcess():
    def __init__(self,):
        self.MINIO_URL = "localhost:9000"
        self.ACCESS_KEY = "ai-reader-user"
        self.SECRET_KEY = "g7jgKu20uXsd"
        self.SECURE = False

        self.model_pt_path = "training/outputs/yolo12n_2026-06-24_00-16-46/weights/best.pt"
        self.url = "http://localhost:8081/v1"

        self.pdf_minio_path = "1/811131b0-67ff-443e-89fb-4b956a7fb2b6.pdf"
        self.bucket_name = "documents"

        self.qdrant_url = "http://localhost:6333"
        self.qdrant_passwd = "sjnf98hs99uCNBAsd0asdbA8"


    def extract_and_upload(self):

        bucket_minio = StorageDataMinio(
            self.MINIO_URL,
            self.ACCESS_KEY,
            self.SECRET_KEY,
            self.SECURE
        )

        path_pdf = bucket_minio.download_file(
            self.bucket_name,
            self.pdf_minio_path,
            delete=False
        )

        effective_rag = EffectiveRag(
            self.url,
            self.model_pt_path
        )

        id_name = path_pdf.replace(".pdf","").split("/")[-1]
        local_file_md = effective_rag.extract_markdown(id_name,path_pdf)
        os.remove(path_pdf)

        status = bucket_minio.put_md_file(
            "extraction",
            self.pdf_minio_path.replace(".pdf",".md"),
            local_file_md
        )
        if(status is not None):
            print(status)
            os.remove(local_file_md)



    def chunknizer_and_save(self):
        effective_rag = EffectiveRag(
            server_ip=self.url,
            model_pt_path=self.model_pt_path,
            qdrant_url=self.qdrant_url,
            qdrant_passwd=self.qdrant_passwd
        )

        bucket_minio = StorageDataMinio(
            self.MINIO_URL,
            self.ACCESS_KEY,
            self.SECRET_KEY,
            self.SECURE
        )

        path_md = bucket_minio.download_file(
            bucket_name="extraction",
            object_name="1/811131b0-67ff-443e-89fb-4b956a7fb2b6.md",
            suffix=".md",
            delete=False
        )

        effective_rag.vectorize_markdown_file(path_md=path_md)

        os.remove(path_md)


test_process = TestProcess()
test_process.chunknizer_and_save()