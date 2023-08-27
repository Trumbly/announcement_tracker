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
socketio = SocketIO()

### functions ###

def load_model():
    st = time.time()
    model = tf.keras.models.load_model("model/model_1.h5")
    model.compile('Adam', loss='BinaryCrossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision()])
    et = time.time()
    print("Loading model time: "+str((et-st)*1000))
    return model

def load_wav_16k_mono(path):
    # Load encoded wav file
    file_contents = tf.io.read_file(path)
    # Decode wav (tensors by channels)
    wav, sample_rate = tf.audio.decode_wav(file_contents, desired_channels=1)
    # Removes trailing axis
    wav = tf.squeeze(wav, axis=-1)
    sample_rate = tf.cast(sample_rate, dtype=tf.int64)
    # Goes from 44100Hz to 16000hz - amplitude of the audio signal
    wav = tfio.audio.resample(wav, rate_in=sample_rate, rate_out=16000)
    return wav

def predictBlob(path, model):
    wav = load_wav_16k_mono(path)
    spectogram = createSpectro(wav)
    return model.predict(np.array( [spectogram,]))

def saveBlob(socketId, audioBlob):
    # Load blob
    filename = str(socketId) + str(time.time()) + ".wav"
    filepath = os.path.join("data/", filename)
    with open(filepath, 'wb') as f: 
        f.write(audioBlob)
    return filepath

def createSpectro(wav):
    wav = wav[:1600]
    zero_padding_size = tf.zeros([1600] - tf.shape(wav)[0], dtype=tf.float32)
    wav = tf.concat([zero_padding_size, wav],0)

    spectrogram = tf.signal.stft(wav, frame_length=320, frame_step=32)
    spectrogram = tf.abs(spectrogram)
    spectrogram = tf.expand_dims(spectrogram, axis=2)
    return spectrogram


# returns cached predictions of client session and current run
def cachePredictions(socketId, dt, result,path):
    dt = str(dt)
    
    # prepare struct
    if not dt in client_chache[socketId]["data"]:
        client_chache[socketId]["data"][dt] = {}
        client_chache[socketId]["data"][dt]["predictions"] = []
        client_chache[socketId]["data"][dt]["path"] = []
    # add actual data
    client_chache[socketId]["data"][dt]["predictions"].append(str(result[0][0]))
    client_chache[socketId]["data"][dt]["path"].append(str(path))
    return client_chache[socketId]["data"][dt]


# detects announcements in a prediction list based on prediction-threshold and announcement-threshold
# returns a list of tuples with start and end indexes of the cachedPrediciton list
# usage_treshold: minimum secs of detected announcement
def detectAnnouncement(cachedPredictions, pred_threshold, announ_thresheld, usage_treshold, end_padding):
    startIndex = -1
    endIndex = -1
    indexList = []
    changeCounter = 0
    isAnnouncement = 0

    for i, pred in enumerate(cachedPredictions):
        pred = float(pred)
        if (pred > pred_threshold):
            changeCounter+=1

        if changeCounter >= announ_thresheld:
            changeCounter = 0
            if isAnnouncement == 0:
                # announcement starts
                isAnnouncement = 1
                startIndex = i
            else:
                isAnnouncement = 0
                # announcement ends
                endIndex = i
                # add padding
                
                if endIndex - startIndex >= usage_treshold:
                    indexList.append([startIndex, endIndex+end_padding])
                startIndex = -1
                endIndex = -1
    return indexList

# delete all cached data from sid (files + metadata)
def delSidData(sid, metaData = False):
    for runs in client_chache[sid]["data"]:
        for path in client_chache[sid]["data"][runs]["path"]:
                os.remove(path)
    if metaData:
        client_chache.pop(str(sid))

# delete all cached data from sid run (files + metadata)
def delSidRunData(sid, metaData = False):
    for runs in client_chache[sid]["data"]:

        for path in client_chache[sid]["data"][runs]["path"]:
                os.remove(path)
        #empty file list to prevent error when deleting (again)
        client_chache[sid]["data"][runs]["path"] = []
    
    if metaData:
        client_chache[sid]["data"]



def combAnonuncFiles(sid, cachedPredictions, predAnnouncResults):
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
        filepath = "data/"+str(sid)+"_"+str(i)+".wav"
        combinedAudio.export(filepath,format="wav")
        # save filename for llm
        combinedFiles.append(filepath)
    return combinedFiles


def applyLLM(sid, filepaths):
    texts = []
    for path in filepaths:
        # recognize (convert from speech to text)
        try:
            result = llm.transcribe(path)
            print(result["text"])
            texts.append(result["text"])
        except:
            print('Sorry.. run again...')
    return texts


        

### Globals ###
model_const = load_model()
llm = whisper.load_model("base")
# sockedtId: [blobs]
client_chache = {}


# MVP route
@app.route("/")
def test():
    return render_template('sender.html')

@socketio.on("connection")
def connect(sid):
    print("Client connected: "+str(sid))
    client_chache[str(sid)] = {"data": {},"last_ping": time.time()}
    print("Client cache: "+str(client_chache))

@socketio.on("disconnection")
def disconnection_test(sid):
    print("Client disconnected: "+str(sid))
    delSidData(sid,metaData=True)
    socketio.emit("disconnected","disconnected", room=sid)
    print("Client cache: "+str(client_chache))

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
    print("Overall processing time: "+str((et-st)*1000))

# API route (WebSocket)
# can receive 100ms blobs (wav audios), caches them and predicts them in return
@socketio.on("predict_sequence")
def api(socketId, audioBlob, dt):
    st = time.time()
    # save blob from bytes
    path = saveBlob(socketId, audioBlob)
    # predict single blob
    result = predictBlob(path, model_const)
    # cache prediction for client session and run with the result and file path
    cachedPredictions = cachePredictions(socketId, dt, result, path)
    # check in cummulated predictions if announcement can be detected
    predAnnouncResults = detectAnnouncement(cachedPredictions["predictions"], 0.1 , 5, 2, 10)
    # when announcement detect, combine files and make one out of i
    announcFiles = combAnonuncFiles(socketId, cachedPredictions, predAnnouncResults)
    # give announcement files to LLM to return announcement text
    announcTexts = applyLLM(socketId, announcFiles)
    socketio.emit("prediction_result",str(announcTexts), room=socketId)
    et = time.time()
    print("Overall processing time: "+str((et-st)*1000))

@socketio.on("stop")
def stop(socketId):
    # del files from run when recording is stopped
    print("Deleting files from run. ID: "+str(socketId))
    delSidRunData(socketId)



if __name__ == '__main__':
    socketio.init_app(app)

socketio.run(app, port=8000)