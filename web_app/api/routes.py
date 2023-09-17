from flask import render_template, request, Blueprint
from .functions import *

main = Blueprint("main", __name__)

# MVP route
@main.route("/")
def test():
    return render_template('sender.html')

@main.route("/file_prediction", methods=['POST'])
def file_prediction():
    f = request.files['file']
    filename = f.filename
    f.save("api/data/"+f.filename)  
    filepath = os.path.join("api/data/", filename)
    
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

    announcements = map(toSecs, announcements)

    return str(announcements), 200

@main.route("/file_prediction_transcription", methods=['POST'])
def file_prediction_transcription():
    f = request.files['file']
    filename = f.filename
    f.save("api/data/"+f.filename)  
    filepath = os.path.join("api/data/", filename)
    
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