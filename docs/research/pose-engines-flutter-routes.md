# MediaPipe from Flutter on iOS - route survey

Supplementary note to [#3](https://github.com/grez-lucas/poseperfect/issues/3), 2026-08-07. Grading convention matches `pose-engines.md`.

**Verdict: the "MediaPipe has no Flutter story" belief is stale in its details but true in its substance.** Nobody maintains a production-grade Flutter binding to MediaPipe Tasks Vision on iOS. You either write ~400 lines of Swift yourself, accept a hobby-grade wrapper, or leave MediaPipe's graph behind for LiteRT.

---

## 1. Binary-level confirmation of the rear-view root cause

**VERIFIED, and this is the most valuable line in the note.** `strings` on the extracted `pose_detector.tflite` shows the embedded TFLite metadata description reads:

> "Detects human face with frontal camera" / "Full Range Face Detection"

That is Google's own shipped bundle describing its **person** detector as a **face** detector. It is a copy-paste error in their metadata, but it is also direct binary-level corroboration of the claim in `pose-engines.md` that BlazePose locates people by finding faces - which is the root cause of the rear-view failure on three of our eight mandatories.

Also confirmed: the weights are named `blazepose_ghum_39kp_lite_oss_2021_07_02` and `blazepose_detector_eff_retina_4kp_sparse_2021_10_18`. **Not retrained since 2021.**

---

## 2. The hypothesis worth testing: swap the person detector

**INFERRED, but well-grounded and cheap to test.**

If the rear-view failure originates in the *detection* stage (a face detector cannot find a face that is facing away), then a pipeline that uses a **general person detector** instead should not fail the same way.

`pose_detection` 3.6.0 does exactly this: it pairs the BlazePose **landmark** model with a **YOLOv8n** person detector rather than BlazePose's face-based one. YOLO detects "person" from any orientation.

This does not fix everything. The landmark model is still BlazePose, still trained on a corpus of people facing their phones, so landmark *accuracy* on rear views remains unproven. But it plausibly removes the failure mode where the pipeline never locates the subject at all and falls back to a learned average pose. **That is a distinct and testable hypothesis, and it belongs in the bake-off.**

**Licensing caveat, and it is serious.** `pose_detection` is Apache-2.0, but it bundles `yolov8n_float32.tflite`. Ultralytics YOLOv8 weights are **AGPL-3.0**, which `pose-engines.md` already flagged as a hard blocker for a closed-source app. A package's own licence does not launder the licence of weights it ships. **Verify the provenance and licence of that specific `.tflite` before building anything on it.**

---

## 3. The pod is now a compatibility hazard

**VERIFIED by downloading and unpacking the actual tarballs.**

`MediaPipeTasksVision` 0.10.35 and **1.0.0 ship a 928-byte dummy framework binary** - an `ar` archive containing one object, `MediaPipeTasksVision_framework_dummy.o`. The implementation moved into `MediaPipeTasksCommon` (symbol inspection confirms `_OBJC_CLASS_$_MPPPoseLandmarker` now lives there). The modulemap lost all 17 of its `link framework` directives.

Consequences:
- Open linking bug [mediapipe#6258](https://github.com/google-ai-edge/mediapipe/issues/6258) (opened 2026-03-25) reports exactly this breakage. Still tagged `stat:awaiting googler`, **no Google response, no workaround**.
- Version 0.10.33's podspec has been **removed from the CocoaPods Specs repo** (404), consistent with being pulled after the bug.
- Minimum iOS deployment target silently jumped **12.0 to 15.0** between 0.10.21 and 0.10.35. The official setup guide still says 12.0.
- Linked code size grew roughly **2.8x**: ~29 MB of sections on 0.10.21 against ~83 MB on 1.0.0.

**If MediaPipe were ever revisited, pin `0.10.21`** - the last version with a self-contained Vision framework.

---

## 4. The Flutter landscape, measured

**VERIFIED** from the pub.dev and GitHub APIs, observed 2026-08-07.

| Package | Ver | Last publish | Likes | DL/30d | Wraps |
|---|---|---|---|---|---|
| `google_mlkit_pose_detection` | 0.15.0 | 2026-07-07 | **79** | **18,966** | ML Kit |
| `pose_detection` (hugo.ml) | 3.6.0 | 2026-07-25 | 5 | **1,689** | LiteRT + YOLOv8n + BlazePose |
| `flutter_mediapipe_vision` | 0.3.2 | 2026-08-01 | 2 | 164 | MediaPipeTasksVision |
| `flutter_mp_pose_landmarker` | 0.1.8 | 2026-04-27 | 6 | 112 | MediaPipeTasksVision |
| `thinksys_mediapipe_plugin` | 0.0.13 | 2024-10-22 | 20 | 43 | MediaPipeTasksVision |

The adoption gap is the story: the best-adopted MediaPipe wrapper has **20 likes and 43 downloads a month**; the ML Kit binding has 79 and nearly 19,000.

**Google's own `flutter-mediapipe` is abandonware.** Vision was never implemented - `packages/mediapipe-task-vision/pubspec.yaml` carries `publish_to: none` and an unedited Flutter template README. `mediapipe_vision` **404s on pub.dev**. Issue #51, "Add PoseLandmarker task", has been open since 2024-05-20. Last substantive commit was 2025-06-04, titled "turns off CI jobs". It is not archived and carries no deprecation banner, which makes it look alive from pub.dev. **Do not use it.**

The official iOS pose sample has not been touched since 2024-05-21 and pins a pod 14 versions behind. The Pose Landmarker task is **still labelled "Preview / early release"** on Google's docs.

Community wrapper quality, from reading the sources:
- `flutter_mediapipe_vision`: `runningMode` hardcoded to `.image`, CPU only, model hardcoded to lite, and **a full-frame BGRA copy across the method channel per frame** (3.7 MB at 720p, each direction). Its podspec declares `ios 13.0` while the pod it resolves to declares 15.0 - a conflict out of the box. The example app has no iOS runner.
- `flutter_mp_pose_landmarker`: technically the best - `.liveStream`, GPU with CPU fallback, native camera so frames never cross the channel. But iOS is "under testing", it bundles all three `.task` files (**45.8 MB**), and its licence is unstated on pub.dev and `NOASSERTION` on GitHub. **A real legal blocker.**

---

## 5. `pose_detection` + `flutter_litert`, assessed

The most maintained and best-engineered Flutter package in the survey: 160/160 pub points, Apache-2.0, CI with integration tests, all six platforms, active weekly releases. `flutter_litert` exposes **Metal, CoreML and XNNPACK delegates on iOS**.

But it is BlazePose-the-model, not MediaPipe-the-pipeline. Reading the source, it omits: rotation-aligned ROI derivation (it uses an axis-aligned letterbox crop, so rotated subjects degrade), heatmap refinement (the tensor is allocated but unused), the previous-frame tracking loop, and landmark smoothing.

**For our use case those omissions matter less than they would for video** - we score held still poses, one frame at a time, where tracking and smoothing are irrelevant by construction. The rotation-alignment gap is the one that could bite, and only if the subject is significantly off-vertical, which a standing bodybuilder is not.

Cost: **49.8 MB of model assets** declared unconditionally in every build, plus LiteRT xcframeworks, plus `opencv_dart`'s native OpenCV.

---

## Bottom line for the map

Three things to carry forward:

1. **The face-detector root cause is confirmed at the binary level.** Google's shipped detector metadata literally says "Full Range Face Detection".
2. **The YOLOv8n-detector hypothesis is worth one bake-off test** - it may escape the rear-view detection failure while keeping BlazePose landmarks. Subject to resolving the AGPL question on those weights first.
3. **MediaPipe's native pod is currently hazardous** (stub framework, unanswered linking bug, pulled version, 2.8x size growth), which independently reinforces the decision not to pursue it.
