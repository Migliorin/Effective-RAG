import os
import fitz
from PIL import Image
from ultralytics import YOLO
from tqdm import tqdm
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom


model_pt = "/home/lumalfa/projetos/Effective-RAG/training/outputs/yolo12n_2026-06-24_00-16-46/weights/best.pt"
output_dir =  "/home/lumalfa/datasets"
zoom = 2

model = YOLO(model_pt)
model = model.cuda()



for i, path_pdf in enumerate(["../PUR521.pdf","../PUR520_NPI.pdf","../PUR_PPI40.pdf","../PUR_522.pdf"]):
    #path_pdf = "/home/lumalfa/projetos/Effective-RAG/training/PUR520_NPI.pdf"
    output = f"{output_dir}/paper_parts_pre_labeled-v1.{i}"

    images_dir = os.path.join(output, "images")
    os.makedirs(images_dir, exist_ok=True)

    doc = fitz.open(path_pdf)

    # Pega nomes das classes do modelo YOLO.
    # Ultralytics costuma expor model.names como dict: {0: "classe_a", 1: "classe_b"}
    if isinstance(model.names, dict):
        class_names = {int(k): str(v) for k, v in model.names.items()}
    else:
        class_names = {i: str(name) for i, name in enumerate(model.names)}

    # Raiz CVAT
    annotations = ET.Element("annotations")
    ET.SubElement(annotations, "version").text = "1.1"

    meta = ET.SubElement(annotations, "meta")
    task = ET.SubElement(meta, "task")

    ET.SubElement(task, "id").text = "0"
    ET.SubElement(task, "name").text = "PUR520_NPI"
    ET.SubElement(task, "size").text = str(len(doc))
    ET.SubElement(task, "mode").text = "annotation"
    ET.SubElement(task, "overlap").text = "0"
    ET.SubElement(task, "bugtracker").text = ""
    ET.SubElement(task, "flipped").text = "False"

    now = datetime.now().isoformat()
    ET.SubElement(task, "created").text = now
    ET.SubElement(task, "updated").text = now

    labels_el = ET.SubElement(task, "labels")
    for cls_id in sorted(class_names):
        label_el = ET.SubElement(labels_el, "label")
        ET.SubElement(label_el, "name").text = class_names[cls_id]
        ET.SubElement(label_el, "type").text = "bbox"
        ET.SubElement(label_el, "attributes")

    segments_el = ET.SubElement(task, "segments")
    segment_el = ET.SubElement(segments_el, "segment")
    ET.SubElement(segment_el, "id").text = "0"
    ET.SubElement(segment_el, "start").text = "0"
    ET.SubElement(segment_el, "stop").text = str(len(doc) - 1)
    ET.SubElement(segment_el, "url").text = ""

    owner_el = ET.SubElement(task, "owner")
    ET.SubElement(owner_el, "username").text = ""
    ET.SubElement(owner_el, "email").text = ""

    ET.SubElement(meta, "dumped").text = now

    mat = fitz.Matrix(zoom, zoom)

    for i, page in tqdm(enumerate(doc), total=len(doc)):
        pix = page.get_pixmap(matrix=mat)

        # Garante RGB mesmo se vier RGBA/alpha
        if pix.alpha:
            img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples).convert("RGB")
        else:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        img_name = f"{path_pdf.replace('.pdf','').replace('../','')}_{i}.png"
        img_path = os.path.join(images_dir, img_name)
        img.save(img_path)

        width, height = img.size

        image_el = ET.SubElement(
            annotations,
            "image",
            {
                "id": str(i),
                "name": f"images/{img_name}",
                "width": str(width),
                "height": str(height),
            },
        )

        results = model(img)

        if not results:
            continue

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            continue

        xywhn = result.boxes.xywhn.detach().cpu().numpy()
        cls = result.boxes.cls.detach().cpu().numpy()

        for idx in range(cls.shape[0]):
            cls_id = int(cls[idx])
            label_name = class_names.get(cls_id, str(cls_id))

            x_center_n, y_center_n, w_n, h_n = xywhn[idx]

            # YOLO xywhn -> CVAT xyxy absoluto
            x_center = x_center_n * width
            y_center = y_center_n * height
            box_w = w_n * width
            box_h = h_n * height

            xtl = x_center - box_w / 2
            ytl = y_center - box_h / 2
            xbr = x_center + box_w / 2
            ybr = y_center + box_h / 2

            # Clipa para os limites da imagem
            xtl = max(0, min(float(xtl), width))
            ytl = max(0, min(float(ytl), height))
            xbr = max(0, min(float(xbr), width))
            ybr = max(0, min(float(ybr), height))

            # Ignora caixas inválidas
            if xbr <= xtl or ybr <= ytl:
                continue

            ET.SubElement(
                image_el,
                "box",
                {
                    "label": label_name,
                    "source": "auto",
                    "occluded": "0",
                    "xtl": f"{xtl:.2f}",
                    "ytl": f"{ytl:.2f}",
                    "xbr": f"{xbr:.2f}",
                    "ybr": f"{ybr:.2f}",
                    "z_order": "0",
                },
            )

    # Salva XML formatado
    xml_bytes = ET.tostring(annotations, encoding="utf-8")
    xml_pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")

    xml_path = os.path.join(output, "annotations.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_pretty)

    print(f"CVAT XML salvo em: {xml_path}")
    print(f"Imagens salvas em: {images_dir}")