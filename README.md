# RoadSense

### AI-powered road-incident monitoring

> Built for **Smart India Hackathon 2026** — Problem Statement **SIH26124**: *AI-Powered Mobile Urban Intelligence Platform Using Public Transport Fleet*.

**Live dashboard:** bespoke-malabi-7137a9.netlify.app 
**Backend API:** https://road-sense-ekn7.onrender.com

RoadSense detects road incidents from a video or camera source, records confirmed incidents, and presents them in a web dashboard. AI inference runs locally on the machine processing the video; the Node.js backend stores the confirmed results and the frontend visualises the stored incident data.

## What is implemented

- Separate local YOLO models for accidents and potholes.
- Temporal confirmation: a class must appear in **3 of the most recent 5 frames** before it is treated as an incident.
- Per-class cooldown (currently 8 seconds) to reduce duplicate reports while an incident remains in view.
- `Non Accident` predictions are discarded in `yolo/video_detect.py` **before** temporal confirmation, drawing, or backend reporting. They therefore do not reach MongoDB or the dashboard.
- Confirmed AI incidents include captured image evidence, class, confidence, configured bus ID, and configured coordinates.
- Manual accident and pothole reports from the dashboard.
- MongoDB storage, ImageKit image uploads, and reverse geocoding for a road name when one is not supplied.
- Dashboard cards and details, a Leaflet map with clustered incident markers, road intelligence, and incident-based traffic/fleet analytics.

## Architecture


flowchart LR
    A[Phone / IP Webcam or video source] --> B[Local laptop / edge device]
    B --> C[accident_best.pt]
    B --> D[pothole_best.pt]
    C --> E[Filter Non Accident in video_detect.py]
    D --> F[3-of-5 temporal confirmation]
    E --> F
    F --> G[Cooldown]
    G --> H[Confirmed incident with image and metadata]
    H --> I[Express backend]
    J[Manual dashboard report] --> I
    I --> K[MongoDB]
    I --> L[Image storage]
    K --> M[Frontend dashboard]
    L --> M


## AI detection flow

`yolo/video_detect.py` runs inference locally on the laptop/edge device. It loads two specialised trained models and runs both on each frame:

- `yolo/accident_best.pt` — Accident detection model (approximately 5.5 MB)
- `yolo/pothole_best.pt` — Pothole detection model (approximately 5.5 MB)

Predictions below the configured confidence threshold are excluded by YOLO. `Non Accident` predictions from the accident model are discarded immediately in `video_detect.py`, before they enter temporal confirmation, are drawn, or are reported. Remaining relevant labels enter a rolling five-frame history; only labels seen in at least **3 of 5 frames** are confirmed. A confirmed class is reported only if its cooldown has expired.

Only relevant confirmed detections proceed to the backend. The backend receives the already-confirmed AI result, image evidence, and metadata; it does **not** run the detection model as part of the current reporting path. `Non Accident` detections are never sent to the backend, database, or frontend.

### Location note

The AI script currently sends configured latitude and longitude values in `video_detect.py`. It does not automatically obtain GPS coordinates from the camera, phone, or vehicle. Update those configured values or integrate a location source before treating AI reports as live geolocated incidents.

## Dashboard

The static frontend in `frontend/index.html` provides:

- incident totals, cards, and detailed incident views;
- a Leaflet map that clusters stored incident locations and fits the view to them;
- manual reporting with image, bus ID, coordinates, road name, and incident type;
- road search and a simple risk classification based on stored incidents; and
- traffic/fleet summary values: total incidents, accidents, potholes, high-risk roads, and unique bus IDs.

“Active Buses” means unique bus IDs represented in stored incident records. It is not live bus tracking or active-vehicle telemetry. Similarly, the traffic/fleet view is incident-based, not a real-time traffic-density system.

### Road risk rules

Road intelligence uses the currently stored reports for a searched road:

| Risk | Rule |
| --- | --- |
| High | At least one accident, or at least three potholes |
| Medium | At least one pothole and no accident |
| Low | No recorded incidents |

This is a transparent count-based classification, not a predictive risk model.

## Technology

| Area | Used technology |
| --- | --- |
| Local inference | Python, Ultralytics YOLO, OpenCV |
| API | Node.js, Express, Multer |
| Data | MongoDB and Mongoose |
| Image storage | ImageKit |
| Dashboard | HTML, CSS, JavaScript, Leaflet, Leaflet.markercluster |
| Road-name lookup | OpenStreetMap Nominatim reverse geocoding |

