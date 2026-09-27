# BheedRakshak AI

BheedRakshak AI is a predictive crowd safety and automated intervention system built for hackathons. It processes video streams (local MP4 files or phone IP cameras) using YOLOv8 tracking, zone spatial analytics, density risk classification, predictive rate-of-change forecasting, what-if exit simulations, and ESP32 hardware command dispatch.

## Core Pipeline Architecture

1. **Video Source**: Swappable via `config.py` (`"file"` or `"phone"`).
2. **YOLO Detection & Tracking**: Persistent IDs across frames using Ultralytics YOLOv8.
3. **Zone Assignment**: Point-in-polygon assignment (Zones A, B, C) using bottom-center ground coordinates.
4. **Risk Engine**: Per-zone density evaluation (`NORMAL`, `WARNING`, `HIGH`, `CRITICAL`).
5. **Predictor**: Rolling 10s buffer computing rate-of-change (RoC) and estimated seconds to critical density.
6. **What-If Simulator**: Evaluates exit-state scenarios (`NORMAL`, `OPEN_EXIT_1`, `OPEN_EXIT_2`, `OPEN_ALL_EXITS`) to choose the safest intervention.
7. **ESP32 Dispatch**: Dispatches HTTP GET command (`/command?action=...`) to ESP32 with request throttling.
8. **Real-Time Output**: Flat OpenCV HUD dashboard and structured console data stream.

## Setup & Running

1. **Install dependencies**:
   ```bash
   pip install ultralytics opencv-python numpy requests
   ```

2. **Calibrate Zones (Optional)**:
   ```bash
   python calibrate_zones.py
   ```
   Click points for Zone A, B, and C on a captured frame and copy the coordinates into `config.py`.

3. **Run Pipeline**:
   ```bash
   python app.py
   ```
   Press `q` or `ESC` in the display window to exit.
