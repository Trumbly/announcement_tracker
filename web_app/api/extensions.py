from flask_socketio import SocketIO

socketio = SocketIO(ping_timeout=1000, ping_interval=1000)
    