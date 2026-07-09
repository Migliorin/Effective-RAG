import logging

import fitz
from tempfile import NamedTemporaryFile
from PIL import Image

import time
from io import BytesIO

import os
import base64

from .preprocess import Preprocess
from .llm_openai import LlmOpenAi
from .detection import DetectionYolo
from .chunknizer import Chunknizer
from .storage_data import StorageDataQdrant


class EffectiveRag():
    def __init__(
        self,
        server_ip:str,
        model_pt_path:str,
        qdrant_url:str,
        qdrant_passwd:str,
        tokenizer_id="Qwen/Qwen3-Embedding-0.6B",
        max_tokens=1024
    ):
        self.preprocess = Preprocess()
        self.llm_openai = LlmOpenAi(server_ip)
        self.detection_yolo = DetectionYolo(model_pt_path)
        self.logger = logging.getLogger(__name__)
        self.chunknizer = Chunknizer(
            tokenizer_id=tokenizer_id,
            max_tokens=max_tokens,
            embedder=LlmOpenAi(server_ip)
        )
        self.storage = StorageDataQdrant(qdrant_url,qdrant_passwd)
        self.max_tokens = max_tokens

    def __get_image_b64(self,path:str)->str:

        crop_img = Image.open(path)
        buffer = BytesIO()
        crop_img.save(buffer, format="PNG")

        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        b64 = f"data:image/png;base64,{b64}"

        return b64


    def __call_ocr_with_retry(self,img_b64:str, max_retries=5, base_delay=2)->str:
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                return self.llm_openai.glm_ocr_call(img_b64)
            except Exception as e:
                last_error = e

                if attempt == max_retries:
                    break

                delay = base_delay * (2 ** (attempt - 1))
                print(f"Erro na tentativa {attempt}/{max_retries}: {e}. Retentando em {delay}s...")
                time.sleep(delay)

        raise last_error

    def extract_markdown(self,id_name:str, pdf_path:str, zoom=2 ) -> str:
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(zoom, zoom)

        path_img_save = list()


        self.logger.info(f"[{id_name}] - Iniciando extracao BBox pdf")
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            results = self.detection_yolo(img)
            if(results):
                boxes_sorted, cls_sorted = results

            else:
                continue


            for (x_min,y_min, x_max, y_max), cls_ in zip(boxes_sorted,cls_sorted):
                crop_img = img.crop((x_min,y_min, x_max, y_max))

                tmp_img_path = NamedTemporaryFile("w", suffix=".png", delete=False)

                crop_img.save(tmp_img_path.name)

                path_img_save.append([int(cls_), tmp_img_path.name])

        self.logger.info(f"[{id_name}] - Extracao concluida")


        self.logger.info(f"[{id_name}] - Iniciando OCR das imagens: {len(path_img_save)}")
        results = list()
        for idx,(cls_, path_) in enumerate(path_img_save):
            img_b64 = self.__get_image_b64(path_)

            try:
                response = self.__call_ocr_with_retry(
                    img_b64=img_b64,
                    max_retries=5,
                    base_delay=2,
                )

                results.append({
                    "cls": cls_,
                    "response": response,
                })
                self.logger.info(f"[{id_name}] - [{idx+1}]/[{len(path_img_save)}] extraido")
            except Exception as e:
                self.logger.exception(f"[{id_name}] - Falha definitiva: {e}")

                results.append({
                    "cls": cls_,
                    "response": None,
                })

                time.sleep(2)

            finally:
                os.remove(path_)


        self.logger.info(f"[{id_name}] - Extracao OCR concluida")

        self.logger.info(f"[{id_name}] - Salvando Markdown")
        tmp_md_file = NamedTemporaryFile("w+", suffix=".md", delete=False)

        for idx in range(len(results)):
            obj_ = results[idx]
            text_ = obj_.get("response")
            if(text_ is not None):
                cls_ = obj_.get("cls")
                text = self.preprocess(cls_,text_)
                obj_["format"] = text

        with open(tmp_md_file.name, "w+") as outfile:
            for idx in range(len(results)):
                obj_ = results[idx]
                text_ = obj_.get("response")
                if(text_ is not None):
                    outfile.write(obj_.get("format"))

            outfile.close()

        self.logger.info(f"[{id_name}] - Markdown salvo")

        return tmp_md_file.name

    def vectorize_markdown_file(self,path_md:str):
        text_list = self.chunknizer.create_chunker_from_md(path_md)
        embeddings = self.chunknizer.embedding_chunks(text_list)
        self.storage.insert_data(
            md_pdf_name=path_md.split("/")[-1].replace(".md",""),
            chunks=text_list,
            embedding=embeddings,
            collection_name="extraction",
            size=self.max_tokens
        )
