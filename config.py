# Video source settings
SOURCE = "phone"  # "phone" (mobile IP webcam), "webcam" (laptop cam), or "file" (MP4)
PHONE_URL = "http://192.168.1.13:8080/video"
WEBCAM_INDEX = 0
VIDEO_FILE = "videos/test_crowd.mp4"

# YOLO model settings
MODEL_PATH = "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.35

# Zone definitions: polygon coordinates [[x1, y1], [x2, y2], ...]
ZONE_POLYGONS = {
    "A": [[0, 0], [640, 0], [640, 1080], [0, 1080]],
    "B": [[640, 0], [1280, 0], [1280, 1080], [640, 1080]],
    "C": [[1280, 0], [1920, 0], [1920, 1080], [1280, 1080]]
}

# Risk thresholds per zone (person counts)
RISK_THRESHOLDS = {
    "A": {"WARNING": 2, "HIGH": 4, "CRITICAL": 6},
    "B": {"WARNING": 2, "HIGH": 4, "CRITICAL": 6},
    "C": {"WARNING": 2, "HIGH": 4, "CRITICAL": 6}
}

# Flat risk colors in BGR format
RISK_COLORS = {
    "NORMAL": (0, 255, 0),       # Green
    "WARNING": (0, 255, 255),    # Yellow
    "HIGH": (0, 140, 255),       # Orange
    "CRITICAL": (0, 0, 255)      # Red
}

# Exit throughput assumptions (persons cleared per second)
EXIT_THROUGHPUT = {
    "NORMAL": 0.5,
    "OPEN_EXIT_1": 1.5,
    "OPEN_EXIT_2": 2.0,
    "OPEN_ALL_EXITS": 3.5
}

# Prediction settings
HISTORY_WINDOW_SECONDS = 10.0

# ESP32 Hardware settings
MODE = "real"  # "real" or "simulated" (one-line live demo fallback)
ESP32_IP = "192.168.1.14"  # Discovered ESP32 IP address

# Display settings
DISPLAY_WINDOW_NAME = "BheedRakshak AI"
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 540
