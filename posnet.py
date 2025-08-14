# import cv2
# import numpy as np
# import tensorflow as tf
# import time
# from flask import Flask, jsonify

# MODEL_PATH = "posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite"

# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
# interpreter.allocate_tensors()

# input_details = interpreter.get_input_details()
# output_details = interpreter.get_output_details()
# input_shape = input_details[0]['shape']
# height, width = input_shape[1], input_shape[2]

# def run_pose_estimation(frame):
#     input_image = cv2.resize(frame, (width, height))
#     input_image = input_image.astype(np.float32) / 255.0
#     input_image = np.expand_dims(input_image, axis=0)
#     interpreter.set_tensor(input_details[0]['index'], input_image)
#     interpreter.invoke()
#     heatmaps = interpreter.get_tensor(output_details[0]['index'])
#     offsets = interpreter.get_tensor(output_details[1]['index'])
#     keypoints = process_output(heatmaps, offsets, frame)
#     return keypoints

# def process_output(heatmaps, offsets, frame, threshold=0.2):
#     keypoints = []
#     heatmap = heatmaps[0]
#     offset = offsets[0]
#     for i in range(heatmap.shape[-1]):
#         heatmap_i = heatmap[:, :, i]
#         y, x = np.unravel_index(np.argmax(heatmap_i), heatmap_i.shape)
#         confidence = heatmap_i[y, x]
#         if confidence > threshold:
#             offset_y = offset[y, x, i]
#             offset_x = offset[y, x, i + 17]
#             keypoint_x = (x * frame.shape[1] / heatmap.shape[1]) + offset_x
#             keypoint_y = (y * frame.shape[0] / heatmap.shape[0]) + offset_y
#             keypoints.append({"x": int(keypoint_x), "y": int(keypoint_y), "confidence": float(confidence)})
#         else:
#             keypoints.append(None)
#     return keypoints

# app = Flask(__name__)

# @app.route('/pose')
# def pose():
#     ret, image = cap.read()
#     if not ret:
#         return jsonify({"error": "Camera read failed"}), 500
#     keypoints = run_pose_estimation(image)
#     return jsonify({"keypoints": keypoints})

# if __name__ == '__main__':
#     time.sleep(0.1)
#     app.run(host='0.0.0.0', port=5000)





import cv2
import numpy as np
import tensorflow as tf
import time
from flask import Flask, jsonify, Response, render_template_string

# Đường dẫn đến mô hình PoseNet
MODEL_PATH = "posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite"

# Khởi tạo camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Khởi tạo TensorFlow Lite Interpreter
try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# Lấy thông tin đầu vào và đầu ra
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape']
height, width = input_shape[1], input_shape[2]
print(f"Model input shape: {input_shape}")

# Hàm xử lý pose estimation
def run_pose_estimation(frame):
    try:
        input_image = cv2.resize(frame, (width, height))
        input_image = input_image.astype(np.float32) / 127.5 - 1.0  # Chuẩn hóa [-1, 1]
        input_image = np.expand_dims(input_image, axis=0)
        
        interpreter.set_tensor(input_details[0]['index'], input_image)
        interpreter.invoke()
        
        heatmaps = interpreter.get_tensor(output_details[0]['index'])
        offsets = interpreter.get_tensor(output_details[1]['index'])
        print(f"Heatmaps shape: {heatmaps.shape}, Offsets shape: {offsets.shape}")
        
        keypoints = process_output(heatmaps, offsets, frame)
        return keypoints
    except Exception as e:
        print(f"Error in pose estimation: {e}")
        return None

# Hàm xử lý heatmaps và offsets
def process_output(heatmaps, offsets, frame, threshold=0.1):
    keypoints = []
    heatmap = heatmaps[0]
    offset = offsets[0]
    
    for i in range(heatmap.shape[-1]):
        heatmap_i = heatmap[:, :, i]
        y, x = np.unravel_index(np.argmax(heatmap_i), heatmap_i.shape)
        confidence = 1 / (1 + np.exp(-heatmap_i[y, x]))  # Áp dụng sigmoid
        print(f"Keypoint {i}: Confidence = {confidence}")
        
        if confidence > threshold:
            offset_y = offset[y, x, i]
            offset_x = offset[y, x, i + 17]
            keypoint_x = (x * frame.shape[1] / heatmap.shape[1]) + offset_x
            keypoint_y = (y * frame.shape[0] / heatmap.shape[0]) + offset_y
            keypoints.append({"x": int(keypoint_x), "y": int(keypoint_y), "confidence": float(confidence)})
        else:
            keypoints.append({})
    return keypoints

# Hàm vẽ keypoints lên frame
def draw_keypoints(frame, keypoints):
    for kp in keypoints:
        if kp:
            x, y = kp["x"], kp["y"]
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
    return frame

# Hàm stream video
def generate_frames():
    prev_time = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        keypoints = run_pose_estimation(frame)
        if keypoints:
            frame = draw_keypoints(frame, keypoints)

        # Tính FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time else 0
        prev_time = curr_time

        # Hiển thị FPS lên frame
        cv2.putText(
            frame,
            f"FPS: {fps:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Khởi tạo Flask app
app = Flask(__name__)

# Endpoint cho JSON keypoints
@app.route('/pose')
def pose():
    ret, image = cap.read()
    if not ret:
        return jsonify({"error": "Camera read failed"}), 500
    
    keypoints = run_pose_estimation(image)
    if keypoints is None:
        return jsonify({"error": "Pose estimation failed"}), 500
    
    keypoints_json = [kp if kp else {} for kp in keypoints]
    return jsonify({"keypoints": keypoints_json})

# Endpoint cho video stream
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Trang HTML chính
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pose Estimation</title>
    </head>
    <body>
        <h1>Pose Estimation Video Stream</h1>
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
    </body>
    </html>
    """)

# Endpoint để dừng server
@app.route('/shutdown')
def shutdown():
    cap.release()
    cv2.destroyAllWindows()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return jsonify({"message": "Server shutting down"})

if __name__ == '__main__':
    try:
        time.sleep(0.1)
        app.run(host='0.0.0.0', port=5000)
    finally:
        cap.release()
        cv2.destroyAllWindows()