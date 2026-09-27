import cv2
import config


def run_calibration():
    """Interactive tool to click polygon corners for zones A, B, C and export to config.py."""
    source = config.PHONE_URL if config.SOURCE == "phone" else config.VIDEO_FILE
    cap = cv2.VideoCapture(source)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print(f"Error: Could not read frame from source: {source}")
        return

    zones = {"A": [], "B": [], "C": []}
    current_zone = "A"

    def mouse_callback(event, x, y, flags, param):
        """Record polygon vertex for current active zone on left click."""
        if event == cv2.EVENT_LBUTTONDOWN:
            zones[current_zone].append([x, y])
            print(f"Zone {current_zone} added point: [{x}, {y}]")

    cv2.namedWindow("Calibrate Zones")
    cv2.setMouseCallback("Calibrate Zones", mouse_callback)

    colors = {"A": (0, 255, 0), "B": (255, 255, 0), "C": (0, 165, 255)}

    print("--- Zone Calibration Tool ---")
    print("Click to add points for current zone.")
    print("Keys: 'a' for Zone A, 'b' for Zone B, 'c' for Zone C, 'r' to reset current zone, 'q' to finish.")

    while True:
        display_frame = frame.copy()

        for z_name, pts in zones.items():
            col = colors[z_name]
            for pt in pts:
                cv2.circle(display_frame, (pt[0], pt[1]), 5, col, -1)
            if len(pts) > 1:
                for i in range(len(pts) - 1):
                    cv2.line(display_frame, tuple(pts[i]), tuple(pts[i + 1]), col, 2)
                if len(pts) >= 3:
                    cv2.line(display_frame, tuple(pts[-1]), tuple(pts[0]), col, 1)

        cv2.putText(display_frame, f"Active Zone: {current_zone} (Press a/b/c/r/q)",
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Calibrate Zones", display_frame)

        key = cv2.waitKey(25) & 0xFF
        if key in [ord('a'), ord('A')]:
            current_zone = "A"
            print("Switched to Zone A")
        elif key in [ord('b'), ord('B')]:
            current_zone = "B"
            print("Switched to Zone B")
        elif key in [ord('c'), ord('C')]:
            current_zone = "C"
            print("Switched to Zone C")
        elif key in [ord('r'), ord('R')]:
            zones[current_zone] = []
            print(f"Reset points for Zone {current_zone}")
        elif key in [27, ord('q'), ord('Q')]:
            break

    cv2.destroyAllWindows()
    print("\n--- Calibration Output ---")
    print("ZONE_POLYGONS = {")
    for z, pts in zones.items():
        print(f'    "{z}": {pts},')
    print("}")


if __name__ == "__main__":
    run_calibration()
