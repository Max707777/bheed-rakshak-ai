import cv2
import numpy as np
import config


class ZoneManager:
    """Manages zone polygons and point-in-polygon assignments."""

    def __init__(self, zone_polygons=None):
        """Initialize zone manager with polygon coordinates."""
        self.polygons = zone_polygons if zone_polygons is not None else config.ZONE_POLYGONS

    def assign_zone(self, point):
        """Return the zone name ('A', 'B', 'C', etc.) containing the given (x, y) point, or None."""
        pt = (float(point[0]), float(point[1]))
        for zone_name, coords in self.polygons.items():
            if len(coords) >= 3:
                poly = np.array(coords, dtype=np.int32)
                if cv2.pointPolygonTest(poly, pt, False) >= 0:
                    return zone_name
        return None

    def draw_zones(self, frame, zone_risks=None):
        """Draw zone polygon outlines and names with flat risk colors on the frame."""
        for zone_name, coords in self.polygons.items():
            if len(coords) >= 3:
                poly = np.array(coords, dtype=np.int32)
                risk_state = (zone_risks.get(zone_name, "NORMAL")) if zone_risks else "NORMAL"
                color = config.RISK_COLORS.get(risk_state, (0, 255, 0))
                cv2.polylines(frame, [poly], isClosed=True, color=color, thickness=2)
                # Label at first vertex
                x, y = coords[0]
                label = f"Zone {zone_name} [{risk_state}]"
                cv2.putText(frame, label, (x + 10, max(30, y + 35)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
