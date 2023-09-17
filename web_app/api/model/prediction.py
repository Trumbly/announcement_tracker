import time
import datetime
import uuid
import numpy as np
class Prediction:
    uid:str
    filePath:str
    value:float
    receivedAt:time

    def __init__(self, filePath:str, value:float, receivedAt:time=None, uid:str=None):
        if uid == None:
            self.uid = str(uuid.uuid4())
        else:
            self.uid = uid
        if receivedAt == None:
            self.receivedAt = time.time()
        else:
            self.time = time
        self.filePath = filePath
        self.value = np.format_float_positional(value, trim='-')
        self.receivedAt = receivedAt

    def toDict(self):
        return {
            "uid":self.uid,
            "filePath":self.filePath,
            "value":str(self.value),
            "receivedAt": str(datetime.datetime.fromtimestamp(self.receivedAt))
        }