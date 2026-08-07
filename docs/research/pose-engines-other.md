# On-device pose engines, part 2: Apple Vision, the raw-model routes, and the rest of the 2026 field

Companion note to [`pose-engines.md`](./pose-engines.md), resolving the remainder of [issue #3](https://github.com/grez-lucas/poseperfect/issues/3).

`pose-engines.md` covers Google ML Kit Pose Detection and MediaPipe PoseLandmarker. This note covers everything else the ticket asks for:

- **Apple Vision** body pose, 2D and 3D
- **TFLite / LiteRT and ONNX Runtime** as a route to running a pose model directly, and which models are actually licensable that way
- **The long tail**: commercial SDKs with pricing, other platform APIs, newer runtimes, cloud fallbacks, depth sensors

**Status:** evidence, not a verdict. As in the companion note, this deliberately does **not** pick an engine. That belongs to a later prototype ticket running real captures of a real subject in the eight mandatories.

**Date of research:** 2026-08-07. Every version number, release date, price and issue count below was read on that date and will rot.

**Convention** (identical to `pose-engines.md`):

- **VERIFIED** - stated in a primary source (official vendor documentation, model card, published paper, package registry metadata, source code). Quoted or closely paraphrased, with a URL.
- **INFERRED** - my reasoning from verified facts. Explicitly not measured by anyone.
- **ANECDOTAL** - developer reports, issue trackers, forum posts. Signal, not measurement.

Vendor marketing that compares a product to its competitors is treated as marketing and labelled as such wherever it appears. It is never cited as fact.

I have not re-argued section 0 of `pose-engines.md`. It stands, and everything below is written against it: we score **still images**, scoring is **self-referential** so consistent bias largely cancels, and **five of the eight mandatories are not front-on**. The consequences of that framing are, if anything, sharper for the options in this note than for the two in the companion.

---

## 0b. One cross-cutting fact that no engine escapes

Before the per-engine sections, a piece of evidence that applies to every option in both notes, because every option in both notes is trained or evaluated on COCO keypoints or something like it.

**COCO is strongly biased towards front-facing subjects, and this is measured.**

The MEBOW dataset (CVPR 2020, Penn State and Amazon Lab126) exists precisely to add body-orientation labels to COCO. The authors labelled roughly **130,000 human instances across 55,000 COCO images**, partitioning 360 degrees into **72 bins of 5 degrees each** - the finest-grained body-orientation labelling published at the time.

> "It can be seen that our dataset covers all possible body orientation, with a Gaussian like peak around 180 degrees, which is natural because photos with humans tend to capture the main person from the front."

**VERIFIED** - MEBOW paper, section 3.2, [arXiv:2011.13688](https://arxiv.org/abs/2011.13688). (In their convention 180 degrees is the camera looking at the person's front.)

And the consequence, stated by the same authors in their own supplementary material:

> "It is not surprising that our model performs best when the camera point of view is towards the Front of the person because a larger portion of MEBOW dataset falls into this category."

**VERIFIED** - MEBOW supplementary material, section B, same arXiv entry.

That is an orientation-estimation model rather than a pose model, but the mechanism is identical and the training distribution is the same COCO images. **INFERRED:** every 2D keypoint model in this evaluation that was trained on COCO keypoints - MoveNet, YOLO-pose, RTMPose, ViTPose, and by strong implication Apple's and Google's undisclosed training sets, which are near-certainly COCO-derived or COCO-shaped - inherits a front-facing prior. Our acceptance-critical cases (rear lat spread, rear double biceps, rear quarter turn, side chest, side triceps) sit in the tail of that distribution.

Nobody has published a per-viewpoint keypoint accuracy breakdown for any of the production engines in either note. **That is a genuine finding and it is the single largest reason this evaluation cannot be closed on paper.**

### The specific failure mode to hunt for: left-right swapping

The reason viewpoint matters more than raw accuracy here is section 0 point 2 of the companion note. A consistent bias cancels between reference and capture. A **bimodal** error does not.

The canonical bimodal error in 2D pose estimation is left-right keypoint swapping on a subject facing away from the camera. Evidence that this is real and not theoretical:

- **VERIFIED (mechanism):** MMPose ships `flip_test` as a default test-time augmentation. The documentation describes it as sending "an image and its flipped version [...] into the model to inference, and the output of the flipped version will be flipped back, then average them **to stabilize the prediction**". The `flip_pairs` / `swap` metadata exists because "when applying image horizontal flip, the left part will become the right part". [MMPose framework guide](https://mmpose.readthedocs.io/en/latest/guide_to_framework.html). **INFERRED:** a whole field would not ship a default 2x-cost TTA whose stated purpose is stabilisation unless the un-augmented prediction were unstable in exactly this dimension. Note also that flip_test *averages* two heatmaps - if the model is genuinely bimodal on a rear view, averaging a correct and a mirrored prediction produces a keypoint set that is wrong in a third way.
- **VERIFIED (measured, in a controlled marker-based comparison):** Nakano et al., *Scientific Reports* 11, comparing OpenPose, AlphaPose and DeepLabCut against 15-camera marker-based mocap on 15 participants, state plainly: "For all pose estimation methods, our results include larger errors caused by issues such as false positive detections, tracking failures and **erroneous switching of limbs**." [Scientific Reports / PMC8526586](https://pmc.ncbi.nlm.nih.gov/articles/PMC8526586/). Their headline 3D joint-centre errors were roughly 27-41 mm at the knee and 27-34 mm at the shoulder for OpenPose - the useful point is that limb switching is called out separately from ordinary localisation error.
- **ANECDOTAL / literature:** self-supervised and unsupervised 3D pose work repeatedly reports the model cannot distinguish left from right when the subject faces away from the camera, attributing it to depth ambiguity in the 2D input (e.g. [arXiv:2210.04514](https://arxiv.org/abs/2210.04514)). This is a different model class from ours, but it is the same ambiguity.

### The counter-evidence, which is worth taking seriously

"Rear views are obviously worse" is an assumption, and there is at least one published measurement pointing the other way.

**VERIFIED:** *Sensors* 2025;25(3):799, "Influence of the Camera Viewing Angle on OpenPose Validity in Motion Analysis", compared four viewing angles against marker-based mocap for knee, hip, elbow and shoulder angles. Its finding, verbatim: there were "significant biases when comparing the joint angles inferred from the different viewing angles. In general, **back-viewing cameras performed best and resulted in the lowest percental deviations.**" [doi:10.3390/s25030799](https://doi.org/10.3390/s25030799).

**INFERRED:** this is OpenPose, a different model with a different training distribution, so it does not transfer to any engine in this note. But it is a strong reason not to assume the answer. And it suggests the right mental model: a back view can be *easier* for keypoint localisation - fewer self-occlusions of the torso, cleaner limb silhouettes against the background - while being *harder* for chirality, because the disambiguating cues are gone.

**These are two different failure modes and the prototype must measure them separately:**

- **Positional error** - how far is each joint from where it should be? Consistent, and therefore largely cancelled by self-referential scoring.
- **Chirality error** - is the left/right labelling correct and, crucially, *stable*? Bimodal, and therefore fatal.

Conflating them is how an evaluation talks itself into the wrong engine. A model with worse positional error on rear views but rock-solid chirality is a better fit for this product than one with the reverse profile.

### Practical implication

**For the prototype, not a decision:** the cheapest possible instrument is to run the same rear-view capture through a candidate engine N times (and on N near-identical frames) and check whether the left/right assignment is stable, before measuring any accuracy number at all. An engine that is bimodal on rear views is disqualified regardless of how good its front-view numbers are. A design mitigation exists - score against a mirror-invariant representation, or detect and canonicalise the swap using the orientation estimate - but it is a real cost and should be priced in, not assumed.

---

## 1. Apple Vision

### 1.1 What Apple actually ships in August 2026

The ticket asks not to assume the older API is current. It very nearly is, but not quite, and the difference matters.

| API | Joints | Min iOS | Status |
|---|---|---|---|
| `VNDetectHumanBodyPoseRequest` (2D) | **19** | 14.0 | Legacy Obj-C/Swift API. Only `Revision1` exposed. Not deprecated |
| `VNDetectHumanBodyPose3DRequest` (3D) | **17** | 17.0 | Legacy API. Still on its initial revision |
| `DetectHumanBodyPoseRequest` (2D, Swift-only) | **19** + optional hands | 18.0 | Current. Exposes **`Revision.revision2`** and `detectsHands` |
| `DetectHumanBodyPose3DRequest` (3D, Swift-only) | **17** | 18.0 | Current. Only `Revision.revision1` |

**VERIFIED** - availability blocks on [`VNDetectHumanBodyPoseRequest`](https://developer.apple.com/documentation/vision/vndetecthumanbodyposerequest), [`VNDetectHumanBodyPose3DRequest`](https://developer.apple.com/documentation/vision/vndetecthumanbodypose3drequest), [`DetectHumanBodyPoseRequest`](https://developer.apple.com/documentation/vision/detecthumanbodyposerequest), [`DetectHumanBodyPose3DRequest`](https://developer.apple.com/documentation/vision/detecthumanbodypose3drequest), and the [Vision framework landing page](https://developer.apple.com/documentation/vision) ("Starting in iOS 18.0, the Vision framework provides a new Swift-only API").

**Has Apple shipped anything newer? No.** Apple's own [Vision updates page](https://developer.apple.com/documentation/updates/vision) is the authority, and as of 2026-08-07 it has exactly two dated headings:

- **June 2025** (iOS 26): `DetectLensSmudgeRequest`, `RecognizeDocumentsRequest`. Nothing about pose.
- **June 2024** (iOS 18): the new Swift API, `CalculateImageAestheticsScoresRequest`, `detectsHands`, and verbatim "Use `revision2` to improve 2D human body pose detection."

There is **no 2026 heading at all**, and the framework's current "Pose analysis" topic group lists exactly four requests - animal body pose, human body pose 3D, human body pose, human hand pose. **VERIFIED.**

**One caution before treating revision2 as a free upgrade.** **ANECDOTAL**, [forum thread 766505](https://developer.apple.com/forums/thread/766505): the new Swift Vision API produced measurably **worse** output than the legacy `VN*` API for the same configuration on text recognition, with an Apple DTS engineer engaged. **INFERRED:** do not assume `VNDetectHumanBodyPoseRequest` and `DetectHumanBodyPoseRequest` are one model behind two facades. Verify parity on your own captures before adopting either.

**Conclusion (VERIFIED by absence, checked against the updates page, the framework topic listing, and the WWDC 2025 / 2026 image-understanding sessions): the last substantive change to Apple's human body pose API was WWDC 2024.** The 3D request has been on revision 1 since iOS 17 and remains single-person, all-17-joints-or-none, with no per-joint confidence. Apple's 2025 and 2026 Vision work went to document understanding, segmentation and Foundation Models integration, not pose.

### 1.2 Landmark set and count

- **2D, 19 joints, VERIFIED** from [`VNHumanBodyPoseObservation.JointName`](https://developer.apple.com/documentation/vision/vnhumanbodyposeobservation/jointname) and confirmed identical in the iOS 18 [`HumanBodyPoseObservation.JointName`](https://developer.apple.com/documentation/vision/humanbodyposeobservation/jointname): `nose, leftEye, rightEye, leftEar, rightEar, neck, leftShoulder, leftElbow, leftWrist, rightShoulder, rightElbow, rightWrist, root, leftHip, leftKnee, leftAnkle, rightHip, rightKnee, rightAnkle`. Grouped as 7 group names (`face, torso, leftArm, rightArm, leftLeg, rightLeg, all`). Coordinates normalised 0-1, origin **bottom-left**.
- **3D, 17 joints, VERIFIED** from [`VNHumanBodyPose3DObservation.JointName`](https://developer.apple.com/documentation/vision/vnhumanbodypose3dobservation/jointname): `topHead, centerHead, centerShoulder, spine, leftShoulder, rightShoulder, leftElbow, rightElbow, leftWrist, rightWrist, root, leftHip, rightHip, leftKnee, rightKnee, leftAnkle, rightAnkle`.

**Anatomical read for bodybuilding (INFERRED):** the 2D set is adequate but thin. It gives shoulders, elbows, wrists, hips, knees, ankles - the ticket's minimum - plus `neck` and `root`, which most COCO-derived engines do not have and which are genuinely useful for a torso axis. What it lacks is any mid-torso point: there is nothing between `neck` and `root`, so lat spread and abdominal-and-thigh are described only by a shoulder-hip quadrilateral.

The **3D set fixes exactly that** - it adds `spine`, `centerShoulder` and `topHead`, giving a real torso chain. **But the 3D set is not a superset of the 2D set:** it drops `nose`, both eyes, both ears and `neck`. **INFERRED, and it matters here:** the facial landmarks are the strongest available cue for "is this subject facing away from me?", so the 3D request removes the very signal you would use to detect and correct a left/right swap. See 1.5.

### 1.3 Depth and 3D, and whether it is metric

This is the most misunderstood part of the API, so it is worth being exact.

- **VERIFIED:** `VNHumanBodyPose3DObservation` returns positions **in metres**, origin at the `root` joint between the hips; `position` is root-relative, `localPosition` is parent-relative, `cameraRelativePosition(_:)` gives camera-relative, `cameraOriginMatrix` gives the hip-to-camera transform, and `pointInImage(_:)` projects back to 2D. WWDC23 session 111241, verbatim: "position of the 3D joints is returned in meters relative to the captured scene in the real world with an origin at a root joint." [WWDC23 111241](https://developer.apple.com/videos/play/wwdc2023/111241/).
- **VERIFIED:** it is **monocular**. Apple: "The request doesn't require images with depth data to run. However, providing depth data improves detection accuracy." WWDC23: "Vision now enables you to retrieve that 3D position from images without ARKit or ARSession."
- **VERIFIED, and this is the catch:** `bodyHeight` is metres, and `heightEstimation` tells you which of two techniques produced it. `.measured` requires LiDAR depth. `.reference` means, verbatim from WWDC23: "Depending on the available depth metadata, this height will either be a more accurate measured height or a **reference height of 1.8 meters**."

**INFERRED, high confidence:** for our use case - a still image, captured on demand, on an arbitrary iPhone - `heightEstimation` will be `.reference` essentially always. LiDAR is rear-camera-only and only on Pro models, and Apple restricts `.measured` to an `AVCaptureSession` configured for the LiDAR camera. So the "metres" are metres **under a hardcoded 1.8 m body-height assumption**: every length is off by the ratio (true height / 1.8), uniformly.

**How much does that hurt us? Less than it sounds, and then suddenly a lot.** A uniform scale factor is exactly the kind of consistent systematic bias that section 0 point 2 says cancels in a self-referential comparison, and joint **angles** are scale-invariant anyway. The danger is the discontinuity: if `heightEstimation` were `.measured` for the reference capture and `.reference` for the scoring capture, the two skeletons are in different scales and the comparison is silently wrong. **Practical note for the prototype:** record `heightEstimation` alongside every capture and refuse to compare across techniques, or normalise to a unitless skeleton and ignore `bodyHeight` entirely. The one existing Flutter package does **not** expose `heightEstimation` (verified from source, section 1.6), so on that package you cannot even detect the condition.

### 1.4 Determinism and the confidence signal

- **VERIFIED (2D):** `VNRecognizedPoint` inherits `confidence: VNConfidence` from [`VNDetectedPoint`](https://developer.apple.com/documentation/vision/vndetectedpoint), described only as "A confidence score that indicates the detected point's accuracy." No documented range, no semantics, no calibration statement. Apple's only concrete guidance is a validity filter: "Ignore any recognized points with a `confidence` value of 0, because they're invalid."
- **VERIFIED (3D):** [`VNHumanBodyRecognizedPoint3D`](https://developer.apple.com/documentation/vision/vnhumanbodyrecognizedpoint3d) has **no confidence property at all**. Combined with the documented all-or-nothing rule - "The framework doesn't return a partial list of joints, so you get all 17 joints or none" - the 3D API emits **zero uncertainty signal**.

**VERIFIED, and it is a trap:** `VNConfidence` is documented as ranging 0.0 to 1.0 "under most circumstances", but **1.0 is overloaded** - it also signals "this observation does not assign meaning to confidence". A confidence of exactly 1.0 is therefore not evidence of certainty.

**INFERRED:** Vision's 2D confidence is usable as an ordinal hint and as a validity flag, not as a probability. Critically, it cannot detect a left/right swap: a mirrored-but-anatomically-plausible skeleton will carry high confidence on both sides, because the model is confident about the *point*, not about the *label*. And on the 3D request you have no signal whatsoever.

**Documented determinism guarantees: none.** **VERIFIED by absence:** Apple documents nothing about reproducibility, temporal smoothing or frame-to-frame stability for body pose. There is no built-in temporal filter, no tracking-ID continuity across pose observations, and no guarantee that the same input yields the same output across runs, devices or OS builds.

And there is one developer report severe enough to be a must-reproduce item. **ANECDOTAL**, [Apple developer forums thread 744794](https://developer.apple.com/forums/thread/744794), "VNDetectHumanBodyPose3DRequest Gives Inconsistent Results": on an iPhone 14 Pro **with LiDAR**, gating on `heightEstimation == .measured` - that is, the good path - the reporter states "the values never seem to settle and they can fluctuate anywhere from **5'4" to 10'1"** (I'm about 6'0")... I rarely see any values that are close enough (within an inch) of the ground truth." 572 views, **zero replies, no Apple response.**

**INFERRED:** if `bodyHeight` is that unstable on a static subject under the best available conditions, the underlying skeleton scale is unstable too. That is precisely the run-to-run, non-cancelling error that section 0 point 2 identifies as fatal for self-referential scoring. One unanswered forum post is not a measurement, but this specific behaviour has to be reproduced or ruled out before the 3D request is taken seriously.

Two adjacent reports worth carrying into the prototype plan, both **ANECDOTAL** and both unanswered by Apple: [thread 790825](https://developer.apple.com/forums/thread/790825) reports the 3D request consuming about **1 GB of RAM after a minute** of real-time use with a minimal repro attached; and [threads 777300 / 777314](https://developer.apple.com/forums/thread/777300) report the 3D request failing outright on visionOS despite the docs listing visionOS 1.0+ availability. **INFERRED:** treat Apple's documented availability matrix as a claim to confirm on device, not a fact.

One clarification that matters, because it is easy to cite wrongly: [forum thread 660966](https://developer.apple.com/forums/thread/660966) is titled "VNDetectHumanBodyPoseRequest -> left leg wrong?" and looks like left/right evidence. It is **not**. It is an API *grouping* bug - `recognizedPoints(.rightLeg)` returning left-leg keys - with a workaround of calling `recognizedPoint(.rightAnkle)` directly. **Do not cite it as evidence that Vision flips joints on rear views. It does not show that.**

### 1.5 Back and side views: what Apple documents, and what it does not

Apple **does** publish a limitations list. WWDC20 session 10653, verbatim ([link](https://developer.apple.com/videos/play/wwdc2020/10653/)):

- "If the people on the scene are bent over or upside down, the body pose algorithm will not perform as well."
- "The pose might not be determinable due to obstructive flowing clothing."
- "If one person is partially occluding another in the view, it is possible for the algorithm to get confused."
- "Results may get worse if the subject is close to the edges of the screen."

Plus, from the docs: the subject's height should be at least a third of the image height; a large portion of key body regions should be present; flowing clothing reduces accuracy; dense crowds produce inaccurate results. And from the 3D sample project page: "The input image should have all limbs of the subject visible."

**The finding, VERIFIED by absence** - checked across WWDC20 10653, WWDC23 111241, WWDC24 10163, the "Detecting Human Body Poses in Images" and "Identifying 3D human body poses in images" articles, both request reference pages, and the 3D sample page:

> **Apple documents nothing about view dependence.** Every published limitation is about occlusion, clothing, crowding, framing or extreme body orientation. There is not one Apple statement about rear-facing subjects, camera azimuth, front-versus-back, or left/right disambiguation, and Apple publishes nothing about training-data composition. The only viewpoint caveat anywhere in the pose documentation is about *hands* parallel to the camera axis.

**Nobody outside Apple has measured it either, and I checked hard enough to say that with confidence.** **VERIFIED by absence:** direct arXiv API queries for `all:"VNDetectHumanBodyPose"`, `abs:"Apple Vision" AND abs:"pose estimation" AND abs:"iPhone"`, and `abs:"left-right" AND abs:"ambiguity" AND abs:"human pose"` all return **zero results**, while control queries on the same endpoint return hits normally - so the zeros are real, not a tooling artefact. On GitHub, `VNDetectHumanBodyPose3DRequest` appears in **8 issues in total across all of GitHub**, all hobby apps. A sweep of roughly 80 recent Vision-tagged Apple developer forum threads found body pose in a handful, and **not one about left/right swapping, back views, mirrored skeletons or view-dependent accuracy**.

> **There is no MPJPE, no PCK, no per-view breakdown, and no Apple-versus-anything body-pose comparison in the published or preprint literature.** Apple publishes no accuracy numbers of any kind for these APIs, and the independent literature has not filled the gap.

What *does* exist is clinical shoulder range-of-motion validation, all frontal or lateral, all reporting joint **angles** rather than keypoint error:

- **VERIFIED:** *Sensors* 2024;24(2):534 compared Apple's Vision framework against marker-based mocap (n=20), R-squared above 0.93, with Vision "somewhat overestimating" ROM and adduction "the worst performer among all tested movements". [doi:10.3390/s24020534](https://doi.org/10.3390/s24020534). It varied *iPhone placement*, not subject facing.
- **VERIFIED:** *Shoulder & Elbow* 2025 (n=17) found R-squared above 0.98 but **2 to 25 degrees of overestimation** at greater ranges, concluding Vision "should not be used interchangeably with 3D-mocap". [doi:10.1177/17585732251360746](https://doi.org/10.1177/17585732251360746).
- **VERIFIED:** *JSES International* 2025, same pipeline, reports consistency by movement: abduction R-squared 0.99, flexion 0.95, extension 0.69, **functional internal rotation 0.52**. [doi:10.1016/j.jseint.2025.05.026](https://doi.org/10.1016/j.jseint.2025.05.026). **INFERRED and worth flagging:** the worst performer is precisely the movement where the arm goes **behind the back**, self-occluded from a frontal camera. The paper does not attribute it that way, but it is the closest published signal that occlusion degrades Vision badly - and arms occluding the torso is the normal condition in several mandatories.

**Consequences for this evaluation, stated as costs:** you cannot source this number, you must generate it, and a rear-view and side-view accuracy harness becomes a first-class work item rather than a spike. Vision's obscurity also cuts the other way: with eight public issues in existence there is no accumulated community knowledge, no Stack Overflow canon, and no third-party wrapper that has already hardened against these failure modes.

**INFERRED, and this is the expected failure mode:** a 19-joint model with explicit `left*`/`right*` labels - including `leftEye`, `rightEye`, `leftEar`, `rightEar` - must resolve chirality from appearance. From behind, the evidence that disambiguates left from right is absent or inverted. Section 0b establishes that this is the documented, canonical failure of the whole field and that COCO-shaped training data is peaked on front views. Apple's silence is not evidence the failure does not occur; it is evidence Apple never characterised it.

**Compounding, INFERRED:** on the 3D request the risk is strictly worse. You get 17 joints or nothing, no per-joint confidence, and no facial landmarks with which to independently estimate facing. A left/right swap in 3D is silent and indistinguishable from a correct result. The three rear mandatories are precisely the case where this bites.

Two things partially help and should be tested rather than assumed:

- **VERIFIED:** the 2D request keeps `leftEye`/`rightEye`/`leftEar`/`rightEar`. **INFERRED:** low or zero confidence on all four facial points is a usable "subject is facing away" detector, and you can then canonicalise the skeleton. This is a reason to prefer the **2D** request for the rear mandatories even though the 3D one has a better torso chain.
- **VERIFIED:** `cameraOriginMatrix` on the 3D observation is "A transform from the skeleton hip to the camera", which WWDC23 frames as "useful to get an understanding of where the camera was relative to the person". **INFERRED:** that is a facing estimate, but it is derived from the same skeleton that may already be mirrored, so it is not an independent check.

### 1.6 Flutter integration

**VERIFIED:** exactly one package family on pub.dev wraps Apple Vision body pose - `apple_vision_pose` and `apple_vision_pose_3d`, from the GitHub user **Knightro63** ([repo](https://github.com/Knightro63/apple_vision), MIT, 20 stars, 0 open issues, last push 2026-07-25, not archived). Everything else on pub.dev with "pose" in the name is MediaPipe, ML Kit or LiteRT. There is no first-party Apple or Flutter-team binding.

pub.dev metadata read 2026-08-07 via the pub.dev API. **No verified publisher on any of them** (`publisherId: null`):

| Package | Latest | Published | Likes | Pub points | Downloads/30d | Platforms |
|---|---|---|---|---|---|---|
| `apple_vision_pose` | 0.1.0 | 2026-07-25 | **1** | 160/160 | **358** | ios, macos |
| `apple_vision_pose_3d` | 0.1.0 | 2026-07-25 | **2** | 160/160 | **174** | ios, macos |
| `apple_vision` (umbrella) | 0.1.0 | 2026-07-25 | 16 | 160/160 | 246 | ios, macos |

Four versions in three years. MIT, Dart 3 compatible, `ios.deployment_target = '14.0'` for 2D and `'17.0'` for 3D.

**VERIFIED from reading the Swift sources** (`AppleVisionPosePlugin.swift` and `AppleVisionPose3DPlugin.swift`):

- They wrap the **legacy `VN*` API**, not the iOS 18 Swift API. So **no `detectsHands` and, more importantly, no `revision2`** - you get the 2020-era 2D model.
- The Dart API is `processImage(Uint8List image, ...)`: **every frame crosses the MethodChannel as raw bytes** and Swift rebuilds a `CIImage(bitmapData:)`. A 640x360 BGRA frame is roughly 921 KB. This is architectural, not tunable.
- The 3D plugin has a **provable bug**: `relativePosition` and `childPosition` are both assigned `point?.position`, the same matrix, despite a comment claiming parent-relative. `pitch` is hardcoded to `Float.pi / 2` and yaw/roll are naive trig on the position vector, discarding the rotation block of the 4x4. Joint orientation is effectively unavailable.
- It does **not** expose `heightEstimation`, so you cannot tell measured from reference scale (see 1.3).
- No confidence threshold, no revision selection, no max-body-count.

**INFERRED:** this is a useful binding *reference*, not a dependency you would ship. At 1-2 likes and ~350 downloads a month you would be the one finding the remaining bugs.

**The realistic route is a hand-written Swift plugin.** VERIFIED: a GitHub code search for Flutter plus `VNDetectHumanBodyPoseRequest` returns zero results outside that one repo, so there is essentially no public prior art. INFERRED, the shape of a correct implementation: own the capture session in Swift, build `VNImageRequestHandler(cvPixelBuffer:orientation:)` from the `CMSampleBuffer` directly, allocate the request once, and return only joints (19 x (x, y, confidence) is a few hundred bytes) over an `EventChannel`. That is maybe 300 lines. Since we score **stills on demand**, not a live stream, this is far easier than the general case - we do not need a preview-texture pipeline at all, just "hand me a `CVPixelBuffer` or file URL, give me back joints".

**Maturity verdict:** binding maturity is **low but the risk is low too**. There is no mature package, but Vision itself is a stable system framework and the surface we need is small. The cost is real engineering work rather than a `pubspec.yaml` line.

### 1.7 iOS binary size, minimum version, entitlements, acceleration

- **Binary size: effectively zero.** VERIFIED that Vision is a system framework at `/System/Library/Frameworks/Vision.framework`; nothing is bundled. INFERRED (effectively certain): the added cost is a dyld load command plus your glue code. This is Vision's single largest advantage - MediaPipe and TFLite routes bundle both a runtime and a multi-megabyte model blob.
- **Minimum iOS:** 14.0 for the 2D request, 17.0 for 3D, 18.0 if you want revision2 or `detectsHands`. **INFERRED:** targeting revision2 means an iOS 18 floor or a dual path.
- **Entitlements: none.** VERIFIED by absence on every request page. You need `NSCameraUsageDescription` / `NSPhotoLibraryUsageDescription` to *acquire* pixels, not to run Vision. Nothing here interacts with free-team signing constraints (no special capability, no App Group, no push).
- **Acceleration:** VERIFIED, WWDC24 10163: "Vision will remove CPU and GPU support for some requests on devices with a Neural Engine. On these device, the Neural Engine is the most performant option", and `supportedComputeDevices()` exists to query it at runtime. Apple does **not** publish a per-request table. INFERRED (strong): body pose runs on the ANE on A12+. Verify with `supportedComputeDevices()` rather than assuming.
- **Hard device gate on the 3D request, and it is only documented in a forum reply.** **VERIFIED** (Apple Frameworks Engineer, [forum thread 743402](https://developer.apple.com/forums/thread/743402)): "This request is not supported on simulator, and **requires a device with a neural engine**." The sample-code page separately states A12 or later. Neither appears in the API reference availability block. **Practical consequence: the 3D request cannot be exercised in the iOS Simulator at all**, which affects how a prototype and its CI are set up.
- **Everything is on-device, confirmed by Apple rather than inferred.** **VERIFIED**, Apple Frameworks Engineer on [forum thread 799529](https://developer.apple.com/forums/thread/799529): "All Vision Framework requests are on device and are highly performance tuned for the on device inference while still maintaining high quality and accuracy." No network, no per-call cost.

### 1.8 Licensing

- **VERIFIED:** Vision ships as part of the iOS SDK under the [Apple Developer Program License Agreement](https://developer.apple.com/support/terms/apple-developer-program-license-agreement/). Section 3.3.1(A) requires use of Documented APIs only; sections 2.1 and 2.6 forbid redistributing or reverse-engineering the Apple Software itself.
- **VERIFIED by exhaustive grep of the agreement text:** the ADPLA **never mentions Vision, `VNDetect`, Core ML or body pose anywhere**. Its section 3.3.11, "AI & Machine Learning Technologies", covers only Foundation Models, SiriKit and App Intents. Where Apple does restrict export of a framework's output - SiriKit is the example - it says so explicitly. **INFERRED, high confidence:** there is no royalty, no attribution requirement, no open-source obligation, no per-call fee, and no restriction on Vision-derived output. **There is also no separate model-weight licence**, because the weights are part of the OS and are never yours to ship. This is cleaner than any other option in either note.
- **One flag:** ADPLA section 3.3.2 requires FDA compliance if the app's output is framed as diagnostic or medical. Scoring a bodybuilding pose is not that, but "posture assessment" framing could drift towards it. Keep the marketing language on the athletic side.
- **Caveat:** I am reporting the shape of the agreement, not giving legal advice. If Vision becomes the choice, have counsel read the current ADPLA.

### 1.9 Latency

**Apple publishes no latency numbers for body pose.** VERIFIED absence, checked across the docs, WWDC20 10653, WWDC23 111241 and WWDC24 10163. Apple's only performance statements are qualitative: "real time", "a lightweight option", and "Vision requests can be memory-intensive, so I recommend limiting the number of Vision requests performed at the same time".

In fact the absence is on the record. **VERIFIED:** on [forum thread 799529](https://developer.apple.com/forums/thread/799529) a developer asked an Apple Frameworks Engineer point-blank whether there is a performance report. The engineer answered the on-device question and **did not provide one**.

- **ANECDOTAL, and the only public measurement found anywhere:** [forum thread 679909](https://developer.apple.com/forums/thread/679909), "Optimising VNDetectHumanBodyPoseRequest for live 60fps", reports roughly **40 ms per frame for the 2D request on an iPhone 11**, capping the app at about 45 fps. The community reply was "It takes as long as it takes... If you want a faster body pose detection method, you will have to train your own model."
- **INFERRED (2D):** WWDC20 demos and Apple's own sports-analysis sample run body pose on a live 30-60 fps camera stream on then-current iPhones, so a single 2D request must sit under ~33 ms on A12+. Combined with the iPhone 11 figure, a planning band of **roughly 10-40 ms depending on device generation** is defensible. It is inference plus one anecdote, not measurement.
- **INFERRED (3D):** `VNDetectHumanBodyPose3DRequest` inherits `VNStatefulRequest` and takes a `frameAnalysisSpacing`, which exists precisely so you can run it slower than capture. Expect 3D cost >= 2D cost. **Note for us:** a stateful request designed around frame accumulation is a slightly awkward fit for one-shot still images, and how it behaves on a single frame with no history is worth checking in the prototype.

### 1.10 The iOS-only question, stated plainly

The app targets iOS first-class with Android best-effort and kept compiling. Vision is iOS-only by construction: it is an Apple platform framework, there is no redistributable binary, and sections 2.1/2.6 of the ADPLA would forbid extracting one if there were. **VERIFIED trivially.**

So choosing Vision forces a second engine on Android. The question is what that actually costs, and the answer is worse than "we write the integration twice".

**The landmark sets are not interchangeable.** Vision 2D emits 19 joints; ML Kit Pose Detection and MediaPipe PoseLandmarker both emit 33. **VERIFIED** for ML Kit's count from [Google's ML Kit pose detection docs](https://developers.google.com/ml-kit/vision/pose-detection). The two sets are not in a subset relationship:

- Vision has `neck` and `root`. **Neither exists in the 33-landmark set.**
- The 33-landmark set has mouth corners, inner and outer eye points, pinky, index and thumb points, heels and foot indices. **None exist in Vision.**
- The usable intersection is roughly 15 points: nose, two eyes, two ears, shoulders, elbows, wrists, hips, knees, ankles - and even there "left eye" means the eye centre in one set and one of three eye points in the other.

You can synthesise a neck as the shoulder midpoint and a root as the hip midpoint on the Android side, but a synthesised midpoint is a *different anatomical quantity* from a learned `neck` joint, placed differently and biased differently.

**And that is the disqualifying point.** Section 0 point 2 of the companion note is the load-bearing assumption of the whole scoring design: a capture is compared against the same athlete's own earlier reference, so consistent systematic bias cancels. **That argument only holds when reference and capture come from the same model.** The moment a reference is captured on iOS via Vision and a later capture is scored on Android via ML Kit, the two skeletons carry two different, uncancelled systematic biases, and that inter-model bias becomes the dominant error term - larger, plausibly, than the pose difference we are trying to measure. Every reference the athlete has recorded becomes unusable the day they switch phones, and cross-device or cross-platform comparison is off the table entirely.

**Stated as the decision it is:** an iOS-only engine does not just mean two integrations. It means **references cannot transfer between platforms**, and it silently breaks the premise that makes self-referential scoring forgiving in the first place. Nobody has measured how large the Vision-vs-ML-Kit inter-model bias actually is - that is itself a finding, and if Vision is seriously in contention, measuring exactly that on the same captures should be the first prototype experiment. But the burden of proof sits squarely on Vision here, and it is a heavy one.

Three ways out exist, and each has a cost worth naming rather than assuming away:

1. **Accept iOS-only for scoring.** Android gets capture and viewing but no references and no scores. Honest, cheap, and a real product limitation.
2. **Run the same cross-platform engine everywhere and use Vision for nothing.** This is what the companion note's options give you.
3. **Store references as raw images, not landmarks**, and re-derive landmarks with whatever engine is local at scoring time. This restores same-model comparison at the cost of storing and re-processing images, and of a scoring model that can change under you across app versions - which is its own determinism problem, and arguably a worse one.

### 1.11 Adjacent Apple option: ARKit body tracking

Worth naming because it is the only Apple API with a rich skeleton, and worth ruling out quickly.

- **VERIFIED:** `ARBodyTrackingConfiguration` is iOS 13+ and, per Apple, "tracks human body poses, planar surfaces, and images using the **rear-facing camera**". WWDC19 session 607 states the skeleton has **91 joints** and that the feature is A12+ because it runs on the Neural Engine, using only the camera image - no LiDAR.
- **VERIFIED:** `ARSkeletonDefinition.defaultBody3D` documents "The default height of this skeleton is 1.66 meters" - the same fixed-reference-scale issue as Vision 3D, with a different constant, mitigated by `automaticSkeletonScaleEstimationEnabled`.
- **VERIFIED:** only a subset of the 91 joints is actually estimated; WWDC19 607 describes untracked joints that "just follow the motion of the closest green parent". A high joint count is not a high information count.
- **INFERRED, and decisive for us:** ARKit body tracking is a *live session*, not a request. It needs a running rear-camera AR session and **cannot be run over a stored image or an arbitrary video file**. For an app that scores stills captured on demand - and that may want front-camera self-capture - this is out.
- The Flutter route, `arkit_plugin` ([pub.dev](https://pub.dev/packages/arkit_plugin), v1.5.0 published 2026-08-03, verified publisher `leushchenko.com`, 509 likes, ~5,300 downloads/30d, 842 GitHub stars) is by far the healthiest Apple-adjacent package. **VERIFIED blocking limitation:** its `AnchorSerializer.swift` hardcodes exactly 8 joints - root, head, hands, feet, shoulders. Elbows, knees, hips, spine and wrists never cross the channel. Fixable with a fork or upstream PR, but out of the box it is unusable for form analysis.



## 2. Running a pose model directly: TFLite / LiteRT and ONNX Runtime

This is not one option, it is a matrix: **a runtime** times **a Flutter binding** times **a model** times **a weights licence**. Each axis has an independent way to disqualify the combination, and the licence axis kills more candidates than the technical one.

### 2.1 State of the runtimes in August 2026

| | LiteRT (ex-TensorFlow Lite) | ONNX Runtime |
|---|---|---|
| Framework activity | Alive. v2.1.6 released 2026-07-02. Apache-2.0 | Very active. v1.28.0 released 2026-07-25. MIT |
| Official iOS binary | **Effectively frozen.** `TensorFlowLiteC` / `TensorFlowLiteSwift` CocoaPods, last stable **2.17.0 built 2024-07-29**; nightlies stopped **2025-06-19**. No `LiteRT` pod exists | `onnxruntime-c` / `onnxruntime-objc` published in lockstep with the framework, **1.28.0 on 2026-08-04** |
| First-party Dart binding | **None** | **None** |
| Min iOS (runtime) | 12.0 | **15.1** |

**VERIFIED**, and this is the headline finding on the LiteRT side: Google renamed TensorFlow Lite to LiteRT and kept the Android side moving - v2.1.6 Maven artifacts, a Kotlin `CompiledModel` API, NPU delegates - while the iOS binary distribution stopped. The stable `TensorFlowLiteC` CocoaPod ends at 2.17.0 with a build stamp of 2024-07-29, the nightly pod pipeline stopped on 2025-06-19, and there is no CocoaPod named `LiteRT` or `LiteRTC` with any stable release. Google's own [iOS quickstart](https://developers.google.com/edge/litert/ios/quickstart), last updated 2026-05-28, still tells you to write `pod 'TensorFlowLiteSwift', '~> 2.10.0'` and never mentions a LiteRT-named pod. The `litert_cc_sdk.zip` release asset contains 129 files, all C++ headers and sources, **no prebuilt iOS binaries at all**.

**INFERRED:** if you go LiteRT on iOS in 2026 through official channels, you are shipping a runtime built in July 2024.

There is one green shoot. **VERIFIED:** `google-ai-edge/LiteRT` now contains a root `Package.swift` (copyright 2026 Google LLC) declaring `.iOS(.v15)` and a real Swift `CompiledModel` wrapper under `litert/swift/Sources/`, including Metal `MTLBuffer`-backed tensors. But its `binaryTarget(path:)` entries point at `prebuilt/CLiteRT.xcframework.zip`, and **`prebuilt/` does not exist in the repo**. **INFERRED:** a first-party iOS LiteRT Next story is coming but has not shipped; you would have to build the xcframework yourself with Bazel. Worth watching, not worth planning around.

ONNX Runtime has no equivalent problem. Its iOS pods track the framework release for release, and `onnxruntime-mobile-c` is dead (stable stops at 1.18.0) because Microsoft folded mobile into the main package. The cost is a higher OS floor.

### 2.2 Flutter bindings

| Package | Publisher | Latest | Likes | Pub pts | DL/30d | Verdict |
|---|---|---|---|---|---|---|
| `tflite_flutter` | **tensorflow.org** (verified) | 0.12.1, **2025-10-28** | 901 | 140/160 | 58,868 | Google badge, stale runtime. See below |
| `flutter_litert` | hugo.ml (verified) | 3.8.0, **2026-08-06** | 23 | 160/160 | 6,285 | The living successor |
| `tflite_flutter_helper` | tensorflow.org | 0.3.1, **2021-12-22** | 80 | 120 | 170 | Dead since 2021, never replaced |
| `flutter_onnxruntime` | masic.ai (verified) | 1.8.3, **2026-07-19** | 48 | 150/160 | 10,864 | The live ONNX one. **Not Microsoft** |
| `onnxruntime` (gtbluesky) | **unverified uploader** | 1.4.1, **2024-03-27** | 73 | 150/160 | 13,299 | Dead. High downloads are legacy inertia |
| `fonnx` (Telosnex) | not on pub.dev | - | - | - | - | **GPL-2.0. Hard blocker** |

All pub.dev figures **VERIFIED** via the pub.dev API on 2026-08-07.

**`tflite_flutter` is the trap.** It carries the `tensorflow.org` verified-publisher badge and 901 likes, which makes it look like the safe institutional choice. **VERIFIED:** its GitHub repo `tensorflow/flutter-tflite` has **108 open issues** and was **last pushed 2025-10-28** - nine months before this note. There is an open issue literally titled *"is this repo dead? last commit 9 months ago"* (opened 2026-06-09). And **VERIFIED from the podspec on `main`**, its iOS side pins:

```
tflite_version = '2.12.0'
s.dependency 'TensorFlowLiteSwift', tflite_version
```

`TensorFlowLiteSwift` **2.12.0 was released 2023-04-15**. Meanwhile the October 2025 commit that produced 0.12.1 migrated the **Android** side to LiteRT 1.4.0. **INFERRED:** the plugin now runs a 2025 LiteRT on Android and a 2023 TFLite on iOS - a genuine cross-platform version skew that will produce different op support per platform, which is exactly the class of bug that is expensive to find. The podspec's `homepage` is still `http://example.com` and its author is still `Your Company`.

Open iOS issues on that tracker, **VERIFIED** as issue titles: *"useMetalDelegateForIOS = true results in Interpreter not being able to load"* (2025-07-18, open), *"Inference bottlenecking GPU in Flutter 3.35.7 on iOS 26"* (2026-01-30, open), *"In release mode the android version is working but iOS version is not working"*, *"No podspec found for flutter_tflite"*. **ANECDOTAL**, but consistently pointing at iOS.

**`flutter_litert` is the living alternative, with a caveat you must decide about.** Apache-2.0, 84 versions since 2026-02-11, source-compatible with `tflite_flutter`'s `Interpreter` API, and it is the only binding that ships current iOS runtimes plus LiteRT Next plus actual pre/post-processing primitives (`bounding_box.dart`, `landmark_mixin.dart`, `ssd_anchors.dart`, letterbox coordinate mapping, isolate interpreters, interpreter pooling). **The caveat, VERIFIED from its podspec:** because Google publishes no current iOS binaries, the maintainer builds them himself in GitHub Actions and the podspec **curls a zip from a personal GitHub release at `pod install` time**. Apache-2.0 makes that legal; it is a supply-chain and reproducible-build decision, not a legal one, and it needs a vendoring plan before anything ships commercially. Adoption is 23 likes and 16 GitHub stars - **effectively a single-maintainer dependency**, mitigated only by the permissive licence letting you fork.

**On the ONNX side, `flutter_onnxruntime` (masic.ai, MIT, 61 stars, 3 open issues, last push 2026-07-19) is the one to use.** **VERIFIED** that its iOS EP selection is real rather than aspirational: `OrtProvider` exposes `CORE_ML`, `XNNPACK`, `NNAPI`, `QNN`, and `CoreML`/`XNNPACK` are wired in the Swift plugin. Its podspec pins `onnxruntime-objc 1.23.0` with the comment *"last ORT without the KleidiAI conv memory regression of 1.24.x (microsoft/onnxruntime#29538)"* - **VERIFIED** that issue #29538, *"Large CPU memory regression starting in 1.24 for fully-convolutional models with dynamic input shapes"*, was opened 2026-07-03 and is still open. A pose model is a fully-convolutional model with (often) dynamic input shape, so that regression is directly on our path. The pin is good maintenance and a warning about ORT at the same time.

**`fonnx` is a hard no.** **VERIFIED:** the LICENSE at Telosnex/fonnx is the verbatim **GNU GPL v2**, with no linking exception, and the package is not published on pub.dev. Statically linked into a closed-source app it would require releasing the app's source. Easy to avoid, but it has 296 stars and shows up in searches.

### 2.3 iOS acceleration, and why it matters less for us than usual

| | LiteRT | ONNX Runtime |
|---|---|---|
| ANE | Core ML delegate, **still labelled experimental since 2.4.0**, **24 ops, float only** | Core ML EP; `MLProgram` format (iOS 15+) covers **40+ ops** incl. ConvTranspose, LayerNormalization, GridSample |
| GPU | Metal delegate (shipped; see the open Flutter issues above) | No Metal EP for iOS; Core ML EP may route to GPU |
| CPU SIMD | XNNPACK built in | XNNPACK EP, but needs manual thread tuning (it keeps its own threadpool) |
| Quantised + accelerator | **Core ML delegate rejects quantised models** | XNNPACK EP has QLinearConv etc. int8 is first-class |
| Fallback observability | None documented | **`ProfileComputePlan`** logs per-op hardware dispatch |

All **VERIFIED** from [LiteRT Core ML delegate docs](https://developers.google.com/edge/litert/ios/coreml) and the [ONNX Runtime Core ML EP](https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html) and [XNNPACK EP](https://onnxruntime.ai/docs/execution-providers/Xnnpack-ExecutionProvider.html) docs.

**INFERRED for pose specifically:** heatmap-style pose models (Conv2D, DepthwiseConv2D, TransposeConv, ResizeBilinear, Add, Relu6) map onto LiteRT's 24-op Core ML list reasonably well. But SimCC and regression heads use `ArgMax`, `Gather`, `TopK`, `Slice`, `Transpose`, `MatMul` - none of which appear on that list. Each unsupported op partitions the graph and costs a CPU-to-ANE round trip. Expect to bake the decode out of the graph and do it yourself.

**And a specific accuracy warning that matters more here than throughput.** `flutter_litert`'s README publishes iPhone 15 Pro measurements: strict `{npu}` placement runs the full graph on the ANE for **1 of 29 models**; mixed `{npu, cpu}` runs 24 of 29 but only **12 match a CPU reference on accuracy**. The stated cause is that Core ML hardware runs **fp16** - roughly three decimal digits of mantissa - while pose graphs emit **pixel-space coordinates**, so mantissa loss shows up directly as keypoint jitter, and `CoreMlDelegateOptions` exposes **no precision control**. **VERIFIED** as statements in that README; the measurements themselves are **ANECDOTAL** (one maintainer, one device). **INFERRED, and it is the honest read: the ANE is not a reliable target for a pose model through LiteRT today.** Plan Metal-GPU or XNNPACK-CPU as the shipping path and treat ANE as an opportunistic optimisation you A/B against a CPU reference.

**How much of this matters to us?** Less than to a video app, and this is section 0 point 1 doing real work. We score stills on demand. A 25 ms model and a 60 ms model are indistinguishable to a user tapping a shutter button. **INFERRED:** on this route the acceleration question is mostly not a latency question at all - it is a **determinism** question. An fp16 ANE path that produces different keypoints from the CPU path, and that Core ML may silently switch between compute units (Apple exposes no ANE-only mode), is exactly the non-deterministic behaviour section 0 point 2 says is fatal. **The prototype should pin a single compute path and verify bit-stability across runs before it measures anything else.**

### 2.4 iOS binary size and minimum version

Measured by downloading the official archives and inspecting the `ios-arm64` device slice. **VERIFIED (measurement).**

| Artifact | Download | arm64 device slice |
|---|---|---|
| `TensorFlowLiteC-2.17.0.tar.gz` | 76.5 MB | `TensorFlowLiteC` **22.3 MB**, `...Metal` **19.3 MB**, `...CoreML` **15.1 MB** |
| `pod-archive-onnxruntime-c-1.28.0.zip` | 54.7 MB | `onnxruntime` **42.8 MB** |

**These are not app-size deltas.** **VERIFIED:** `file` reports the ONNX artifact as a normal `ar` archive of many objects, so dead-stripping works at object granularity; the TFLite artifact is a **single pre-linked Mach-O object**, and the copy checked did not carry `SUBSECTIONS_VIA_SYMBOLS`, which limits how much `-dead_strip` can remove. **INFERRED:** budget **3-6 MB** for the TFLite core plus a few MB each for Metal and Core ML delegates - and note that `tflite_flutter`'s podspec re-adds **both** delegate subspecs unconditionally, so a naive integration links all three. For ORT, a `--minimal_build extended` plus `--include_ops_by_config` build for one fixed model should land around **1.5-4 MB**, at the cost of a CI job and of converting the model to ORT format, which breaks the "just drop in a new `.onnx`" workflow.

**One thing to avoid outright:** the Select-TF-ops / Flex delegate. The community-built `TensorFlowLiteFlex` xcframework measures **474 MB compressed**. If a converted pose model needs Select TF ops on iOS, the size story collapses. **Verify op coverage before committing to a model.**

Google publishes **no iOS binary-size figures at all** - its [reduce binary size doc](https://developers.google.com/edge/litert/build/reduce_binary_size) gives Android numbers only. Microsoft publishes no MB figures for custom ORT builds. **VERIFIED absences.** **Practical instruction: build a hello-world Flutter app, then the same app with the runtime linked, and read the App Store Connect App Thinning Size Report. That takes an afternoon and it is the only number that matters.**

Minimum iOS, **VERIFIED from podspecs**: `TensorFlowLiteC` 2.17.0 is **12.0**; `flutter_litert` declares **13.0**; `onnxruntime-c` 1.28.0 is **15.1** and `flutter_onnxruntime` bumps to **16.0**. **ORT costs a materially higher floor.** Compare with Apple Vision at 14.0 for 2D.

### 2.5 Which models are actually available and licensable

This is where the route is decided. Weights licences are separate from code licences and are frequently the blocker.

| Model | Weights licence | Closed-source commercial? | Mobile-ready | Keypoints | z |
|---|---|---|---|---|---|
| **MoveNet Lightning / Thunder** | **Apache 2.0** (verbatim on the model card) | **Yes, cleanly** | **Yes**, official TFLite | COCO-17 | No |
| **MoveNet MultiPose** | Apache 2.0 via the Kaggle collection page; the card itself is silent | Yes | Yes, TFLite | COCO-17 x6 | No |
| **BlazePose lite/full/heavy** | **Apache 2.0** (verbatim on the GHUM model card) | **Yes, cleanly** | **Yes**, TFLite | 33 | **Yes, up to scale** |
| **RTMPose (COCO ckpt)** | Code Apache 2.0; **checkpoints carry no explicit grant** | Probably, with legal review | Yes, ONNX/ncnn | 17 / **26** / 133 | No |
| **RTMW (Cocktail14)** | Trained on InterHand2.6M, whose LICENSE is **CC-BY-NC 4.0** | **Avoid** | No mobile numbers | 133 | No |
| **YOLOv8 / YOLO11 / YOLO26-pose** | **AGPL-3.0, weights included** | **No**, without a quote-only Enterprise deal | Yes | COCO-17 | No |
| **YOLO-NAS-Pose** | Bespoke: "may not use the Software for any commercial use" | **No. No paid tier exists** | n/a | COCO-17 | No |
| **ViTPose / ViTPose++** | **Apache 2.0** | Yes | **No** - ViT-scale, no published latency | COCO-17 | No |
| **Sapiens / Sapiens2** | **CC-BY-NC 4.0** (v1 verified; v2 unresolved) | **No** | **No** - 0.4B-5B params | 17 / 133 / 308 | No |
| **MotionBERT / MotionAGFormer** (2D-to-3D lifters) | Code Apache 2.0; checkpoints trained on H36M (academic-only) | Code yes, **checkpoints risky** | Plausible but needs a 243-frame window | H36M-17 | Yes |
| **HMR2.0 / TokenHMR / SMPLer-X / NLF** | Blocked by SMPL non-commercial and/or their own NC terms | **No** | No | SMPL(-X) | Yes |

Three licence findings deserve to be stated rather than buried in a table:

**Ultralytics AGPL-3.0 is the trap most 2026 evaluations walk into**, because YOLO11-pose is the accuracy leader and everyone reaches for it first. **VERIFIED verbatim from [ultralytics.com/license](https://www.ultralytics.com/license):** "All Ultralytics YOLO trained models fall under the AGPL-3.0 License by default", and it applies "even if you: Train your own model from scratch / Do not use pretrained weights". Their page also states AGPL-3.0 requires publicly releasing "the complete corresponding source code for the entire derivative work, including the larger application, modifications, scripts, configuration files, and, where applicable, model weights." **Enterprise pricing is quote-only and unpublished** - the $29/seat figure that circulates is HUB Pro, a different product.

**And the contamination is transitive, which I verified concretely.** The `pose_detection` package (publisher hugo.ml, 3.6.0, declared **Apache-2.0**) is the most attractive turnkey option on this route - it is the only pose package with a `detect()` that takes image bytes rather than a camera stream, which is exactly our shape. I downloaded the published archive from pub.dev. **VERIFIED:** it ships

```
assets/models/yolov8n_float32.tflite     12,865,523 bytes
assets/models/pose_landmark_lite.tflite   2,818,390 bytes
assets/models/pose_landmark_full.tflite   6,438,874 bytes
assets/models/pose_landmark_heavy.tflite 27,704,918 bytes
```

The package LICENSE is Apache-2.0 and the README mentions "YOLOv8n for person detection" while saying **nothing about Ultralytics or AGPL anywhere** - grep for "licen", "agpl" or "ultralytics" returns only the Apache badge. **A package declaring Apache-2.0 does not make bundled Ultralytics weights Apache-2.0.** The BlazePose landmark stage alone is clean; only the YOLO detector stage is contaminated. **INFERRED, and it is the useful part:** for a single-subject bodybuilding photograph you may be able to drop the person detector entirely and run the landmark model on the whole frame, or substitute any Apache-2.0 detector, which resolves the problem.

**RTMPose's checkpoints are legally unresolved, not permissive.** **VERIFIED:** MMPose code is plain Apache 2.0. **VERIFIED by absence:** the RTMPose project README contains **zero occurrences of "licence", "license" or "commercial"** - the released checkpoints carry no grant of their own. GitHub issue #2393 asked exactly this in May 2023 and was **closed without a substantive maintainer answer**. Provenance is the real risk: COCO-only checkpoints are lowest risk; AIC+COCO and Body8 add datasets with research-oriented terms; Human-Art's access form grants use "for non-commercial purposes"; and **RTMW / Cocktail14 checkpoints include InterHand2.6M, whose LICENSE file is verbatim CC-BY-NC 4.0**. Whether a dataset's non-commercial term propagates to weights trained on it is legally unsettled - note that Ultralytics asserts the strong version of that doctrine for its own models, which cuts both ways. **The defensible engineering position is: prefer COCO-only checkpoints, or retrain the architecture on cleared data - which Apache-2.0 code makes legitimate, and which is RTMPose's real advantage over Ultralytics.**

### 2.6 The keypoint-set argument, which is the strongest reason to consider this route at all

**VERIFIED: COCO-17 contains no torso, spine, pelvis or neck point.** Its 17 are nose, two eyes, two ears, two shoulders, two elbows, two wrists, two hips, two knees, two ankles. That means MoveNet, YOLO-pose, ViTPose and RTMPose-COCO all describe the entire trunk as a line between two synthesised midpoints, and a synthesised midpoint is noisier than either parent joint because the two shoulder errors compound.

For bodybuilding this bites hardest exactly where it matters. Lat spread, abdominal-and-thigh and side chest are judged on torso shape and the relationship between shoulder girdle and waist. A single shoulder-midpoint-to-hip-midpoint line cannot represent that.

**RTMPose is the only mainstream family shipping Halpe-26 weights**, and Halpe-26 adds an explicit **Neck** and an explicit **Hip (pelvis centre)** plus six foot points - giving a *measured* trunk axis rather than a derived one. **VERIFIED** from the MMPose model zoo. Model sizes run 3.51M to 50M parameters. **INFERRED:** if torso geometry is a scoring requirement - and for five of the eight mandatories it is - this is the single strongest technical argument for the raw-model route over any packaged engine. Note that Halpe-26 still has no *spine* point, so true spinal curvature is out of reach for every 2D option here, Apple Vision 3D's `spine` joint included in the comparison only because it is one of the few that has one.

RTMPose also has **the best-documented mobile latency of any family.** **VERIFIED** from the RTMPose README, ncnn-FP16 on a Snapdragon 865, COCO-17 at 256x192:

| Model | AP (COCO) | Params | ncnn-FP16 SD865 |
|---|---|---|---|
| RTMPose-t | 68.5 | 3.34 M | **9.02 ms** |
| RTMPose-s | 72.2 | 5.47 M | **13.89 ms** |
| RTMPose-m | 75.8 | 13.59 M | **26.44 ms** |
| RTMPose-l | 76.5 | 27.66 M | **45.37 ms** |

**CRITICAL CAVEAT, and it is exactly the trap section 0 point 1 warns about:** RTMPose is **top-down**, so these are pose-model-only numbers that assume a person detector already ran. Real single-image cost is detector plus pose. **INFERRED:** budget roughly 2x the table for a one-shot still, where you cannot amortise the detector across frames the way a video app does.

By contrast, **Google publishes no phone latency for MoveNet at all** - the only latency table on the model card is TF.js/WebGL on desktop GPUs (17-64 ms). **VERIFIED absence.** Any "MoveNet at X FPS on a Pixel" figure in circulation is third-party.

### 2.7 Back and side views on this route

Same answer as everywhere else, with one model-specific finding that is sharper than anything in the companion note.

**VERIFIED by absence, checked across every model card and README:** MoveNet, BlazePose, RTMPose, ViTPose and Ultralytics all report accuracy or fairness broken down by gender, age, skin tone or geography. **None of them ever reports it by viewpoint.** COCO mAP aggregates over all camera angles, so a model can be badly broken on the rear-view tail and lose almost nothing on its headline number. That is why the published leaderboard is nearly uninformative for us.

**The one hard, model-specific finding: BlazePose is architecturally predicated on a visible face.** From the BlazePose paper, section 2.2, verbatim:

> "We observed that in many cases, the strongest signal to the neural network about the position of the torso is the person's face [...] we make the strong, yet for AR applications valid, **assumption that the head of the person should always be visible** for our single-person use case. As a consequence, **we use a fast on-device face detector as a proxy for a person detector**."

And the BlazePose GHUM model card independently lists **"Head is not visible"** as an out-of-scope application. **Both VERIFIED.**

**INFERRED, high confidence, from two verified primary statements:** BlazePose is structurally the weakest mainstream option for rear-facing subjects. In video tracking mode it can coast on the previous frame's region of interest, so a subject who turns around mid-clip may keep tracking - but **we do not have a previous frame.** We hand it one still image of an athlete facing away, which is precisely the acquisition case its detector was designed not to handle. This applies equally to MediaPipe PoseLandmarker and ML Kit in the companion note, and to `pose_detection` on pub.dev, all of which are BlazePose. It is the single most consequential piece of evidence in this note after section 0b.

Two further notes on determinism specific to this route:

- **VERIFIED (mechanism):** the flip test does **not** resolve chirality. It assumes the left/right mapping via `flip_indices` and applies it, then averages. If the model is genuinely bimodal on a rear view, averaging a correct and a mirrored heatmap produces a keypoint set wrong in a third way.
- **VERIFIED by absence:** GitHub issue evidence for *body* left/right swapping is essentially absent - searches surface MediaPipe *hand* handedness instead. **INFERRED:** that most likely reflects silent failure rather than correctness. Nobody notices a mirrored skeleton on a back view because there is no visual cue that it is wrong, and because almost nobody is scoring rear views.

**A measurable path exists, and it is cheap.** COCO-MEBOW publishes a test split of 5,536 instances with 5-degree orientation labels. Running a candidate engine over that split and reporting keypoint accuracy and left/right swap rate **as a function of body orientation** would be genuinely novel data, and it is days of work rather than weeks. **This is the highest-value experiment in the whole evaluation and it does not require a single real capture.**

### 2.8 What you actually build yourself

Every binding on both routes gives you approximately one thing: hand a typed buffer in, get typed buffers out. `tflite_flutter_helper`, which supplied `ImageProcessor`, `ResizeOp`, `NormalizeOp` and `TensorImage`, has been **discontinued since 2021-12-22 and was never replaced**; the request to fold it back in (flutter-tflite #171) has sat open since 2023. **VERIFIED.** `flutter_onnxruntime` additionally **cannot introspect model input/output shapes on iOS** (its README lists "Input/Output Info" and "Model Metadata" as unsupported on iOS/Swift), so you hardcode them.

The work you own:

1. **Image to tensor.** Colour conversion, rotation, front-camera mirror. In pure Dart this is a per-pixel loop over ~2M pixels.
2. **Letterbox, resize, normalise**, and record the scale and offset so you can invert it on the keypoints. Off-by-one in the inverse map is the classic "keypoints are subtly offset" bug.
3. **Layout.** TFLite is NHWC, ONNX pose models are almost always NCHW. Bake the transpose into the graph at export; do not do it in Dart.
4. **Decode.** Heatmap argmax plus sub-pixel refinement (quarter-offset or DARK), or SimCC's two 1-D argmaxes, or bottom-up grouping plus NMS. Single-person top-down is far cheaper to build.
5. **Coordinate inversion** back through letterbox, rotation, mirror and `BoxFit`.
6. **Quantisation choice**, which interacts badly with acceleration: LiteRT's Core ML delegate is **float only**, so quantising forecloses the ANE entirely, while ORT's XNNPACK EP has QLinear kernels and treats int8 as a first-class CPU path.

**Here is where our workload changes the estimate substantially.** A published effort estimate for this route, camera-to-overlay at 30 fps, production quality, single-person, iOS and Android, is **4-8 weeks of one engineer**, dominated by the live frame pipeline and the threading/backpressure work. **INFERRED, and I think this is right: items 1, 5 and the entire threading and temporal-smoothing burden mostly evaporate for us.** We score a still image the user has already framed. There is no 30 fps budget, no backpressure, no dropped-frame policy, no One-Euro filter, and the image can be decoded and resized once on a background isolate with no real-time constraint. What remains is items 2, 3, 4 and 6 - genuinely a few weeks, not a quarter.

The counter-evidence on ecosystem thinness is real, though. **VERIFIED:** a GitHub repository search for `flutter pose estimation tflite` returns **five repositories in total**, with 1, 3, 8, 1 and 9 stars, most recent push 2024-04-19 and three of the five last touched in 2020-2021. For a framework as popular as Flutter, that is a damning signal: almost nobody has shipped this and written it up. The only credible worked example is hugocornellier's own `flutter_litert` plus `pose_detection` stack - **and that it depends on `opencv_dart` is itself evidence for item 1**: the one person who has actually built this concluded you cannot do the frame pipeline in Dart.



## 3. The rest of the 2026 field

The ticket asks for "anything else current that a serious 2026 evaluation should not miss". I went looking for engines that have emerged recently rather than only re-checking the well-known names. The most useful results in this section are negative: several names that appear in every comparison table are not options at all.

### 3.1 Commercial SDKs, with pricing where it exists

| Vendor | Publishes price | Free tier | On-device | Flutter | Verdict |
|---|---|---|---|---|---|
| QuickPose.ai | Partly | 100 devices/mo; 100 img/mo API | SDK yes, JointTrack no | No | Wraps MediaPipe |
| Sency AI | **Yes, full table** | 100 MAU trial | Yes | **Yes, first-party** | Proprietary, per-MAU, video-oriented |
| Vay / VAY Sports | No | No | Unknown | No | Ownership chain in bankruptcy |
| Kemtai | No | No | Browser | No | Web-only |
| Exer AI | No | No | Unknown | No | Clinical vertical, not a component vendor |
| Kaia Health | No | No | n/a | No | Not a vendor |
| Asensei | No | No | Unknown | No | Partner-only, opaque |
| Tempo | Yes (consumer) | No | Hardware | No | Not a vendor |
| **Physimax** | n/a | n/a | n/a | n/a | **Defunct** |
| Move.ai / Theia | No | No | Cloud / camera rig | No | Wrong product |
| Plask | Yes | 15 s/day | Cloud | No | Wrong billing unit |
| DeepMotion | Credits | 60 s/mo, non-commercial | Cloud | No | Free tier is non-commercial |
| **wrnch** | n/a | n/a | n/a | n/a | **Absorbed into Hinge Health, 2021** |
| pose.dev | No | No | Yes | No | Scoring layer, not a detector |

Three names that appear in most published comparisons are **not available in 2026**:

- **Physimax is dead.** **VERIFIED:** physimax.com is a domain-sale listing on Spaceship ("Buy now $3,000").
- **wrnch / wrnchAI was acquired by Hinge Health in September 2021** and absorbed into their internal stack. **VERIFIED** from the [Hinge Health press release](https://www.hingehealth.com/resources/press-releases/hinge-health-acquires-the-most-advanced-computer-vision-technology/). **INFERRED:** there is no public developer portal, SDK download or pricing in 2026. Treat as unavailable.
- **Vay** went Nautilus (Sept 2021) to BowFlex (Nov 2023) to Chapter 11 (March 2024), assets to Johnson Health Tech. **ANECDOTAL** on the acquisition chain (secondary sources); **VERIFIED by absence** that vay.ai publishes no pricing, no mobile SDK docs and no Flutter path.

Of the survivors, two matter:

**QuickPose.ai** wraps MediaPipe. **VERIFIED** from its own [iOS SDK README](https://github.com/quickpose/quickpose-ios-sdk), which states the SDK "leverages MediaPipe and BlazePose" and offers MediaPipe lite/standard/full/heavy variants; the [Android SDK](https://github.com/quickpose/quickpose-android-sdk) depends on ONNX Runtime. Its published comparisons against MediaPipe are therefore **marketing about its own feature layer, not about a different model**, and are not cited here as fact. No Flutter plugin exists. QuickPose also sells a per-image cloud "JointTrack API" at roughly **$0.025-$0.10 per image** across its tiers - **ANECDOTAL**, from search snippets only, because quickpose.ai was blocked by the network proxy during this research and should be re-verified. What QuickPose sells that we could not build is rep counting and range-of-motion tracking, both irrelevant to static bodybuilding poses.

**Sency AI** is the only vendor with a first-party Flutter plugin - `flutter_smkit` v1.1.3 and `flutter_smkit_ui` v1.5.3, both live on pub.dev with 0 and 2 likes respectively. **VERIFIED** from the [smkit-sdk README](https://github.com/sency-ai/smkit-sdk). Its licence is proprietary: the repo LICENSE grants a "fully revocable, limited license" and states "ANY COMMERCIAL OR PRODUCTION USE ... SHALL BE GOVERNED BY A SEPARATE PAID ENTERPRISE/PERSONAL SERVICE AGREEMENT". **VERIFIED** pricing from [sency.ai/pricing](https://www.sency.ai/pricing): $99.99/month for up to 100 MAU, $499 to 500 MAU, $5,500 to 10,000 MAU, negotiated below ~$0.10/user above that.

**The structural point (INFERRED, but it holds across every vendor examined):** they all price for *continuous video coaching* - per monthly active user, per device-month, or per second of video. Our unit is roughly eight still images per athlete per submission. Sency's $99.99/month floor is real money before a single paying customer exists, and it buys a per-MAU licence for a workload that is per-image. The economics are backwards, and the product on offer (rep counting, ROM, workout plans) is not the product we need.

**One genuinely new entrant worth naming, `pose.dev`.** **VERIFIED** from [pose.dev](https://pose.dev/): a "Movement Intelligence Engine for Fitness Apps" that is deliberately **detector-agnostic** - it consumes normalised landmarks from "MediaPipe, MoveNet, Apple Vision, YOLO pose, custom ML, prerecorded video, or raw landmark streams" and layers scoring on top. Rust core, bindings for iOS, Android, web, React and React Native, **no Flutter binding**, no published pricing. As a vendor it adds nothing here. **As an architecture it is exactly the shape this app should take**: the detector is a swappable front end, the scoring is our own domain layer. That framing is worth adopting whatever engine wins, because it is what keeps the engine decision reversible.

### 3.2 Platform APIs beyond ML Kit and Vision

- **Apple publishes no pose Core ML model.** **VERIFIED** against the full [Apple Core ML model gallery](https://developer.apple.com/machine-learning/models/): FastViT, MobileNetV2, ResNet-50, MNIST, DeepLabv3, DETR-ResNet50, Depth Anything V2, YOLOv3, an updatable drawing classifier, BERT-SQuAD. Apple's pose story is entirely the Vision framework. But note **Depth Anything V2 is there** - see 3.4.
- **Create ML Action Classifier is video-only.** **VERIFIED** from [Apple's docs](https://developer.apple.com/documentation/createml/creating-an-action-classifier-model): it needs at least 50 example videos per action and classifies a *temporal* window of Vision landmarks. Dead end for single frames. **INFERRED, and worth naming because evaluations usually miss it:** the correct Apple analogue for still images is a plain Create ML classifier trained over the Vision landmark vector - detect landmarks with Vision, then train a small model on the 2D or 3D joint coordinates. That is cheap, fully offline and closed-source-friendly, and it is a scoring option rather than a detection option.
- **Qualcomm AI Hub** ships a ready-optimised MediaPipe-Pose-Estimation model (256x256 input, 3.14 MB detector plus 12.9 MB landmark model) under **Apache-2.0**. **VERIFIED** from [aihub.qualcomm.com](https://aihub.qualcomm.com/models/mediapipe_pose). Licence-clean, Snapdragon-only, and it is the same BlazePose weights pre-compiled for Hexagon. **INFERRED:** for an eight-image one-shot workload the latency win is irrelevant.
- **Huawei ML Kit skeleton detection** (14 points, requires HMS Core) - **ANECDOTAL**, developer.huawei.com returned 502 during this research. Irrelevant unless Chinese Android distribution matters.
- **Unity Inference Engine** (ex-Barracuda, ex-Sentis, `com.unity.ai.inference`, ONNX opset 7-15) **cannot be used outside Unity**. **VERIFIED by absence** - there is no standalone library. Embedding Unity-as-a-Library in a Flutter app to run an ONNX model means shipping a game engine. Rule out.

### 3.3 Newer runtimes, 2025-2026

- **ExecuTorch (PyTorch Edge) is now GA but is not a 2026 option for us.** **VERIFIED:** v1.0.0 shipped 2025-10-17 and v1.4.0 was tagged 2026-08-07, with native Objective-C and Swift APIs for Apple platforms ([release notes](https://github.com/pytorch/executorch/releases/tag/v1.0.0)). Also **VERIFIED:** the **MPS backend was deprecated as of v1.2.0**, so the intended iOS path is XNNPACK plus Core ML. And **VERIFIED by absence:** there are **no pose models anywhere in the ExecuTorch release notes** - the project's centre of gravity is LLMs and multimodal - and **no first-party Flutter binding exists**. Choosing ExecuTorch means writing the Dart FFI layer *and* exporting the pose model ourselves. Strictly more work than LiteRT for the same result. Re-check in 12 months.
- **MLX / MLX Swift** (MIT, Apple silicon only, [ml-explore/mlx-swift](https://github.com/ml-explore/mlx-swift)) has a C API so `dart:ffi` is theoretically possible, but there is no pose model, no deployment story and nothing for Android. **VERIFIED by absence** of any Flutter binding. Not a path.
- **Flutter GPU / Impeller cannot run inference.** **VERIFIED:** Flutter GPU is an early-preview, API-unstable package requiring Impeller and the master channel, and is a low-level *rendering* API; compute-shader support is not documented, and the public Impeller docs mention only fragment shaders. Any GPU acceleration must come from the native runtime's delegate. **WebGPU** would require a WebView. Both ruled out.

### 3.4 Depth sensors as an assist, and why LiDAR is a trap

This is worth taking seriously because depth could in principle disambiguate front from back, which is the failure mode section 0b identifies as fatal. It does not work out.

- **`sceneDepth` requires LiDAR.** **VERIFIED** from Apple's [`supportsFrameSemantics(_:)`](https://developer.apple.com/documentation/arkit/arconfiguration/supportsframesemantics(_:)) documentation. LiDAR is rear-facing only and Pro-model only. And ARKit depth is a live-session concept, so it never attaches to a photo from the library.
- **The still-photo depth API is different and better supported:** `AVCapturePhotoOutput.isDepthDataDeliveryEnabled` plus `AVCapturePhoto.depthData` attaches an `AVDepthData` map to a captured photo and embeds it in the saved file. **VERIFIED** from [Capturing photos with depth](https://developer.apple.com/documentation/avfoundation/capturing-photos-with-depth). The rear dual camera gives **relative disparity**; the front TrueDepth camera can give **absolute metres**. You must explicitly select `.builtInDualCamera` or `.builtInTrueDepthCamera` - the defaults do not deliver depth.
- **No API fuses depth with 2D pose.** **VERIFIED by absence** across Vision, ARKit, ML Kit and Apple's Core ML gallery. You would sample the depth map at each 2D landmark yourself and compare, say, shoulder-versus-nose relative depth to decide facing.

**Honest assessment (INFERRED):** a bodybuilder posing for a rear lat spread cannot frame with the front camera, so TrueDepth's absolute depth is unusable for exactly the poses that need it. Rear dual-camera disparity at 2-3 m subject distance is weak. LiDAR restricts us to Pro models. And if references ever come from the photo library there is no depth at all.

Two better options, in order of cost:

1. **Test the free signals first.** BlazePose-class engines already emit per-landmark `visibility` and `presence`, and Apple Vision 2D emits per-joint confidence on `nose`, `leftEye`, `rightEye`, `leftEar`, `rightEar`. A rear-facing subject should drop all of those together. **INFERRED**, and it costs nothing to check on the first captures.
2. **Monocular depth, not a sensor.** Apple publishes **Depth Anything V2 as a Core ML model** in its own gallery (**VERIFIED**, 3.2). It runs on any device, on any image including library imports, with no hardware gate. Same fusion algorithm, none of the device restrictions.

**Recommendation, not a decision: do not gate the product on LiDAR.**

### 3.5 Cloud fallback, briefly: no hyperscaler sells body pose

Included because it is commonly assumed to exist. It does not.

- **AWS Rekognition has no body pose.** **VERIFIED:** `DetectFaces` returns facial landmarks and a `Pose` object that is only the **face's roll, yaw and pitch**. That field name is a trap. Person detection gives bounding boxes only. [Docs](https://docs.aws.amazon.com/rekognition/latest/dg/faces-detect-images.html).
- **Google Cloud Vision has no body pose.** **VERIFIED** from the [pricing page](https://cloud.google.com/vision/pricing) feature list. Its "Landmark Detection" means **famous buildings and places**, not body landmarks - a second naming trap. Most features are $1.50 per 1,000 units.
- **Azure Vision** returns person bounding boxes only, and **Image Analysis 4.0 is deprecated with retirement on 2028-09-25**. **VERIFIED.**
- **Roboflow** supports keypoint detection but its free tier forces data and models open-source on Roboflow Universe (**disqualifying for a closed product**), and the "Commercial Inference model license" is gated behind unpriced Enterprise. **VERIFIED** from [roboflow.com/pricing](https://roboflow.com/pricing).
- **Replicate** bills GPU-seconds, not images (T4 at $0.000225/s). **INFERRED:** roughly $0.002 per image once cold starts are amortised.

**Conclusion:** a cloud fallback is really "self-host the same open model you would have run on-device", so the model choice is the decision and the deployment target is not. For eight images per submission, on-device is free and cloud is $0.002-$0.10 per image **plus** shipping photographs of oiled, minimally-clothed subjects off the device, which is an App Store review, GDPR and storage-liability problem all at once. That privacy argument is a cost argument, not only an ethics one, and it favours on-device independently of price.

### 3.6 Research direction, 2025-2026

Scanned arXiv for recent on-device human pose work. Reporting it mainly so it can be explicitly ruled out:

- The dominant new thread is **WiFi-CSI-based pose estimation** (WiLHPE, RePos, C-MambaPose, TinySense, all 2026). Sensor-free and completely inapplicable to scoring a photograph.
- **Efficiency architectures** continue to appear (LAPX at 2.3M params, PriorFormer at under 2 ms on CPU, eMamba, H2OT). **MoViD** (2026-03-29) is the closest research match to our problem because it is explicitly **view-invariant**, but there is no shipping implementation.
- **Visibility-aware** egocentric pose work is conceptually relevant - occluded keypoints are exactly the rear-facing problem - again with nothing shippable.

**INFERRED, and well supported by the vendor survey above: nothing from the 2025-2026 literature has shipped as a drop-in mobile SDK.** The production landscape in 2026 is still BlazePose, MoveNet and YOLO-pose. Every commercial SDK examined turned out to be wrapping one of them.

---

## 4. Comparison across the ticket's seven dimensions

No winner is declared. This is the evidence laid out so the prototype can be designed against it.

| | Apple Vision 2D | Apple Vision 3D | LiteRT + MoveNet | LiteRT + BlazePose | ONNX RT + RTMPose |
|---|---|---|---|---|---|
| **1. Flutter binding maturity** | One community package, 1 like, ~350 DL/mo, provable defects. Realistic route is a hand-written Swift plugin | Same package; its 3D output has a verified bug | `flutter_litert` (23 likes, single maintainer) or `tflite_flutter` (Google badge, iOS pinned to 2023) | Same, plus `pose_detection` which is still-image-first | `flutter_onnxruntime` (48 likes, MIT, active). Not Microsoft |
| **2. Landmark set** | **19**, incl. `neck` + `root`, plus face points. No mid-torso | **17**, incl. `spine`, `centerShoulder`, `topHead`, `root`. **No face points** | COCO-**17**. No torso, spine, pelvis or neck | **33**, no explicit spine | COCO-17, **Halpe-26** (adds Neck + pelvis + feet), or 133 |
| **3. Depth / 3D** | None | Metres, but **1.8 m reference scale** without a LiDAR capture session | None | `z`, up to scale, non-metric | None (add a lifter, with H36M checkpoint risk) |
| **4. Back / side views** | Undocumented, unmeasured by anyone. Face points survive as a facing cue | Undocumented, unmeasured. **No face points, no confidence, all-17-or-none** | Undocumented. Card is silent on viewpoint | **Detector is architecturally predicated on a visible face** | Undocumented. COCO-trained, so front-peaked |
| **5. iOS specifics** | **~0 bytes**, min iOS 14, no entitlements | ~0 bytes, min iOS 17, **needs a Neural Engine, no Simulator** | ~3-6 MB core + delegates, min iOS 12-13 | Same, plus 3-28 MB of weights | ~1.5-4 MB with a custom build, **min iOS 16** via the plugin |
| **6. Licensing** | Cleanest available. ADPLA never mentions Vision. No weight licence exists | Same | Runtime Apache-2.0, **weights Apache-2.0** | Runtime Apache-2.0, **weights Apache-2.0** | Runtime MIT, code Apache-2.0, **checkpoints have no explicit grant** |
| **7. Single-image latency** | ~40 ms on iPhone 11 (one anecdote); band 10-40 ms | Unpublished; stateful, assume heavier | **No phone numbers published at all** | Pixel 3 CPU numbers exist | Best documented: 9-45 ms ncnn on SD865, **plus a detector** |

Two patterns are worth naming across the whole table.

**Dimension 4 is empty for every column.** Not "weak", empty. No engine in either note has a published per-viewpoint accuracy breakdown, and every published fairness analysis slices by gender, age, skin tone or geography and never by camera angle. Since COCO mAP aggregates over all angles, the headline leaderboard is close to uninformative for a product where five of eight target poses are off-axis. **This is the finding that should shape the prototype.**

**Dimension 6 disqualifies more candidates than dimension 4 or 7.** Ultralytics AGPL, YOLO-NAS-Pose's outright commercial prohibition, Sapiens' CC-BY-NC, SMPL's non-commercial term blocking every monocular mesh regressor, `fonnx`'s GPL-2.0, and RTMPose's unresolved checkpoint provenance all remove otherwise-strong options. Only three things in this note carry an unambiguous grant for a closed-source commercial app: **Apple Vision** (system framework), **MoveNet** (Apache 2.0 on the card), and **BlazePose** (Apache 2.0 on the card).

## 5. Open questions this note could not close

Each of these is a genuine gap, not a search failure. Listed so the prototype ticket can pick them up.

1. **Rear-view keypoint accuracy and left/right swap rate, per engine.** Nobody has measured it. **COCO-MEBOW publishes a 5,536-instance test split with 5-degree orientation labels**, which makes both measurable in days and without a single real capture. This is the highest-value experiment available and it would produce genuinely novel data.
2. **Vision-versus-ML-Kit inter-model landmark bias**, on identical captures. This is the number that decides whether section 1.10's cross-platform objection is fatal or merely expensive. Nobody has published it.
3. **Whether Vision 3D's `bodyHeight` instability reproduces** (forum thread 744794: 5'4" to 10'1" on a static subject with LiDAR). If it does, the 3D request is out.
4. **Whether `VNDetectHumanBodyPoseRequest` and the iOS 18 `DetectHumanBodyPoseRequest` revision2 actually differ** on our captures, given the reported regression on the Swift API for text recognition.
5. **Real iOS app-size delta** for each runtime. Neither Google nor Microsoft publishes iOS figures. Build a hello-world app with and without, read the App Store Connect App Thinning Size Report. An afternoon.
6. **Whether `pose_detection`'s bundled YOLOv8n can be dropped entirely** for single-subject photographs, which would clear its AGPL exposure without replacing the package.
7. **QuickPose's actual pricing** - quickpose.ai was blocked by the network proxy during this research and the tier figures here are from search snippets only.

## 6. What this note does not say

It does not pick an engine. It does not rank them. Three things it *does* assert, because the evidence supports them and a later prototype should not have to rediscover them:

- **Any engine choice must be validated on rear views before anything else**, and validated for *chirality stability* separately from positional accuracy. Those are different failure modes with opposite implications for self-referential scoring.
- **A cross-platform landmark mismatch breaks the premise that makes self-referential scoring forgiving.** Whatever is chosen, references and captures must come from the same model, or the design must store images rather than landmarks.
- **Licensing must be cleared on the weights, not only the code**, and it should be cleared before any prototype effort goes into a model. Several of the technically strongest options are legally unusable and one popular Flutter package ships AGPL weights under an Apache-2.0 badge.


