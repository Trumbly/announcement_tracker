import time
from .detection import Detection
from .prediction import Prediction
from .transcription import Transcription


class Cache:
    # TODO: user instead of socketId
    uid:str
    predictions:list[Prediction]
    detections:list[Detection]
    transcriptions:[Transcription]
    lastCall:time

    def __init__(self, uid:str, predictions:[]=[],detections:[]=[],transcriptions:[]=[]):
        self.uid = uid
        self.predictions = predictions
        self.detections = detections
        self.transcriptions = transcriptions

    def addPrediction(self, prediction:Prediction):
        for pred in self.predictions:
            if pred.uid == prediction.uid:
                return
        self.predictions.append(prediction)

    def addDetection(self, detection:Detection):
        for det in self.detections:
            if det.uid == detection.uid:
                return
        self.detections.append(detection)

    def addTranscription(self, transcription:Transcription):
        for tras in self.transcriptions:
            if tras.uid == transcription.uuid:
                return
        self.transcriptions.append(transcription)

    def getDetectionList(self):
        detectionList = []
        for det in self.detections:
            detectionList.append(det.toDict())
        return detectionList
    