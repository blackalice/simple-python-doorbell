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

app = Flask(__name__)

config = configparser.ConfigParser()
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

def create_tray_icon():
    image = Image.open("icon.png")  # Replace with path to your icon
    menu = pystray.Menu(pystray.MenuItem("Exit", exit_action))
    icon = pystray.Icon("name", image, "Doorbell Server", menu)
    icon.run()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--tray':
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()
        create_tray_icon()
    else:
        run_flask()