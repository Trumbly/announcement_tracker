import 'package:app/model/prediction.dart';
import 'package:uuid/uuid.dart';

class Detection {
  late String _id;
  late List<Prediction> _predictions;
  late String _filePath;
  late DateTime _start;
  late DateTime _end;

  Detection(this._predictions, this._filePath, {String? id}) {
    _id = id ?? const Uuid().v4();
    _start = _predictions[0].receivedAt;
    _end = _predictions[_predictions.length - 1].receivedAt;
  }

  Detection.fromMap(Map<String, dynamic> map) {
    _id = map["uid"];
    _filePath = map["filePath"];
    _predictions = [];
    for (int i = 0; i < map["predictions"].length; i++) {
      Prediction prediction = Prediction(
        map["predictions"][i]["filePath"]!,
        double.parse(map["predictions"][i]["value"]!),
        id: map["predictions"][i]["id"],
        receivedAt: DateTime.parse(map["predictions"][i]["receivedAt"]!),
      );
      _predictions.add(prediction);
    }
    _start = _predictions[0].receivedAt;
    _end = _predictions[_predictions.length - 1].receivedAt;
  }

  String get id => _id;
  List<Prediction> get predictions => _predictions;
  String get filePath => _filePath;
  DateTime get start => _start;
  DateTime get end => _end;
}
