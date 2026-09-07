# RoadSense Architecture

## System Architecture

### High-level flow

Video Input
  |
  v
Local Laptop / Edge Device
  |
  +------------------> Accident YOLO Model
  |
  +------------------> Pothole YOLO Model
  |
  v
Non Accident Filtering
  |
  v
Temporal Confirmation (3 of 5 frames)
  |
  v
Confirmed Incident
  |
  +------------------> ImageKit
  |
  v
Backend API
  |
  +------------------> MongoDB
  |
  v
Frontend Dashboard
  |
  +------------------> GIS Map
  |
  +------------------> Road Intelligence
  |
  +------------------> Fleet Analytics

## Components

### Video Input

Provides the camera or video stream used for road monitoring.

RoadSense supports:

- Laptop webcam
- Local video files
- Smartphone camera using IP Webcam

### Local Laptop / Edge Device

Receives the video input and performs AI inference locally using Python, OpenCV, and Ultralytics YOLO.

### Accident YOLO Model

Uses `accident_best.pt` to detect accident-related events.

The application filters `Non Accident` detections before they proceed through the incident pipeline.

### Pothole YOLO Model

Uses `pothole_best.pt` to detect potholes in the road scene.

### Temporal Confirmation

RoadSense uses a 3-of-5 frame confirmation rule to reduce transient or unstable detections.

An incident is considered confirmed when the detected class appears in at least 3 of the previous 5 frames.

### Backend API

The Node.js / Express.js backend receives confirmed incident data and image evidence, validates the request, and coordinates storage.

### Database

MongoDB stores incident records including:

- Bus ID
- Latitude
- Longitude
- Road name
- Detection information
- Image URL
- Timestamp

### Image Storage

ImageKit stores incident images uploaded by the detection pipeline or manual reporting system.

### Frontend Dashboard

The web dashboard displays the collected incident data and provides:

- GIS incident visualization
- Road condition intelligence
- Traffic / fleet analytics
- Manual incident reporting

## Data Flow

The complete RoadSense flow is:

Video Input → Local YOLO Inference → Filtering → Temporal Confirmation → Backend API → MongoDB / ImageKit → Frontend Dashboard