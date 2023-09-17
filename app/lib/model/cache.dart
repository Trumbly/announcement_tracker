import 'package:app/model/prediction.dart';
import 'package:app/model/transcription.dart';
import 'package:app/model/user.dart';

import 'detection.dart';

class Cache {
  late User _user;
  late List<Prediction> _predictions;
  late List<Detection> _detections;
  late List<Transcription> _transcriptions;

  Cache(this._user,
      {List<Prediction>? predictions,
      List<Detection>? detections,
      List<Transcription>? transcriptions}) {
    _user = user;
    _predictions = predictions ?? [];
    _detections = detections ?? [];
    _transcriptions = transcriptions ?? [];
  }

  User get user => _user;
  List<Prediction> get predictions => _predictions;
  List<Detection> get detections => _detections;
  List<Transcription> get transcription => _transcriptions;

  set detections(List<Detection> detections) => _detections = detections;

  bool _isPredictionExisting(Prediction prediction) {
    for (int i = 0; i < _predictions.length; i++) {
      if (_predictions[i].id == prediction.id) return true;
    }
    return false;
  }

  bool _isDetectionExisting(Detection detection) {
    for (int i = 0; i < _detections.length; i++) {
      if (_detections[i].id == detection.id) return true;
    }
    return false;
  }

  bool _isTranscriptionExisting(Transcription transcription) {
    for (int i = 0; i < _transcriptions.length; i++) {
      if (_transcriptions[i].id == transcription.id) return true;
    }
    return false;
  }

  void addPrediction(Prediction prediction) {
    if (!_isPredictionExisting(prediction)) _predictions.add(prediction);
  }

  void addAllPredictions(List<Prediction> predictions) {
    for (int i = 0; i < predictions.length; i++) {
      if (!_isPredictionExisting(predictions[i])) {
        _predictions.add(predictions[i]);
      }
    }
  }

  void addTranscription(Transcription transcription) {
    if (!_isTranscriptionExisting(transcription)) {
      _transcriptions.add(transcription);
    }
  }

  void addAllTranscriptions(List<Transcription> transcription) {
    for (int i = 0; i < transcription.length; i++) {
      if (!_isTranscriptionExisting(transcription[i])) {
        _transcriptions.add(transcription[i]);
      }
    }
  }

  void addDetection(Detection detection) {
    if (!_isDetectionExisting(detection)) _detections.add(detection);
  }

  void addAllDetection(List<Detection> detection) {
    for (int i = 0; i < detection.length; i++) {
      if (!_isDetectionExisting(detection[i])) {
        _detections.add(detection[i]);
      }
    }
  }
}
