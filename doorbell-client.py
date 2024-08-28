from inputs import get_gamepad
import requests
import time
from requests.exceptions import RequestException
import configparser
import threading
import urllib3
import logging
import json

# Disable SSL warnings (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')
PC_IP = config['NETWORK']['ip']
PC_PORT = config['NETWORK']['port']
API_KEY = config['API']['key']

# Check if BUTTON section exists, if not, create it
if 'BUTTON' not in config:
    config['BUTTON'] = {'code': 'BTN_TRIGGER', 'type': 'Key'}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

BUTTON_CODE = config['BUTTON']['code']
BUTTON_TYPE = config['BUTTON']['type']

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
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"https://{PC_IP}:{PC_PORT}/ring", 
                                headers=headers, 
                                verify=False)
        if response.status_code == 200:
            logging.info("Doorbell rung successfully!")
        elif response.status_code == 403:
            logging.info("Server is in listening mode, cannot ring doorbell.")
        else:
            logging.error(f"Failed to ring doorbell. Status code: {response.status_code}")
    except RequestException as e:
        logging.error(f"Failed to send doorbell notification: {e}")

def check_listening_status():
    try:
        response = requests.get(f"https://{PC_IP}:{PC_PORT}/listening_status", 
                                headers={"X-API-Key": API_KEY}, 
                                verify=False, timeout=5)
        return response.status_code == 200 and response.json()['listening']
    except RequestException:
        return False

def set_button(code, type):
    try:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "code": code,
            "type": type
        }
        response = requests.post(f"https://{PC_IP}:{PC_PORT}/set_button", 
                                 headers=headers, 
                                 json=data,
                                 verify=False)
        if response.status_code == 200:
            logging.info(f"New button set: {type} - {code}")
            config['BUTTON']['code'] = code
            config['BUTTON']['type'] = type
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            global BUTTON_CODE, BUTTON_TYPE
            BUTTON_CODE = code
            BUTTON_TYPE = type
            
            # Send update to server UI
            update_server_ui(code, type)
        else:
            logging.error(f"Failed to set button. Status code: {response.status_code}")
    except RequestException as e:
        logging.error(f"Failed to set button: {e}")

def update_server_ui(code, type):
    try:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "code": code,
            "type": type
        }
        response = requests.post(f"https://{PC_IP}:{PC_PORT}/update_ui", 
                                 headers=headers, 
                                 json=data,
                                 verify=False)
        if response.status_code == 200:
            logging.info("Server UI updated successfully")
        else:
            logging.error(f"Failed to update server UI. Status code: {response.status_code}")
    except RequestException as e:
        logging.error(f"Failed to update server UI: {e}")

def periodic_health_check():
    while True:
        if not check_connection():
            logging.warning("Connection lost. Attempting to reconnect...")
            while not check_connection():
                time.sleep(60)
            logging.info("Connection re-established.")
        time.sleep(60)

# Start the health check in a separate thread
health_check_thread = threading.Thread(target=periodic_health_check, daemon=True)
health_check_thread.start()

logging.info("Doorbell client started. Listening for button press on gamepad...")

last_press_time = 0
COOLDOWN_PERIOD = 1  # 1 second cooldown between presses

# Main loop
while True:
    try:
        events = get_gamepad()
        for event in events:
            if event.ev_type == 'Key' and event.state == 1:  # Only process key presses, not releases
                if check_listening_status():
                    logging.info(f"Server is listening. Sending new button info: {event.ev_type} - {event.code}")
                    set_button(event.code, event.ev_type)
                    break  # Exit the loop after setting the button
                elif event.code == BUTTON_CODE:
                    current_time = time.time()
                    if current_time - last_press_time >= COOLDOWN_PERIOD:
                        logging.info("Doorbell button pressed!")
                        if check_connection():
                            ring_doorbell()
                            last_press_time = current_time
                        else:
                            logging.warning("Connection lost. Cannot ring doorbell.")
    except Exception as e:
        logging.error(f"Error in main loop: {e}", exc_info=True)
    time.sleep(0.0001)  # Small delay to prevent CPU overuse