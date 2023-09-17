import time
from .extensions import socketio
from .functions import *
from .model.cache import Cache

caches:[] = []
def getCacheById(caches, id):
    for cache in caches:
        if cache.uid == id:
            return cache
    newCache = Cache(id)
    caches.append(newCache)
    return newCache
@socketio.on("connection/sid")
def connection(sid):
    print("connected to: "+ str(sid))
    caches.append(Cache(sid))

@socketio.on("disconnect")
def disconnection_test():
    print("Disconnected from a socket")
    #saveLog(client_chache)

# API route (WebSocket)
# can receive 100ms blobs (wav audios) and predicts in return
@socketio.on("predict_only")
def api(socketId, audioBlob):
    st = time.time()
    path = saveBlob(socketId, audioBlob)
    result = predictBlob(path)
    socketio.emit("prediction_result",str(result[0][0]), room=socketId)
    os.remove(path)
    et = time.time()

# API route (WebSocket)
# can receive 100ms blobs (wav audios), caches them and predicts them in return
@socketio.on("predict_sequence")
def api(socketId, audioBlob, dt):
    cache = getCacheById(caches, socketId)
    # save blob from bytes
    incoming_blob_path = saveBlob(socketId, audioBlob)
    # queue if audio blob > 1600 samples
    queue = queueBlobs(incoming_blob_path)
    for path in queue:
        # predict single blob
        result = predictBlob(path)
        # cache prediction for client session and run with the result and file path
        cache = cachePredictions(cache, dt, result, path)
    # check in cummulated predictions if announcement can be detected
    # when announcement was found, delete * up to max of prediction list (for now, cause llm is very slow)
    cache = detectAnnouncement(cache, 0.1 , 4, 2, 10)
    # when announcement detect, combine files and make one out of i
    #cache = combAnonuncFiles(cache)
    # give announcement files to LLM to return announcement text
    #cache = applyLLM(cache)
    detectionList = cache.getDetectionList()
    socketio.emit("detection",detectionList, room=socketId)
    et2 = time.time()
