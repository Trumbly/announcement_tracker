import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:app/widget/predictionListElement.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart';
import 'package:sound_stream/sound_stream.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'dart:math' as math;

import 'model/cache.dart';
import 'model/detection.dart';
import 'model/user.dart';

const _SERVER_URL = 'https://ladendorf.tech:80/';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: MyHomePage(title: 'Announcement Tracker'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  RecorderStream _recorder = RecorderStream();
  PlayerStream _player = PlayerStream();

  bool _isRecording = false;
  bool _isPlaying = false;

  late StreamSubscription _recorderStatus;
  late StreamSubscription _playerStatus;
  late StreamSubscription _audioStream;
  String _result = "";
  String dt = "";
  bool connected = false;
  String _socketId = "";
  late User user;
  late Cache cache;

  List<int> bufferList = [];

  Socket socket = io(
      _SERVER_URL,
      OptionBuilder().setTransports(['websocket']) // for Flutter or Dart VM
          .build());
  final _resultSC = StreamController<List<Detection>>();
  Sink get updateResult => _resultSC.sink;
  Stream<List<Detection>> get result => _resultSC.stream;

  Float64List normalizeRmsVolume(List<double> a, double target) {
    final b = Float64List.fromList(a);
    double squareSum = 0;
    for (final x in b) {
      squareSum += x * x;
    }
    double factor = target * math.sqrt(b.length / squareSum);
    for (int i = 0; i < b.length; ++i) {
      b[i] *= factor;
    }
    return b;
  }

  Uint64List linSpace(int end, int steps) {
    final a = Uint64List(steps);
    for (int i = 1; i < steps; ++i) {
      a[i - 1] = (end * i) ~/ steps;
    }
    a[steps - 1] = end;
    return a;
  }

  String gradient(double power) {
    const scale = 2;
    const levels = [' ', '░', '▒', '▓', '█'];
    int index = math.log((power * levels.length) * scale).floor();
    if (index < 0) index = 0;
    if (index >= levels.length) index = levels.length - 1;
    return levels[index];
  }

  Future<List> save(List<int> data, int sampleRate) async {
    // create new file
    final Directory directory = await getApplicationDocumentsDirectory();
    Random random = new Random();
    int randomNumber = random.nextInt(10000000);
    final String path = directory.path +
        "/" +
        DateTime.now().toString() +
        randomNumber.toString() +
        ".wav";
    File recordedFile = File(path);

    var channels = 1;

    int byteRate = ((16 * sampleRate * channels) / 8).round();

    var size = data.length;

    var fileSize = size + 36;

    Uint8List header = Uint8List.fromList([
      // "RIFF"
      82, 73, 70, 70,
      fileSize & 0xff,
      (fileSize >> 8) & 0xff,
      (fileSize >> 16) & 0xff,
      (fileSize >> 24) & 0xff,
      // WAVE
      87, 65, 86, 69,
      // fmt
      102, 109, 116, 32,
      // fmt chunk size 16
      16, 0, 0, 0,
      // Type of format
      1, 0,
      // One channel
      channels, 0,
      // Sample rate
      sampleRate & 0xff,
      (sampleRate >> 8) & 0xff,
      (sampleRate >> 16) & 0xff,
      (sampleRate >> 24) & 0xff,
      // Byte rate
      byteRate & 0xff,
      (byteRate >> 8) & 0xff,
      (byteRate >> 16) & 0xff,
      (byteRate >> 24) & 0xff,
      // Uhm
      ((16 * channels) / 8).round(), 0,
      // bitsize
      16, 0,
      // "data"
      100, 97, 116, 97,
      size & 0xff,
      (size >> 8) & 0xff,
      (size >> 16) & 0xff,
      (size >> 24) & 0xff,
      ...data
    ]);
    recordedFile.writeAsBytesSync(header, flush: true);
    return [recordedFile, path];
  }

  // Platform messages are asynchronous, so we initialize in an async method.
  Future<void> initPlugin() async {
    socket.onConnect((_) {
      socket.emit("connection/sid", [socket.id]);
      setState(() {
        connected = true;
        _socketId = socket.id!;
      });
      print('connected with sid: $_socketId');
    });
    socket.onDisconnect((_) {
      print('disconnected with sid: $_socketId');
      setState(() {
        connected = false;
        _socketId = "";
      });
    });

    socket.on("detection", (data) {
      //List<Prediction> predictions = data.map((item)=> Prediction.fromJson(item)).toList<Prediction>();
      print(data);
      List<Detection> detections = [];
      for (var i = 0; i < data.length; i++) {
        /*Detection detection = Detection.fromList(
            (data[i] as List).map((e) => e as Map<String, dynamic>).toList());*/
        Detection detection = Detection.fromMap(data[i]);
        detections.add(detection);
      }
      cache.addAllDetection(detections);
      _resultSC.add(cache.detections);
      setState(() {
        //_result = data;
      });
    });

    _audioStream = _recorder.audioStream.listen((data) async {
      // Add data to bufferlist
      bufferList += data;
      // loop at size 3200 (0.1s audio slice)
      while (bufferList.length > 3200) {
        List<int> dataChunk = data.sublist(0, 3200);
        List blobInfo = await save(dataChunk, 16000);
        File blob = blobInfo[0];
        socket
            .emit("predict_sequence", [socket.id, blob.readAsBytesSync(), dt]);
        //predictOffline(blobInfo[1]);
        try {
          bufferList.removeRange(0, 3200);
        } catch (ex) {
          print(ex);
        }
        // Remove File again
        await blob.delete();
      }
      // Do one last time
      List blobInfo = await save(bufferList, 16000);
      File blob = blobInfo[0];
      socket.emit("predict_sequence", [socket.id, blob.readAsBytesSync(), dt]);
      // predict Offline
      //  String result = await predictWav(wav);
      // Remove File again
      await blob.delete();
      bufferList = [];
    });

    _recorderStatus = _recorder.status.listen((status) {
      if (mounted) {
        setState(() {
          _isRecording = status == SoundStreamStatus.Playing;
        });
      }
    });

    _playerStatus = _player.status.listen((status) {
      if (mounted) {
        setState(() {
          _isPlaying = status == SoundStreamStatus.Playing;
        });
      }
    });

    await Future.wait([
      _recorder.initialize(),
      _player.initialize(),
    ]);

    socket.connect();
  }

  late Interpreter _interpreter;

  loadModel() async {
    _interpreter = await Interpreter.fromAsset('assets/model_6_small.tflite');
  }

  @override
  void initState() {
    super.initState();
    dt = DateTime.now().toString();
    initPlugin();
    loadModel().then((value) {
      setState(() {});
    });
    user = User("test@test.de", "FOR", "SUR", "PW");
    cache = Cache(user);
  }

  @override
  void dispose() {
    super.dispose();
    _recorder.dispose();
  }

  void _startRecord() async {
    await _player.stop();
    await _recorder.start();
    setState(() {
      _isRecording = true;
    });
  }

  void _stopRecord() async {
    await _recorder.stop();
    await _player.start();
    setState(() {
      _isRecording = false;
    });
  }

  void _startStopRecording() async {
    if (connected) {
      if (_isRecording) {
        _stopRecord();
      } else {
        _startRecord();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text("Sousi - Dear - Whatever"),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Material(child: Text(connected ? 'Connected' : 'Not connected')),
            Container(height: 20),
            //TextButton.icon(onPressed: _startStopRecording, icon: _isRecording ? const Icon(Icons.stop) : const Icon(Icons.record_voice_over), label: Text(_isRecording ? 'Stop' : 'Start')),
            CupertinoButton.filled(
              onPressed: _startStopRecording,
              child: Text(_isRecording ? 'Stop' : 'Start'),
            ),
            StreamBuilder(
                stream: _resultSC.stream,
                builder: (ctx, snapchot) {
                  if (snapchot.hasData) {
                    return ListView.builder(
                        scrollDirection: Axis.vertical,
                        shrinkWrap: true,
                        itemCount: snapchot.data!.length,
                        padding: const EdgeInsets.all(5),
                        itemBuilder: (context, index) {
                          if (snapchot.data!.isNotEmpty) {
                            return Material(
                                child: DetectionListElement(
                                    index, snapchot.data![index]));
                          } else {
                            return Container();
                          }
                        });
                  } else {
                    return Container();
                  }
                }),
          ],
        ),
      ),
    );
  }
}
