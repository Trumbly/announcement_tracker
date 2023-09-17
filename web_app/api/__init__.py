from flask import Flask
from .functions import load_models
from .events import socketio
from .routes import main

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["DEBUG"] = True

app.register_blueprint(main)
