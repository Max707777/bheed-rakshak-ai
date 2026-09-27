from ultralytics import YOLO
import config


class PersonDetector:
    """YOLOv8 wrapper for detecting persons in video frames."""

    def __init__(self, model_path=config.MODEL_PATH, conf=config.CONFIDENCE_THRESHOLD):
        """Load YOLO model and set confidence threshold."""
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        """Run inference on frame and return list of person bounding boxes [x1, y1, x2, y2, conf]."""
        results = self.model(frame, conf=self.conf, classes=[0], imgsz=640, verbose=False)
        boxes = []
        if results and len(results) > 0:
            for box in results[0].boxes:
                coords = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                boxes.append([int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]), conf])
        return boxes
