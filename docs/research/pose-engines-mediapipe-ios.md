# MediaPipe PoseLandmarker on iOS - packaging, licensing and telemetry

Supplementary note to [#3](https://github.com/grez-lucas/poseperfect/issues/3). Method: where documentation was thin, primary artifacts were fetched and unpacked - the actual `.task` bundles, the actual CocoaPods tarballs, the xcframeworks and TFLite flatbuffers. Those are the strongest claims here.

Grading convention matches `pose-engines.md`: **VERIFIED** / **INFERRED** / **ANECDOTAL**.

---

## 1. The disqualifier: MediaPipe sends telemetry to Google

**VERIFIED.** The pod's `NOTICE` file ships a "MediaPipe Tasks Privacy Notice", last modified 2026-06-05:

> "MediaPipe Tasks APIs send metrics about the performance and utilization of the APIs in your app to Google. Google uses this metrics data to measure performance, usage, debug, maintain and improve the MediaPipe Tasks, as further described in our Privacy Policy... **You are responsible for obtaining informed consent from your app users about Google's processing of MediaPipe metrics data as required by applicable law.**"

Input images and video stay on device. Telemetry does not. **It is not opt-out-able through the public API.**

**This directly contradicts map decision 20**, which commits to offline absolute with no network permission in v1, and which was justified partly on the grounds that it leaves nothing to write a privacy policy about. Adopting MediaPipe would mean shipping network egress we did not choose, plus a consent obligation.

This is a second, independent reason to rule MediaPipe out, on top of the Flutter binding problem established in `pose-engines.md`. The binding problem is a cost; this is a conflict with a stated product commitment.

**VERIFIED, related:** no `PrivacyInfo.xcprivacy` ships in either pod. Required-reason API symbols are present in the binary (`mach_absolute_time` x17, `fstat` x38, `statfs` x6, `NSUserDefaults` x3), so `NSPrivacyAccessedAPITypes` declarations would have to be authored by hand.

---

## 2. The finding that helps: segmentation masks are free

**VERIFIED, and this is the useful one for [#17](https://github.com/grez-lucas/poseperfect/issues/17).**

From `pose_landmarks_detector_graph.cc`, the single TFLite inference **always** produces all five output tensors, and `SplitTensorVectorCalculator` splits them *after* inference. `segmentation_tensors` is merely gated by a `GateCalculator` on pose presence.

**The segmentation head runs on every frame whether you ask for it or not.** Setting `shouldOutputSegmentationMasks = true` switches on downstream post-processing only. The inference cost of enabling segmentation is **zero**.

Costs that are real (INFERRED from the graph, magnitude not benchmarked): a sigmoid over 65,536 pixels, a 3x3 matrix inversion, a warp-affine resample to full frame resolution, and allocation of a W x H buffer per frame per pose.

**Resolution, two distinct numbers.** Parsing the TFLite flatbuffer of `pose_landmarks_detector.tflite`, output tensor `Identity_2` has shape **1 x 256 x 256 x 1**. But the API hands back a mask at **full input image resolution**, warped back from the letterboxed ROI. So a 1920x1080 frame yields a 1920x1080 mask whose true detail is capped at 256x256 *within the person's bounding box*.

For a lat-spread width measurement that is likely plenty - torso width spans a large fraction of the bounding box - but it is an upper bound worth knowing before designing a metric around it.

Buffer lifetime caveat, verbatim from `MPPMask.h`: masks "are owned by the underlying C++ Task", so the buffer is invalid after the callback returns unless `copy()` is called. And "the first time you access the data as a type different from the underlying type, an expensive type conversion is performed".

---

## 3. Binary size: the story is `-force_load`, not the models

**VERIFIED.** The `MediaPipeTasksCommon` podspec applies:

```
"OTHER_LDFLAGS[sdk=iphoneos*]": "$(inherited) -force_load \"$(PODS_ROOT)/MediaPipeTasksCommon/frameworks/graph_libraries/libMediaPipeTasksCommon_device_graph.a\""
```

`-force_load` links **every object file** in the archive regardless of reachability, defeating object-level dead-stripping. Parsing all 6,394 Mach-O objects in the arm64 archive and summing segments: `__TEXT` **70.40 MB**, `__DATA` 4.14 MB, `__LD` 9.86 MB. (`__DWARF` 198 MB is debug info and does not ship.)

**INFERRED, high confidence:** ~74 MB uncompressed arm64 linkable surface before function-level dead-stripping and App Store thinning. The archive is shared across all MediaPipe task pods, so you pay for calculators you never use, and MediaPipe registers calculators through static-initializer registries, which anchors much of it against stripping.

**Not measured:** the final `.ipa` delta could not be linked on Linux. Do not treat any single MB figure as verified. Measure in an Xcode archive before committing.

Pod download cost is also non-trivial: `MediaPipeTasksCommon-1.0.0.tar.gz` is **352 MB**, unpacking to **1.3 GB** of CocoaPods checkout.

Model bundles, exact bytes (VERIFIED via `curl -sIL` and the GCS JSON API, both agreeing):

| Bundle | Bytes | MiB |
|---|---|---|
| `pose_landmarker_lite.task` | 5,777,746 | 5.51 |
| `pose_landmarker_full.task` | 9,398,198 | 8.96 |
| `pose_landmarker_heavy.task` | 30,664,242 | 29.24 |

The `.task` is a ZIP. The detector inside is the same ~2.96 MB model in all three; only the landmark model grows. Stored uncompressed, so no further app-thinning gain.

**VERIFIED: the weights are frozen at April 2023.** Only one version exists (`/1/` and `/latest/` are byte-identical), `last-modified` 2023-04-27. No upstream improvements are coming.

---

## 4. Acceleration and latency

**VERIFIED - exactly two delegates on iOS, CPU and GPU. No CoreML delegate exists.** From the shipped `MPPBaseOptions.h`, `MPPDelegate` has only `MPPDelegateCPU` and `MPPDelegateGPU`. `strings` over the shipped arm64 archive: `InferenceCalculatorMetal` x159, `TFLGpuDelegate` x23, `MetalDelegate` x15. Precise search for `CoreMlDelegate` / `coreml_delegate`: **zero hits**.

GPU on iOS resolves to the TFLite **Metal** delegate. Caveat quoted from `acceleration.proto`: "For GPU delegate, Mediapipe Tasks tries to run the whole pipeline on GPU, and falls back to CPU if calculators are not GPU supported" - best-effort per calculator, not all-or-nothing.

**VERIFIED - the `delegate` option is undocumented on iOS.** Google's config-options table lists `running_mode`, `num_poses`, the three confidence thresholds, `output_segmentation_masks` and `result_callback`. No `delegate` row. The API exists and works; the docs never mention it.

**VERIFIED - Google publishes no latency for pose landmarker.** The only official numbers are Pixel 3 FPS in the model card, and they are **landmark-model-only, tracking mode, detector excluded** - confirmed three ways in the same PDF (the input is a pre-cropped 256x256x3 region; the only evaluation mode listed is TRACKING MODE; the quoted model sizes match the landmark `.tflite` alone).

This independently corroborates `pose-engines.md`'s conclusion that every published FPS figure understates true cost. There is no BlazePose Detector model card at all - the entire `mediapipe-assets` bucket was listed to confirm this.

Pixel 3 is a 2018 Snapdragon 845 and a poor proxy for any iPhone; treat those CPU numbers as a pessimistic floor.

---

## 5. Licensing - clean, and free provisioning is unaffected

**VERIFIED - Apache 2.0 for both code and weights.** The repo `LICENSE` is Apache 2.0, both podspecs declare it, and the BlazePose GHUM 3D model card carries a field labelled exactly "**LICENSED UNDER** Apache License, Version 2.0" on page 2. The `.task` files are served from plain `storage.googleapis.com` with no click-through, no EULA, no auth, and no `LICENSE` object anywhere under the `pose_landmarker/` prefix. The Generative AI Prohibited Use Policy does not attach - that rides on the Gemini API terms, and BlazePose GHUM is a discriminative vision model.

So the weights can ship in a closed-source commercial app. Obligations are Apache 2.0 §4 only: retain notices, include the licence, preserve `NOTICE`. **The pod's `NOTICE` is 1.56 MB of third-party licences** - budget for an acknowledgements screen rather than discovering this at submission.

Note the model card's stated OUT-OF-SCOPE APPLICATIONS include "People too far away from the camera (e.g. further than 14 feet/4 meters)". Non-binding, but relevant given the frame-fit gate's ~2.5m working distance.

**VERIFIED-by-absence - free provisioning works.** The podspec declares **zero entitlements** and links only `AudioToolbox, Accelerate, CoreMedia, AssetsLibrary, CoreFoundation, CoreGraphics, CoreImage, QuartzCore, AVFoundation, CoreVideo`. Metal is not among them; the Metal delegate links Metal symbols through TFLite without a declared capability, and Metal has never required an entitlement. Nothing touches the capabilities free provisioning withholds. Only an `NSCameraUsageDescription` plist string is needed.

---

## 6. Deployment target and tooling

**VERIFIED - the podspec is authoritative and the docs are stale.**

| Pod version | `platforms.ios` |
|---|---|
| 0.10.3 | 11.0 |
| 0.10.14 - 0.10.21 | 12.0 |
| 0.10.35 - **1.0.0 (current)** | **15.0** |

Google's setup page still says "iOS device with at least iOS 12.0", which is wrong for current versions.

**VERIFIED - CocoaPods only, no Swift Package Manager support**, per the same setup page. A maintainability consideration in its own right.

---

## Bottom line for the map

MediaPipe was already effectively ruled out on Flutter binding reality. This note adds a harder reason: **its telemetry conflicts with map decision 20**, and that conflict is not fixable through configuration.

The segmentation-mask finding is the part worth keeping. It is free at inference time, which materially improves the odds on [#17](https://github.com/grez-lucas/poseperfect/issues/17) - but only if an engine that exposes it is chosen, and MediaPipe now looks unlikely to be that engine. Whether ML Kit or Apple Vision expose an equivalent silhouette signal is an open question that #17 must answer.
