import 'package:flutter/material.dart';
import 'package:poseperfect_features/poseperfect_features.dart';

void main() {
  runApp(const PosePerfectApp());
}

class PosePerfectApp extends StatelessWidget {
  const PosePerfectApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PosePerfect',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1B1B1F),
          brightness: Brightness.dark,
        ),
      ),
      // Issue #8 only: the whole app is the camera check until the pipeline is
      // proven. The real shell arrives with the tracer bullet, issue #14.
      home: const CameraCheckScreen(),
    );
  }
}
