from flask import Flask, request, abort
from winotify import Notification, audio
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import ssl
import os
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['API']['key']

@app.route('/ring')

def ring():
    # API Key validation
    if request.headers.get('X-API-Key') != API_KEY:
        abort(401)  # Unauthorized

    toast = Notification(app_id= config['DETAILS']['appid'],
                         title= config['DETAILS']['title'],
                         msg= ['DETAILS']['msg'],
                         duration= config['DETAILS']['duration'],
                         icon= config['DETAILS']['icon'])
    
    toast.set_audio(audio.IM, loop=False)
    
    toast.show()
    return "OK"

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ssl_cert_path = os.path.join(current_dir, 'ssl', 'server.crt')
    ssl_key_path = os.path.join(current_dir, 'ssl', 'server.key')
    
    app.run(host='0.0.0.0', port=5000, ssl_context=(ssl_cert_path, ssl_key_path))