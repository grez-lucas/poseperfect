# On-device pose estimation engines for Flutter, 2026

Research note resolving [issue #3](https://github.com/grez-lucas/poseperfect/issues/3).

**Status: evidence, not a verdict.** This note deliberately does **not** pick an engine. That decision belongs to a later prototype ticket that runs real captures of a real subject in the eight mandatories. What follows is the material that prototype should be designed against, plus the specific measurements it has to make because nobody else has made them.

**Research date:** 2026-08-07. Every version number, release date, issue count and file size below was read on that date and will rot.

**Evidence grading used throughout:**

- **VERIFIED** - stated in a primary source: official vendor documentation, model card, published paper, package-registry metadata, or source code. Quoted or closely paraphrased, with a URL.
- **INFERRED** - reasoning from verified facts. Explicitly not measured by anyone.
- **ANECDOTAL** - developer reports, issue trackers, forum posts. Signal, not measurement.

Vendor marketing that compares a product to its competitors is labelled as marketing wherever it appears and is never cited as fact. QuickPose.ai in particular is a vendor selling a MediaPipe wrapper; its comparisons to MediaPipe are sales copy. See section 9.3.

---

## 0. Why the usual benchmarks mislead for this app

Three properties of PosePerfect change which numbers matter, and most published pose-estimation benchmarks assume the opposite of all three.

1. **We score still images captured on demand, not video** (map decision 7). Per-frame throughput, the FPS number every vendor leads with, is close to irrelevant. What matters is single-image latency, and almost nobody publishes it. Worse, the headline FPS figures are *tracking-mode* numbers measured with the person-detection stage skipped, so they systematically **understate** our cost. See section 8.

2. **Scoring is self-referential** (map decision 6): a capture is compared against the same athlete's own earlier reference under matched framing. This is more forgiving than it sounds. A model with a *consistent systematic bias* remains usable, because the bias largely cancels between reference and capture. What is **not** forgiving is **bimodal or non-deterministic** error: a model that sometimes mirrors left and right, or sometimes latches onto a different body configuration, destroys the comparison rather than shifting it. This reframes the whole evaluation. We are not shopping for accuracy. We are shopping for **repeatability**, and specifically for the absence of catastrophic mode-switching.

3. **Five of the eight mandatories are not front-on.** Three rear-facing, two side-on, plus the rear quarter turn. The subject is heavily muscled, oiled, minimally clothed, and in several poses the arms occlude the torso. This is the acceptance-critical case, and it is the one the industry has not measured.

Point 2 is why this note is less depth-obsessed than it might have been. Point 3 is why it is far more viewpoint-obsessed.

---

## 1. Headline findings

1. **Nobody has measured back-view accuracy for any of these engines.** Not Google, not Apple, not the academic literature. Every vendor model card evaluates fairness along geography, skin tone and gender, and stops there. Viewpoint is not an evaluated factor in any of them. This is the single most important output of this ticket, and it is a negative result. Section 7.

2. **The gap is not neutral.** ML Kit's own documentation states a precondition a rear pose violates: *"The user's face must be present in order to detect a pose."* BlazePose, which powers both ML Kit and MediaPipe, uses a **face detector as its person detector**, on the explicit stated assumption that the head is always visible. Both model cards list *"Head is not visible"* as an out-of-scope application. Three of our eight mandatories are documented out-of-scope inputs.

3. **A Google engineer has confirmed the rear-view failure on the tracker, and it is silent.** MediaPipe issue #5197: a subject filmed from behind returns visibility and presence of ~0.9999 on the nose and eyes, on lite, full *and* heavy. Google labelled it a model bug in July 2024 and it is still open. These engines fail **confidently**, so no confidence threshold catches it.

4. **The side poses are the lower risk, not the higher one.** The biomechanics validation literature consistently finds the sagittal (side-on) plane is the *best*-measured plane. The risk on side chest and side triceps is the far-side limbs, which carry roughly double the error of camera-side limbs, not the viewpoint itself. This inverts the intuition in the ticket.

5. **Neither depth axis is metric.** MediaPipe's world landmarks are documented as *"in meters"* in the API guides but the model card says *"Z is not metric but up to scale"* and lists *"Applications requiring metric accurate depth"* as out of scope. ML Kit's z is *"an experimental value... not a true 3D value."* Apple's 3D request is genuinely metric only when LiDAR depth is present; otherwise it scales by an assumed reference height. Section 6.

6. **The Flutter binding situation is the practical discriminator.** Exactly one option has a real, maintained, widely-used Flutter binding: `google_mlkit_pose_detection`. MediaPipe's Flutter story is two hobby packages with 8 likes between them and a Google stub issue open since May 2024. Everything else is a hand-written platform channel.

---

## 2. Comparison table

| | **ML Kit Pose Detection** | **MediaPipe PoseLandmarker** | **Apple Vision (2D)** | **Apple Vision 3D** | **MoveNet via LiteRT/TFLite** | **ONNX route** |
|---|---|---|---|---|---|---|
| **Q1 Flutter binding** | `google_mlkit_pose_detection` **0.15.0, 2026-07-07**. Community (`flutter-ml.dev`), MIT. 79 likes, 150/160 pts, ~19k downloads/30d. Repo 1,270 stars, 4 open issues (stale-bot deflated) | **None credible.** Google's `flutter-mediapipe` PoseLandmarker issue #51 open, unassigned, since 2024-05-20; repo's last act was turning CI off. `mediapipe_vision` on pub.dev **404s**. Community: `flutter_mediapipe_vision` (2 likes) and `flutter_mp_pose_landmarker` (6 likes, **licence Unknown**) | **None first-party.** `apple_vision_pose` 0.1.0, 2026-07-25, **1 like**, 358 dl/30d, MIT. Repo 20 stars | `apple_vision_pose_3d` 0.1.0, 2026-07-25, **2 likes**, 174 dl/30d | `tflite_flutter` 0.12.1, **2025-10-28**. tensorflow.org publisher but README says "work-in-progress" since Apr 2023; **108 open issues**. iOS podspec still pins **TFLite 2.12.0 (2023)** | `flutter_onnxruntime` 1.8.3, 2026-07-19, 48 likes. Older `onnxruntime` pkg abandoned since 2024-03 |
| **Q2 Landmarks** | **33**, BlazePose topology. All of shoulders/elbows/wrists/hips/knees/ankles bilateral. 3 hand pts/side, 2 foot pts/side, 11 face | **33**, identical topology | **19** joints: 6 head (incl. **neck**), 6 arm, **root** (waist), 6 leg. No hands, no feet detail | 17 joints, hip-rooted skeleton | **17** COCO keypoints. No neck, no hands, no feet | 17 (COCO), 26 (Halpe) or 133 (WholeBody) depending on model |
| **Q3 Depth** | `z` in "image pixels", hip-plane origin. Model card: **"Z is not metric but up to scale"**, and **excluded from every published accuracy number** | `worldLandmarks` "in meters", hip origin. Model card contradicts: **"not metric but up to scale"**. Paper: **121 mm MPJPE** un-aligned | **None.** 2D normalized points + confidence only | **Metric only with LiDAR.** `.measured` uses LiDAR; `.reference` assumes a height. Hip-root, `simd_float4x4` | **None.** Output is `[1,1,17,3]` = **(y, x, score)** | None for any 2D model |
| **Q4 Back/side** | **"The user's face must be present in order to detect a pose."** *"Head is not visible"* = out-of-scope. **No viewpoint measurement anywhere** | Face detector as person proxy. *"Head is not visible"* out-of-scope. **Confirmed bug #5197**: 0.9999 visibility on the nose of a rear-facing subject, all 3 models. **No viewpoint measurement anywhere** | **Apple publishes nothing.** No model card, no benchmark, no limitation statement on orientation | Same | Card says model predicts joints *"even when they are occluded"* and emits low confidence **only** for out-of-frame. **No viewpoint measurement** | Model-dependent; none measure viewpoint |
| **Q5 iOS** | **+29.6 MB** base / **+33.2 MB** accurate (official). iOS 15.5+, Xcode 16+. Static framework, CocoaPods only, **no SPM**. No CoreML/Metal documented on iOS. arm64-sim fixed only in 0.15.0 | Pod `MediaPipeTasksVision` 1.0.0 (2026-07-28), iOS **15.0+**. `MediaPipeTasksCommon` tarball is **351 MB** in CI. GPU = Metal only, **no CoreML delegate**. `use_frameworks!` + `static_framework` + `-force_load` is fragile | **+0 MB.** System framework. iOS **14.0+**. ANE-backed, no entitlement | iOS **17.0+**. `.measured` needs LiDAR hardware | **~55 MB** unstripped arm64 across 3 frameworks. **README: "TFLite may not work in the iOS simulator"** | ORT `onnxruntime-c` 1.28.0, iOS 15.1+, **~44.9 MB** unstripped arm64. CoreML + XNNPACK EPs |
| **Q6 Licence** | Plugin MIT; SDK under **ML Kit ToS**. Closed-source OK. **Must disclose ML Kit metrics collection** | Apache 2.0 code **and** Apache 2.0 weights (model card, "LICENSED UNDER"). Cleanest of the lot | System framework, no separate licence. **iOS-only, Android gets nothing** | Same | MoveNet **Apache 2.0** (all 13 Kaggle variants) | **YOLO-pose = AGPL-3.0 or paid Enterprise: hard blocker.** RTMPose Apache code but **murky weight provenance**. Sapiens **CC-BY-NC** |
| **Q7 Still-image latency** | **Not published.** Only ~45 FPS (base) / ~29 FPS (accurate) on iPhone X, and those are **STREAM_MODE** | **Not published for this task.** Paper Table 2, Pixel 4 CPU: lite 25 ms, full 40 ms, heavy 147 ms - **tracker only, detector excluded** | **Not published.** Apple publishes no latency figures | Not published | No official mobile numbers. Card's figures are desktop TF.js/WebGL | Not published |
| **Verdict shape** | Only mature Flutter binding, but **frozen in beta since 2022** and face-dependent | Best evidence quality, best licence, **worst Flutter story** | Zero size, zero licence risk, **zero Android**, thinnest evidence | Adds metric depth only on LiDAR devices | Licence-clean fallback, **most hand-written code**, unrunnable on CI | Licence minefield; no unique upside |

---

## 3. Google ML Kit Pose Detection (`google_mlkit_pose_detection`)

### Q1 Binding maturity - the only genuinely mature option, and it is one person

**VERIFIED.** Community, not first-party. Publisher is the verified `flutter-ml.dev`; copyright is *"Copyright (c) 2021 Bharat Biradar and Francisco Bernal"*. Google publishes no official ML Kit Flutter plugin. <https://pub.dev/packages/google_mlkit_pose_detection>

- **v0.15.0, published 2026-07-07T20:28:20Z.** Prior: 0.14.1 (2026-02-03), 0.14.0 (2025-03-20). Cadence roughly twice a year, mostly dependency bumps.
- 79 likes, 150/160 pub points, **18,966 downloads / 30 days**. Tagged `is:darwin-legacy-native-build`, i.e. CocoaPods only, no SPM.
- Repo `flutter-ml/google_ml_kit_flutter`: 1,270 stars, **4 open issues**, MIT, last push 2026-08-03.

**INFERRED: the 4-issue count is misleading.** The repo runs `actions/stale`, which auto-closes issues. Real signal is that #861 ("Apple Silicon arm64 Simulator Build Failure (iOS 26+)", opened 2026-05-04) and #890 (SPM migration) are both still open. Recent commits are overwhelmingly dependabot; the last substantive maintainer commit is 2026-07-07. **Bus factor 1.**

**VERIFIED - 0.15.0 changelog** (extracted from the published pub archive):

```
* Migrate Android implementation from Java to Kotlin.
* Migrate iOS implementation from Objective-C to Swift.
* Bump Android compileSdk to 36 for AGP 9 compatibility.
* Enable support for Apple Silicon simulator on iOS 26+.
```

That last line matters for ios-builder: on 0.14.1 and below, Google's MLKit binary pods lacked arm64 simulator slices and both `flutter build ipa` and Apple Silicon simulator runs failed. **Do not pin below 0.15.0.**

### Q2 Landmarks - 33, BlazePose topology

**VERIFIED**, exact `PoseLandmarkType` enum order from the published 0.15.0 `lib/src/pose_detector.dart`:

`nose, leftEyeInner, leftEye, leftEyeOuter, rightEyeInner, rightEye, rightEyeOuter, leftEar, rightEar, leftMouth, rightMouth, leftShoulder, rightShoulder, leftElbow, rightElbow, leftWrist, rightWrist, leftPinky, rightPinky, leftIndex, rightIndex, leftThumb, rightThumb, leftHip, rightHip, leftKnee, rightKnee, leftAnkle, rightAnkle, leftHeel, rightHeel, leftFootIndex, rightFootIndex`

All eight primary joint pairs present. Hands are 3 knuckle points per side, feet 2 points per side. `PoseLandmark` exposes `type, x, y, z, likelihood`.

**Structural gap for physique scoring, and it applies equally to MediaPipe:** there is **no neck, no spine, no sternum, no pelvis-centre and no torso-twist landmark**. The BlazePose paper is explicit that the topology exists to bootstrap the tracker, not to describe a body: *"we use only a minimally sufficient number of keypoints on the face, hands, and feet to estimate rotation, size, and position of the region of interest for the subsequent model"* (<https://arxiv.org/abs/2006.10204> §2.3). Lat spread width, V-taper and back thickness are **not observable** from these 33 points. You would synthesise a mid-shoulder/mid-hip axis yourself and still have no torso depth. Apple Vision, notably, is the only engine here that gives you an actual `neck` and `root` joint.

### Q3 Depth - see section 6

### Q4 Back and side - see section 7

### Q5 iOS

| Item | Value | Source |
|---|---|---|
| App size, base | **Up to 29.6 MB** | <https://developers.google.com/ml-kit/vision/pose-detection/ios> |
| App size, accurate | **Up to 33.2 MB** | same |
| Linkage | *"Assets for base detector are statically linked to your app at build time."* | same |
| Min iOS | 15.5 (plugin podspec and ML Kit release notes) | 0.15.0 podspec |
| Min Xcode | 16.0 (ML Kit release notes, 2025-03-25) | release notes |
| CoreML / Metal | **Not mentioned anywhere in the iOS guide.** Android docs do document GPU for the accurate model; iOS does not | iOS guide |

**VERIFIED - free-team signing is not a problem here.** ML Kit's ToS states *"processing of the input data... fully happens on-device"*. No capability, no App Group, no push or iCloud entitlement. Nothing a Personal Team cannot issue. The free-team constraints that bite (7-day profile expiry, 10 App IDs, no Certificates/IDs/Profiles portal access) are orthogonal to the engine choice and apply identically to every option in this note.

The real iOS cost is the **~29.6 MB** static addition and the CocoaPods-only constraint.

### Q6 Licence

Plugin is **MIT**. SDK and models are governed by the **ML Kit Terms of Service** (<https://developers.google.com/ml-kit/terms>), which incorporate the Google APIs ToS. **VERIFIED**, the two binding clauses:

> "you may not reverse engineer or attempt to extract the source code or any related software"

> "The ML Kit APIs also send metrics about the performance and utilization of the APIs in your app to Google. ... You are responsible for informing users of your app about Google's processing of ML Kit metrics data as required by applicable law."

**INFERRED: shipping closed-source is fine** - no fee, no copyleft, no field-of-use restriction. But note the second clause interacts badly with **map decision 20 ("Offline absolute: no network permission in v1, therefore no analytics and no privacy policy")**. ML Kit reserves the right to phone home with usage metrics and makes disclosing that *your* responsibility. That is a direct tension with the stated v1 posture and should be resolved deliberately, not discovered at App Store review.

### Q7 Latency, and the mode that matters

**VERIFIED**, the only official iPhone figure: *"iPhone X: ~45FPS [base] / ~29FPS [accurate]"*.

**VERIFIED**, the two modes, identical wording on both platforms:

> **STREAM_MODE (default):** "The pose detector will first detect the most prominent person in the image and then run pose detection. In subsequent frames, the person-detection step will not be conducted unless the person becomes obscured or is no longer detected with high confidence."
>
> **SINGLE_IMAGE_MODE:** "The pose detector will detect a person and then run pose detection. **The person-detection step will run for every image, so latency will be higher, and there is no person-tracking.**"

**INFERRED, and this is the load-bearing point for us:** ~45 FPS is the amortised steady-state cost with the detector stage skipped. We score independent stills, so we are in SINGLE_IMAGE_MODE and pay person-detection on every call. **Google publishes no single-image latency figure for either platform.** Any FPS number quoted at us is the wrong number.

### The finding that should weight most heavily: ML Kit Pose is frozen

**VERIFIED.** No formal deprecation notice exists, but:

1. Every pose page carries: *"This API is offered in beta, and is not subject to any SLA or deprecation policy. Changes may be made to this API that break backward compatibility."* Read precisely: **Google owes no notice period if it removes this API.**
2. The last ML Kit release note mentioning Pose Detection is **2022-09-20**. Roughly four years of silence while the same page shows active 2025-2026 work on GenAI and Speech.
3. Android artifacts sit at `18.0.0-beta5`; the model card is dated **June 22, 2021**. The pose model has not shipped a functional change since September 2022.
4. Google's active investment is MediaPipe / AI Edge. No ML Kit-to-MediaPipe migration guide exists for pose.

**INFERRED: maintenance-only status.** Same BlazePose GHUM weights as MediaPipe, wrapped in a beta API frozen in 2022, with an explicit no-SLA disclaimer. Given map decision 1 (architected so becoming a product does not require a rewrite), this is a real strategic consideration, not just a footnote. It also makes the "gold rep invalidation" fog item on the map more pressing: a frozen model is at least stable, which cuts the other way.

---

## 4. MediaPipe PoseLandmarker

### Q1 Binding maturity - the disqualifying weakness

**VERIFIED. Google's own `google/flutter-mediapipe` never shipped a vision package and is functionally abandoned.**

- Repo: <https://github.com/google/flutter-mediapipe>, 296 stars, 31 open issues, not archived.
- Last substantive commit **2024-06-06**. The only later commit is **2025-06-04, "turns off CI jobs"**. The last act of maintenance was disabling CI.
- Issue #51 *"[mediapipe_task_vision] Add PoseLandmarker task"*, opened **2024-05-20**, still open, no assignee, no PR. It is one of **13 identical vision-task stubs all filed that day, none ever implemented**.
- `mediapipe_core`, `mediapipe_text`, `mediapipe_genai` each published **exactly one version** in May 2024. **`mediapipe_vision` returns 404 on pub.dev. It does not exist.**

Community alternatives:

| Package | Version | Last release | Likes | Notes |
|---|---|---|---|---|
| `flutter_mediapipe_vision` | 0.3.2 | 2026-08-01 | 2 | 164 downloads. iOS impl package has **exactly 1 version ever** |
| `flutter_mp_pose_landmarker` | 0.1.8 | 2026-04-27 | 6 | 112 downloads, **unverified uploader, licence Unknown** |
| `flutter_mediapipe` | 0.0.7 | 2021-06-14 | - | Dead 5 years |

**8 likes and 276 lifetime downloads between the two live ones.** Neither is a defensible dependency.

**The hand-written platform channel is the only credible route.** Wrap `pod 'MediaPipeTasksVision'` on iOS and `com.google.mediapipe:tasks-vision` on Android. Concretely: two native implementations of task construction, image conversion, invocation and serialisation of 33 x (x, y, z, visibility, presence) x 2 coordinate spaces across the channel. Roughly 400-700 lines of Swift plus Kotlin plus a Dart codec, owned forever. Both native SDKs are genuinely first-party and actively released (iOS pod **1.0.0, 2026-07-28**), which is the one thing in MediaPipe's favour here.

### Q2 Landmarks

Identical 33-point BlazePose topology to ML Kit, same structural gaps. Not repeated.

### Q5 iOS - three specific hazards

**VERIFIED**, from the CocoaPods trunk API and podspec JSON:

- `MediaPipeTasksVision` **1.0.0, 2026-07-28**. `platforms: {"ios": "15.0"}`. The setup docs still claim iOS 12.0; **the docs are stale, trust the podspec.** `static_framework: true`, Apache licensed, vendored prebuilt xcframework.
- Depends on `MediaPipeTasksCommon`, whose source tarball is **351 MB** (measured by HTTP HEAD). That lands in every uncached `pod install` on a GitHub Actions runner. Cache `Pods/` aggressively.
- It requires `-force_load` of a large static archive. Combined with `use_frameworks!` (which the official Podfile snippet requires but Flutter's generated Podfile does not include) and `static_framework: true`, this is a known-fragile CocoaPods configuration with a live bug: <https://github.com/google-ai-edge/mediapipe/issues/6258>. **INFERRED: this is the most likely place the iOS build breaks, and it will break in CI rather than locally.**

**Model bundle sizes**, measured directly by HTTP HEAD on `storage.googleapis.com/mediapipe-models/...`:

| Bundle | .task total | detector | landmarker |
|---|---|---|---|
| lite | **5.51 MB** | 2.82 MB | 2.69 MB |
| full | **8.96 MB** | 2.82 MB | 6.14 MB |
| heavy | **29.24 MB** | 2.82 MB | 26.42 MB |

The detector is byte-identical across tiers. The model card's headline "Lite 3MB / Full 6MB / Heavy 26MB" refers to the landmark model only.

**Delegates. VERIFIED** from `MPPBaseOptions.h`: the enum is exactly `{MPPDelegateCPU, MPPDelegateGPU}`. **There is no CoreML delegate on iOS - no API surface exists to request one.** GPU means TFLite's Metal delegate, is undocumented on the pose landmarker iOS page, and has an open bug trail (#5609, #4757, #6223, #6041, #6216). **Plan for CPU.**

### Q6 Licence - the cleanest of any option

**VERIFIED.** Code is Apache 2.0. Separately, the BlazePose GHUM 3D model card carries its own **"LICENSED UNDER: Apache License, Version 2.0"** heading for the weights. The `.task` bundles are served as unauthenticated GETs with no click-through EULA; unzipping `pose_landmarker_lite.task` and grepping for licence text finds none embedded. Both podspecs declare Apache.

Caveats to log, none blocking: the solutions docs still carry an *"early release"* preview banner three years on, with no API stability commitment; Apache 2.0 §4 requires shipping the licence text and a NOTICE (a third-party-licences screen).

### Q7 Latency

**VERIFIED: there is no official latency table for pose landmarker.** The rendered page has no "Task benchmarks" section, no device names, no milliseconds. This is unusual - the hand landmarker page *does* have one (*"HandLandmarker (full) 17.12ms / 12.27ms"* on Pixel 6). Pose was simply never given one.

The real published numbers are from the paper (<https://arxiv.org/abs/2206.11678> Table 2), in ms:

| Device | Lite | Full | Heavy |
|---|---|---|---|
| Pixel 4 CPU (single core, XNNPACK) | 25 | 40 | **147** |
| Pixel 4 GPU | 8 | 9 | 22 |
| Desktop (i9-10900K + GTX 1070) | 7 | 8 | 10 |

**No iOS device appears in any official MediaPipe pose benchmark.** And these are **tracker-only** numbers on an already-cropped ROI. They exclude the detector, so they understate our cost.

**VERIFIED at source level - IMAGE mode disables tracking.** From `pose_landmarker_graph.cc`:

> "While **not in stream mode**, the input images are not guaranteed to be in series, and we **don't want to enable the tracking** and rect associations between input images. **Always use the pose detector graph.**"

For still-image scoring, every call pays detector plus landmarker. That is the right mode for independent judging photos (no drift, no stale-ROI lock-in) but it is strictly slower, and critically **it removes the tracking fallback that normally masks the face-proxy detector's failures on rear-facing subjects.** See section 7.

---

## 5. Apple Vision

### Q1 Binding maturity

**VERIFIED.** No first-party Flutter binding. The only real option is the `Knightro63/apple_vision` package family (repo: 20 stars, 0 open issues, MIT, last push 2026-07-25):

| Package | Version | Published | Likes | Downloads/30d | Points |
|---|---|---|---|---|---|
| `apple_vision_pose` | 0.1.0 | 2026-07-25 | **1** | 358 | 160/160 |
| `apple_vision_pose_3d` | 0.1.0 | 2026-07-25 | **2** | 174 | 160/160 |

Platforms `ios, macos` only. `flutter_apple_vision` (gokhanvaris) published one version in 2023 and is dead.

**INFERRED:** 160/160 pub points measures packaging hygiene, not adoption or correctness. One and two likes is pre-adoption. But the hand-written platform channel here is unusually cheap compared to MediaPipe's: a Swift method channel calling `VNImageRequestHandler` on a `CVPixelBuffer` and returning 19 joints. The gotchas are well-known and bounded: image orientation, pixel buffer conversion, and the fact that **Vision uses a normalized bottom-left origin**, so y must be flipped for Flutter's top-left convention.

### Q2 Landmarks - 19, and the topology is different in a way that matters

**VERIFIED** from `VNHumanBodyPoseObservation.JointName` (iOS 14.0+, <https://developer.apple.com/documentation/vision/vnhumanbodyposeobservation/jointname>), 19 joints in six groups:

- Head (6): `nose, leftEye, rightEye, leftEar, rightEar, neck`
- Left arm (3) and right arm (3): `shoulder, elbow, wrist`
- Torso (1): `root` (waist)
- Left leg (3) and right leg (3): `hip, knee, ankle`

All eight primary joint pairs present. **Missing versus the 33-point models:** all hand detail (no pinky/index/thumb), all foot detail (no heel, no foot index), and the inner/outer eye and mouth points.

**INFERRED, and this cuts both ways for us.** The missing hand and foot points are close to irrelevant for mandatory-pose scoring - we care about limb angles, not knuckles. Meanwhile Apple is the **only** engine here that gives an explicit `neck` and `root` joint, which are exactly the two synthetic landmarks we would otherwise have to derive from shoulder and hip midpoints. For a torso-axis-based scoring metric, 19 well-chosen joints may be worth more than 33 loosely-chosen ones.

### Q3 Depth

**2D request emits no z.** Normalized points plus confidence only.

**`VNDetectHumanBodyPose3DRequest` is separate. VERIFIED**, availability **iOS 17.0+ / macOS 14.0+ / visionOS 1.0+**. Abstract: *"A request that detects points on human bodies in 3D space, relative to the camera."* Overview: *"If the system allows it, the request uses `AVDepthData` information to improve the accuracy."*

Read that carefully: depth **improves** accuracy, it is not **required**. It works on a plain image. But the metric claim then rests on `heightEstimation`, and **VERIFIED** the two cases are:

- `.measured` - *"A technique that uses LiDAR depth data to measure body height, in meters."*
- `.reference` - *"A technique that uses a reference height."*

**INFERRED, and this is the crux for arbitrary stored photos:** without LiDAR depth metadata, Apple falls back to an **assumed** reference height. The skeleton is then metric-shaped but scaled by a guess, which is the same "up to scale" property MediaPipe has, just arrived at more honestly. Our captures come from a stored still through ios-builder, so **assume `.reference` unless we verify LiDAR depth survives our capture path.** `bodyHeight` is documented as *"The estimated human body height, in meters"*, `cameraOriginMatrix` as *"A transform from the skeleton hip to the camera"* (confirming a **hip root**), and `pointInImage(_:)` gives you the 2D projection back.

### Q4 Back and side - Apple documents nothing

**VERIFIED as a documentation gap.** Apple publishes no model card, no benchmark numbers, no evaluation protocol, and no limitation statement about orientation, occlusion or subjects facing away. The only guidance on the confidence value is *"Ignore any recognized points with a confidence value of 0, because they're invalid"* (<https://developer.apple.com/documentation/vision/detecting-human-body-poses-in-images>). `VNRecognizedPoint` is documented only as *"a normalized point in an image, along with an identifier label and a confidence value"* - the **semantics of the value are undefined**.

**This is the thinnest evidence base of any engine here.** It is not evidence of a problem, and it is not evidence of safety. It is simply unknowable from documentation, which means for Apple Vision the prototype in section 10 is not a nice-to-have, it is the *only* source of information.

**INFERRED, one architectural note in Apple's favour:** unlike BlazePose, there is no public evidence that Vision uses a face detector as a person-detector proxy. Apple has never described the architecture. So the specific, documented, structural front-bias that disqualifies ML Kit on paper is not known to apply here. That is an argument for *testing* Apple Vision, not for trusting it.

### Q5 iOS

**+0 MB.** Vision is a system framework. iOS 14.0+ for 2D, iOS 17.0+ for 3D. No entitlement, so **no free-team signing conflict whatsoever** - this is the only option with literally zero packaging risk on ios-builder. Apple does not document whether Vision uses the Neural Engine, but it is a system CoreML-backed framework.

### Q6 Licence

No separate model licence, no redistribution question, no ToS to disclose. Also **no Android**. Under map decision 15 (iOS first-class, Android best-effort) that is survivable, but it means either a second engine for Android or an Android build that cannot score at all. That is an architectural fork and, per the map's standing preference, a decision for Lucas rather than for this note.

### Q7 Latency

**VERIFIED: Apple publishes no latency figures.** None in the docs, none in WWDC20's "Detect Body and Hand Pose with Vision". The only claim is qualitative real-time capability. Anything quoted elsewhere is secondary.

---

## 6. Question 3 in full: the depth axis, precisely

The ticket asks for precision on MediaPipe's world landmarks versus ML Kit's non-metric z. Here it is, and the honest answer is that the distinction is **real but much narrower than the framing suggests**.

### ML Kit's z

**VERIFIED**, verbatim from <https://developers.google.com/ml-kit/vision/pose-detection>:

> "The Z Coordinate is an experimental value that is calculated for every landmark. It is measured in "image pixels" like the X and Y coordinates, but it is not a true 3D value. The Z axis is perpendicular to the camera and passes between a subject's hips. The origin of the Z axis is approximately the center point between the hips... Negative Z values are towards the camera; positive values are away from it. The Z coordinate does not have an upper or lower bound."

**VERIFIED**, from the Android API reference for `PoseLandmark`:

> "The unit of measure for the Z value is the same as X and Y." / "The Z value is an experimental feature that returns an extra Z coordinate along with X and Y. Please note that **this value is less accurate than the X and Y values**." / "The Z origin is approximately at the center of the subject's hips."

### MediaPipe's two outputs

**VERIFIED.** `landmarks` are normalized image coordinates; its z is defined (legacy `pose.md`) as *"the landmark depth with the depth at the midpoint of hips being the origin... The magnitude of `z` uses roughly the same scale as `x`"* - so **normalized-image-width units, not metres**.

`worldLandmarks` are documented in the current guides as *"Real-world 3-dimensional coordinates **in meters**, with the midpoint of the hips as the origin."* The paper describes it as *"3D body pose in **relative** coordinates of a metric space with origin in the subject's hips center"* - note "relative": a metric-*shaped* space with a free global scale and no camera translation.

### The contradiction, and it is the answer to the question

The API guides say "in meters". **The model card says otherwise, and the model card is the load-bearing document.** VERIFIED, verbatim from <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf>:

> **Out-of-scope applications:** "Applications requiring metric accurate depth"

> "Z coordinate scale is similar with X, Y scales but has different nature as obtained not via human annotation, by fitting synthetic data (GHUM model) to the 2D annotation. **Note, that Z is not metric but up to scale.**"

> "The model is providing 3D coordinates, but the z-coordinate... obtained from synthetic data using the GHUM model... fitted via an algorithm to the 2D key point projections."

ML Kit's model card carries **the identical sentence**, because it is the same model. And both add the sentence that settles it:

> "The model is providing 3D coordinates, but the screen z-coordinate, as well as world 3D coordinates obtained from synthetic data, so for a fair comparison with human annotations, **only 2D screen coordinates are employed**."

**Every published accuracy number for either engine is 2D-only. The depth axis has never been evaluated by its authors.**

### Quantified, as far as the sources allow

The depth ground truth is synthetic throughout: GHUM, a statistical body model, was fitted to existing 2D annotations to manufacture 3D labels. No depth sensor, no mocap. The paper concedes *"fitting can result in several realistic 3D body poses for the given 2D annotation (i.e. with the same X and Y but different Z)"*, and mitigated it with human **ordinal** depth annotations that reduced *"depth ordering errors during fitting from 25% to 3%"*. That is a claim about correct **ordering**, not correct **magnitude**.

**VERIFIED** numbers, <https://arxiv.org/abs/2206.11678>:

| Metric | Value |
|---|---|
| 3D mae vs GHUM fits, Heavy / Full / Lite | 36 / 39 / 45 mm |
| **MPJPE-PA** (Procrustes-aligned), 10k in-the-wild | **78 mm** |
| **MPJPE** (un-aligned), 10k in-the-wild | **121 mm** |

Read these carefully. The 36-45 mm figures are measured against **the same synthetic pipeline that generated the training labels**; they measure self-consistency with the fitting procedure, not agreement with a physically measured body. **The honest figure for absolute 3D joint placement is 121 mm - about 12 cm average per-joint error.**

### The verdict on the distinction

| | ML Kit `z` | MediaPipe `worldLandmarks` | Apple 3D `.reference` | Apple 3D `.measured` |
|---|---|---|---|---|
| Units | image pixels | metric-shaped, scale free | metres, assumed height | **metres, LiDAR-measured** |
| Origin | hip midpoint | hip midpoint | hip root | hip root |
| Cartesian, limb ratios computable? | No, it is x/y pixels plus a depth in the same units | **Yes** | Yes | Yes |
| Vendor-evaluated? | **No** | **No** | No | No |
| Documented error | none published | 121 mm MPJPE | none published | none published |

MediaPipe genuinely gives a **better-structured** output: a hip-origin Cartesian space where limb-length ratios and true 3D joint angles are computable, which ML Kit's z simply does not support. But "in meters" is contradicted by Google's own model card. **Treat world landmarks as shape-correct up to an unknown global scale, with roughly 12 cm absolute per-joint error, and never as a body measurement.**

**INFERRED, and this is the practical conclusion for us:** given map decision 6 (self-referential scoring) and the map's central correctness constraint, **we should not build any scoring metric that depends on the depth axis at all**, from any engine. Angle-based and ratio-based scoring on well-measured 2D is defensible. Absolute depth is not, and the map already ruled 3D pose estimation out of scope on exactly this reasoning. The depth question turns out to be much less decisive than the ticket assumed, and the viewpoint question much more.

---

## 7. Question 4 in full: back and side views. The central finding

### The verdict

**No primary source measures rear-view pose accuracy for MediaPipe/BlazePose, ML Kit, MoveNet, or Apple Vision. Not one.** No vendor model card evaluates viewpoint or body orientation as a factor. No academic paper found breaks BlazePose accuracy down by subject-facing direction. **That gap is itself the finding, and it means the prototype ticket is not optional.**

But the gap is not neutral. Four things fill it and they point the same way.

### 7.1 First-party documentation states a precondition that a rear pose violates

**VERIFIED**, ML Kit, verbatim:

> "**The user's face must be present in order to detect a pose.** Pose detection works best when the subject's entire body is visible in the frame, but it also detects a partial body pose. In that case the landmarks that are not recognized are assigned coordinates outside of the image."

**VERIFIED**, the architectural reason, BlazePose paper §2.2:

> "To make such a person detector fast and lightweight, we make the **strong, yet for AR applications valid, assumption that the head of the person should always be visible** for our single-person use case. As a consequence, **we use a fast on-device face detector as a proxy for a person detector**."

MediaPipe's docs restate it: *"The detector is inspired by our own lightweight BlazeFace model... as a proxy for a person detector."* The underlying BlazeFace is a frontal face detector.

**VERIFIED**, both model cards list under **out-of-scope applications**: *"Head is not visible"*. And under limitations: *"The model is optimized for real-time performance on a wide variety of mobile devices, but is **sensitive to face position, scale and orientation in the input image**."*

**INFERRED, high confidence:** a rear-facing subject presents no face and falls in Google's own declared out-of-scope set. **Three of our eight mandatories are documented out-of-scope inputs for both Google engines.** This is not a measured degradation curve; it is a stated non-support, which is arguably worse because there is no number to plan against.

### 7.2 The failure is confirmed by Google, and it is silent

**ANECDOTAL in origin, but vendor-confirmed.** MediaPipe issue #5197 (<https://github.com/google-ai-edge/mediapipe/issues/5197>), opened 2024-03-06, **still open**, labelled Bug / Pose Landmarker.

Reporter, verbatim:

> "The video is taken from behind of a single person which means that nose and eyes should not be visible at all... Since the person is facing away, landmarks like the nose and eyes should have low visibility scores. Actual Behavior: **All three Pose Landmark models I downloaded (lite, full, and heavy) consistently report high visibility and presence scores for the nose, eyes, and other front-facing joints.**"

Logged values across 51 frames: **0.999991 to 0.999994**, uniformly.

Google maintainer, 2024-07-30, verbatim:

> "Unfortunately, **it appears that this is a bug in our pose detection model. We need to fix this.** For now, we are marking it as a bug and sharing it with our team, but we cannot provide a timeline for the fix."

The reporter's outcome: *"shifted to another pose detection model for visibility."* **Unfixed for over two years.**

### 7.3 The one adjacent quantity anyone has measured

**VERIFIED.** Martiš P, Košutzká Z, Kranzl A. *"A Step Forward Understanding Directional Limitations in Markerless Smartphone-Based Gait Analysis."* Sensors 2024;24(10):3091. DOI 10.3390/s24103091. OpenCap (OpenPose backend), two iPhones, n=10, against Vicon. Mean RMSE, walking **toward** camera (WTC) versus walking **away** (WAC):

| Angle | Toward | Away |
|---|---|---|
| Pelvic obliquity | 2.8° | **5.3°** |
| Hip abduction | 3.5° | **6.1°** |
| Ankle flexion | 4.7° | **11.9°** |
| Knee flexion | 5.6° | 5.8° |
| Hip flexion | 8.9° | 8.0° |

Grand means (Front Digit Health 2026 scoping review, DOI 10.3389/fdgth.2026.1882536): **4.7° / ICC 0.75 toward, 6.7° / ICC 0.64 away.** The review's stated cause: *"OpenPose-based pose estimation algorithm has inherently lower recognition accuracy for anatomical keypoints on the posterior aspect."*

Read the pattern precisely: **sagittal-plane angles barely change. The out-of-plane angles blow up when the subject turns away** - 1.4x to 2.5x error inflation. This is a different engine (OpenPose) so it does not transfer directly, but it is the closest measured proxy that exists.

Corroborating, **VERIFIED**: Yang J, Park K, *Bioengineering* 2024;11(2):141, a MediaPipe BlazePose gait study, states verbatim: *"Preliminary experiments with smartphone cameras in front of and behind the subject showed that it was difficult to obtain reliable datasets for gait analysis."* **A BlazePose study explicitly abandoned rear camera placement as unusable.**

### 7.4 The training data is frontally skewed, and it is quantified

**VERIFIED**, BlazePose GHUM 3D model card: *"This model was trained and evaluated on images, including consented images (30K), of people **using a mobile AR application** captured with smartphone cameras... The majority of training images (85K) capture a wide range of fitness poses."*

The bias mechanism is concrete: the corpus is people **using an AR app on their own phone**, a population that by construction is looking at the screen, i.e. facing the camera. (Note the phrase *"captured on a diverse set of back-facing smartphone cameras"* elsewhere in the card means the phone's rear camera. It is **not** evidence of rear-view coverage.)

For MoveNet, whose training set is COCO, the skew has been measured directly. **VERIFIED**, Wu C, Chen Y, Luo J et al., *"MEBOW: Monocular Estimation of Body Orientation in the Wild"*, CVPR 2020 - 130K human instances across 55K COCO images, hand-annotated for body orientation:

> "our dataset covers all possible body orientation, with a **Gaussian like peak around 180° [front-facing]**, which is natural because photos with humans tend to capture the main person from the front."

> "It is not surprising that our model performs best when the camera point of view is towards the Front of the person because a larger portion of MEBOW dataset falls into this category."

And **VERIFIED**, MoViD (SenSys '26, DOI 10.1145/3774906.3802786) on HuMMan's 8 camera azimuths, across HMR2.0, ReFit, HSMR, WHAM and SPIN: per-view error spans **57.6 mm to 81.7 mm**, a 1.42x spread from camera azimuth alone. The paper states plainly: *"While the training data includes various viewing angles, **it is dominated by frontal views**."*

### 7.5 The side poses are the *lower* risk. This inverts the ticket's assumption

The biomechanics validation literature is consistent and one-directional: **sagittal-plane (side-on) measurement is the most accurate plane; frontal and transverse are worse.**

- **VERIFIED**, OpenCap scoping review (Front Digit Health 2026): *"OpenCap performed most accurately for sagittal-plane measurements"* - hip flexion/extension median RMSE **5.99°**.
- **VERIFIED**, *"Examination of 2D frontal and sagittal markerless motion capture"*, PLoS One 2023;18(11):e0293917: camera-side sagittal knee and hip were *"near or within marker-based error values"*, while **frontal-plane ankle** reached ±12.0° SD with limits of agreement −23.4° to 23.8°, which the authors declare *"should not currently be used in clinical or sporting applications"*.
- **VERIFIED**, Sci Rep 2025 (DOI 10.1038/s41598-025-22626-7, 18 models including BlazePose lite/full/heavy): *"vertical errors are much greater than the horizontal errors when viewing the participants in the frontal plane. When viewing the sagittal plane, the horizontal and vertical errors tended to be more similar."*

**The real risk on side chest and side triceps is the far-side limbs, not the view.** VERIFIED, PLoS One 2023, sagittal camera, bias ± SD:

| Joint | Camera-side | Occluded-side |
|---|---|---|
| Hip | 1.5° ± 4.6° | −4.6° ± **9.5°** |
| Knee | 1.5° ± 4.1° | 1.6° ± **6.9°** |

**Occluded-side variability roughly doubles.** And self-occlusion in raw 2D keypoints costs about the same: **VERIFIED**, arXiv 2504.10350v2 on BlendMimic3D, visible keypoints 6.11 ± 3.53 px versus **self-occluded 11.47 ± 4.72 px** for CPN, roughly 1.9-2.1x.

One number that should worry us across **all eight** poses, not just the side ones: the OpenCap review reports **upper-extremity RMSE of 13.81° to 52.17°** across planes, dramatically worse than lower limb. Every mandatory is scored substantially on arm position.

### 7.6 You cannot detect the failure at runtime

| Signal | Documented meaning | Usable as a rear-view alarm? |
|---|---|---|
| MediaPipe `visibility` | *"probability that a keypoint is located within the frame **and not occluded**"* | **No.** Issue #5197: 0.9999 on the nose of a rear-facing subject, on all three models. Google confirmed a bug |
| MediaPipe `presence` | *"probability that a keypoint is located within the frame. **It does not indicate whether the keypoint is occluded**"* | No, by definition |
| ML Kit `InFrameLikelihood` | *"the probability that the landmark is within the image frame"* | No. A frame-membership test, not a correctness test. The Flutter binding collapses visibility and presence into one `double likelihood` and does not say which |
| MoveNet confidence | Card: predicts joints *"even when they are occluded"*; low confidence emitted **only** for out-of-frame | No, by the vendor's own description |
| Apple Vision `confidence` | Undefined in docs. Only guidance: *"ignore points with confidence 0"* | Unknown. No published semantics or calibration |

Supporting general result, **VERIFIED**: *"On the Calibration of Human Pose Estimation"* (arXiv 2311.17105) finds systematic miscalibration across HPE confidence scores - a "scaling gap" for heatmap methods and a "form gap" for RLE methods. Taking a heatmap maximum as a confidence is known-broken in general.

**Conclusion: these engines fail confidently. No threshold on any shipped score reliably catches a rear-view collapse.** Any detector we build has to be geometric or learned on top - for example an explicit body-orientation classifier, which is exactly what a published soccer-analytics system had to bolt on (arXiv 2003.00943) after finding that flipped left/right detections *"introduce errors that might oscillate between 120° and 180°"*.

**This has a direct design consequence for us.** Map decision 14 already specifies a frame-fit gate that refuses or flags captures framed unlike the reference. That gate is currently conceived as a *framing* check. This research says it may also need to be an **orientation and plausibility** check, because the engine will not tell us when it is wrong. That is new information for the "First-run setup ritual" and gate-design fog items on the map.

### 7.7 The left/right swap risk, and why it is the top-priority experiment

**VERIFIED as a documentation gap:** no primary source states whether landmark 11 ("left shoulder") refers to the subject's anatomical left or to image-left when the subject faces away. None of the engines documents an anatomical-versus-image convention at all.

**ANECDOTAL corroboration:** OpenPose issue #865 reports *"openpose gets confused about which arm/leg is the left one and which one is the right"*, at up to 7 flips in ~10 frames, occurring specifically **as the subject turns away from and back toward the camera** - which is precisely the quarter-turn motion.

**INFERRED, high confidence:** labels are anatomical, the training distribution is front-dominated, and the detector's alignment signal (shoulder-hip incline plus face box) is **sign-degenerate between a front view and a back view of the same pose**. A model that has rarely seen a back view has no feature to flip on.

**Why this is the top-priority experiment:** per section 0's point 2, self-referential scoring tolerates systematic bias but is destroyed by bimodal error. A silent left/right swap is the purest possible instance of bimodal error. It would corrupt every per-side comparison on three of eight poses **without ever surfacing as an error**, and it would make the gold-rep reference itself untrustworthy. It is also cheap to test: one subject, two photographs.

### 7.8 One more domain-shift warning

**INFERRED but with a verified magnitude.** There is **zero** literature on pose estimation of bodybuilders, physique athletes or competition posing. This appears genuinely unstudied. The nearest evidence on athletic domain shift is AthletePose3D (CVPR-W 2025), where MotionAGFormer trained on Human3.6M scored **237.43 mm MPJPE** on athletic motion (ankle 535.56 mm), dropping to roughly 65 mm after fine-tuning. That is a domain-shift result, not a viewpoint one, but the magnitude is a warning: oiled skin, extreme muscular definition and posing trunks are a texture and silhouette domain far from COCO and YouTube fitness video. **Testing on a clothed volunteer will produce a falsely green result.**

---

## 8. Question 7 in full: inference cost

**The headline finding is that the number we need does not exist.** No vendor publishes single-still-image latency for any of these engines on iPhone-class hardware.

What is published, and why each figure is the wrong one:

| Engine | Published figure | Why it does not apply |
|---|---|---|
| ML Kit | ~45 FPS base, ~29 FPS accurate, iPhone X | STREAM_MODE, i.e. person detection skipped. SINGLE_IMAGE_MODE runs it every call and Google publishes no figure |
| MediaPipe | Pixel 4 CPU: lite 25 ms, full 40 ms, heavy 147 ms | Tracker-only on a pre-cropped ROI. Excludes the detector. **No iOS device in any official pose benchmark**, and the task page has no benchmark section at all |
| Apple Vision | none | Apple publishes no latency numbers |
| MoveNet | Lightning 10.5-39.0 ms, Thunder 15.0-64.0 ms | **Desktop browser TF.js/WebGL only.** No official mobile TFLite numbers exist in the model card |

**INFERRED: this barely matters, and that is the point.** Per map decision 7 and decision 20, we score a handful of stills in the background and the NFR is "feels instant", not "30 fps sustained". Even MediaPipe **heavy** at 147 ms on a Pixel 4 CPU, plus an un-benchmarked detector pass, plus generous headroom, lands comfortably inside a background scoring job that must be ready by review time.

**The practical conclusion is a recommendation to spend latency on accuracy.** Use the most accurate tier available (MediaPipe `heavy`, ML Kit `accurate`, MoveNet Thunder), because we need every point of accuracy on the five non-frontal poses nobody has measured, and the cost is a one-off in the low hundreds of milliseconds. The performance question this ticket was expected to answer turns out not to be a constraint at all. The **background scoring orchestration** fog item on the map is therefore much less risky than it looked: the numbers say a simple deferred queue will do.

---

## 9. The roll-your-own routes, and other 2026 options

### 9.1 LiteRT / TFLite

**VERIFIED.** The TensorFlow-to-LiteRT rebrand produced **no official Flutter package**. <https://developers.google.com/edge/litert> lists Android, iOS/macOS, Web, Desktop, embedded and MCUs; **Flutter and Dart appear nowhere**. The plugin was never transferred to `google-ai-edge`.

`tflite_flutter` 0.12.1 (published **2025-10-28**, 901 likes, ~59k downloads/30d, verified `tensorflow.org` publisher, Apache 2.0) is the only real option, and it is limping:

- The repo README still carries an *"Announcement - Update: 26 April, 2023"* saying the project *"is currently a work-in-progress"*. Unchanged for three years.
- **108 open issues, 19 of them mentioning iOS.**
- The last commit on `main` (2025-10-28) merged an **outside contributor's** fix for Google Play's 16 KB page-size mandate.
- **Critically:** unpacking the published archive shows `android/build.gradle` migrated to `com.google.ai.edge.litert:litert:1.4.0`, but **`ios/tflite_flutter.podspec` still pins `TensorFlowLiteSwift` at 2.12.0** - released 2023-04-14. **On iOS you would be running a three-year-old TFLite.**

The community fork `flutter_litert` (3.8.0, 2026-08-06, 160/160 points) is more current but its podspec **shells out to `curl` at pod-install time to download ~85 MB of xcframeworks from one person's GitHub release**, then performs `xcrun nmedit` symbol surgery, with App Store rejection history (`ITMS-90426`) documented in its own comments. For a CI-built app that is a supply-chain and reproducibility liability.

**MoveNet** is the licence-clean model: **VERIFIED**, all 13 variations on <https://www.kaggle.com/models/google/movenet> are **Apache 2.0**. SinglePose Lightning is 192x192 uint8, Thunder 256x256, both output `[1,1,17,3]` as **(y, x, score)** - note the axis order, an easy silent bug. **No z, no visibility, no presence.**

MoveNet's intended use is unusually well aligned with a fitness app - **VERIFIED** from the model card: *"Tuned to be robust on detecting fitness/fast movement with difficult poses and/or motion blur"*, *"most suitable for... a single person who is 3ft ~ 6ft away"*, background-people rejection. Its trained-on set adds 23.5k YouTube fitness/yoga/dance frames to COCO.

Two things to weigh against it. First, **VERIFIED**, a documented skin-tone gap on COCO: Lightning **60.5 / 61.2 / 74.4** mAP for darker / medium / lighter skin (Thunder 74.4 / 73.7 / 82.9) - a ~14-point spread. The card claims fairness only on its own Active fitness set. Second, the canonical download link in Google's own sample app (`tfhub.dev/google/lite-model/movenet/...`) now **404s**; you must fetch from Kaggle Models with an account token and vendor the file.

**iOS reality check, VERIFIED:** the `tflite_flutter` README states *"TFLite may not work in the iOS simulator. It's recommended that you test with a physical device."* GitHub Actions macOS runners have no physical iOS device. **On our CI the iOS pose path could only be compiled, never executed.** Given ios-builder is the entire delivery mechanism, that is a serious objection to the whole roll-your-own iOS story.

### 9.2 ONNX Runtime

`flutter_onnxruntime` (1.8.3, 2026-07-19, 48 likes, MIT, ships ORT 1.23.0, iOS 16+) is the only maintained wrapper; the higher-download `onnxruntime` package has been dead since 2024-03. Note its status table marks **input/output metadata introspection as unsupported on iOS and macOS**, so tensor shapes must be hard-coded.

**The models are the problem, and it is mostly licensing:**

- **YOLO-pose (v8 / v11 / v26) is a hard blocker.** **VERIFIED**, <https://www.ultralytics.com/license>: *"An Enterprise License is required if you want to use Ultralytics YOLO **without open-sourcing your entire project**."* The trigger list includes using *"pretrained weights"* and even training *"your own model from scratch"*; AGPL compliance requires *"publicly releasing the complete corresponding source code for the entire derivative work, including... **model weights**"*. No public pricing. The `ultralytics_yolo` Flutter plugin is itself AGPL-3.0. Ironically it is the **best-engineered pose plugin on pub.dev** (160/160 points, CoreML on iOS, LiteRT on Android) and we almost certainly cannot use it. Map decision 11 makes the repo public, but AGPL reaches the *whole application*, not just the repo, so this remains a blocker for any closed-source future.
- **RTMPose** is Apache 2.0 in code, but the headline `body7`/`body8` checkpoints are pretrained on a cocktail of 7-8 datasets, several carrying research-only or CC-BY-NC terms, with no per-checkpoint licence attached. **INFERRED: a quiet provenance risk** that needs legal review or a COCO-only retrain.
- **ViTPose** is Apache 2.0 and the most accurate (81.1 AP) but is a server-class ViT. **Sapiens** is CC-BY-NC and 1.17B parameters. Both are out.

That leaves MoveNet, which we could have run on TFLite anyway. **ONNX offers a better-maintained runtime wrapped by a worse-maintained Flutter plugin, with no pose model we can both use and afford.**

### 9.3 Others, briefly

- **QuickPose.ai - vendor marketing, treated as such.** A commercial iOS/Android SDK wrapping MediaPipe. Priced per monthly active device: free to 100 devices, $50/mo to 1,000, up to $1,000/mo for 100,000; custom exercises from $750 each. **It requires a network-issued SDK key**, which is a runtime licensing dependency and a kill switch on a feature that would otherwise be fully offline - a direct contradiction of map decision 20. **There is no Flutter SDK**, so we would pay for it *and* still write the platform channels. A credibility note worth recording: their own pricing page's client testimonials are unedited **lorem ipsum** attributed to named people. Their content marketing on whether MediaPipe can be used commercially is a sales funnel, not a legal opinion - MediaPipe is Apache 2.0 and needs no intermediary.
- **Sency.ai** - the only commercial SDK with actual Flutter demo repos (`smkit-ui-flutter-demo`, pushed 2026-06-22). No public pricing, sales-gated, demo repos have 0-1 stars. Enterprise motion, sells exercise logic rather than keypoints.
- **PoseTracker** - a pose **API**, i.e. network round-trip. Disqualified by decision 20.
- **Kinetix** - no current mobile pose SDK product found. Not applicable.
- **Apple Create ML action classifier** - consumes Vision pose sequences to train a video action classifier. Attractive (zero size, zero licence, ANE-accelerated) but iOS-only, no Flutter package, and Create ML is a **macOS GUI app**, so retraining is a manual step that cannot run on ios-builder. Also largely moot here: it classifies *actions over video*, and we score *stills* (map decision 7, video out of scope).
- **ExecuTorch** - `executorch_flutter` 0.5.0 exists (2026-07-25, 11 likes, 482 downloads/30d). Runtime is very active but **no pose model ships as a ready-made `.pte`**. Note it for completeness; do not pick it.
- **`litert-torch`** (formerly `ai-edge-torch`; the old repo 404s) is a PyTorch-to-`.tflite` converter, not a runtime. Relevant only as the sanctioned path to get a custom pose model into TFLite.
- **Pure Dart / FFI** - no viable Dart tensor runtime. The one place Dart genuinely enters the hot path is image preprocessing, and that is precisely where it is too slow; the `image` package cannot do per-frame work. Any roll-your-own route needs a native or FFI preprocessing path for YUV420-to-RGB with stride handling, rotation and letterboxing - **a week or two of work that ML Kit and PoseLandmarker both do internally for free.**

---

## 10. Reasoning toward a recommendation, without declaring a winner

The engine is chosen by prototype on real captures. What follows is the reasoning the prototype should be designed to test, stated explicitly so it can be argued with.

### What the evidence actually changed

Three of the ticket's implicit assumptions did not survive contact with the sources:

1. **Depth was expected to be a discriminator. It is not.** Neither Google engine's depth axis has ever been evaluated by its authors, both model cards say "not metric but up to scale", and Apple's is metric only with LiDAR. Combined with map decision 6 and the out-of-scope ruling on 3D pose estimation, the right move is to **build no metric that depends on depth from any engine**. That removes MediaPipe's headline advantage over ML Kit.
2. **Latency was expected to be a constraint. It is not.** We score stills in the background. Even the heaviest model is comfortably fast enough. Spend the time on accuracy.
3. **Side views were expected to be a risk alongside back views. They are the safer case.** The sagittal plane is the best-measured plane in the literature. The genuine risks are far-side limbs (roughly 2x error) and upper-extremity angles generally (13.81° to 52.17° RMSE), which affect **all eight** poses.

So the evaluation collapses onto two axes that actually discriminate: **binding maturity and delivery risk**, and **behaviour on rear views**.

### How each option sits on those two axes

- **ML Kit** is the only option with a mature, widely-used Flutter binding, and it is the **worst-positioned on rear views** - not by measurement, but by explicit documentation: *"The user's face must be present in order to detect a pose."* It is also frozen in beta since 2022 with no SLA, and its metrics-collection clause is in tension with the map's no-network posture. **Strongest on delivery, weakest on the acceptance-critical case.**
- **MediaPipe** has the best evidence quality, the cleanest licence (Apache 2.0 on both code and weights), and the **worst Flutter story by a wide margin** - a hand-written platform channel, a 351 MB CI dependency, and a fragile `use_frameworks!` interaction. It runs the same BlazePose weights as ML Kit, so it inherits the same face-proxy architecture, plus a **confirmed, still-open, silent rear-view bug**. Choosing MediaPipe over ML Kit buys better-structured world landmarks that we just decided not to use, and costs the only mature binding available.
- **Apple Vision** has zero binary cost, zero licensing risk, zero free-team signing friction, and the only topology that includes a `neck` and a `root` joint - which are exactly the torso landmarks the 33-point models lack. It also has the **thinnest evidence base of anything here**: Apple documents nothing about accuracy, viewpoint, or even what its confidence value means. And it is iOS-only, which under map decision 15 means Android either gets a second engine or cannot score. **Its rear-view behaviour is unknown rather than documented-bad**, and because there is no public evidence it uses a face detector as a person proxy, it is the one engine whose architecture does *not* carry a known structural front-bias. That is a reason to test it, not to trust it.
- **Roll-your-own (MoveNet on LiteRT)** is the licence-clean fallback with a fitness-tuned model, but it costs the most hand-written code (crop-region heuristic, letterboxing, YUV conversion), its iOS binding is pinned to a 2023 TFLite, and **it cannot be executed on our CI at all**. Given ios-builder is the delivery mechanism, that last point is close to disqualifying on its own.
- **ONNX** offers nothing unique. Every model is AGPL, provenance-murky, non-commercial, or server-sized, except MoveNet, which does not need ONNX.

### The shape of the recommendation

**Prototype ML Kit and Apple Vision head to head, in that priority order, and treat the rear-view cold-start test in section 11 as the gate.**

The reasoning, made explicit:

- ML Kit first because it is the only option that can be integrated in an afternoon, which means the rear-view experiment can be run this week rather than after a fortnight of platform-channel work. **Even if ML Kit loses, running it first is the cheapest way to learn what rear-view failure looks like** and to build the measurement harness the other engines will reuse.
- Apple Vision second because it is the natural counterpart on an iOS-first project: zero size, zero licence, zero signing friction, a better torso topology, and an unknown-rather-than-documented-bad rear-view posture. It is also the only candidate whose weakness (no Android) is a **known architectural cost** rather than an unmeasured technical risk.
- MediaPipe is worth the platform-channel investment **only if both of the above fail the rear-view gate**, since it shares BlazePose's architecture and would likely fail the same way. Its advantages (world landmarks, licence) are not advantages we are currently able to spend.
- MoveNet/LiteRT is the fallback if all three fail, accepting the CI-execution problem as a known cost.

**This is a reading of the evidence, not a decision.** In particular, if the prototype finds that ML Kit cold-starts fine on a back view despite the documentation - which is entirely possible, since the documentation describes a supported envelope rather than a hard failure - the ordering above changes completely.

### The architectural question this raises for Lucas

One decision is genuinely architectural and, per the map's standing preference, should not be made inside a research ticket:

**Do we accept an iOS-only scoring engine?** Apple Vision is materially the lowest-risk option on delivery, size, licensing and signing, and it is the only one with no third-party dependency at all. But it makes Android non-scoring, which changes map decision 15 from "Android best-effort" to "Android cannot score". The alternative is a pose-engine abstraction in the domain layer with two implementations, which is cheap to design now and expensive to retrofit later, but which guarantees the two platforms disagree on scores. Options, with the obvious trade-off, should go to Lucas before the prototype ticket picks a direction.

---

## 11. What the prototype ticket must measure, because nobody else has

Ordered by decision value. **Item 1 is the gate: if an engine cannot cold-start on a back view, its front-facing accuracy is irrelevant and the decision is made.**

1. **Cold-start acquisition rate by orientation.** For each engine, with no prior tracking state, feed single frames of a subject at 0/45/90/135/180/225/270/315°. Measure only: **does it return a pose at all?** This directly tests the face-detector-proxy hypothesis. Run it both as isolated stills **and** as a continuous turn video, because the detector/tracker split gives different answers and we use the harder mode.
2. **Left/right assignment correctness at 180°.** Not joint position error, **label** error. Fraction of frames where `leftWrist` and `rightWrist` are swapped relative to ground truth on rear double biceps and rear lat spread. Per section 7.7 this is the failure that silently destroys self-referential scoring, and no vendor metric covers it. One subject, two photographs.
3. **Confidence calibration on rear poses.** Log `likelihood` / `visibility` / `presence` / Vision `confidence` on frames independently labelled wrong. Compute whether **any** threshold separates correct from incorrect. Expect not, per section 7.6 - but we need our own number to justify building an orientation check into the frame-fit gate.
4. **Per-pose keypoint error for all eight mandatories** against hand-annotated ground truth, reported **separately per pose**, with front double biceps as the control. The deliverable is a table where rear lat spread sits next to front double biceps.
5. **Far-side limb error on side chest and side triceps**, split camera-side versus occluded-side, to check whether the ~2x doubling from PLoS One 2023 reproduces on a muscular subject.
6. **Repeatability, not just accuracy.** Per section 0's point 2, the metric that actually matters is run-to-run variance on the *same* pose across sessions. Capture the same pose on three separate days and measure score drift with no intentional change. An engine with 2x the absolute error but half the variance is the better engine for us.
7. **The quarter-turn transition**, 90° to 180°: does tracking survive the sweep, or drop and fail to re-acquire?
8. **Subject realism.** Oiled, posing trunks, contest-condition musculature, and more than one skin tone given MoveNet's documented ~14-point COCO gap and BlazePose's Fitzpatrick-1 weakness. **Testing on a clothed volunteer will produce a falsely green result** (section 7.8).

Also worth measuring while the harness exists, since it feeds open map items: real added IPA size per engine on a thinned archive (nobody publishes a usable number for MediaPipe), and real single-still latency on Lucas's iPhone (nobody publishes one at all).

---

## 12. Primary sources

**ML Kit**
- <https://developers.google.com/ml-kit/vision/pose-detection>, `/android`, `/ios`
- <https://developers.google.com/android/reference/com/google/mlkit/vision/pose/PoseLandmark>
- Pose model card: <https://developers.google.com/static/ml-kit/images/vision/pose-detection/pose_model_card.pdf>
- ML Kit Terms of Service: <https://developers.google.com/ml-kit/terms>
- <https://pub.dev/packages/google_mlkit_pose_detection>, <https://github.com/flutter-ml/google_ml_kit_flutter>

**MediaPipe**
- <https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker> (the `ai.google.dev` URL 301s here)
- BlazePose GHUM 3D model card: <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf>
- BlazePose: <https://arxiv.org/abs/2006.10204> · BlazePose GHUM Holistic: <https://arxiv.org/abs/2206.11678>
- `pose_landmarker_graph.cc`, `MPPBaseOptions.h` in <https://github.com/google-ai-edge/mediapipe>
- Issue #5197 (rear-view visibility bug): <https://github.com/google-ai-edge/mediapipe/issues/5197>
- <https://github.com/google/flutter-mediapipe/issues/51>

**Apple**
- <https://developer.apple.com/documentation/vision/vnhumanbodyposeobservation/jointname>
- <https://developer.apple.com/documentation/vision/vndetecthumanbodypose3drequest>
- <https://developer.apple.com/documentation/vision/vnhumanbodypose3dobservation>
- <https://developer.apple.com/documentation/vision/detecting-human-body-poses-in-images>
- WWDC20 "Detect Body and Hand Pose with Vision": <https://developer.apple.com/videos/play/wwdc2020/10653/>

**Models and runtimes**
- MoveNet: <https://www.kaggle.com/models/google/movenet>; SinglePose model card <https://storage.googleapis.com/movenet/MoveNet.SinglePose%20Model%20Card.pdf>
- <https://developers.google.com/edge/litert> · <https://pub.dev/packages/tflite_flutter> · <https://github.com/tensorflow/flutter-tflite>
- <https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html>
- Ultralytics licensing: <https://www.ultralytics.com/license>
- MMPose RTMPose: <https://github.com/open-mmlab/mmpose/blob/main/projects/rtmpose/README.md>

**Literature on viewpoint and validity**
- Martiš et al., *Sensors* 2024;24(10):3091, DOI 10.3390/s24103091 (walking toward vs away)
- Zhang et al., *Front Digit Health* 2026, DOI 10.3389/fdgth.2026.1882536 (OpenCap scoping review)
- *PLoS One* 2023;18(11):e0293917, DOI 10.1371/journal.pone.0293917 (frontal vs sagittal, occluded side)
- Yang & Park, *Bioengineering* 2024;11(2):141, DOI 10.3390/bioengineering11020141 (BlazePose camera position)
- *Sci Rep* 2025, DOI 10.1038/s41598-025-22626-7 (18 models incl. BlazePose, plane-wise error)
- Wu et al., MEBOW, CVPR 2020 (COCO orientation distribution)
- Liu et al., MoViD, SenSys '26, DOI 10.1145/3774906.3802786 (per-azimuth 3D error)
- arXiv 2504.10350v2 (occlusion benchmark) · arXiv 2311.17105 (HPE calibration) · arXiv 2003.00943 (orientation flips)
