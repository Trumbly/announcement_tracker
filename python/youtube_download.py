from __future__ import unicode_literals
import os
import youtube_dl
from pathlib import Path
# import youtube_api

# session = youtube_api.session

#TODO steer search
# search = youtube_api.Search(part="snippet", q="airport ambiance noise", type = "video", eventType = "completed")
# session.add(search)
# search.execute()
#TODO get video ids

#download youtube video
videoId = "p7eeZz_t4QE"  #TODO insert videoId from youtube search request
file_path = Path(os.path.realpath(__file__))
download_path = f'{file_path.parent.parent.absolute()}/data/yoututbe/'

ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f"{download_path}%(id)s.%(ext)s"}
# on error: editing file: your/path/to/site-packages/youtube_dl/extractor/youtube.py Line 1794 and add the option fatal=False
# https://stackoverflow.com/questions/75495800/error-unable-to-extract-uploader-id-youtube-discord-py
youtube_dl.YoutubeDL(ydl_opts).download(url_list=[f'https://www.youtube.com/watch?v={videoId}'])

# session.commit()
# session.close()