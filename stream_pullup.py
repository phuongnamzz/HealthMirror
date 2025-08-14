import cv2
import mediapipe as mp
import numpy as np
import argparse
import time
import sys
import threading
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# ----------------- Global frame for threaded capture -----------------
latest_frame = None
lock = threading.Lock()

def capture_thread(camera_index):
    global latest_frame
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("Error: Cannot open camera.")
        sys.exit(1)

    while True:
        ret, frame = cap.read()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        if not ret:
            break
        with lock:
            latest_frame = frame.copy()
    cap.release()

# ----------------------------------------------------------------------

def get_landmark_coords(landmarks, name, mp_pose):
    lm = landmarks[mp_pose.PoseLandmark[name].value]
    return [lm.x, lm.y]

def draw_info(image, pullup_count, shoulder_y, stage, fps):
    color = (0, 255, 0) if stage == 'up' else (0, 0, 255) if stage == 'down' else (255, 255, 0)
    cv2.putText(image, f'Pull-ups: {pullup_count}', (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.putText(image, f'Shoulder_y: {shoulder_y:.2f}', (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(image, f'Stage: {stage}', (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(image, f'FPS: {fps:.1f}', (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

def gen_frames(bar_y=0.15):
    global latest_frame
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pullup_count = 0
    stage = 'waiting'

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        smooth_landmarks=False
    ) as pose:
        prev_time = time.time()
        while True:
            frame = None
            with lock:
                if latest_frame is not None:
                    frame = latest_frame.copy()

            if frame is None:
                time.sleep(0.01)
                continue

            frame = cv2.resize(frame, (640, 480))
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # frame = cv2.rotate(frame, cv2.ROTATE_180)
            results = pose.process(image_rgb)

            image = frame.copy()
            shoulder_y = 0.0
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                right_shoulder = get_landmark_coords(landmarks, 'RIGHT_SHOULDER', mp_pose)
                left_shoulder = get_landmark_coords(landmarks, 'LEFT_SHOULDER', mp_pose)
                shoulder_y = (right_shoulder[1] + left_shoulder[1]) / 2

                if shoulder_y > bar_y + 0.20:
                    if stage == 'waiting':
                        stage = 'down'
                elif shoulder_y < bar_y + 0.05 and stage == 'down':
                    stage = 'up'
                    pullup_count += 1
                    stage = 'waiting'

                h, w, _ = image.shape
                cv2.line(image, (0, int(bar_y * h)), (w, int(bar_y * h)), (255, 255, 0), 2)
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if curr_time != prev_time else 0
            prev_time = curr_time

            draw_info(image, pullup_count, shoulder_y, stage, fps)

            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template_string("""
    <html>
    <head><title>Smart Pull-up Counter</title></head>
    <body>
        <h1>Smart Pull-up Counter</h1>
        <img src="{{ url_for('video_feed') }}" width="800">
    </body>
    </html>
    """)

@app.route('/video_feed')
def video_feed():
    bar_y = float(app.config.get('BAR_Y', 0.15))
    return Response(gen_frames(bar_y),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def main(camera_index=0, bar_y=0.15, use_flask=False):
    # Start capture thread
    t = threading.Thread(target=capture_thread, args=(camera_index,), daemon=True)
    t.start()

    if use_flask:
        app.config['BAR_Y'] = bar_y
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    else:
        # Local OpenCV display
        for frame_bytes in gen_frames(bar_y):
            nparr = np.frombuffer(frame_bytes.split(b'\r\n\r\n')[1], np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv2.imshow("Smart Pull-up Counter", img)
            if cv2.waitKey(1) & 0xFF in (27, ord('q')):
                break
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Pull-up Counter using Mediapipe (Threaded)")
    parser.add_argument('--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('--bar_y', type=float, default=0.15, help='Normalized Y position of the bar')
    parser.add_argument('--flask', action='store_true', help='Run with Flask')
    args = parser.parse_args()
    try:
        main(camera_index=args.camera, bar_y=args.bar_y, use_flask=args.flask)
    except KeyboardInterrupt:
        print("\nExiting...")
