from api import app, socketio

if __name__ == '__main__':
    socketio.init_app(app)

socketio.run(app, port=80, host="0.0.0.0", keyfile='/home/privkey.pem', certfile='/etc/ssl/certs/ladendorf_ca.crt')