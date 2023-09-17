import time
import datetime
import tensorflow as tf
import tensorflow_io as tfio
from pydub import AudioSegment
import numpy as np
import os
import json
from .model.cache import Cache
from .model.detection import Detection
from .model.prediction import Prediction
from .model.transcription import Transcription

def load_models(path):
    st = time.time()
    model = tf.keras.models.load_model(path)
    model.compile('Adam', loss='BinaryCrossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision()])
    llm = whisper.load_model("medium")
    et = time.time()
    print("Loaded models in "+str(et-st))
    return model, llm

model_const, llm = load_models("api/mls/model_6_small_1f_8020_AUG/model.h5")

def load_wav_16k_mono(path):
    st = time.time()
    # Load encoded wav file
    file_contents = tf.io.read_file(path)
    # Decode wav (tensors by channels)
    wav, sample_rate = tf.audio.decode_wav(file_contents, desired_channels=1)
    # Removes trailing axis
    wav = tf.squeeze(wav, axis=-1)
    sample_rate = tf.cast(sample_rate, dtype=tf.int64)
    # Goes from 44100Hz to 16000hz - amplitude of the audio signal
    wav = tfio.audio.resample(wav, rate_in=sample_rate, rate_out=16000)
    et = time.time()
    return wav

def predictBlob(path):
    st = time.time()
    wav = load_wav_16k_mono(path)
    spectogram = createSpectro(wav)
    st = time.time()
    prediction = model_const.predict(np.array( [spectogram,]))
    et = time.time()
    return prediction

def saveBlob(socketId, audioBlob):
    st = time.time()
    # Load blob
    filename = str(socketId) + str(time.time()) + ".wav"
    filepath = os.path.join("api/data/", filename)
    with open(filepath, 'wb') as f: 
        f.write(audioBlob)
    et = time.time()
    return filepath

def saveBlob_UInt8(socketId, audioBlob):
    st = time.time()
    # Load blob
    filename = str(socketId) + str(time.time()) + ".wav"
    filepath = os.path.join("api/data/", filename)

    et = time.time()
    return filepath

def createSpectro(wav):
    st = time.time()
    wav = wav[:1600]
    zero_padding_size = tf.zeros([1600] - tf.shape(wav)[0], dtype=tf.float32)
    wav = tf.concat([zero_padding_size, wav],0)

    spectrogram = tf.signal.stft(wav, frame_length=320, frame_step=32)  
    spectrogram = tf.abs(spectrogram)
    spectrogram = tf.expand_dims(spectrogram, axis=2)
    et = time.time()
    return spectrogram


# returns cached predictions of client session and current run
def cachePredictions(cache:Cache, dt, result, path):
    # add actual data
    prediction = Prediction(path, result)
    cache.addPrediction(prediction)
    return cache


def detectAnnouncement(cache:Cache, pred_threshold, announ_thresheld, usage_treshold, end_padding):
    """ detects announcements in a prediction list based on prediction-threshold and announcement-threshold
    returns a list of tuples with start and end indexes of the cachedPrediciton list
    usage_treshold: minimum secs of detected announcement """
    startIndex = -1
    endIndex = -1
    changeCounter = 0
    isAnnouncement = 0
    # TODO: Cut out predictions, that are already user in a detection
    usedPredictions = []
    # gather predictions that are already used
    for det in cache.detections:
        usedPredictions+=det.predictions

    for i, pred in enumerate(cache.predictions):
        # skip the ones already used
        if pred in usedPredictions: continue
        pred = float(pred.value)
        pred_threshold = float(pred_threshold)
        # detect 0-->1
        if (pred > pred_threshold and isAnnouncement == 0):
            changeCounter+=1
        if (pred < pred_threshold and isAnnouncement == 0) and changeCounter>0:
            changeCounter-=1

        # detect 1-->0
        if (pred < pred_threshold and isAnnouncement == 1):
            changeCounter+=1
        if (pred > pred_threshold and isAnnouncement == 1) and changeCounter>0:
            changeCounter-=1

        if isAnnouncement == 0:
            if changeCounter >= announ_thresheld:
                changeCounter = 0
                print("Announcement start detected!")
                # announcement starts
                isAnnouncement = 1
                startIndex = i - announ_thresheld
                if startIndex <0: startIndex = 0
        else:
            if changeCounter >= int(announ_thresheld * .4):
                changeCounter = 0
                isAnnouncement = 0
                # announcement ends 
                endIndex = i - announ_thresheld
                if endIndex <0:endIndex = 0
                
                if endIndex - startIndex >= usage_treshold:
                    print("Announcement end detected!")
                    endIndex = i
    # If no end detected, check if "smaller" end can be detected 
    #if isAnnouncement == 1 and startIndex != -1 and endIndex == -1:
    #    endCounter = 0
    #    for i, pred in enumerate(cache.predictions[len(cache.predictions)-announ_thresheld:]):
    #        pred = float(pred.value)
    #        pred_threshold = float(pred_threshold)
    #        if pred < pred_threshold:
    #            endCounter+=1
    #        if endCounter >= int(announ_thresheld / 2):
    #            endIndex = len(cache.predictions) - announ_thresheld + i
    #            break
        #if endIndex == -1:endIndex = len(cache.predictions) - 1
        #if endIndex == -1: return cache
        if endIndex != -1 and startIndex != -1:
            detection = Detection(cache.predictions[startIndex:endIndex])
            cache.addDetection(detection)
    return cache

def indexToDateTime(sid, indexList, paths):
    returnDates = []
    """Expects a list of tuples with the indexs and returns a list of the same structure but with timestamps"""
    for i,t in enumerate(indexList):
        currDateInterval = []
        startPath = paths[t[0]-1].replace("api/data/"+sid,"").replace(".wav","")
        
        if "slice" in startPath:
            startPath = startPath.replace("_slice_", ""[:-1])
        start = float(startPath)
        start = datetime.datetime.fromtimestamp(start)
        currDateInterval.append(str(start))

        if t[1] > len(paths):
            t[1] = len(paths) - 1
        endPath = paths[t[1]-2].replace("api/data/"+sid,"").replace(".wav","")
        if "slice" in endPath:
            endPath = endPath.replace("_slice_", ""[:-1])
        end = float(endPath)
        end = datetime.datetime.fromtimestamp(end)
        currDateInterval.append(str(end))

        returnDates.append(currDateInterval)

    return returnDates


def delSidData(sid, data, metaData = False):
    """ delete all cached data from sid (files + metadata) """
    runs = data[sid]["data"]
    for run in runs:
        for path in data[run]["path"]:
                os.remove(path)
    if metaData:
        data.pop(str(sid))


def delSidRunData(sid, data,metaData = False):
    """ delete all cached data from sid run (files + metadata) """
    for run in data:

        for path in data[run]["path"]:
                os.remove(path)
        #empty file list to prevent error when deleting (again)
        data[run]["path"] = []
    
    if metaData:
        data



def combAnonuncFiles(cache):
    combinedFiles = []
    # we may have multiple predictions in one run, so loop over em
    for i, det in enumerate(cache.detections):
        # create subset of cachedPredictions for predicted sequence
        preds = det.predictions
        combinedAudio = None
        if det.filePath == "":
            for j, pred in enumerate(preds):
                # load file
                file = AudioSegment.from_wav(pred.filePath)
                if combinedAudio == None:
                    combinedAudio = file
                else:
                    combinedAudio = combinedAudio + file
            # save each new audio file with sid and pred number
            if combinedAudio != None:
                filepath = "api/data/"+str(cache.uid)+"_"+str(i)+".wav"
                combinedAudio.export(filepath,format="wav")
                # save filename for llm
                det.filePath = filepath
    return cache


def applyLLM(cache:Cache):
    
    for i, det in enumerate(cache.detections):
        if any(trans.detection.uid == det.uid for trans in cache.transcriptions):
            continue
        text = ""
        # recognize (convert from speech to text)
        try:
            result = llm.transcribe(det.path, language="en", fp16=False, verbose=True)
            if result != "" and result is not None:
                # If transcribtion successful, remove from indexList
                text += result["text"]
                transcrption = Transcription(det, text)
                cache.addTranscription(transcrption)
        except:
            return
    return cache


def queueBlobs(path):
    """ if received audios are bigger than 0.1s, slice and queue them. If queued, than remove orginial path and put new
    insert new ones"""
    st = time.time()
    queue = []
    audio = AudioSegment.from_wav(path)
    while audio.duration_seconds > 0.1:
        sliced_audio = audio[0:100]
        new_path = path[:-4] + "_slice_"+str(len(queue)+1)+".wav"
        sliced_audio.export(new_path,format="wav")
        queue.append(new_path)
        audio = audio[1000:]
    if len(queue)>0:
        # dont forget the last part
        new_path = path[:-3] + "_slice_"+str(len(queue)+1)+".wav"
        audio.export(new_path,format="wav")
        queue.append(new_path)
        # delete old file
        os.remove(path)
    else:
        queue.append(path)
        audio.export(path,format="wav")

    et = time.time()
    # insert new path
    return queue


def cacheTranscriptions(sid, data, dt, text):
    """ ******* OBSOLET ****** caches transcripted texts and clear "path"
    in that way positive predicted files wont be transcripted twice
    """
    # just cache and clear if data is provided
    if text is not None and text != "":
        older_transcriptions = data[dt]["transcriptions"]
        combined_transcription = older_transcriptions + text
        data[dt]["transcriptions"] = combined_transcription
        return text
    else:
       data[dt]["transcriptions"]

def toSecs(x):
    return float(x/1000)

def saveLog(newLog):
    jsonFilePath = "api/log.json"
    newJsonLog = dictToJson(newLog)
    oldJsonLog = openJson(jsonFilePath)
    # check which entries are already in existing log and skip them
    for key in newJsonLog:
        if not key in oldJsonLog:
            oldJsonLog[key] = newJsonLog[key]
    saveJson(oldJsonLog, jsonFilePath)


def openJson(path):
    f = open(path)
    return json.load(f)

def dictToJson(dicti):
    r = json.dumps(dicti)
    return json.loads(r)

def saveJson(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
