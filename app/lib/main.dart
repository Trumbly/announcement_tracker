import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';

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
  final _recorder = FlutterSoundRecorder();
  StreamSink<Food>? _stream;

  @override
  void initState(){
    super.initState();

    initRecorder();
  }

  @override
  void dispose(){
    _recorder.closeRecorder();
    super.dispose();
  }

  Future initRecorder() async {
    final status = await Permission.microphone.request();
    if(status != PermissionStatus.granted){
      print("Microphone permission not granted");
    }
    await _recorder.openRecorder();

    _recorder.setSubscriptionDuration(
      const Duration(milliseconds: 500),
    );
  }

  void _startStopRecording() async {
    if (_recorder.isRecording) {
      final path = await _recorder.stopRecorder();
      //final audioFile = File(path!);

      print("Off");
      print("Recorded audio: $path");
    } else {
      _recorder.startRecorder(toStream: _stream, codec: Codec.pcm16WAV);
      print("On");
    }
  }



  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            StreamBuilder(
              //stream: ,
              builder: (context, snapchot){
              return Text(snapchot.hasData?snapchot.data!.toString():"no data yet..");
            }),
            StreamBuilder<RecordingDisposition>(
              stream: _recorder.onProgress, 
              builder: (context, snapchot) {
                final duration = snapchot.hasData 
                    ? snapchot.data!.duration : Duration.zero;
              return Text("${duration.inSeconds} s");
            }),
            TextButton.icon(onPressed: _startStopRecording, icon: _recorder.isRecording ? const Icon(Icons.stop) : const Icon(Icons.start), label: Text(_recorder.isRecording ? 'Stop' : 'Start')),
          ],
        ),
      ),
    );
  }
}
