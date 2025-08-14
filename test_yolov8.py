from flask import Flask, Response
import cv2
from ultralytics import YOLO
import time

app = Flask(__name__)

# Tải model pose nhẹ nhất
model = YOLO("yolov8n-pose.pt")  # Tự tải nếu chưa có

# Mở camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def gen_frames():
    prev_time = 0
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.rotate(frame, cv2.ROTATE_180)
        # Dự đoán pose
        results = model(frame, imgsz=320, verbose=False)

        # Vẽ keypoints
        annotated_frame = results[0].plot()

        # Tính FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time else 0
        prev_time = curr_time

        # Hiển thị FPS lên frame
        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        # Chuyển sang JPEG để stream
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<h1>YOLOv8 Pose Stream</h1><img src="/video">'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
