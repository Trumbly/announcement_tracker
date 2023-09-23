# !pip install python-dotenv --break-system-packages
# !pip install boto3 --break-system-packages
# !pip install pymediainfo --break-system-packages
# !pip install librosa --break-system-packages
# !pip install soundfile --break-system-packages

import os
from dotenv import load_dotenv
import io
import warnings
from scipy.io.wavfile import write
import boto3
from pymediainfo import MediaInfo
import librosa as lb

load_dotenv()
aws_access_key_id = os.getenv("aws_access_key_id")
aws_secret_access_key = os.getenv("aws_secret_access_key")
aws_bucket_name = 'sousi'

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

def audio_to_wav_binary(file_path:str, sr:int=16000, mono:bool=True):
    """
    Convert audio file to wave binary file. Audio file is converted to 16k Hz mono by default. 
    Takes the path of the audio file as an input. File can be in any audio format supported by librosa.  
    Returns wave file as binary.
    """
    #TODO load audio as np.array
    with warnings.catch_warnings(record=True):
        y, sr_orig = lb.load(path=file_path, sr=sr, mono=mono)
    wav_binary:io.BytesIO = io.BytesIO(bytes())
    write(wav_binary, sr_orig if sr==None else sr, y)
    return wav_binary

#TODO put binary to S3 without batch mode  
def binary_to_s3(binary:io.BytesIO, key:str, bucket:str=aws_bucket_name):
    """
    Persit binary file on the S3 storage. 
    The environemnt variables aws_access_key_id and aws_secret_access_key provided in the .evn file are used.
    The variable aws_bucket_name is used as a default value for the bucket name.
    """
    s3.put_object(Body=binary, Bucket=bucket, Key=key)
    #TODO load binary here


def audio_file_to_s3(file_path:str, key:str, **kwargs):
    """
    Convert audio file to a wave file and persists on S3.
    """
    # convert audio to wave binary
    audio_to_wav_binary_params:dict={'file_path':file_path}
    if 'sr' in kwargs: audio_to_wav_binary_params['sr']=kwargs['sr']
    if 'mono' in kwargs: audio_to_wav_binary_params['mono']=kwargs['mono']
    wav_binary=audio_to_wav_binary(**audio_to_wav_binary_params)
    # persist wave binary on S3
    binary_to_s3_params:dict={'binary':wav_binary, 'key':key}
    if 'bucket' in kwargs: binary_to_s3_params['bucket']=kwargs['bucket']
    binary_to_s3(**binary_to_s3_params)
    wav_binary.close()

def audio_files_to_s3(paths:list, folder:str, **kwargs):
    """
    Convert a list fo audio files to a wave files and persists on S3.
    """
    for i, path in enumerate(paths):
        file_name=os.path.split(path)[1]
        file_name=os.path.splitext(file_name)[0]
        key=f'{folder}/{file_name}.wav'
        print(f'{i+1} of {len(file_paths)}: {key}')
        audio_file_to_s3(file_path=path, key=key, **kwargs)

audio_files_to_s3(paths=file_paths, folder='youtube', sr=16000, mono=True)

# https://librosa.org/blog/2019/07/29/stream-processing/#Samples,-frames,-and-blocks