import os
from dotenv import load_dotenv
load_dotenv()

#Connect to youtube API
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
youtube = googleapiclient.discovery.build(serviceName='youtube', version='v3', developerKey=GOOGLE_API_KEY)

def youtubeSearch(q):
    request = youtube.search().list(
        part = "snippet",
        eventType = "completed",
        q = q,
        type = "video"
    )
    response = request.execute()
    return response

#TODO Check if youtube query exists already 


#Youtube querry
response = youtubeSearch("airport ambient noise")
print(response)

#TODO postgresql queries (check if video exist in database, add querry parameter, add video if not existing)
import psycopg2
POSTGRE_USER = os.environ.get("POSTGRE_USER")
POSTGRE_PASSWORD = os.environ.get("POSTGRE_PASSWORD")
POSTGRE_HOST = os.environ.get("POSTGRE_HOST")
conn = psycopg2.connect(dbname="youtube_search", user=POSTGRE_USER, password=POSTGRE_PASSWORD, host=POSTGRE_HOST)
cur = conn.cursor()

#TODO download Video, extract audio, save audio file on Server
