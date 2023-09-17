import time
import datetime
import uuid
from .detection import Detection


class Transcription:
    uid:str
    detection:list[Detection]
    value:str
    transcripedAt:time

    def __init__(self, detection:Detection, value:str, uid:str=None, transcripedAt:time=None):
        if uid == None:
            self.uid = str(uuid.uuid4())
        else:
            self.uid = uid
        if time == None:
            self.time = time.time()
        else:
            self.time = time
        self.detection = detection
        self.value = value
        self.transcripedAt = transcripedAt

    def toDict(self):
        detectionList = []
        for det in self.detections:
            detectionList.append(det.toDict())
        return {
            "uid":self.uid,
            "detection":detectionList,
            "value":str(self.value),
            "transcripedAt": str(datetime.datetime.fromtimestamp(self.transcripedAt))
        }