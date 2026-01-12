from fastapi import FastAPI, Request
import requests
from ultralytics import YOLO
import cv2, os,  numpy as np
from datetime import datetime

app = FastAPI()
model = YOLO(r"C:\Users\chinn\Desktop\Backend fly\best2.pt")
ESP32_CONTROL_URL = "http://10.84.177.176/control"

SAVE_DIR1 = "saved_images original v2"
os.makedirs(SAVE_DIR1, exist_ok=True)

SAVE_DIR = "saved_images v2"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.post("/predict")
async def predict(req: Request):
    img_bytes = await req.body()
    print(f"Received data size: {len(img_bytes)} bytes")
    
    if len(img_bytes) == 0:
        return {"error": "No image data received"}
    
    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    if img is None:
        return {"error": "Failed to decode image"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    original_path = f"{SAVE_DIR1}/original_{ts}.jpg"
    cv2.imwrite(original_path, img)
    
    results = model(img, conf=0.6, verbose=False)[0]

    annotated = results.plot()
    result_path = f"{SAVE_DIR}/result_{ts}.jpg"
    cv2.imwrite(result_path, annotated)


    detected = False
    if results.boxes:
        print(f"Number of boxes: {len(results.boxes)}")
        for b in results.boxes:
            cls = int(b.cls[0])
            conf = float(b.conf[0])
            print(f"Class: {cls}, Confidence: {conf}")
            if cls == 0:
                detected = True
                print("Fly detected")
    else:
        print("No boxes detected")

    if detected:
        try:
            response = requests.post(ESP32_CONTROL_URL, json={
                "action": "ON",
                "delay_ms": 1000
            })
            print(f"Sent to ESP32: {response.status_code}")
        except Exception as e:
            print(f"Error sending to ESP32: {e}")
    else:
        try:
            response = requests.post(ESP32_CONTROL_URL, json={
                "action": "OFF",
                "delay_ms": 5000
            })
            print(f"Sent to ESP32: {response.status_code}")
        except Exception as e:
            print(f"Error sending to ESP32: {e}")

    return {"detected": detected}

#uvicorn main:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)