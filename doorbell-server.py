from flask import Flask, request, abort, jsonify
from winotify import Notification, audio
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import ssl
import os
import configparser
import pystray
from PIL import Image
import threading
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import font as tkfont
import json
import time
import logging
import sv_ttk

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_default_config():
    config = configparser.ConfigParser()
    config['API'] = {
        'key': ''  # Empty by default
    }
    config['NETWORK'] = {
        'ip': '127.0.0.1',
        'port': '5000'
    }
    config['DETAILS'] = {
        'appid': 'DoorBell',
        'title': 'Doorbell',
        'msg': 'Someone is at the door!',
        'length': '5',
        'icon': 'path/to/icon.png'
    }
    config['BUTTON'] = {
        'code': 'BTN_TRIGGER',
        'type': 'Key'
    }
    config['SYSTEM'] = {
        'initial_setup_done': 'NO'
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    return config, True  # Return True to indicate a new config was created

# Load or create configuration
config = configparser.ConfigParser()
new_config_created = False
if not os.path.exists('config.ini'):
    logging.info("Config file not found. Creating new config with default values.")
    config, new_config_created = create_default_config()
else:
    config.read('config.ini')
    if 'SYSTEM' not in config:
        config['SYSTEM'] = {'initial_setup_done': 'NO'}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

API_KEY = config['API']['key']

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# Global variables
listening_for_button = False
listening_timeout = None
new_button_info = None

@app.route('/listening_status', methods=['GET'])
def listening_status():
    global listening_for_button
    logging.debug(f"Listening status requested. Current status: {listening_for_button}")
    if request.headers.get('X-API-Key') != API_KEY:
        abort(401)
    return json.dumps({"listening": listening_for_button}), 200

@app.route('/set_button', methods=['POST'])
def set_button():
    global listening_for_button, listening_timeout, new_button_info
    logging.debug(f"Set button request received. Current listening status: {listening_for_button}")
    if not listening_for_button:
        return "Not listening for button", 400

    if request.headers.get('X-API-Key') != API_KEY:
        abort(401)

    data = request.json
    logging.debug(f"Received new button data: {data}")
    new_button_info = data  # Store the new button info
    
    listening_for_button = False
    if listening_timeout:
        listening_timeout.cancel()
    logging.debug("Button set successfully")
    return "Button set successfully", 200

@app.route('/update_ui', methods=['POST'])
def update_ui():
    global new_button_info
    if request.headers.get('X-API-Key') != API_KEY:
        abort(401)
    
    data = request.json
    new_button_info = data
    return "UI update received", 200

@app.route('/ring', methods=['GET'])
@limiter.limit("5 per minute")
def ring():
    global listening_for_button
    logging.debug("Ring endpoint called")
    # API Key validation
    if request.headers.get('X-API-Key') != API_KEY:
        logging.debug("Unauthorized ring attempt")
        abort(401)  # Unauthorized
    
    if listening_for_button:
        logging.debug("Ring attempt while in listening mode, ignoring")
        return "Server is in listening mode", 403

    # Create and show notification
    toast = Notification(app_id=config['DETAILS']['appid'],
                         title=config['DETAILS']['title'],
                         msg=config['DETAILS']['msg'],
                         duration=config['DETAILS']['length'],
                         icon=config['DETAILS']['icon'])
    
    toast.set_audio(audio.IM, loop=False)
    toast.show()
    logging.debug("Doorbell notification sent")
    return "Doorbell rung", 200

@app.route('/health', methods=['GET'])
def health_check():
    logging.debug("Health check endpoint called")
    if request.headers.get('X-API-Key') != API_KEY:
        logging.debug("Unauthorized health check attempt")
        abort(401)
    return "OK", 200

def run_flask():
    logging.debug("Starting Flask server")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ssl_cert_path = os.path.join(current_dir, 'ssl', 'server.crt')
    ssl_key_path = os.path.join(current_dir, 'ssl', 'server.key')
    
    app.run(host='0.0.0.0', port=5000, ssl_context=(ssl_cert_path, ssl_key_path), debug=True, use_reloader=False)

def exit_action(icon):
    icon.stop()
    os._exit(0)

class ConfigDialog:
    def __init__(self, master, show_welcome=False):
        self.master = master
        self.master.title("Doorbell Server Configuration")
        self.default_font = tkfont.nametofont("TkDefaultFont")
        
        # Apply Sun Valley theme (dark by default, you can change to "light" if preferred)
        sv_ttk.set_theme("dark")
        
        self.create_widgets()
        self.adjust_window_size()

        if show_welcome:
            messagebox.showinfo("Welcome", "Welcome! Please configure your doorbell server.")

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.entries = {}
        row = 0
        for section in config.sections():
            if section != 'SYSTEM':  # Skip the SYSTEM section
                section_label = ttk.Label(main_frame, text=section, font=(self.default_font.cget("family"), self.default_font.cget("size"), "bold"))
                section_label.grid(row=row, column=0, sticky=tk.W, pady=(10,5))
                row += 1
                for key in config[section]:
                    ttk.Label(main_frame, text=key).grid(row=row, column=0, sticky=tk.W)
                    self.entries[f"{section}.{key}"] = ttk.Entry(main_frame, width=40)
                    self.entries[f"{section}.{key}"].insert(0, config[section][key])
                    self.entries[f"{section}.{key}"].grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
                    row += 1

        ttk.Button(main_frame, text="Set Doorbell Button", command=self.set_doorbell_button).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save_config).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.master.destroy).grid(row=0, column=1, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def adjust_window_size(self):
        self.master.update_idletasks()  # Ensure the window has been drawn
        width = self.master.winfo_reqwidth() + 20  # Add some padding
        height = self.master.winfo_reqheight() + 20  # Add some padding
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def save_config(self):
        for key, entry in self.entries.items():
            section, option = key.split('.')
            config[section][option] = entry.get()

        config['SYSTEM']['initial_setup_done'] = 'YES'

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        global API_KEY
        API_KEY = config['API']['key']

        messagebox.showinfo("Config Updated", "Configuration has been updated successfully!")
        self.master.destroy()

    def set_doorbell_button(self):
        global listening_for_button, listening_timeout, new_button_info
        logging.debug("Set doorbell button clicked")
        listening_for_button = True
        new_button_info = None
        
        # Set a timeout for listening mode (e.g., 30 seconds)
        def timeout_listening():
            global listening_for_button
            listening_for_button = False
            logging.debug("Listening mode timed out")
            messagebox.showinfo("Timeout", "Button setting timed out. Please try again.")

        listening_timeout = threading.Timer(30.0, timeout_listening)
        listening_timeout.start()

        messagebox.showinfo("Set Doorbell Button", "Press the desired button on the client device within 30 seconds.")
        logging.debug("Entered listening mode")

        # Start a thread to update the dialog with listening status
        threading.Thread(target=self.update_listening_status, daemon=True).start()

    def update_listening_status(self):
        status_label = ttk.Label(self.master, text="Listening for button press...")
        status_label.grid(row=len(self.entries) + 3, column=0, columnspan=2)

        while listening_for_button:
            status_label.config(text="Listening for button press..." + "." * (int(time.time()) % 3 + 1))
            time.sleep(0.5)
            self.master.update()

        if new_button_info:
            status_label.config(text=f"New button set: {new_button_info['type']} - {new_button_info['code']}")
            self.entries['BUTTON.type'].delete(0, tk.END)
            self.entries['BUTTON.type'].insert(0, new_button_info['type'])
            self.entries['BUTTON.code'].delete(0, tk.END)
            self.entries['BUTTON.code'].insert(0, new_button_info['code'])
        else:
            status_label.config(text="Listening timed out")
        
        logging.debug(f"Listening mode ended. Button info: {new_button_info}")
        self.master.after(3000, status_label.destroy)  # Remove the label after 3 seconds

def open_config_dialog(icon=None, show_welcome=False):
    root = tk.Tk()
    dialog = ConfigDialog(root, show_welcome)
    root.mainloop()

def create_tray_icon():
    image = Image.open("icon.png")  # Replace with path to your icon
    menu = pystray.Menu(
        pystray.MenuItem("Config", lambda: open_config_dialog(show_welcome=False)),
        pystray.MenuItem("Exit", exit_action)
    )
    icon = pystray.Icon("name", image, "Doorbell Server", menu)
    icon.run()

if __name__ == '__main__':
    show_welcome = new_config_created or config.get('SYSTEM', 'initial_setup_done', fallback='NO').upper() != 'YES'
    
    if show_welcome:
        open_config_dialog(show_welcome=True)
        config['SYSTEM']['initial_setup_done'] = 'YES'
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--tray':
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()
        create_tray_icon()
    else:
        run_flask()