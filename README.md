# Simple Python Doorbell

A wireless doorbell system using a gamepad as the button and a PC for notifications.

## 🚀 Features

- Gamepad-triggered doorbell
- Windows toast notifications
- Secure HTTPS communication
- Configurable settings
- Cooldown period to prevent spam

## 🛠️ Components

1. `doorbell-client.py`: Runs on a device with the gamepad (e.g., Raspberry Pi)
2. `doorbell-server.py`: Runs on the PC to receive and display notifications

## 📋 Requirements

### Client
- Python 3.x
- `inputs` library
- `requests` library
- `configparser` library

### Server
- Python 3.x
- Flask
- winotify
- flask_limiter
- configparser
- SSL certificate and key

## 🔧 Setup

1. Clone the repository:

```

git clone <https://github.com/blackalice/simple-python-doorbell.git> cd simple-python-doorbell

```

2\. Install required libraries:

```

pip install -r requirements.txt

```

3\. Create a `config.ini` file in the project root:
```ini
[NETWORK]
ip = <SERVER_IP_ADDRESS>
port = <SERVER_PORT>

[API]
key = <YOUR_API_KEY>

[DETAILS]
appid = <YOUR_APP_ID>
title = <NOTIFICATION_TITLE>
msg = <NOTIFICATION_MESSAGE>
duration = <NOTIFICATION_DURATION>
icon = <PATH_TO_ICON_FILE>

```

1.  Generate SSL certificate and key for the server, name them server.crt and server.key and add them to an ssl folder within the root.

2.  Run the server:

    ```
    python doorbell-server.py

    ```

3.  Run the client:

    ```
    python doorbell-client.py

    ```

🔐 Security
-----------

-   HTTPS encryption
-   API key authentication
-   Configuration file for sensitive data
-   (Optional) Implement rate limiting

🎛️ Customization
-----------------

-   Modify `config.ini` for network settings, API key, and notification details
-   Adjust cooldown period in `doorbell-client.py`
-   Change monitored gamepad button in `doorbell-client.py`

🐛 Troubleshooting
------------------

-   Verify `config.ini` is correctly formatted and complete
-   Check firewall settings for the specified port
-   Ensure SSL certificate is valid


📞 Contact
----------

[@stuart_foy](https://twitter.com/stuart_foy)

Project Link: <https://github.com/blackalice/simple-python-doorbell>