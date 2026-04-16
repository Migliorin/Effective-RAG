from tempfile import NamedTemporaryFile

import fitz
from PIL import Image


class PDF:
    def __init__(self):
        pass

    def extract_pages_into_imgs(self, path_pdf: str, zoom=2, delete=False) -> list:
        doc = fitz.open(path_pdf)
        mat = fitz.Matrix(zoom, zoom)
        list_paths = list()
        for page in doc:
            tmp_img_path = NamedTemporaryFile("w", suffix=".png", delete=delete)
            pix = page.get_pixmap(matrix=mat)
            Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(
                tmp_img_path.name
            )

            list_paths.append(tmp_img_path.name)
        return list_paths
