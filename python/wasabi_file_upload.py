import os
from dotenv import load_dotenv
import io
import warnings
from scipy.io.wavfile import write
import numpy as np
import boto3
from pymediainfo import MediaInfo
import librosa as lb

aws_access_key_id = os.environ.get("aws_access_key_id")
aws_secret_access_key = os.environ.get("aws_secret_access_key")
aws_bucket_name = 'youtubedl'

s3 = boto3.client('s3',
                  endpoint_url='https://s3.eu-central-2.wasabisys.com',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)


# return list of audio files for of given folder
def get_audio_files(path: str, exclude_dirs: list = []):
    filtered_files=[]
    for root, dirs, files in os.walk(path, topdown=True):
        if root not in exclude_dirs:
            for file in files:
                file_path = root + "/" + file
                fileInfo = MediaInfo.parse(file_path)
                for track in fileInfo.tracks:
                    if track.track_type == "Audio":
                        filtered_files.append(file_path)
    return filtered_files

dir = '/root/data/announcement_tracker/youtube'
file_paths = get_audio_files(path=dir)


target_sr: int = 16000
target_track_len = 2.7*60


def audio_to_s3(key:str, y:np.array, bucket:str=aws_bucket_name, sr:int=target_sr):
    wav_object = io.BytesIO(bytes())
    write(wav_object, sr, y)
    #TODO write file to S3 storage
    print(key)
    # s3.put_object(Body=wav_object, Bucket=bucket, Key=key)

def audio_file_sliced_to_s3(path:str, folder:str, bucket:str=aws_bucket_name, sr:int=target_sr):
    file_name = os.path.split(path)[1]
    file_name=os.path.splitext(file_name)[0]
    with warnings.catch_warnings(record=True):
        duration = lb.get_duration(path=path)
    slice_count = np.math.floor(duration/target_track_len)
    slice_count = 1 if slice_count==0 else slice_count
    slice_duration = duration/slice_count
    #TODO previous parts of audiofile seem to be loaded using lb.load.
    # Is it may more efficent to load the files entierly and slice it from the loaded file?
    # Is it possible to use a data loader to load the file with an iterrator bit by bit?
    # https://stackoverflow.com/questions/70613499/python-reading-a-large-audio-file-to-a-stream
    # https://stackoverflow.com/questions/36799902/how-to-splice-an-audio-file-wav-format-into-1-sec-splices-in-python 
    # https://python-programs.com/how-to-find-the-duration-of-a-wav-file-in-python/#:~:text=Approach%3A%20Import%20AudioSegment%20from%20pydub%20module%20using%20the,function%20on%20it%20to%20convert%20it%20into%20seconds.
    for i, t in enumerate(np.arange(0, slice_duration * slice_count, slice_duration)):
        with warnings.catch_warnings(record=True):
            y = lb.load(path=path,
                        mono=True,
                        sr=sr,
                        offset=t, 
                        duration=slice_duration-(1/sr))[0]
        key = f'{folder}/{file_name}_{i}.wav'
        audio_to_s3(y=y, sr=sr, bucket=bucket, key=key)

def audio_files_sliced_to_s3(paths:str, folder:str, bucket:str=aws_bucket_name):
    for path in paths:
        file_name=os.path.split(path)[1]
        file_name=os.path.splitext(file_name)[0]
        audio_file_sliced_to_s3(path=path, bucket=bucket, folder=f'{folder}/{file_name}')


audio_files_sliced_to_s3(paths=file_paths, bucket=aws_bucket_name, folder='')
