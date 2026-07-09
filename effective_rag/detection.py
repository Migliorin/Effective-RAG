from ultralytics import YOLO
import numpy as np

class DetectionYolo():
    def __init__(self,model_path:str):
        self.model = YOLO(model_path,verbose=False).cuda().eval()

    def __call__(self,image,conf=0.6)->tuple[list[list[float]],list[int]] | None:
        results = self.model(image,conf=conf,verbose=False)

        if(results):
            boxes = results[0].boxes.xyxy.detach().cpu().numpy()
            cls = results[0].boxes.cls.detach().cpu().numpy()
            order = np.lexsort((boxes[:, 0], boxes[:, 1]))
            boxes_sorted = boxes[order]
            cls_sorted = cls[order]

            return boxes_sorted, cls_sorted
        else:
            return None
