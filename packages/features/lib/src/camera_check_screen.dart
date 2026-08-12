import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:poseperfect_domain/poseperfect_domain.dart';

/// The hello-world screen for issue #8, "Prove the ios-builder pipeline end to
/// end".
///
/// Its only job is to answer one question on a physical iPhone signed by a free
/// Apple ID: does the camera actually open? Everything it renders is evidence
/// for that question, including the failures - a permission denial or a plugin
/// error is drawn on screen rather than swallowed, because a blank preview and
/// a refused preview look identical otherwise.
class CameraCheckScreen extends StatefulWidget {
  const CameraCheckScreen({super.key});

  @override
  State<CameraCheckScreen> createState() => _CameraCheckScreenState();
}

class _CameraCheckScreenState extends State<CameraCheckScreen> {
  CameraController? _controller;
  List<CameraDescription> _cameras = const [];
  int _selected = 0;
  Object? _error;
  StackTrace? _stackTrace;

  @override
  void initState() {
    super.initState();
    _start();
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _start() async {
    try {
      // On iOS this is what triggers the NSCameraUsageDescription prompt.
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw StateError('availableCameras() returned an empty list');
      }
      if (!mounted) return;
      setState(() {
        _cameras = cameras;
        _error = null;
        _stackTrace = null;
      });
      await _open(_selected);
    } catch (error, stackTrace) {
      if (!mounted) return;
      setState(() {
        _error = error;
        _stackTrace = stackTrace;
      });
    }
  }

  Future<void> _open(int index) async {
    final previous = _controller;
    _controller = null;
    await previous?.dispose();

    final controller = CameraController(
      _cameras[index],
      ResolutionPreset.high,
      // Issue #8 needs stills and a preview only. Audio would drag in
      // NSMicrophoneUsageDescription for no reason.
      enableAudio: false,
    );
    try {
      await controller.initialize();
      if (!mounted) return;
      setState(() {
        _controller = controller;
        _selected = index;
        _error = null;
        _stackTrace = null;
      });
    } catch (error, stackTrace) {
      if (!mounted) return;
      setState(() {
        _error = error;
        _stackTrace = stackTrace;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PosePerfect - camera check')),
      body: SafeArea(child: _body(context)),
      floatingActionButton: _cameras.length > 1
          ? FloatingActionButton(
              onPressed: () => _open((_selected + 1) % _cameras.length),
              tooltip: 'Switch camera',
              child: const Icon(Icons.cameraswitch),
            )
          : null,
    );
  }

  Widget _body(BuildContext context) {
    if (_error != null) {
      return _Failure(error: _error!, stackTrace: _stackTrace, onRetry: _start);
    }

    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }

    final camera = _cameras[_selected];
    return Column(
      children: [
        Expanded(
          child: Center(
            child: AspectRatio(
              aspectRatio: controller.value.aspectRatio,
              child: CameraPreview(controller),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Camera identity is a domain invariant (issue #6): the ML Kit
              // Flutter plugin swaps left/right on the front camera, and the
              // class of bug is not unique to it. Showing it here is a habit
              // worth forming early.
              Text(
                'Camera: ${camera.name} (${camera.lensDirection.name}, '
                'sensor ${camera.sensorOrientation} deg)',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              Text(
                'Preview: ${controller.value.previewSize?.width.toInt()}'
                'x${controller.value.previewSize?.height.toInt()}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 8),
              // Reaching through to packages/domain proves the workspace edge
              // app -> features -> domain actually links on a real device.
              Text(
                'Domain reachable: '
                '${MandatoryPose.values.length} mandatory poses, '
                'first is ${MandatoryPose.values.first.displayName}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Failure extends StatelessWidget {
  const _Failure({
    required this.error,
    required this.stackTrace,
    required this.onRetry,
  });

  final Object error;
  final StackTrace? stackTrace;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final description = error is CameraException
        ? 'CameraException ${(error as CameraException).code}: '
              '${(error as CameraException).description}'
        : error.toString();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Camera failed to open',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          SelectableText(description),
          const SizedBox(height: 12),
          Text(
            'If the code is CameraAccessDenied, permission was refused - '
            'grant it in Settings > PosePerfect > Camera and retry.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: onRetry, child: const Text('Retry')),
          if (stackTrace != null) ...[
            const SizedBox(height: 24),
            SelectableText(
              stackTrace.toString(),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ],
      ),
    );
  }
}
