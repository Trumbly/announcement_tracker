from dataclasses import dataclass
from typing import List
from label_studio_sdk import Client
import os
from dotenv import load_dotenv
load_dotenv() #load environment variables from .env file

@dataclass
class organization:
    id: int
    title: str

#https://labelstud.io/guide/sdk#Start-using-the-Label-Studio-Python-SDK
LABEL_STUDIO_API_KEY = os.environ.get("LABEL_STUDIO_API_KEY")
LABEL_STUDIO_HOST = os.environ.get("LABEL_STUDIO_HOST")
LABEL_STUDIO_PORT = os.environ.get("LABEL_STUDIO_PORT")
ls = Client(url=f'http://{LABEL_STUDIO_HOST}:{LABEL_STUDIO_PORT}', api_key=LABEL_STUDIO_API_KEY)
ls.check_connection()