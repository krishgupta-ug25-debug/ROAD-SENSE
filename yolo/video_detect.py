import json

import cv2
import time
import threading
import requests
from collections import deque
from ultralytics import YOLO

# ---- CONFIG: change these to match your setup ----
POTHOLE_MODEL_PATH = "pothole_best.pt"              
ACCIDENT_MODEL_PATH = "accident_best.pt"            
VIDEO_SOURCE = "https://192.168.29.197:8080/video"  # RTSP or HTTP video stream URL, or local file path             
BACKEND_URL = "https://road-sense-ekn7.onrender.com/yolo/api/createdetection" 
BUS_ID = "TEST-BUS-01"
CONF_THRESHOLD = 0.4   
CONFIRM_FRAMES = 3      
HISTORY_SIZE = 5        
REPORT_COOLDOWN = 8     
SEND_TO_BACKEND = True  
REQUEST_TIMEOUT = 30   
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


def report_to_backend(frame, detection_type, confidence):
    print(f"[BACKEND] Reporting {detection_type} with confidence {confidence:.2f}")

    success, encoded = cv2.imencode(".jpg", frame)

    if not success:
        print("[BACKEND] Could not encode frame")
        return

    files = {
        "Image": (
            "webcam_frame.jpg",
            encoded.tobytes(),
            "image/jpeg"
        )
    }

    detections = [
        {
            "type": detection_type,
            "confidence": confidence
        }
    ]

    data = {
        "busId": BUS_ID,
        "latitude": "28.6139",
        "longitude": "77.2090",
        "detections": json.dumps(detections)
    }

    print("[BACKEND] Sending:", data)

    try:
        response = requests.post(
            BACKEND_URL,
            files=files,
            data=data,
            timeout=10
        )

        print("[BACKEND] Status:", response.status_code)
        print("[BACKEND] Response:", response.text)

    except Exception as e:
        print("[BACKEND] ERROR:", e)


def main():
    print("Loading models on-device (edge inference)...")
    pothole_model = YOLO(POTHOLE_MODEL_PATH)
    accident_model = YOLO(ACCIDENT_MODEL_PATH)
    models = [pothole_model, accident_model]  # run both on every frame

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
            # A single failed read is normal on a live camera/RTSP stream
            # (brief network hiccup) — don't treat it as "video ended" the
            # way we would for a finite video file. Retry a few times
            # before giving up, so a flaky bus camera connection doesn't
            # kill the whole pipeline over one dropped frame.
            print("[warn] frame read failed, retrying...")
            time.sleep(0.5)
            retry_count = getattr(main, "_retry_count", 0) + 1
            main._retry_count = retry_count
            if retry_count > 20:  # ~10 seconds of consecutive failures
                print("Lost connection to video source. Exiting.")
                break
            continue
        main._retry_count = 0

        # --- on-device inference (the actual "edge AI" step) ---
        # run each specialized model separately, then merge their boxes —
        # this generally gives cleaner results than one combined model,
        # since each model only has to learn one class instead of
        # distinguishing between two visually-overlapping ones.
        this_frame_classes = set()
        detections_this_frame = []

        for m in models:
            results = m(frame, conf=CONF_THRESHOLD, verbose=False)[0]
            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = m.names[cls_id]
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
                    target=report_to_backend, args=(frame.copy(),label,conf), daemon=True
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