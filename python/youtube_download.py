from __future__ import unicode_literals
import os
from pathlib import Path
import youtube_api
import youtube_dl

session = youtube_api.session

#TODO steer search
# search = youtube_api.Search(part="snippet", q="airport ambiance noise", type = "video", eventType = "completed")
# session.add(search)
# search.execute()
# session.commit()
session.close()
#TODO get video ids

#download youtube video
video_id = "KJ7ZLeWxo2A"  #TODO insert videoId from youtube search request
video_ids = [
    '9JFC1xzdMx0',
    'Z2CD4OyIM8U',
    'cZa7jamQSuM',
    'AtMzngYdx4s',
    'jBcyGEEZqTA']
video_urls=[f"https://www.youtube.com/watch?v={id}" for id in video_ids]

video_url = f'https://www.youtube.com/watch?v={video_id}'
file_path = Path(os.path.realpath(__file__))
download_path = f'{file_path.parent.parent.absolute()}/data/yoututbe/'

ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f"{download_path}%(id)s.%(ext)s"}
# on error: editing file: your/path/to/site-packages/youtube_dl/extractor/youtube.py Line 1794 and add the option fatal=False
# https://stackoverflow.com/questions/75495800/error-unable-to-extract-uploader-id-youtube-discord-py
#TODO error handling
for u in video_urls:
    youtube_dl.YoutubeDL(ydl_opts).download(url_list=[u])