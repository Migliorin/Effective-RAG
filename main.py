from config import get_dotenv_values
from services import BucketMinio
from processing import PDF
from models import OcrExtraction

import os


if __name__ == "__main__":
    values = get_dotenv_values()

    print(values)
    ocr_ext = OcrExtraction()

    minio_client = BucketMinio(
        endpoint=values.get("MINIO_ENDPOINT"),
        access_key=values.get("MINIO_ACCESS_KEY"),
        secret_key=values.get("MINIO_SECRET_KEY"),
        secure=False
    )
    pdf_processing = PDF()

    path = minio_client.download_pdf("pdfs-files","upload/termo.pdf")
    list_paths = pdf_processing.extract_pages_into_imgs(path)
    #print(json.dumps(list_paths,indent=1))
    print(ocr_ext(list_paths[0]))
    for path_ in [path,*list_paths]:
        os.remove(path_)