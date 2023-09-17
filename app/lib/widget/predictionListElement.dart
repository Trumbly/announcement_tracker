import 'package:flutter/cupertino.dart';
import 'package:intl/intl.dart';

import '../model/detection.dart';

class DetectionListElement extends StatelessWidget {
  final int _index;
  final Detection _detection;
  const DetectionListElement(this._index, this._detection, {super.key});
  @override
  Widget build(Object context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text("#$_index  "),
        Text("From: ${DateFormat("HH:mm:ss").format(_detection.start)}"),
        Container(width: 20),
        Text("To: ${DateFormat("HH:mm:ss").format(_detection.end)}"),
      ],
    );
  }
}