## Project layout

```text
YOLO AI/
├── backend/
│   ├── src/
│   ├── requirements.txt
│   ├── package.json
│   └── server.js
├── frontend/
│   └── index.html
├── uploads/
└── yolo/
    ├── video_detect.py
    ├── accident_best.pt
    └── pothole_best.pt
```


## Setup

### Prerequisites

- Python with `venv`
- Node.js and npm
- A MongoDB connection
- An ImageKit private key
- The included `yolo/accident_best.pt` and `yolo/pothole_best.pt` model files

### 1. Create and activate a Python environment

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
```

### 2. Install backend packages

```powershell
cd backend
npm install
```

### 3. Configure backend environment variables

Create `backend/.env`:

```env
MONGO_URI=your_mongodb_connection_string
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
```

### 4. Configure local inference

The current accident and pothole model files are already in `yolo/`. Review the configuration near the top of `yolo/video_detect.py` and ensure the paths point to `accident_best.pt` and `pothole_best.pt`:

- `POTHOLE_MODEL_PATH`
- `ACCIDENT_MODEL_PATH`
- `VIDEO_SOURCE`
- `BACKEND_URL`
- `BUS_ID`
- `CONF_THRESHOLD`, confirmation, and cooldown values
- the currently configured latitude and longitude used for AI reports

### 5. Start the backend

Keep the virtual environment available if you will run local inference, then from `backend/` run:

```powershell
node server.js
```

### 6. Open the dashboard

Open `frontend/index.html` in a browser or serve the `frontend/` directory with a static web server. The frontend reads from the configured API base URL in `index.html`.

### 7. Run local detection

In a separate terminal, from the repository root:

```powershell
.\venv\Scripts\Activate.ps1
cd yolo
python video_detect.py
```

Press `q` in the OpenCV window to stop the detection loop.

## Video Input Options

RoadSense uses a **phone/IP Webcam stream as its primary mobile-camera demonstration**. The smartphone streams video over the local Wi-Fi network to the laptop, where YOLO inference runs locally on the laptop/edge device. A laptop webcam and a local `.mp4` file are alternative testing sources.

The current script selects its source through the `VIDEO_SOURCE` setting near the top of `yolo/video_detect.py`.

### 1. Laptop Webcam

```python
VIDEO_SOURCE = 0
```

```powershell
python video_detect.py 0
```

### 2. Local Video File

```python
VIDEO_SOURCE = "accident.mp4"
```

```powershell
python video_detect.py "accident.mp4"
```

### 3. Phone Camera via IP Webcam

```python
VIDEO_SOURCE = "http://PHONE_IP:8080/video"
```

```powershell
python video_detect.py "http://PHONE_IP:8080/video"
```

Replace `PHONE_IP` with the IP address displayed by the IP Webcam app on the phone. Ensure the phone and laptop are connected to the same local Wi-Fi network.

> **Current implementation note:** `video_detect.py` currently reads `VIDEO_SOURCE` from its configuration and does not parse positional command-line arguments. Set the matching `VIDEO_SOURCE` value first, then run:
>
> ```powershell
> python video_detect.py
> ```

## API

The backend currently exposes:

```text
POST /yolo/api/createdetection
GET  /yolo/api/getalldetection
GET  /yolo/api/getdetection/:id
```

Stored incident records contain a source (`AI` or `Manual`), bus ID, latitude, longitude, road name, image URL, detection data, and timestamps. The create endpoint requires an image upload and detection data; it can reverse-geocode a road name from the supplied coordinates when no road name is provided.

## Current limitations

- Detection quality varies with the training data, camera position, lighting, and scene conditions. False accident detections can still occur; filtering `Non Accident` labels only prevents those labels from being reported.
- AI location is configured in the script, rather than acquired automatically from GPS.
- The current cooldown is class-based, so it limits repeated reports for the same class within its time window; it is not object tracking.
- Dashboard map, road intelligence, and analytics reflect stored incidents after the dashboard is loaded or refreshed; they are not a live telemetry feed.
- Road risk uses simple stored-incident counts and does not forecast future risk.

## Potential next steps

- Integrate a GPS/location source for AI reports.
- Add live fleet telemetry and vehicle tracking.
- Improve and retrain the accident model as a single-class incident detector.
- Add object-aware duplicate suppression, alerts, historical trends, and operational deployment configuration.
