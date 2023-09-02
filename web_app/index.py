from flask import Flask, request, render_template
from tensorflow.keras.models import load_model as tfk__load_model
import tensorflow as tf
import tensorflow_io as tfio
import numpy as np
from flask_socketio import SocketIO
import time
import os
from pydub import AudioSegment
import speech_recognition as sr
import whisper

### Init

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["DEBUG"] = True
socketio = SocketIO(ping_timeout=1000, ping_interval=1000)

### functions ###

def load_model():
    st = time.time()
    model = tf.keras.models.load_model("model/model_6_small_1f_8020_AUG/model.h5")
    model.compile('Adam', loss='BinaryCrossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision()])
    et = time.time()
    return model

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

def predictBlob(path, model):
    st = time.time()
    wav = load_wav_16k_mono(path)
    spectogram = createSpectro(wav)
    st = time.time()
    prediction = model.predict(np.array( [spectogram,]))
    print("Result of prediction: "+str(prediction))
    et = time.time()
    return prediction

def saveBlob(socketId, audioBlob):
    st = time.time()
    # Load blob
    filename = str(socketId) + str(time.time()) + ".wav"
    filepath = os.path.join("data/", filename)
    with open(filepath, 'wb') as f: 
        f.write(audioBlob)
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
def cachePredictions(socketId, dt, result, path):
    st = time.time()
    dt = str(dt)
    
    # prepare struct
    if not dt in client_chache[socketId]["data"]:
        client_chache[socketId]["data"][dt] = {}
        client_chache[socketId]["data"][dt]["predictions"] = []
        client_chache[socketId]["data"][dt]["path"] = []
        client_chache[socketId]["data"][dt]["transcriptions"] = "Audio"
    # add actual data
    client_chache[socketId]["data"][dt]["predictions"].append(str(result[0][0]))
    client_chache[socketId]["data"][dt]["path"].append(str(path))
    et = time.time()
    return client_chache[socketId]["data"][dt]


def detectAnnouncement(cachedPredictions, pred_threshold, announ_thresheld, usage_treshold, end_padding):
    """ detects announcements in a prediction list based on prediction-threshold and announcement-threshold
    returns a list of tuples with start and end indexes of the cachedPrediciton list
    usage_treshold: minimum secs of detected announcement """
    st = time.time()
    startIndex = -1
    endIndex = -1
    indexList = []
    changeCounter = 0
    isAnnouncement = 0
    print(cachedPredictions)
    for i, pred in enumerate(cachedPredictions):
        pred = float(pred)
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
                    indexList.append([startIndex, endIndex+end_padding])
                startIndex = -1
                endIndex = -1
    if isAnnouncement == 1 and startIndex != -1 and endIndex == -1:
        endCounter = 0
        for i, pred in enumerate(cachedPredictions[len(cachedPredictions)-announ_thresheld:]):
            if pred < pred_threshold:
                endCounter+=1
            if endCounter >= int(announ_thresheld / 2):
                endIndex = len(cachedPredictions) - announ_thresheld + i
                break
        if endIndex == -1:endIndex = len(cachedPredictions) - 1
        indexList.append([startIndex, endIndex])
    """
    maxIndex = 0
    for t in indexList:
        print(t)
        if int(t[1])>maxIndex:
            maxIndex = t[1]
    if maxIndex > 0:
        toBeDeletedPath = client_chache[sid]["data"][dt]["path"][0:maxIndex]
        for path in toBeDeletedPath:
            os.remove(path)
        client_chache[sid]["data"][dt]["predictions"] = client_chache[sid]["data"][dt]["predictions"][maxIndex+1:]
        client_chache[sid]["data"][dt]["path"] = client_chache[sid]["data"][dt]["path"][maxIndex+1:]"""
    et = time.time()
    return indexList


def delSidData(sid, metaData = False):
    """ delete all cached data from sid (files + metadata) """
    for runs in client_chache[sid]["data"]:
        for path in client_chache[sid]["data"][runs]["path"]:
                os.remove(path)
    if metaData:
        client_chache.pop(str(sid))


def delSidRunData(sid, metaData = False):
    """ delete all cached data from sid run (files + metadata) """
    for runs in client_chache[sid]["data"]:

        for path in client_chache[sid]["data"][runs]["path"]:
                os.remove(path)
        #empty file list to prevent error when deleting (again)
        client_chache[sid]["data"][runs]["path"] = []
    
    if metaData:
        client_chache[sid]["data"]



def combAnonuncFiles(sid, cachedPredictions, predAnnouncResults):
    st = time.time()
    combinedFiles = []
    # we may have multiple predictions in one run, so loop over em
    for i, pred in enumerate(predAnnouncResults):
        # create subset of cachedPredictions for predicted sequence
        filePaths = cachedPredictions["path"][pred[0]:pred[1]+1]
        combinedAudio = None

        for j, path in enumerate(filePaths):
            # load file
            file = AudioSegment.from_wav(path)
            if combinedAudio == None:
                combinedAudio = file
            else:
                combinedAudio = combinedAudio + file
        # save each new audio file with sid and pred number
        if combinedAudio != None:
            filepath = "data/"+str(sid)+"_"+str(i)+".wav"
            combinedAudio.export(filepath,format="wav")
            # save filename for llm
            combinedFiles.append(filepath)
    et = time.time()
    return combinedFiles


def applyLLM(sid, filepaths):
    text = ""
    for path in filepaths:
        # recognize (convert from speech to text)
        try:
            result = llm.transcribe(path, language="en", fp16=False, verbose=True)
            print(result["text"])
            text = result["text"]
        except:
            return
    return text


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


def cacheTranscriptions(sid, dt, text):
    """ caches transcripted texts and clear "path"
    in that way positive predicted files wont be transcripted twice
    """
    # just cache and clear if data is provided
    if text is not None and text != "":
        older_transcriptions = client_chache[sid]["data"][dt]["transcriptions"]
        combined_transcription = older_transcriptions + text
        client_chache[sid]["data"][dt]["transcriptions"] = combined_transcription
        return text
    else:
        client_chache[sid]["data"][dt]["transcriptions"]


        

### Globals ###
model_const = load_model()
llm = whisper.load_model("medium")
# sockedtId: [blobs]
client_chache = {}


# MVP route
@app.route("/")
def test():
    return render_template('sender.html')

@app.route("/file_prediction", methods=['POST'])
def file_prediction():
    f = request.files['file']
    filename = f.filename
    f.save("data/"+f.filename)  
    filepath = os.path.join("data/", filename)
    
    if not filepath.endswith(".wav"):
        audioFormat = filepath[-3:]
        audioFile = AudioSegment.from_file(filepath, format=audioFormat)
        os.remove(filepath)
        filepath = filepath[:-3]+"wav"
        print(filepath)
        audioFile.export(filepath, format="wav")
    
    wav = load_wav_16k_mono(filepath)
    slices = []
    while tf.shape(wav)[0] > 1600:
        audioSlice = wav[:1600]
        slices.append(audioSlice)
        wav = wav[1600:]
    # dont forget the last one
    slices.append(wav)

    # predict results
    results = []
    for s in slices:
        spectro = createSpectro(s)
        r = model_const.predict(np.array( [spectro,]))
        results.append(r[0][0])
    
    # detect announcement
    announcements = detectAnnouncement(results, 0.9,10, 20, 0)

    combinedFiles = []
    # we may have multiple predictions in one run, so loop over em
    for i, pred in enumerate(announcements):
        print(announcements)
        audio = AudioSegment.from_wav(filepath)
        announcementAudio = audio[pred[0]*100:pred[1]*100]
        newFilePath = filepath[:-3]+"_slice_"+str(i)+".wav"
        combinedFiles.append(newFilePath)
        announcementAudio.export(newFilePath)

    texts = []
    print(combinedFiles)
    for path in combinedFiles:
        # recognize (convert from speech to text)
        try:
            result = llm.transcribe(path, fp16=False, verbose=True)
            print(result["text"])
            text = result["text"]
        except:
            return
        texts.append(text)

    return str(texts), 200

    

@socketio.on("connection")
def connect(sid):
    client_chache[str(sid)] = {"data": {},"last_ping": time.time()}

@socketio.on("disconnection")
def disconnection_test(sid):
    delSidData(sid,metaData=True)
    socketio.emit("disconnected","disconnected", room=sid)

# API route (WebSocket)
# can receive 100ms blobs (wav audios) and predicts in return
@socketio.on("predict_only")
def api(socketId, audioBlob):
    st = time.time()
    path = saveBlob(socketId, audioBlob)
    result = predictBlob(path, model_const)
    socketio.emit("prediction_result",str(result[0][0]), room=socketId)
    os.remove(path)
    et = time.time()

# API route (WebSocket)
# can receive 100ms blobs (wav audios), caches them and predicts them in return
@socketio.on("predict_sequence")
def api(socketId, audioBlob, dt):
    dt = str(dt)
    st = time.time()
    # save blob from bytes
    incoming_blob_path = saveBlob(socketId, audioBlob)
    # queue if audio blob > 1600 samples
    queue = queueBlobs(incoming_blob_path)
    for path in queue:
        # predict single blob
        result = predictBlob(path, model_const)
        # cache prediction for client session and run with the result and file path
        cachedPredictions = cachePredictions(socketId, dt, result, path)
    # check in cummulated predictions if announcement can be detected
    # when announcement was found, delete * up to max of prediction list (for now, cause llm is very slow)
    predAnnouncResults = detectAnnouncement(cachedPredictions["predictions"], 0.1 , 4, 2, 10)
    # when announcement detect, combine files and make one out of i
    announcFiles = combAnonuncFiles(socketId, cachedPredictions, predAnnouncResults)
    # give announcement files to LLM to return announcement text
    announcTexts = applyLLM(socketId, announcFiles)
    # cache transcriptions and clear announcFiles (so no double transciptions)
    transcriptions = cacheTranscriptions(socketId, dt, announcTexts)

    et1 = time.time()
    socketio.emit("prediction_result",str(transcriptions), room=socketId)
    et2 = time.time()

@socketio.on("stop")
def stop(socketId):
    # del files from run when recording is stopped
    delSidRunData(socketId)



if __name__ == '__main__':
    socketio.init_app(app)

socketio.run(app, port=8000)