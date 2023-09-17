import 'package:app/model/detection.dart';
import 'package:uuid/uuid.dart';

class Transcription {
  late String _id;
  late Detection _detection;
  late String _value;
  late DateTime _transcripedAt;

  Transcription(this._detection, this._value, this._transcripedAt,
      {String? id}) {
    _id = id ?? const Uuid().v4();
  }

  String get id => _id;
  Detection get detection => _detection;
  String get value => _value;
  DateTime get transcripedAt => _transcripedAt;
}
