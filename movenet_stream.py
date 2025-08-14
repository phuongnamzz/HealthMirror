import cv2
import time
import numpy as np
import tensorflow as tf
from flask import Flask, Response

# ===== Load MoveNet TFLite =====
interpreter = tf.lite.Interpreter(model_path="movenet_lightning.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Hàm suy luận MoveNet
def movenet_infer(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = tf.image.resize_with_pad(tf.expand_dims(img, axis=0), 192, 192)  # Thunder: 256x256
    img = tf.cast(img, dtype=tf.uint8)  # Model yêu cầu uint8
    interpreter.set_tensor(input_details[0]['index'], img.numpy())
    interpreter.invoke()
    keypoints = interpreter.get_tensor(output_details[0]['index'])[0][0]
    return keypoints  # 17 điểm [x, y, confidence]

# Hàm vẽ keypoints
def draw_keypoints(frame, keypoints):
    h, w, _ = frame.shape
    for kp in keypoints:
        ky, kx, kp_conf = kp[1], kp[0], kp[2]
        if kp_conf > 0.3:  # Chỉ vẽ nếu đủ tin cậy
            cx, cy = int(kx * w), int(ky * h)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
    return frame

# Flask app
app = Flask(__name__)
cap = cv2.VideoCapture(0)  # Camera index

prev_time = time.time()
fps = 0

def gen_frames():
    global prev_time, fps
    while True:
        success, frame = cap.read()
        if not success:
            break

        keypoints = movenet_infer(frame)
        frame = draw_keypoints(frame, keypoints)

        # FPS tính toán
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
