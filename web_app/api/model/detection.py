import time
import datetime
import uuid
from .prediction import Prediction
class Detection:
    uid:str
    predictions:list[Prediction]
    filePath:str
    start:time
    end:time

    def __init__(self, predictions:[],filePath:str="",uid:str=None, start:time=None, end:time=None):
        if uid == None:
            self.uid = str(uuid.uuid4())
        else:
            self.uid = uid
        self.predictions = predictions
        self.filePath = filePath
        if start == None:
            self.start = self.predictions[0].receivedAt
        if end == None:
            self.end = self.predictions[len(predictions)-1].receivedAt

    def toDict(self):
        predictionList = []
        for pred in self.predictions:
            predictionList.append(pred.toDict())
        return {
            "uid":self.uid,
            "predictions": predictionList,
            "filePath":self.filePath,
            "start":str(datetime.datetime.fromtimestamp(self.start)),
            "end":str(datetime.datetime.fromtimestamp(self.end))
        }