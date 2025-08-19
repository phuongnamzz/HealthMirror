# import serial
# import time
# import json
# import subprocess
# from flask import Flask, jsonify
# from flask_cors import CORS
# app = Flask(__name__)
# CORS(app)
# SERIAL_PORT = '/dev/ttyESP32S3'
# BAUD_RATE = 115200
# SERIAL_TIMEOUT = 1

# VOICE_COMMANDS = {
#     "show mirror": "turn_on_screen",
#     "hide mirror": "turn_off_screen",
#     "turn on camera": "turn_on_camera",
#     "turn off camera": "turn_off_camera"
# }

# def get_serial():
#     try:
#         ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
#         print("Serial port opened:", ser.is_open)
#         return ser
#     except serial.SerialException as e:
#         print("Error opening serial port:", e)
#         return None

# def turn_on_screen():
#     command = ['sudo', 'ddcutil', 'setvcp', 'D6', '1']
#     try:
#         subprocess.run(command, check=True)
#         print("Screen turned on successfully.")
#     except subprocess.CalledProcessError as e:
#         print("Error turning on screen:", e)
#     except FileNotFoundError:
#         print("ddcutil command not found. Please install ddcutil.")

# def turn_off_screen():
#     command = ['sudo', 'ddcutil', 'setvcp', 'D6', '4']
#     try:
#         subprocess.run(command, check=True)
#         print("Screen turned off successfully.")
#     except subprocess.CalledProcessError as e:
#         print("Error turning off screen:", e)
#     except FileNotFoundError:
#         print("ddcutil command not found. Please install ddcutil.")

# heart_rate = 0
# breath_rate = 0
# def process_data(data):
#     try:
#         data_str = data.decode('utf-8').strip()
#         print("Decoded data:", data_str)
#         if data_str.startswith('{') and data_str.endswith('}'):
#             json_data = json.loads(data_str)
#             print("JSON Data:", json_data)

#             voice_command = json_data.get("voice")
#             if voice_command:
#                 print("Voice command:", voice_command)
#                 if voice_command == "show mirror":
#                     turn_on_screen()
#                 elif voice_command == "hide mirror":
#                     turn_off_screen()
#                 # Add camera control here if needed

#             heart_rate = json_data.get("heart")
#             if heart_rate is not None:
#                 print("Heart rate:", heart_rate)

#             breath_rate = json_data.get("breath")
#             if breath_rate is not None:
#                 print("Breath rate:", breath_rate)
#         else:
#             print("Data is not valid JSON.")
#     except (json.JSONDecodeError, UnicodeDecodeError) as e:
#         print("Error decoding data:", e)

# @app.route('/api/stats')
# def api_stats():
#     # Placeholder for API stats endpoint
#     stats = {
#         'pullups': 5,
#         'pushups': 2,
#         'squats': 10,
#         'heartRate': 50,
#         'breathRate': 60,
#     }
#     return jsonify(stats)

# def main():
#     ser = get_serial()
#     if not ser:
#         return
#     try:
#         while True:
#             if ser.in_waiting > 0:
#                 data = ser.readline()
#                 print("Received data:", data)
#                 process_data(data)
#             time.sleep(0.1)
#     except KeyboardInterrupt:
#         print("Exiting...")
#     finally:
#         ser.close()
#         print("Serial port closed.")

# if __name__ == '__main__':
#     import threading
#     serial_thread = threading.Thread(target=main, daemon=True)
#     serial_thread.start()
#     app.run(host='0.0.0.0', port=5000)




import serial
import time
import json
import subprocess
import threading
from flask import Flask, jsonify
from flask_cors import CORS

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
data_lock = threading.Lock()

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
    
    # Run the Flask server on the main thread
    app.run(host='0.0.0.0', port=5000)  