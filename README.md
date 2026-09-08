# RoadSense – AI-Powered Urban Road Intelligence Platform

RoadSense is an AI-powered road monitoring platform that uses public transport fleet cameras to detect road incidents such as potholes and accidents. AI inference runs locally on the edge device, while confirmed incidents are sent to a backend for storage and visualization.

## 1. Project Information

- **Project Title:** RoadSense – AI-Powered Urban Road Intelligence Platform
- **PS ID:** SIH26124
- **PS Title:** AI-Powered Mobile Urban Intelligence Platform Using Public Transport Fleet
- **Organization:** Bharat Electronics Limited
- **Category:** Software
- **Theme:** Smart Automation

## Live Demo

- **Frontend:** [RoadSense Dashboard](bespoke-malabi-7137a9.netlify.app)
- **Backend API:** [RoadSense Backend](https://road-sense-ekn7.onrender.com)

## 2. Problem Statement

Urban roads can develop potholes and other hazardous conditions, while road accidents may go unnoticed or remain difficult to track systematically. Public transport vehicles already travel across large portions of a city, creating an opportunity to use their cameras as a distributed road-monitoring system.

RoadSense addresses this problem by using AI-based visual detection to identify road incidents from camera feeds and provide centralized incident intelligence for monitoring and analysis.

## 3. Proposed Solution

RoadSense uses camera/video feeds from public transport vehicles or other supported video sources. YOLO-based models perform detection locally on the connected laptop/edge device.

The system uses:

- `accident_best.pt` for accident detection
- `pothole_best.pt` for pothole detection
- Temporal confirmation across 3 of 5 frames to reduce transient detections
- Filtering of `Non Accident` predictions before they enter the incident pipeline
- Image evidence and detection metadata for confirmed incidents
- A backend API for incident storage
- MongoDB for incident data
- ImageKit for incident image storage
- A web dashboard for visualization and road-level analysis

## 4. Key Features

- AI-based accident detection
- AI-based pothole detection
- Confidence scores
- Local/edge YOLO inference
- Temporal confirmation using 3 of 5 frames
- Non Accident prediction filtering
- Incident image/evidence capture
- Manual incident reporting
- GPS coordinate recording
- Road name association
- Centralized incident database
- GIS incident map with marker clustering
- Road-wise incident analysis
- Road risk classification
- AI vs Manual incident tracking
- Traffic / fleet analytics
- Unique bus identification from incident data

## 5. Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Node.js, Express.js
- **Machine Learning:** Ultralytics YOLO, Python, OpenCV
- **Models:** YOLO11n-based Accident and Pothole models
- **Database:** MongoDB
- **Image Storage:** ImageKit
- **Maps / GIS:** Leaflet, OpenStreetMap
- **Video Input:** Laptop webcam, local video files, or smartphone IP Webcam
- **Deployment:** Render

## 6. Architecture

The system performs AI inference locally before sending confirmed incidents to the backend.

```text
                    Video Input
                        |
          +-------------+-------------+
          |             |             |
     Laptop Webcam    .mp4       Phone / IP Webcam
          |             |             |
          +-------------+-------------+
                        |
                        v
              Local Laptop / Edge Device
                        |
             +----------+----------+
             |                     |
             v                     v
    accident_best.pt       pothole_best.pt
             |                     |
             +----------+----------+
                        |
                        v
                YOLO Detection
                        |
                        v
             Non Accident Filter
                        |
                        v
             Temporal Confirmation
                  (3 of 5 frames)
                        |
                        v
                Confirmed Incident
                        |
              +---------+---------+
              |                   |
              v                   v
        Backend API          Image Evidence
              |                   |
              v                   v
           MongoDB              ImageKit
              |
              v
        Frontend Dashboard
              |
       +------+------+----------------+
       |             |                |
       v             v                v
    GIS Map     Road Intelligence   Fleet Analytics
```
## How it works ?
A supported camera or video source provides the input.
YOLO models run locally on the laptop/edge device.
Accident and pothole detections are evaluated frame by frame.
Non Accident predictions are filtered out before entering the incident pipeline.
A detection must be confirmed across 3 of 5 frames.
Confirmed incidents are reported to the backend.
The backend stores incident metadata in MongoDB and images through ImageKit.
The frontend displays incidents on the dashboard and GIS map.
Road Intelligence and Traffic/Fleet Analytics provide higher-level incident analysis.
## 7. Repository Structure
```text
ROAD-SENSE/
├── README.md
├── SUBMISSION_GUIDE.md
├── .gitignore
│
├── submission/
│   ├── PRESENTATION.md
│   ├── DEMO.md
│   └── RoadSense_SIH2026_Presentation.pptx
│
├── docs/
│   └── architecture.md
│
├── assets/
│   └── screenshots/
│
├── backend/
│   ├── src/
│   │   ├── routers/
│   │   └── services/
│   ├── server.js
│   ├── package.json
│   └── requirements.txt
│
├── frontend/
│   └── index.html
│
└── yolo/
    ├── accident_best.pt
    ├── pothole_best.pt
    ├── main.py
    └── video_detect.py
```
## What goes where?
Item	Location
Source code	backend/, frontend/, yolo/
YOLO model weights	yolo/
Architecture documentation	docs/
Project screenshots	assets/screenshots/
Final PPT	submission/
Demo video link	submission/DEMO.md
Project overview	README.md
## 8. Final Presentation

The final SIH presentation is included in:

submission/

See submission/PRESENTATION.md for the presentation reference.

## 9. Demo Video

The project demo video will be linked in:

submission/DEMO.md

The demonstration covers the complete workflow from video input and AI detection to backend storage and frontend visualization.

## 10. Screenshots / Prototype Photos

Important project screenshots and prototype images are stored in:

assets/screenshots/

Recommended screenshots include:

Main dashboard
AI detection output
GIS incident map
Road Intelligence
Traffic / Fleet Analytics
Manual incident reporting
Mobile/IP Webcam detection
## 11. Installation
Backend
cd backend
npm install

Configure the required environment variables in:

backend/.env

Do not commit .env or any credentials to GitHub.

YOLO / AI

Create and activate a Python virtual environment, then install the required Python dependencies.

cd yolo
pip install -r requirements.txt

The repository contains:

accident_best.pt
pothole_best.pt

so the trained model weights are available locally after cloning the repository.

Frontend

The frontend can be served using a local web server or opened through the project's configured deployment.

## 12. Run
Start Backend
cd backend
npm start
Run YOLO Detection

RoadSense supports three video input modes.

Laptop webcam:

python video_detect.py 0

Local video file:

python video_detect.py "accident.mp4"

Phone camera using IP Webcam:

python video_detect.py "http://PHONE_IP:8080/video"

The IP Webcam option allows a smartphone camera to stream video over the local Wi-Fi network to the laptop, where YOLO inference is performed locally.

Dashboard

Open the frontend dashboard after the backend is running.

## 13. Future Scope
Live public transport fleet telemetry
Automatic GPS acquisition from connected vehicles
Historical road-condition trends
Predictive road maintenance
Real-time traffic-density estimation
Mobile application
Automated alerts and notifications
Integration with municipal road-management systems
Improved event-level tracking and duplicate prevention
Model Information

RoadSense uses two trained YOLO11n-based models:

Model	Purpose
accident_best.pt	Accident detection
pothole_best.pt	Pothole detection

The accident model was trained using an accident/non-accident dataset. During application inference, Non Accident predictions are filtered before temporal confirmation and backend submission, so they are not stored as incidents or displayed on the frontend.

The pothole model is trained specifically for pothole detection.
