import sys
import os
import json
from ultralytics import YOLO

model_path= os.path.join(os.path.dirname(__file__), 'best.pt')
model= YOLO(model_path)

image_path = sys.argv[1]

results = model(image_path,verbose=False)

detections = []

for result in results:
    for box in result.boxes:
        detections.append({
            "class": result.names[int(box.cls[0])],
            "confidence": float(box.conf[0]),
            "box": [float(x) for x in box.xyxy[0]]
        })

print(json.dumps(detections))