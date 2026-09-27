import time
import threading
import webbrowser
import cv2
from flask import Flask, Response, render_template_string
import config
from tracker import PersonTracker
from zones import ZoneManager
from risk_engine import RiskEngine
from predictor import CrowdPredictor
from simulator import ScenarioSimulator
from esp32_controller import ESP32Controller

app = Flask(__name__)

# Global frame buffer and metrics
latest_frame_bytes = None
latest_metrics = {
    "total": 0,
    "zones": {"A": 0, "B": 0, "C": 0},
    "risks": {"A": "NORMAL", "B": "NORMAL", "C": "NORMAL"},
    "rocs": {"A": 0.0, "B": 0.0, "C": 0.0},
    "action": "NORMAL",
    "esp32": "SIMULATED: NORMAL",
    "ttc": "N/A"
}
frame_lock = threading.Lock()


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>BheedRakshak AI — Live Stream & Analytics</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }
        h1 { font-size: 24px; margin-bottom: 12px; color: #38bdf8; }
        .container { max-width: 1100px; margin: 0 auto; }
        .video-card { background: #1e293b; border-radius: 10px; padding: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); margin-bottom: 20px; }
        .video-box { width: 100%; max-height: 580px; object-fit: contain; border-radius: 8px; background: #000; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-top: 15px; }
        .card { background: #1e293b; border-radius: 8px; padding: 14px; text-align: left; border-left: 4px solid #38bdf8; }
        .card h3 { font-size: 13px; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px; }
        .card .value { font-size: 20px; font-weight: bold; }
        .badge-NORMAL { color: #4ade80; }
        .badge-WARNING { color: #facc15; }
        .badge-HIGH { color: #fb923c; }
        .badge-CRITICAL { color: #f87171; }
    </style>
</head>
<body>
    <div class="container">
        <h1>BheedRakshak AI — Live Predictive Crowd Safety</h1>
        <div class="video-card">
            <img class="video-box" src="/video_feed" alt="Live Feed" />
        </div>
        <div class="dashboard">
            <div class="card">
                <h3>Total Crowd Count</h3>
                <div class="value" id="total">{{ metrics.total }}</div>
            </div>
            <div class="card">
                <h3>Zone Counts</h3>
                <div class="value">A: {{ metrics.zones.A }} | B: {{ metrics.zones.B }} | C: {{ metrics.zones.C }}</div>
            </div>
            <div class="card">
                <h3>Risk Levels</h3>
                <div class="value">
                    <span class="badge-{{ metrics.risks.A }}">A:{{ metrics.risks.A }}</span> |
                    <span class="badge-{{ metrics.risks.B }}">B:{{ metrics.risks.B }}</span> |
                    <span class="badge-{{ metrics.risks.C }}">C:{{ metrics.risks.C }}</span>
                </div>
            </div>
            <div class="card">
                <h3>Recommended Action</h3>
                <div class="value" style="color:#38bdf8;">{{ metrics.action }}</div>
            </div>
            <div class="card">
                <h3>ESP32 Status</h3>
                <div class="value" style="font-size:15px;">{{ metrics.esp32 }}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    """Render the main live dashboard page."""
    with frame_lock:
        metrics = latest_metrics.copy()
    return render_template_string(HTML_PAGE, metrics=metrics)


def generate_mjpeg():
    """Generator function yielding multipart JPEG frames for the web browser."""
    global latest_frame_bytes
    while True:
        with frame_lock:
            frame_data = latest_frame_bytes
        if frame_data is not None:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n")
        time.sleep(0.03)


@app.route("/video_feed")
def video_feed():
    """MJPEG stream endpoint for live browser viewing."""
    return Response(generate_mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")


def pipeline_worker():
    """Background worker thread running the video ingestion, YOLO tracking, and safety analytics."""
    global latest_frame_bytes, latest_metrics

    if config.SOURCE == "webcam":
        source = config.WEBCAM_INDEX
    elif config.SOURCE == "phone":
        source = config.PHONE_URL
    else:
        source = config.VIDEO_FILE

    print(f"[INIT] Connecting to video source [{config.SOURCE}]: {source}")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Unable to open video source '{source}'")
        return

    if config.SOURCE in ["phone", "webcam"]:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps != fps:
        fps = 30.0
    frame_interval = 1.0 / fps

    zone_mgr = ZoneManager()
    tracker = PersonTracker()
    risk_eng = RiskEngine()
    predictor = CrowdPredictor()
    simulator = ScenarioSimulator()
    esp32 = ESP32Controller()

    print("[INIT] Core pipeline initialized. Processing frames...")
    frame_count = 0
    last_print_time = time.time()

    while True:
        loop_start = time.time()
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] End of video stream or cannot fetch frame.")
            break

        frame_count += 1

        # 1. Tracking & Zone assignment
        tracks = tracker.track(frame, zone_manager=zone_mgr)
        total_persons = len(tracks)

        # 2. Per-zone count aggregation
        zone_counts = {z: 0 for z in config.ZONE_POLYGONS}
        for tr in tracks:
            z = tr["zone"]
            if z in zone_counts:
                zone_counts[z] += 1

        # 3. Risk Engine evaluation
        zone_risks = {}
        for z, count in zone_counts.items():
            zone_risks[z] = risk_eng.evaluate_zone(z, count)

        # 4. Predictor updates & time-to-critical calculation
        zone_rocs = {}
        zone_ttc = {}
        for z, count in zone_counts.items():
            predictor.update(z, count)
            crit_thresh = config.RISK_THRESHOLDS.get(z, {}).get("CRITICAL", 6)
            roc, ttc = predictor.predict(z, crit_thresh)
            zone_rocs[z] = roc
            zone_ttc[z] = ttc

        # 5. Determine most critical zone for simulation
        highest_risk_zone = max(
            zone_counts.keys(),
            key=lambda z: (
                3 if zone_risks[z] == "CRITICAL" else
                2 if zone_risks[z] == "HIGH" else
                1 if zone_risks[z] == "WARNING" else 0,
                zone_counts[z]
            )
        )
        target_count = zone_counts[highest_risk_zone]
        target_roc = max(0.0, zone_rocs[highest_risk_zone])
        target_crit = config.RISK_THRESHOLDS.get(highest_risk_zone, {}).get("CRITICAL", 6)

        # 6. Simulator scenario evaluation
        recommended_action, sim_results = simulator.simulate(target_count, target_roc, target_crit)

        # 7. ESP32 Hardware Dispatch
        success, dispatch_url = esp32.send_command(recommended_action)

        # 8. Visual rendering (flat lines, boxes, and HUD)
        zone_mgr.draw_zones(frame, zone_risks=zone_risks)

        for tr in tracks:
            x1, y1, x2, y2 = tr["box"]
            z = tr["zone"] or "?"
            risk_state = zone_risks.get(z, "NORMAL")
            color = risk_eng.get_color(risk_state)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID:{tr['id']} ({z})", (x1, max(20, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Top HUD overlay
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 75), (20, 20, 20), -1)
        hud_row1 = f"Total: {total_persons} | " + " | ".join([
            f"Zone {z}: {zone_counts[z]} [{zone_risks[z]}]" for z in zone_counts
        ])
        cv2.putText(frame, hud_row1, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        ttc_str = f"{zone_ttc[highest_risk_zone]:.1f}s" if zone_ttc[highest_risk_zone] is not None else "N/A"
        hud_row2 = f"Focus {highest_risk_zone} (RoC: {zone_rocs[highest_risk_zone]:+.2f}/s, TTC: {ttc_str}) -> Rec: {recommended_action} | ESP32: {esp32.last_status}"
        cv2.putText(frame, hud_row2, (15, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

        # Encode frame to JPEG for web stream
        display_frame = cv2.resize(frame, (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT))
        ret_enc, buffer = cv2.imencode(".jpg", display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ret_enc:
            with frame_lock:
                latest_frame_bytes = buffer.tobytes()
                latest_metrics = {
                    "total": total_persons,
                    "zones": zone_counts,
                    "risks": zone_risks,
                    "rocs": zone_rocs,
                    "action": recommended_action,
                    "esp32": esp32.last_status,
                    "ttc": ttc_str
                }

        # Also show OpenCV window if interactive session allows it
        try:
            cv2.imshow(config.DISPLAY_WINDOW_NAME, display_frame)
            if cv2.waitKey(1) & 0xFF in [27, ord('q'), ord('Q')]:
                break
        except Exception:
            pass

        now = time.time()
        if now - last_print_time >= 1.0:
            last_print_time = now
            print(f"[Frame {frame_count:04d}] Total: {total_persons} | "
                  f"Zones: {zone_counts} | "
                  f"Risks: {zone_risks} | "
                  f"RoC: {zone_rocs} | "
                  f"Action: {recommended_action} | "
                  f"ESP32: {esp32.last_status}")

        if config.SOURCE == "file":
            elapsed = time.time() - loop_start
            wait_time_ms = max(0.001, frame_interval - elapsed)
            time.sleep(wait_time_ms)

    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass


def run_pipeline():
    """Start background video pipeline worker and launch web dashboard on port 5000."""
    worker = threading.Thread(target=pipeline_worker, daemon=True)
    worker.start()

    print("\n" + "=" * 65)
    print(" BheedRakshak AI Live Stream Server is RUNNING!")
    print(" Open in any browser: http://localhost:5000")
    print("=" * 65 + "\n")

    try:
        webbrowser.open("http://localhost:5000")
    except Exception:
        pass

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_pipeline()
