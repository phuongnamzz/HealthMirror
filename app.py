
import serial
import time
import json
import subprocess
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from gpiozero import Button
from signal import pause
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
BUTTON_PIN = 21


button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.1)

# --- Configuration ---
SERIAL_PORT = '/dev/ttyESP32S3'
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1
VOICE_COMMANDS = {
    "show mirror": "turn_on_screen",
    "hide mirror": "turn_off_screen",
    # Add other commands here (e.g., "turn on camera", "turn off camera")
}

# --- Shared variables and Thread-safe Lock ---
sensor_data = {
    'pullups': 0,
    'pushups': 0,
    'squats': 0,
    'heartRate': 0,
    'breathRate': 0
}

BOTTOM_CAMERA = '/dev/video2'
TOP_CAMERA = '/dev/video0'

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0/np.pi)
    return 360 - angle if angle > 180.0 else angle

def squat_counter():
    cap = cv2.VideoCapture(BOTTOM_CAMERA, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("Camera not accessible")
        return

    counter, stage = 0, None
    with mp_pose.Pose(model_complexity=1,
                      smooth_landmarks=True,
                      min_detection_confidence=0.7,
                      min_tracking_confidence=0.7) as pose:
        start_time = time.time()
        frames = 0              
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            image_rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            frames += 1 

            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                fps = frames / elapsed_time
                print(f"Current FPS: {fps:.2f}")
                start_time = time.time()
                frames = 0

            results = pose.process(image_rgb)
            h, w = frame.shape[:2]

            if results.pose_landmarks:

                lms = results.pose_landmarks.landmark
                hip_r = [lms[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                         lms[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                knee_r = [lms[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                          lms[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                ankle_r = [lms[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                           lms[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
                angle_r = calculate_angle(hip_r, knee_r, ankle_r) 

                hip_l = [lms[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                         lms[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee_l = [lms[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                          lms[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle_l = [lms[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                           lms[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                angle_l = calculate_angle(hip_l, knee_l, ankle_l)

                angle_avg = (angle_r + angle_l) / 2
                print(f"Right Knee Angle: {angle_r:.2f}, Left Knee Angle: {angle_l:.2f}, Average: {angle_avg:.2f}")
                if angle_avg > 160:
                    stage = "up"
                if angle_avg < 90 and stage == "up":
                    stage = "down"
                    counter += 1
                    print(f"Squat Count: {counter}")
                    with data_lock:
                        sensor_data['squats'] = counter
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                                          mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)) 
            # cv2.imshow('Squat Counter', frame)    
    cap.release()
    cv2.destroyAllWindows()


data_lock = threading.Lock()
screen_on = True
def toggle_screen():
    """Toggle the screen state using ddcutil."""
    # Here we can implement a toggle mechanism if needed
    # For simplicity, we'll just turn on the screen when the button is pressed
    global screen_on
    if screen_on:
        run_ddcutil_command("turn_off_screen")
        print("Screen turned off via button")
        screen_on = False
    else:
        run_ddcutil_command("turn_on_screen")
        print("Screen turned on via button")
        screen_on = True

# --- Control Functions ---
def run_ddcutil_command(command_name):
    """Executes a ddcutil command safely and efficiently."""
    command = ['sudo', 'ddcutil', 'setvcp', 'D6', '1' if command_name == "turn_on_screen" else '4']
    try:
        subprocess.run(command, check=True)
        print(f"'{command_name}' command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing '{command_name}' command:", e)
    except FileNotFoundError:
        print("ddcutil command not found. Please ensure ddcutil is installed.")

def get_serial():
    """Opens and returns a serial connection."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        print("Serial connection opened successfully.")
        return ser
    except serial.SerialException as e:
        print("Error opening serial port:", e)
        return None

# --- Data and Voice Command Processing ---
def process_data(data_str):
    """Processes JSON data from the serial port."""
    global sensor_data
    try:
        json_data = json.loads(data_str)
        print("Received JSON data:", json_data)

        # Update sensor data
        with data_lock:
            if "heart" in json_data:
                sensor_data['heartRate'] = int(json_data.get("heart"))
                print("Heart rate:", sensor_data['heartRate'])
            if "breath" in json_data:
                sensor_data['breathRate'] = int(json_data.get("breath"))
                print("Breath rate:", sensor_data['breathRate'])
            
            # Update other metrics if available
            sensor_data['pullups'] = int(json_data.get("pullups", sensor_data['pullups']))
            sensor_data['pushups'] = int(json_data.get("pushups", sensor_data['pushups']))
            sensor_data['squats'] = int(json_data.get("squats", sensor_data['squats']))

        # Process voice commands
        voice_command = json_data.get("voice")
        if voice_command:
            print("Voice command:", voice_command)
            action = VOICE_COMMANDS.get(voice_command)
            if action:
                run_ddcutil_command(action)
    
    except (json.JSONDecodeError, ValueError) as e:
        print("Error processing JSON data:", e)
        print("Invalid data:", data_str)

# --- Flask API ---
app = Flask(__name__)
CORS(app)

@app.route('/api/stats')
def api_stats():
    """API endpoint to return real-time sensor data."""
    with data_lock:
        return jsonify(sensor_data)

# --- Main Thread Logic ---
def serial_reader():
    """Dedicated thread to read data from the serial port."""
    ser = get_serial()
    if not ser:
        return
    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.readline()
                data_str = data.decode('utf-8').strip()
                if data_str:
                    process_data(data_str)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser.close()
        print("Serial port closed.")

# --- Application Startup ---
if __name__ == '__main__':
    serial_thread = threading.Thread(target=serial_reader, daemon=True)
    serial_thread.start()
    
    squat_thread = threading.Thread(target=squat_counter, daemon=True)
    squat_thread.start()

    button.when_pressed = toggle_screen
    # Run the Flask server on the main thread
    app.run(host='0.0.0.0', port=5000)  
    