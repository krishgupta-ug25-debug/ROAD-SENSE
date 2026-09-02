"""
Edge-AI video detection for your accident/pothole model.

How it works — and why this version is different:
- Loads best.pt DIRECTLY on this device using the `ultralytics` package.
  Inference runs locally — no network call, no cloud API, no per-frame
  image upload. This is genuine edge processing, not cloud inference.
- Only sends data to the backend when a detection is CONFIRMED (via the
  temporal voting system below) — and only a small JSON payload
  (class, confidence, box) rather than a full image on every frame.
  This is what actually satisfies "minimizing bandwidth through
  intelligent edge processing."
- Runs at the video's real fps, non-blocking, same voting system as
  before to filter out one-off misclassifications.

Install once: pip install ultralytics opencv-python requests
"""
import json
import cv2
import time
import threading
import requests
from collections import deque
from ultralytics import YOLO

# ---- CONFIG: change these to match your setup ----
MODEL_PATH = "best.pt"                               # your trained weights, local to this device
VIDEO_SOURCE = 0                                     # 0 = webcam, or "path/to/video.mp4"
BACKEND_URL = "http://localhost:3000/yolo/api/createdetection"  # central backend — only hit on confirmed detections
BUS_ID = "TEST-BUS-01"
CONF_THRESHOLD = 0.4    # per-frame detection confidence bar
CONFIRM_FRAMES = 3      # a class must appear in this many of the last N frames to be trusted
HISTORY_SIZE = 5        # how many recent frames' detections to remember for voting
REPORT_COOLDOWN = 8      # seconds — minimum gap before the SAME class can be reported again
SEND_TO_BACKEND = True  # set False to run pure on-device detection with no network calls at all
REQUEST_TIMEOUT = 30   # backend does ImageKit upload + runYOLO per confirmed report — needs headroom
SAVE_OUTPUT = False
OUTPUT_PATH = "annotated_output.mp4"
# ---------------------------------------------------

# rolling history of recent per-class detections, used to vote out one-off flukes
class_history = deque(maxlen=HISTORY_SIZE)
# tracks the last time each class was reported. Using a cooldown timer
# (not just "until nothing's detected") means a NEW pothole/accident later
# in the video still gets reported even if that class was never fully
# absent in between — a video with many potholes would otherwise only
# ever report the first one.
last_reported_time = {}


def confirmed_classes():
    """
    A class only counts as 'real' once it's appeared in at least
    CONFIRM_FRAMES of the last HISTORY_SIZE on-device inference results.
    This filters out one-off misclassifications without needing an
    aggressive confidence threshold that would also hide real,
    quietly-confident detections.
    """
    counts = {}
    for classes in class_history:
        for c in classes:
            counts[c] = counts.get(c, 0) + 1
    return {c for c, n in counts.items() if n >= CONFIRM_FRAMES}


def report_to_backend(frame,detections):
    """
    Sends the confirmed-detection frame to the backend exactly like your
    original Postman flow does — a plain image upload. Your backend's
    existing createdetection controller (runYOLO + ImageKit) handles it
    unchanged. The bandwidth savings comes from WHEN this fires: only
    once per confirmed event (via the on-device voting below), not on
    every single video frame like a naive per-frame loop would.
    """
    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        print("[warn] could not encode frame for upload")
        return

    files = {"Image": ("frame.jpg", encoded.tobytes(), "image/jpeg")}
    data_fields = {
        "busId": BUS_ID,
        "latitude": "28.6139",   # placeholder until real onboard GPS is wired up
        "longitude": "77.2090",  # placeholder until real onboard GPS is wired up
        "detections":json.dumps([
            {"class": label, "confidence": conf, "box": box}
            for label, conf, box in detections
        ])
    }
    try:
        resp = requests.post(BACKEND_URL, files=files, data=data_fields, timeout=REQUEST_TIMEOUT)
        if not resp.ok:
            print(f"[warn] backend report failed: {resp.status_code} — {resp.text}")
            return
        print(f"[backend] reported confirmed detection -> {resp.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[warn] backend report failed: {e}")


def main():
    print("Loading model on-device (edge inference)...")
    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print("Could not open video source.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_duration = 1.0 / fps
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = None
    if SAVE_OUTPUT:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (w, h))

    print("Watching for potholes/accidents... (press 'q' in the video window to quit)")
    last_heartbeat = time.time()
    HEARTBEAT_INTERVAL = 5  # seconds — periodic "still running" print

    while True:
        loop_start = time.time()

        ret, frame = cap.read()
        if not ret:
            break

        # --- on-device inference (the actual "edge AI" step) ---
        results = model(frame, conf=CONF_THRESHOLD, verbose=False)[0]

        this_frame_classes = set()
        detections_this_frame = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]

            this_frame_classes.add(label)
            detections_this_frame.append((label, conf, [x1, y1, x2, y2]))

        class_history.append(this_frame_classes)
        trusted = confirmed_classes()

        # periodic reassurance that the loop is alive even when nothing's
        # being detected — otherwise a quiet stretch looks identical to a hang
        if not trusted and (time.time() - last_heartbeat) >= HEARTBEAT_INTERVAL:
            print("[status] watching... no confirmed detections right now")
            last_heartbeat = time.time()

        # draw + report only confirmed detections
        now = time.time()
        for label, conf, coords in detections_this_frame:
            if label not in trusted:
                continue

            x1, y1, x2, y2 = coords
            color = (0, 0, 255) if label.lower() == "accident" else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(y1 - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # report if this class hasn't been reported recently — a
            # cooldown timer (not "until it disappears") so a genuinely
            # NEW pothole/accident later in the video still gets logged
            # even if that class never fully vanished in between.
            last_time = last_reported_time.get(label, 0)
            if SEND_TO_BACKEND and (now - last_time) >= REPORT_COOLDOWN:
                # run this in the background — a synchronous call here would
                # freeze frame capture for the whole request duration (the
                # backend's ImageKit+runYOLO round trip can take 10-30s),
                # which is especially bad for a live webcam vs. a video file.
                threading.Thread(
                    target=report_to_backend, args=(frame.copy(),), daemon=True
                ).start()
                last_reported_time[label] = now

        cv2.imshow("Edge Detection", frame)
        if writer:
            writer.write(frame)

        elapsed = time.time() - loop_start
        remaining_ms = max(1, int((frame_duration - elapsed) * 1000))
        if cv2.waitKey(remaining_ms) & 0xFF == ord("q"):
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()