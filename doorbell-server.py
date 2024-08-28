from flask import Flask, request, abort
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

app = Flask(__name__)

# Function to create default config
def create_default_config():
    config = configparser.ConfigParser()
    config['API'] = {
        'key': 'your_api_key_here'
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
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    return config

# Load or create configuration
config = configparser.ConfigParser()
if not os.path.exists('config.ini'):
    print("Config file not found. Creating new config with default values.")
    config = create_default_config()
else:
    config.read('config.ini')

API_KEY = config['API']['key']

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

@app.route('/ring', methods=['GET'])
@limiter.limit("5 per minute")
def ring():
    # API Key validation
    if request.headers.get('X-API-Key') != API_KEY:
        abort(401)  # Unauthorized

    # Create and show notification
    toast = Notification(app_id=config['DETAILS']['appid'],
                         title=config['DETAILS']['title'],
                         msg=config['DETAILS']['msg'],
                         duration=config['DETAILS']['length'],
                         icon=config['DETAILS']['icon'])
    
    toast.set_audio(audio.IM, loop=False)
    toast.show()
    return "Doorbell rung", 200

@app.route('/health', methods=['GET'])
def health_check():
    if request.headers.get('X-API-Key') != API_KEY:
        abort(401)
    return "OK", 200

def run_flask():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ssl_cert_path = os.path.join(current_dir, 'ssl', 'server.crt')
    ssl_key_path = os.path.join(current_dir, 'ssl', 'server.key')
    
    app.run(host='0.0.0.0', port=5000, ssl_context=(ssl_cert_path, ssl_key_path))

def exit_action(icon):
    icon.stop()
    os._exit(0)

class ConfigDialog:
    def __init__(self, master):
        self.master = master
        self.master.title("Doorbell Server Configuration")
        self.master.geometry("400x400")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.entries = {}
        row = 0
        for section in config.sections():
            ttk.Label(scrollable_frame, text=section, font=('Helvetica', 12, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5))
            row += 1
            for key in config[section]:
                ttk.Label(scrollable_frame, text=key).grid(row=row, column=0, sticky=tk.W)
                self.entries[f"{section}.{key}"] = ttk.Entry(scrollable_frame)
                self.entries[f"{section}.{key}"].insert(0, config[section][key])
                self.entries[f"{section}.{key}"].grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
                row += 1

        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save_config).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.master.destroy).grid(row=0, column=1, padx=5)

        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

    def save_config(self):
        for key, entry in self.entries.items():
            section, option = key.split('.')
            config[section][option] = entry.get()

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        global API_KEY
        API_KEY = config['API']['key']

        tk.messagebox.showinfo("Config Updated", "Configuration has been updated successfully!")
        self.master.destroy()

def open_config_dialog(icon):
    root = tk.Tk()
    ConfigDialog(root)
    root.mainloop()

def create_tray_icon():
    image = Image.open("icon.png")  # Replace with path to your icon
    menu = pystray.Menu(
        pystray.MenuItem("Config", open_config_dialog),
        pystray.MenuItem("Exit", exit_action)
    )
    icon = pystray.Icon("name", image, "Doorbell Server", menu)
    icon.run()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--tray':
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()
        create_tray_icon()
    else:
        run_flask()