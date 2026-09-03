"""
Edge-AI video detection using:
- best.pt          -> accident + pothole
- pothole_best.pt  -> specialized pothole verification

Inference runs locally on-device.
Backend is contacted only for confirmed detections.
"""

import json
import cv2
import time
import threading
import requests
from collections import deque
from ultralytics import YOLO


# ---- CONFIG ----
MODEL_PATH = "best.pt"
POTHOLE_MODEL_PATH = "pothole_best.pt"

VIDEO_SOURCE = 0
BACKEND_URL = "http://localhost:3000/yolo/api/createdetection"

BUS_ID = "TEST-BUS-01"

CONF_THRESHOLD = 0.4
CONFIRM_FRAMES = 3
HISTORY_SIZE = 5
REPORT_COOLDOWN = 8

SEND_TO_BACKEND = True
REQUEST_TIMEOUT = 30

SAVE_OUTPUT = False
OUTPUT_PATH = "annotated_output.mp4"
# ----------------


class_history = deque(maxlen=HISTORY_SIZE)
last_reported_time = {}


def confirmed_classes():
    counts = {}

    for classes in class_history:
        for c in classes:
            counts[c] = counts.get(c, 0) + 1

    return {
        c for c, n in counts.items()
        if n >= CONFIRM_FRAMES
    }


def report_to_backend(frame, detections):
    success, encoded = cv2.imencode(".jpg", frame)

    if not success:
        print("[warn] could not encode frame for upload")
        return

    files = {
        "Image": (
            "frame.jpg",
            encoded.tobytes(),
            "image/jpeg"
        )
    }

    data_fields = {
        "busId": BUS_ID,
        "latitude": "28.6139",
        "longitude": "77.2090",
        "detections": json.dumps([
            {
                "class": label,
                "confidence": conf,
                "box": box
            }
            for label, conf, box in detections
        ])
    }

    try:
        resp = requests.post(
            BACKEND_URL,
            files=files,
            data=data_fields,
            timeout=REQUEST_TIMEOUT
        )

        if not resp.ok:
            print(
                f"[warn] backend report failed: "
                f"{resp.status_code} — {resp.text}"
            )
            return

        print(
            f"[backend] reported confirmed detection "
            f"-> {resp.status_code}"
        )

    except requests.exceptions.RequestException as e:
        print(f"[warn] backend report failed: {e}")


def main():

    print("Loading models on-device...")

    # Main model
    model = YOLO(MODEL_PATH)

    # Specialized pothole model
    pothole_model = YOLO(POTHOLE_MODEL_PATH)

    print("Main model loaded:", model.names)
    print("Pothole model loaded:", pothole_model.names)

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

        writer = cv2.VideoWriter(
            OUTPUT_PATH,
            fourcc,
            fps,
            (w, h)
        )

    print(
        "Watching for potholes/accidents..."
        " (press 'q' to quit)"
    )

    last_heartbeat = time.time()
    HEARTBEAT_INTERVAL = 5

    while True:

        loop_start = time.time()

        ret, frame = cap.read()

        if not ret:
            break

        # -------------------------------------------------
        # MAIN MODEL
        # Detects accident + pothole
        # -------------------------------------------------

        results = model(
            frame,
            conf=CONF_THRESHOLD,
            verbose=False
        )[0]

        this_frame_classes = set()
        detections_this_frame = []

        for box in results.boxes:

            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])

            x1, y1, x2, y2 = [
                int(v) for v in box.xyxy[0]
            ]

            # ---------------------------------------------
            # ACCIDENT
            # Main model detection is used directly
            # ---------------------------------------------

            if label.lower() == "accident":

                this_frame_classes.add("accident")

                detections_this_frame.append(
                    (
                        "accident",
                        conf,
                        [x1, y1, x2, y2]
                    )
                )

            # ---------------------------------------------
            # POTHOLE
            # Verify using specialized pothole model
            # ---------------------------------------------

            elif label.lower() == "pothole":

                specialist_results = pothole_model(
                    frame,
                    conf=CONF_THRESHOLD,
                    verbose=False
                )[0]

                for pbox in specialist_results.boxes:

                    pconf = float(pbox.conf[0])

                    px1, py1, px2, py2 = [
                        int(v) for v in pbox.xyxy[0]
                    ]

                    this_frame_classes.add("pothole")

                    detections_this_frame.append(
                        (
                            "pothole",
                            pconf,
                            [px1, py1, px2, py2]
                        )
                    )

        # -------------------------------------------------
        # TEMPORAL VOTING
        # -------------------------------------------------

        class_history.append(this_frame_classes)

        trusted = confirmed_classes()

        if (
            not trusted
            and
            (time.time() - last_heartbeat)
            >= HEARTBEAT_INTERVAL
        ):
            print(
                "[status] watching..."
                " no confirmed detections right now"
            )

            last_heartbeat = time.time()

        # -------------------------------------------------
        # DRAW + REPORT CONFIRMED DETECTIONS
        # -------------------------------------------------

        now = time.time()

        for label, conf, coords in detections_this_frame:

            if label not in trusted:
                continue

            x1, y1, x2, y2 = coords

            if label.lower() == "accident":
                color = (0, 0, 255)
            else:
                color = (0, 165, 255)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                f"{label} {conf:.2f}",
                (x1, max(y1 - 8, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

            # ---------------------------------------------
            # BACKEND REPORT WITH COOLDOWN
            # ---------------------------------------------

            last_time = last_reported_time.get(
                label,
                0
            )

            if (
                SEND_TO_BACKEND
                and
                (now - last_time) >= REPORT_COOLDOWN
            ):

                threading.Thread(
                    target=report_to_backend,
                    args=(
                        frame.copy(),
                        detections_this_frame.copy()
                    ),
                    daemon=True
                ).start()

                last_reported_time[label] = now

        # -------------------------------------------------
        # DISPLAY
        # -------------------------------------------------

        cv2.imshow(
            "Edge Detection",
            frame
        )

        if writer:
            writer.write(frame)

        elapsed = time.time() - loop_start

        remaining_ms = max(
            1,
            int(
                (frame_duration - elapsed) * 1000
            )
        )

        if (
            cv2.waitKey(remaining_ms) & 0xFF
            == ord("q")
        ):
            break

    cap.release()

    if writer:
        writer.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()