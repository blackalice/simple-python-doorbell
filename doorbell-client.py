from inputs import get_gamepad
import requests
import time
from requests.exceptions import RequestException
import configparser
import threading
import urllib3

urllib3.disable_warnings()


config = configparser.ConfigParser()
config.read('config.ini')
PC_IP = config['NETWORK']['ip']
PC_PORT = config['NETWORK']['port']
API_KEY = config['API']['key']




def check_connection():
    try:
        response = requests.get(f"https://{PC_IP}:{PC_PORT}/health", 
                                headers={"X-API-Key": API_KEY}, 
                                verify=False, timeout=5)
        return response.status_code == 200
    except RequestException:
        return False
        

def ring_doorbell():
    try:
        headers = {
            "X-API-Key": API_KEY
        }
        response = requests.get(f"https://{PC_IP}:{PC_PORT}/ring", 
                                headers=headers, 
                                verify=False)  # Use verify=True in production with a valid SSL cert
        if response.status_code == 200:
            print("Doorbell rung!")
        else:
            print(f"Failed to ring doorbell. Status code: {response.status_code}")
    except RequestException as e:
        print(f"Failed to send notification: {e}")
        
def periodic_health_check():
    while True:
        if not check_connection():
            print("Connection lost. Attempting to reconnect...")
            reconnect()
        time.sleep(60) # Check every minute

# Start the health check in a separate thread
health_check_thread = threading.Thread(target=periodic_health_check, daemon=True)
health_check_thread.start()

def reconnect():
    while not check_connection():
        print("Attempting to reconnect...")
        time.sleep(60)  # Wait for 1 minute before trying again
    print("Connection re-established.")  

print("Listening for button press on gamepad...")

last_press_time = 0
COOLDOWN_PERIOD = 1  # 1 second cooldown between presses
button_state = 0

while True:
    try:
        events = get_gamepad()
        for event in events:
            if event.code == 'BTN_TRIGGER':
                if event.state == 1 and button_state == 0:  # Button just pressed
                    button_state = 1
                    current_time = time.time()
                    if current_time - last_press_time >= COOLDOWN_PERIOD:
                        print("Button pressed!")
                        if check_connection():
                            ring_doorbell()
                            last_press_time = current_time
                        else:
                            print("Connection lost. Cannot ring doorbell. Will try to reconnect on next press.")
                    else:
                        print("Button press ignored (cooldown period)")
                elif event.state == 0 and button_state == 1:  # Button released
                    button_state = 0
                    print("Button released")
    except Exception as e:
        print(f"Error reading gamepad: {e}")
    time.sleep(0.0001)  # Small delay to prevent CPU overuse
