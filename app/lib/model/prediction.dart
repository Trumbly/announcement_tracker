import 'package:uuid/uuid.dart';

class Prediction {
  late String _id;
  late DateTime _receivedAt;
  final String _filePath;
  late double _value;

  Prediction(this._filePath, double value, {String? id, DateTime? receivedAt}) {
    _id = id ?? const Uuid().v4();

    _receivedAt = receivedAt ?? DateTime.now();
  }

  String get id => _id;
  DateTime get receivedAt => _receivedAt;
  String get filePath => _filePath;
  double get value => _value;

  set value(double value) => _value;
}
