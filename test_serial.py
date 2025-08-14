import serial
import time
import json
import subprocess
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
VOICE_COMMAND_TURN_ON_SCREEN = "Turn on screen"
VOICE_COMMAND_TURN_OFF_SCREEN = "Turn off screen"

print("Serial port opened: ", ser.is_open)


# ddcutil -b 13 setvcp D6 4
# ddcutil -b 13 setvcp D6 1

def turn_on_screen():
    command = ['sudo', 'ddcutil', 'setvcp', 'D6', '1']

    try:
        subprocess.run(command, check=True)
        print("Screen turned on successfully.")
    except subprocess.CalledProcessError as e:
        print("Error turning on screen:", e)
    except FileNotFoundError:
        print("ddcutil command not found. Please install ddcutil.")

def turn_off_screen():
    command = ['sudo', 'ddcutil', 'setvcp', 'D6', '4']

    try:
        subprocess.run(command, check=True)
        print("Screen turned off successfully.")
    except subprocess.CalledProcessError as e:
        print("Error turning off screen:", e)
    except FileNotFoundError:
        print("ddcutil command not found. Please install ddcutil.")


def process_data(data):
    
    data_str = data.decode('utf-8').strip()
    print("Decoded data:", data_str)
    if data_str.startswith('{') and data_str.endswith('}'):
        try:
            json_data = json.loads(data_str)
            print("JSON Data:", json_data)

            if "voice" in json_data:
                voice_command = json_data["voice"]
                print("Voice command:", voice_command)

                if voice_command == VOICE_COMMAND_TURN_ON_SCREEN:
                    print("Turning on screen...")
                    # Add code to turn on the screen here
                    turn_on_screen()
                elif voice_command == VOICE_COMMAND_TURN_OFF_SCREEN:
                    print("Turning off screen...")
                    # Add code to turn off the screen here
                    turn_off_screen()
                    

        except json.JSONDecodeError:
            print("Invalid JSON format")


try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline(ser.in_waiting)
            print("Received data:", data)
            process_data(data)
        # time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
    print("Serial port closed.")