from ultralytics import YOLO
import config


class PersonTracker:
    """YOLOv8 persistent person tracker and zone transition monitor."""

    def __init__(self, model_path=config.MODEL_PATH, conf=config.CONFIDENCE_THRESHOLD):
        """Initialize tracker with YOLO model and confidence."""
        self.model = YOLO(model_path)
        self.conf = conf
        self.last_known_zones = {}
        self.inflow = {z: 0 for z in config.ZONE_POLYGONS}
        self.outflow = {z: 0 for z in config.ZONE_POLYGONS}

    def track(self, frame, zone_manager=None):
        """Run tracking on frame, update zone assignments, and compute inflow/outflow."""
        results = self.model.track(frame, conf=self.conf, classes=[0], imgsz=640, persist=True, verbose=False)
        tracks = []
        active_ids = set()

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.tolist() if results[0].boxes.xyxy is not None else []
            ids = results[0].boxes.id.tolist() if results[0].boxes.id is not None else list(range(len(boxes)))
            confs = results[0].boxes.conf.tolist() if results[0].boxes.conf is not None else [1.0] * len(boxes)

            for box, track_id, conf in zip(boxes, ids, confs):
                track_id = int(track_id)
                active_ids.add(track_id)
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                foot_point = ((x1 + x2) // 2, y2)
                zone_name = zone_manager.assign_zone(foot_point) if zone_manager else None

                prev_zone = self.last_known_zones.get(track_id)
                if prev_zone != zone_name:
                    if prev_zone is not None and prev_zone in self.outflow:
                        self.outflow[prev_zone] += 1
                    if zone_name is not None and zone_name in self.inflow:
                        self.inflow[zone_name] += 1
                    self.last_known_zones[track_id] = zone_name

                tracks.append({
                    "id": track_id,
                    "box": [x1, y1, x2, y2],
                    "zone": zone_name,
                    "conf": float(conf)
                })

        stale_ids = [tid for tid in self.last_known_zones if tid not in active_ids]
        for tid in stale_ids:
            del self.last_known_zones[tid]

        return tracks
