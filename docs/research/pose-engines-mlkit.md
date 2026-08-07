# Google ML Kit Pose Detection - engine dossier

Companion to [`pose-engines.md`](./pose-engines.md), resolving the ML Kit portion of [issue #3](https://github.com/grez-lucas/poseperfect/issues/3).

**Status:** evidence, not a verdict. This note does not pick an engine. It supplies material for the later prototype ticket.

**Date of research:** 2026-08-07. Every version number, release date and issue count below was read on that date and will rot.

**Convention** (identical to `pose-engines.md`):

- **VERIFIED** - stated in a primary source (official vendor documentation, model card, published paper, package registry metadata, source code). Quoted or closely paraphrased, with a URL.
- **INFERRED** - my reasoning from verified facts. Explicitly not measured by anyone.
- **ANECDOTAL** - developer reports, issue trackers, forum posts. Signal, not measurement.

Section 0 of `pose-engines.md` sets the frame and is honoured throughout: we score **still images**, scoring is **self-referential** (consistent bias cancels, bimodal error does not), and **five of eight mandatories are not front-on**.

---

## 1. What the thing actually is

ML Kit Pose Detection is a thin, closed-source SDK wrapper around **MediaPipe BlazePose GHUM 3D**. The model card Google links from the ML Kit page is literally titled "MediaPipe BlazePose GHUM 3D" - the same model family MediaPipe PoseLandmarker ships. **VERIFIED**: the ML Kit overview's "Under the hood" section links to `pose_model_card.pdf`, whose title page reads `MODEL CARD - MediaPipe BlazePose GHUM 3D`. <https://developers.google.com/static/ml-kit/images/vision/pose-detection/pose_model_card.pdf>

This matters for the evaluation: **ML Kit and MediaPipe PoseLandmarker are not independent candidates.** Evidence about BlazePose's viewpoint behaviour applies to both. What differs is the binding, the packaging, the model variants exposed, and the release cadence.

### Pipeline shape - the load-bearing architectural fact

The BlazePose paper describes a two-stage detector-tracker. The first stage is **a face detector standing in for a person detector**:

> "we make the strong, yet for AR applications valid, assumption that the head of the person should always be visible for our single-person use case. As a consequence, we use a fast on-device face detector [BlazeFace] as a proxy for a person detector. This face detector predicts additional person-specific alignment parameters: the middle point between the person's hips, the size of the circle circumscribing the whole person, and incline (the angle between the lines connecting the two mid-shoulder and mid-hip points)."

**VERIFIED** - Bazarevsky et al., *BlazePose: On-device Real-time Body Pose tracking*, CVPR Workshop on CV4AR/VR 2020, section 2.2. <https://arxiv.org/abs/2006.10204>

The model card's own diagram for TRACKING MODE labels the first box **"Face detector with pose alignment"**. **VERIFIED** - model card p.6.

ML Kit restates the consequence in plain language on its overview page:

> "The user's face must be present in order to detect a pose."

**VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection>

And the model card lists, under **OUT-OF-SCOPE APPLICATIONS**:

> "Head is not visible"

and under **TRADE-OFFS**:

> "The model is optimized for real-time performance on a wide variety of mobile devices, but is **sensitive to face position, scale and orientation in the input image**."

**VERIFIED** - model card pp. 3.

Hold onto these three quotes. Section 4 is where they bite.

---

## 2. Dimension 1 - Flutter binding maturity

### The plugin: `google_mlkit_pose_detection`

All figures read from the pub.dev API and the repo on 2026-08-07.

| Field | Value | Source |
|---|---|---|
| Latest version | **0.15.0** | <https://pub.dev/packages/google_mlkit_pose_detection> |
| Published | **2026-07-07** (1 month ago) | pub.dev API `.versions[].published` |
| Publisher | `flutter-ml.dev` (verified publisher) | pub.dev |
| Pub points | 150 / 160 | pub.dev score API |
| Likes | 79 | pub.dev score API |
| Downloads, 30 days | **18,966** | pub.dev score API |
| Platforms | Android, iOS only | pub.dev tags |
| Licence | **MIT** | pub.dev tag `license:mit`; repo `licenseInfo` |
| SDK constraint | Dart `>=3.8.0 <4.0.0`, Flutter `>=3.32.0` | pubspec of 0.15.0 |
| Dependencies | `google_mlkit_commons: ^0.12.0` | pubspec of 0.15.0 |
| Repo | `flutter-ml/google_ml_kit_flutter`, 1270 stars, 887 forks, not archived, default branch `develop` | `gh repo view` |

**VERIFIED.** It is a community monorepo, not a Google first-party plugin. Google publishes no official Flutter binding for ML Kit.

### Release cadence

| Version | Published |
|---|---|
| 0.15.0 | 2026-07-07 |
| 0.14.1 | 2026-02-03 |
| 0.14.0 | 2025-03-20 |
| 0.13.0 | 2024-10-07 |
| 0.12.1 | 2024-09-19 |
| 0.12.0 | 2024-04-25 |

**VERIFIED.** Note the **10.5-month gap** between 0.14.0 and 0.14.1. Human (non-dependabot) commits to the monorepo also show a **~4.5-month gap** from 2025-09-18 to 2026-02-03. `gh api repos/flutter-ml/google_ml_kit_flutter/commits`

0.15.0 is a substantive release, not a version bump: Android Java to Kotlin, **iOS Objective-C to Swift**, compileSdk 36 for AGP 9, Apple Silicon simulator support on iOS 26+. **VERIFIED** - <https://pub.dev/packages/google_mlkit_pose_detection/changelog>

### Open issues - and why the headline number lies

- **Total open issues across the whole monorepo: 4.** None pose-specific. Oldest is 3 months old. **VERIFIED** - `gh issue list --repo flutter-ml/google_ml_kit_flutter --state open`
- The four are: #888 (Kotlin migration), #875 (iOS SPM migration), #866 (GoogleDataTransport duplicate symbols with Firebase via SPM), #861 (Apple Silicon arm64 simulator build failure, iOS 26+).
- Most recent collaborator response: **2026-08-01** by `fbernaly` on #888. **VERIFIED.**

**But:** of 113 issues closed since 2025-01-01, **75 (66%) carry the `stale` label** - auto-closed by `actions/stale` after 30 days idle plus 14 days warning, not resolved. **VERIFIED** - `gh issue list --state closed --json labels`. **INFERRED:** "4 open issues" is a triage artefact, not a health metric. Read it as "this repo retires bug reports rather than fixing them", which is a materially different signal.

Corroborating: **30 issues have "pose" in the title. All 30 are closed.** **VERIFIED.**

### iOS support status

`packages/google_mlkit_pose_detection/ios/google_mlkit_pose_detection.podspec` on `develop` (identical to the podspec inside the published 0.15.0 archive):

```ruby
s.source_files = 'Classes/**/*.swift'
s.dependency 'GoogleMLKit/PoseDetection', '~> 9.0.0'
s.dependency 'GoogleMLKit/PoseDetectionAccurate', '~> 9.0.0'
s.dependency 'google_mlkit_commons'
s.platform = :ios, '15.5'
s.ios.deployment_target = '15.5'
s.static_framework = true
s.swift_version = '5.0'
s.pod_target_xcconfig = { 'DEFINES_MODULE' => 'YES', 'EXCLUDED_ARCHS[sdk=iphonesimulator*]' => 'i386' }
```

**VERIFIED** - <https://raw.githubusercontent.com/flutter-ml/google_ml_kit_flutter/develop/packages/google_mlkit_pose_detection/ios/google_mlkit_pose_detection.podspec>

iOS is fully supported and actively worked on. Two caveats:

1. **The plugin depends on BOTH pods unconditionally** - `PoseDetection` and `PoseDetectionAccurate`. You pay for both models whether or not you use both. See section 7.
2. **The `master` branch is stale** (pose_detection 0.14.0, pods pinned `~> 7.0.0`). `develop` is the source of truth. **VERIFIED.** Anyone reading the repo casually will read the wrong file.

### The upstream SDK is still beta, and the Android artefact is two years cold

- ML Kit Pose Detection is **still labelled beta**, six years after launch: *"This API is offered in beta, and is not subject to any SLA or deprecation policy. Changes may be made to this API that break backward compatibility."* **VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection/ios>
- iOS pod: `MLKitPoseDetection 1.0.0-beta16`, published **2025-06-24**. **VERIFIED** - CocoaPods trunk API, `https://trunk.cocoapods.org/api/v1/pods/MLKitPoseDetection`. Every other ML Kit iOS component is at a stable major (`MLKitFaceDetection 8.0.0`, umbrella `GoogleMLKit 9.0.0`); pose is one of only three still on a `1.0.0-betaN` line.
- Android artefact: `com.google.mlkit:pose-detection:18.0.0-beta5`, last updated **2024-08-07 - exactly two years ago today**. **VERIFIED** - <https://developers.google.com/ml-kit/release-notes>
- The ML Kit pose overview page's own footer reads **"Last updated 2024-07-10 UTC."** **VERIFIED.**

**INFERRED:** the model itself has not been touched in years. The 2025 iOS pod bumps are rebuild-and-renumber releases riding the umbrella ML Kit train (they land on the same dates as every other component: 2024-09-30, 2025-03-25, 2025-06-24). The Flutter plugin is healthier than the SDK it wraps.

---

## 3. Dimension 2 - Landmark set

**33 landmarks.** **VERIFIED** - <https://developers.google.com/android/reference/com/google/mlkit/vision/pose/PoseLandmark>

| Group | Landmarks |
|---|---|
| Face (11) | `NOSE`, `LEFT_EYE_INNER`, `LEFT_EYE`, `LEFT_EYE_OUTER`, `RIGHT_EYE_INNER`, `RIGHT_EYE`, `RIGHT_EYE_OUTER`, `LEFT_EAR`, `RIGHT_EAR`, `LEFT_MOUTH`, `RIGHT_MOUTH` |
| Arms (4) | `LEFT_SHOULDER`, `RIGHT_SHOULDER`, `LEFT_ELBOW`, `RIGHT_ELBOW` |
| Hands (8) | `LEFT_WRIST`, `RIGHT_WRIST`, `LEFT_PINKY`, `RIGHT_PINKY`, `LEFT_INDEX`, `RIGHT_INDEX`, `LEFT_THUMB`, `RIGHT_THUMB` |
| Legs (6) | `LEFT_HIP`, `RIGHT_HIP`, `LEFT_KNEE`, `RIGHT_KNEE`, `LEFT_ANKLE`, `RIGHT_ANKLE` |
| Feet (4) | `LEFT_HEEL`, `RIGHT_HEEL`, `LEFT_FOOT_INDEX`, `RIGHT_FOOT_INDEX` |

Every joint the ticket asks for is present: shoulders, elbows, wrists, hips, knees, ankles. **VERIFIED.**

**Anatomically relevant gaps for bodybuilding**, all **VERIFIED** by absence from the constant list:

- **No spine, no pelvis, no neck, no head-top.** Torso is a four-point quadrilateral (two shoulders, two hips). Lat spread, abdominal-and-thigh and the whole class of *torso shape* judging criteria are simply not represented in the landmark set. You get a wireframe of limb positions, not a silhouette.
- **No hand pose beyond three knuckles per hand** (pinky, index, thumb). Enough to estimate hand orientation, not enough to score a fist.
- **11 of 33 landmarks (a third of the budget) are on the face** - and on the three rear mandatories the face is not visible at all. See section 4.

**INFERRED:** for judging *limb geometry* (elbow flexion, arm elevation, stance width, knee angle) the set is adequate. For judging *muscle display* it is not, and no landmark model would be - that is a silhouette/segmentation problem, not a keypoint problem. This is a scope observation for the scoring design, not a knock against ML Kit specifically.

Also **VERIFIED**: *"Pose detection can only detect one person in an image. If two people are in the image, the model will assign landmarks to the person detected with the highest confidence."* Fine for our single-athlete case; means a spotter or mirror reflection in frame is a hazard.

### Per-landmark confidence

`InFrameLikelihood`, range 0.0-1.0: *"a measure that indicates the probability that the landmark is within the image frame."* **VERIFIED** - ML Kit overview.

Note the semantics carefully. ML Kit exposes **in-frame likelihood**, not the model's *visibility* output. The model card distinguishes the two:

> "**Visibility** ... denotes the probability that a keypoint is located within the frame **and not occluded by another bigger body part or another object**."
> "**Presence** ... denotes the probability that a keypoint is located within the frame."

**VERIFIED** - model card p.2.

**INFERRED, and important:** the field ML Kit surfaces corresponds to *presence*, the weaker of the two. **The occlusion signal - the one that would tell you "this wrist is hidden behind the torso, distrust it" - is computed by the model and not exposed by the ML Kit API.** For a subject whose arms occlude the torso in most mandatories, that is the single most useful confidence channel and we do not get it. This is a genuine ML Kit-specific loss relative to raw BlazePose. *(Worth a targeted check in the prototype: read what `InFrameLikelihood` actually returns for a landmark that is in-frame but occluded. If it drops, the mapping is to visibility after all and this concern evaporates.)*

**And then section 4.2 takes even that consolation away:** on a rear-facing subject the *visibility* output is itself broken, confirmed by Google. So the channel ML Kit withholds would not have saved us on the poses where we most need it.

---

## 4. Dimension 4 (taken out of order, because it is the decisive one) - back and side views

### 4.1 The short answer

**Nobody has measured it.** Not Google, not the academic literature, not the plugin's users. There is no published accuracy number for BlazePose or ML Kit on a rear-facing subject - no paper, no model card, no benchmark. The search that established this, and its two coverage gaps, are documented in section 5.5.

Two things exist instead, and together they are more damning than a benchmark would have been:

1. **Primary-source documentation saying the configuration is out of scope** (section 4.2).
2. **A Google engineer confirming an unfixed model bug on exactly this input** (section 4.2.1) - which tells us the model does not fail loudly on a rear view. It fails confidently.

### 4.2 What Google says, in Google's own words

Three independent primary sources, all saying the same thing:

1. ML Kit overview, product documentation:
   > "The user's face must be present in order to detect a pose."

   **VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection>

2. Model card, OUT-OF-SCOPE APPLICATIONS, listed alongside "Multiple people in an image" and "Applications requiring metric accurate depth":
   > "Head is not visible"

   **VERIFIED** - model card p.3.

3. Model card, TRADE-OFFS:
   > "The model is optimized for real-time performance on a wide variety of mobile devices, but is sensitive to face position, scale and orientation in the input image."

   **VERIFIED** - model card p.3.

And the paper explains *why*: the person detector **is** a face detector (section 1 above).

**A note on how far this goes.** "Head is not visible" is not literally the rear-view case - the head *is* visible from behind, it is the **face** that is not. BlazeFace is trained on faces. Whether it fires on the back of a skull is not documented either way. Two readings were consistent with the documentation:

- **Pessimistic:** the detector fails to fire on a back view, `processImage` returns an empty pose, three of the eight mandatories are unscoreable. Complete failure, but *loud* - trivially detected, and honestly the better outcome, because a hard failure cannot silently corrupt a score.
- **Optimistic:** the detector still produces a region of interest, and the landmark network - which the model card says was "trained and evaluated both on visible and hidden points" - emits a full 33-point pose. Degraded, but present.

The evidence in 4.2.1 settles it on the **optimistic branch, which is the dangerous one.**

### 4.2.1 The one piece of hard evidence about rear views, and Google confirmed it is a bug

**MediaPipe issue [#5197](https://github.com/google-ai-edge/mediapipe/issues/5197), "Presence/Visibility Scores Remain at 0.99 even for joints not visible".** Filed 2024-03-06. Labels `type:bug`, `task:pose landmarker`, `stat:awaiting googler`. **Still OPEN**, last activity 2025-05-20. **VERIFIED** via `gh issue view 5197 --repo google-ai-edge/mediapipe`.

The reporter fed a 1080x1920 30 fps single-person video shot **from behind** to PoseLandmarker:

> "The video is taken from behind of a single person which means that nose and eyes should not be visible at all."
> "Since the person is facing away, landmarks like the nose and eyes should have low visibility scores."
> "**All three Pose Landmark models I downloaded (lite, full, and heavy) consistently report high visibility and presence scores for the nose, eyes, and other front-facing joints.**"

The MediaPipe maintainer `kuaashish`, 2024-07-30:

> "Unfortunately, **it appears that this is a bug in our pose detection model.** We need to fix this. For now, we are marking it as a bug and sharing it with our team, but we cannot provide a timeline for the fix."

The reporter's resolution: *"shifted to another pose detection model for visibility."* A second developer asked for an update on 2025-05-20 and got no reply. Two years on, no fix.

**Be precise about what this proves and what it does not.**

It proves, **VERIFIED**, three things:
1. The model **does** produce a full 33-landmark output on a back-to-camera subject. It does not abstain. The pessimistic branch is dead.
2. On that output, **the model's confidence channel is meaningless** - 0.99 visibility and presence for a nose and eyes that are physically behind a skull.
3. **Google knows, has classified it as a model bug, and has not fixed it in two years.** This is not a third-party complaint; it is an owner's admission.

It does **not** prove left/right swapping, and it must not be quoted as if it did. It is about the confidence scores, not the coordinates.

**INFERRED, but this is the important inference in the whole note:** #5197 is exactly the precondition for silent corruption. The failure signature on a rear view is a plausible-looking skeleton carrying maximal confidence. There is no value in any field ML Kit returns that would let scoring code detect that it is looking at a guess. Section 5.3 explains why a guess is what it must be.

**Caveats, stated plainly:** #5197 is filed against MediaPipe PoseLandmarker in `VIDEO` running mode, not ML Kit, and the field involved (`visibility`) is one ML Kit does not expose. Same model weights, different binding. **INFERRED:** the defect is in the weights, so it applies to ML Kit; but nobody has demonstrated it *through* ML Kit. Confirming it there is a prototype task.

**INFERRED:** the prototype's first experiment remains the cheapest one imaginable - feed one real rear-facing capture of the actual athlete to `processImage` and look at what comes back, landmark by landmark, against a human's judgement of where those landmarks actually are. Expect 33 landmarks and high `InFrameLikelihood`. The question is not whether you get an answer; it is whether the answer is the athlete.

### 4.3 What Google measured instead

The model card publishes a real, quantitative fairness evaluation - 1400 images, 100 from each of 14 UN geoscheme subregions, annotated for perceived gender and Fitzpatrick skin tone. Results (PDJ = PCK@0.2):

| Model | Avg PDJ, geography | Range | Avg PDJ, skin tone | Avg PDJ, gender |
|---|---|---|---|---|
| Lite | 93.8 | 90.3-95.4 | 94.2 | 93.9 |
| Full | 96.6 | 94.6-97.8 | 96.3 | 96.7 |
| Heavy | 98.3 | 97.0-99.0 | 98.2 | 98.4 |

**VERIFIED** - model card pp. 7-8.

**The evaluation is stratified by geography, gender and skin tone. It is not stratified by camera viewpoint at all.** The word "view", "angle", "frontal", "rear" and "sagittal" do not appear in the evaluation section. **VERIFIED by absence** across all 8 pages of the model card.

Worse for us, the eval set's *provenance* is stated:

> "All samples are picked from the same source as training samples and are characterized as **smartphone back-facing camera photos** taken in real-world environments."

and, from the training factors section:

> "All dataset images were captured on a diverse set of **back-facing smartphone cameras**." / "All images were captured in a real-world environment ... via an AR (Augmented Reality) application."

**VERIFIED** - model card pp. 5-6. ("Back-facing" here means the phone's rear camera, not a rear view of the subject.)

**INFERRED:** an AR-application capture corpus is, by construction, a corpus of people **facing the phone**. The 98.3% headline number is a front-facing number. It carries no information about our three rear mandatories, and Google never claimed it did.

**And the headline number is not even stable across Google's own publications.** There are two model cards for the same model, both titled "MediaPipe BlazePose GHUM 3D", both reporting the same tracking-mode PDJ evaluation over 1400 images in 14 subregions:

| Card | Date | Lite | Full | Heavy |
|---|---|---|---|---|
| MediaPipe, `storage.googleapis.com` | 2021-04-16 | 87.0 | 91.8 | 94.2 |
| ML Kit, `developers.google.com` | 2021-06-22 | 93.8 | 96.6 | 98.3 |

**VERIFIED** - <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf> p.7 and the ML Kit card p.7. Same metric, same eval-set description, same tracking-only mode, two months apart, **4.1 to 6.8 points apart.** Presumably a model revision between the two dates; neither card says. **INFERRED:** treat any single PDJ figure as indicative at best. Google's own numbers for this model disagree with each other by more than the entire spread they use to argue the model is fair across regions.

Three further caveats on that headline:

- **PDJ@0.2 is a loose criterion.** A keypoint counts as correct if the 2D error is under **20% of torso diameter**. **VERIFIED** - model card p.6. On a 180 cm athlete that is roughly 9-10 cm of slack per joint. 98.3% PDJ does not mean 98.3% precision; it means "almost never catastrophically wrong on frontal AR footage".
- **All published PDJ numbers are TRACKING-MODE numbers.** The model card's Evaluation Modes section describes exactly one mode - "TRACKING MODE: Main mode that takes place most of the time and is based on obtaining a **highly accurate full-body crop from the prediction on the previous frame**" - and states "Detailed evaluation for the **tracking modes** ... is presented in the table below." **VERIFIED** - model card p.6. Tracking mode receives a crop derived from a *known-good previous frame*. Our single still image has no previous frame. **The published accuracy figures are measured under a strictly easier input condition than ours.** This is section 0's point 1 confirmed from the primary source, and it applies to accuracy as well as to latency.

### 4.4 Side views - the one real measurement, and how far it transfers

There is exactly one peer-reviewed study I found that varies camera viewpoint and reports BlazePose separately from its competitors.

**Mundt M, Born Z, Goldacre M, Alderson J. "Estimating Ground Reaction Forces from Two-Dimensional Pose Data: A Biomechanics-Based Comparison of AlphaPose, BlazePose, and OpenPose." *Sensors* 2022, 23(1):78. doi:10.3390/s23010078.** <https://pmc.ncbi.nlm.nih.gov/articles/PMC9823796/>

Setup, **VERIFIED**: 14 female Australian Rules Football players; three Sony HDR-CX700 cameras at 25 fps, 1920x1080, all sagittal to the plane of movement - one at true sagittal, one slightly posterior and one slightly anterior, the outer two panned approximately **30 degrees**. Movements: running, walking, unplanned 45-degree sidestepping, cross-overs, at 4.5-5.5 m/s.

Keypoint detection rate, **VERIFIED**:

| | AlphaPose | OpenPose | **BlazePose** |
|---|---|---|---|
| Overall | 98.4% | 94.5% | **65.2%** |
| True sagittal, faster movements | 90.4-95.9% | 68.7-87.8% | **25.0-38.8%** |
| Stance phase only | 100% | 100% | **99.6%** |

And the authors' own explanation, **VERIFIED** verbatim:

> "All pose estimation models showed the lowest detection rate in the true sagittal view for the faster movements."
> "Another possible reason is that **one side of the body is regularly occluded in this camera view**."
> "the occlusion of limbs and missing depth information in 2D images might result in **confusion between the left and right limbs** as the pose estimation models try to identify bilateral lower limb keypoints."

**Now the honest reading, because this table is easy to abuse.**

What it does **not** show: that BlazePose fails on static side-on poses. The 25-38% figure is for **fast dynamic movement** (a 5 m/s sprint) and includes lead-in and lead-out frames where the athlete is entering and leaving the field of view. On the **stance phase** - the athlete planted and relatively still, the condition closest to a held mandatory - BlazePose scores **99.6%**, statistically level with the other two. Our subject is standing still. Quoting the 25-38% number at a static-pose problem would be dishonest.

What it **does** show, and what transfers:

1. **BlazePose is markedly more viewpoint- and motion-fragile than its peers on identical footage.** 65.2% overall against 98.4% and 94.5% is not a small gap, and it is the same task, same frames, same annotation. Whatever the mechanism, ML Kit's model is the brittle one of the three in this comparison.
2. **A peer-reviewed biomechanics group, independently, names "confusion between the left and right limbs" as the mechanism**, and attributes it to exactly the condition our two side mandatories create: one side of the body occluded by the other. **This is the closest thing to third-party corroboration of section 5.1's hypothesis that exists**, and it is worth stating exactly what it is: a mechanism proposed by domain experts to explain a measured detection collapse, not a direct measurement of laterality error.
3. It is a **side-view** result. It says nothing about rear views, which remain unmeasured by anyone.

**INFERRED:** the two side mandatories are the *less* risky of the five non-frontal poses, because the face is at least partially visible in profile so the detector stage has something to latch onto - but they are not safe, and this study is the reason to test them explicitly rather than assuming frontal results generalise. BlazeFace's paper reports it was trained with rotation augmentation and evaluated on a "rear-facing camera dataset" (meaning the phone's rear camera), but reports no *subject*-orientation breakdown. <https://arxiv.org/abs/1907.05047>

### 4.5 What about the oiled, minimally-clothed, heavily-muscled part

**Not measured by anyone, and not addressable from documentation.** The model card's bias section covers skin tone, gender, geography, and missing limbs/prosthetics. It says nothing about body composition, specular highlights, or minimal clothing. The training corpus is described as "60K images with a single or few people in the scene in common poses and 25K images with a single person in the scene performing fitness exercises" (paper, section 2.4) - fitness, not physique competition. **VERIFIED** by absence.

**INFERRED:** two mechanisms plausibly hurt here and neither is in any dataset described:
- **Oil produces strong specular highlights along muscle bellies**, which a heatmap-supervised network may read as edges. Direction of effect unknown.
- **Extreme hypertrophy changes the shoulder-to-hip ratio** well outside the training distribution, and the model's *alignment* stage explicitly depends on the mid-shoulder-to-mid-hip line and the circumscribing circle (paper, section 2.6). Its stated tolerance is "10% shift and scale (taking body width/height as 100% for corresponding axis)" and "8 degrees roll" (model card p.5). A physique outside the scale prior degrades the crop before the landmark network ever runs.

Say it plainly: **this is a genuine unknown that only real captures resolve.** It is a finding, not a gap.

---

## 5. The determinism question

Section 0 of `pose-engines.md` argues that consistent bias cancels and bimodal error does not. This section hunts specifically for bimodal error.

### 5.1 The mechanism that would produce it

**INFERRED, but mechanistically well-grounded in the primary sources:**

The landmark labels are **anatomical**, not image-relative. ML Kit is explicit:

> "Figure 1 below shows the landmarks looking through the camera at the user, so it's a mirror image. The user's right side appears on the left of the image."

**VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection>

So `LEFT_WRIST` means *the athlete's left wrist*, wherever it lands in the image. Now consider the alignment stage. The pipeline normalises **roll only**: "We estimate rotation as the line L between mid-hip and mid-shoulder points and rotate the image so L is parallel to the y-axis" (paper, section 2.6). **There is no yaw normalisation and no facing-direction input.** The network must infer which side is anatomically left purely from appearance.

For a front view, the face resolves this instantly and unambiguously - which is exactly why the face is in the topology. For a **rear** view, the image-space mapping **inverts**: the athlete's left hand now appears on the *left* of the image rather than the right. The correct answer flips, and the cue that would tell the network to flip it - the face - is gone.

This is a textbook setup for a **bimodal posterior**: two plausible body configurations differing by a mirror, with weak evidence separating them. The failure mode that follows is not "slightly wrong coordinates". It is **the whole skeleton snapping between two labellings**, capture to capture, on the same athlete in the same pose.

**Label this honestly: this is INFERRED, and nobody has reported it happening.** Section 5.5 documents the search that found no such report. What it has going for it is that the mechanism is spelled out in Google's own paper, that Google independently confirms the model behaves incorrectly on rear views (section 4.2.1), and that an independent biomechanics group proposes left/right limb confusion to explain a measured BlazePose collapse on side views (section 4.4). Three converging lines, no direct measurement.

Under self-referential scoring, that is not a bias that cancels. It is a discrete, silent, ~180-degree error in every lateral joint simultaneously, and a naive per-landmark distance metric will score it as a catastrophic pose change when nothing changed. **This is the failure class the ticket names as fatal, and the architecture predicts it on precisely the poses we care most about.**

### 5.2 Left-right swapping is not hypothetical in this stack

It has been reported twice against the Flutter plugin, for a *different* root cause, and never fixed:

| Issue | State | Dates | Substance |
|---|---|---|---|
| [#210](https://github.com/flutter-ml/google_ml_kit_flutter/issues/210) | closed | 2022-03-11 → 2022-04-08 | "Pose Detection does not return correct coordinates in IOS". Reporter `jtmuller5` reopened on 2022-04-12: *"In addition to the landmarks being out of order, the left and right landmarks are reversed on iOS."* Maintainer `fbernaly` replied *"only reopen if you are going to send a PR to fix the issue."* Never fixed. |
| [#703](https://github.com/flutter-ml/google_ml_kit_flutter/issues/703) | closed | 2024-10-17 → 2024-12-01 | **"Pose Detection sides are wrong when using front camera on iOS"** - *"`poses[0].landmarks[PoseLandmarkType.leftWrist]` returns the data of the **right wrist**"*. And crucially: *"Using the back camera is working as expected. Using Android is working as expected. **Native iOS MLKit example is working as expected.**"* Reproducible in the repo's own example app. **Closed by the stale bot with two comments, both from `github-actions`. No human ever replied.** |

**ANECDOTAL** (issue tracker), but corroborated by source inspection: the shipped 0.15.0 iOS plugin source (`ios/Classes/GoogleMlKitPoseDetectionPlugin.swift`) contains **no mirroring, flip, or camera-position handling** - only a static `PoseLandmarkType`-to-index map and a direct `landmark.position.x/y/z` passthrough. The 0.15.0 Objective-C-to-Swift rewrite did not add it. Nothing in the changelog addresses it. **VERIFIED** by reading the published archive, <https://pub.dev/api/archives/google_mlkit_pose_detection-0.15.0.tar.gz>.

**Read this carefully, because it is easy to over-read.** The reporter's own note that the **native iOS ML Kit sample behaves correctly** settles the attribution: this is a *plugin-level* `InputImage` orientation/mirroring bug, not a BlazePose defect. It is **deterministic**: front camera on iOS always swaps. Under self-referential scoring a consistently-swapped capture compared against a consistently-swapped reference would largely cancel - *provided both were shot on the same camera*.

The real hazard is the **mixed** case, and it is a realistic one for this app: athlete shoots the reference on the rear camera (better optics, someone else holding the phone) and the weekly capture on the front camera (alone, using the screen as a mirror). Then the reference and the capture disagree by a full left-right inversion and the score is garbage, with no error raised anywhere. **INFERRED**, and it is a design constraint on capture UX regardless of engine: **pin the camera, or normalise for it explicitly.**

Second-order: nobody has verified whether the 0.15.0 Swift rewrite reintroduced, preserved or fixed this. #703 was filed against the Objective-C implementation. **Unverified for 0.15.0.**

### 5.3 What the model does when it cannot see a landmark

This is the part that turns "degraded on rear views" into "silently wrong on rear views". From the model card's BIAS section:

> "This model was trained and evaluated both on visible and hidden points. For cases where the point location is present but hard to define by a human annotator, **it is annotated with a 'best guess' and default pose**."

**VERIFIED** - model card p.4. The paper's section 2.6 says the same operationally: occlusions are simulated with random filled rectangles during training precisely "to support the prediction of invisible points".

**The model is trained to always answer.** It does not abstain. On an occluded or ambiguous input it regresses toward a *default pose* prior. **INFERRED:** on the three rear mandatories, with arms occluding the torso, the output will be a confident-looking full 33-point skeleton that is partly the athlete and partly a learned average human. Nothing in the ML Kit API distinguishes the two, because - see section 3 - the visibility (occlusion) channel is not surfaced, only in-frame presence.

This is also why the model card's own environment note matters:

> "When degrading the environment light, noise, motion or **face overlapping** conditions one can expect degradation of quality and increase of 'jittering'."

**VERIFIED** - model card p.3. Google names jitter - inter-frame prediction noise - as the expected symptom of a degraded input, and names *face overlapping* as one of the degrading conditions. Jitter across frames on a video is the same phenomenon as run-to-run variation across captures for us.

### 5.4 Is single-image inference deterministic?

**Not documented by ML Kit.** It publishes nothing about whether `processImage` on identical bytes returns identical output. Two pieces of evidence from the same model family, pointing in opposite directions:

**In favour of determinism in single-image mode.** MediaPipe issue [#5253](https://github.com/google-ai-edge/mediapipe/issues/5253), "FaceLandmarker is non-deterministic in VIDEO/LIVE-STREAM mode" (2024-03-22, now closed): *"Consecutive calls to `detect_for_video` return different results for the same image."* Reproduced on 0.10.9 and 0.10.13. The resolution: switch to `RunningMode.IMAGE`, which **returned identical values across 10 iterations**. Root cause is that VIDEO and LIVE_STREAM carry tracking state across calls. **ANECDOTAL**, and it is FaceLandmarker rather than Pose - but the task runner and the previous-frame-ROI propagation are shared, and it maps directly onto ML Kit's `stream` vs `singleImage` split. **INFERRED:** `singleImage` mode is the stateless one and is the right choice for us on determinism grounds as well as correctness grounds.

**Against.** MediaPipe issue [#4981](https://github.com/google-ai-edge/mediapipe/issues/4981), "Mediapipe Holistic Nondeterministic Behaviour" (2023-11-23, closed without root cause). With `static_image_mode=True` - i.e. tracking nominally off - over a 24,000-image folder: *"If I re-run this loop with shuffled data, results are changing. ... In first run, model failed to detect right hand keypoints in 305 images. In the second run, shuffled one, this number becomes 320."* A ~5% swing in the failure set purely from input **ordering**, on supposedly stateless inference. **ANECDOTAL**, Holistic rather than Pose, closed unresolved. Signal, not measurement - but it is the exact shape of the thing we care about.

**INFERRED:** the model is a feed-forward CNN with no sampling step, so bit-identical input through an identical execution path should be deterministic; ML Kit does not document its accelerator selection (CPU/GPU/Neural Engine) and float paths differ between backends, so small numeric drift is plausible. **That is the tolerable kind of error.** The intolerable kind is section 5.1's discrete mirror flip, which **requires no non-determinism in the arithmetic at all** - a hairline difference in the input crop is enough to tip an ambiguous posterior from one mode to the other, and #4981 suggests hairline differences do arise from causes nobody has pinned down.

**This is directly testable and should be the prototype's second experiment:** take one rear-facing capture, perturb it minutely (re-encode, shift by a few pixels, rotate by 2 degrees - all comfortably inside the model's own stated tolerance of 10% shift/scale and 8 degrees roll), run it 20 times, and check whether the left/right assignment is stable. If the labelling flips inside the model's own documented tolerance band, ML Kit is disqualified for the rear mandatories regardless of how good its frontal numbers are.

### 5.5 What the search did not find, and how hard it looked

**No source anywhere - primary or anecdotal - documents the BlazePose model swapping left and right landmarks on a rear or oblique view.** The hypothesis in 5.1 is mine, mechanistically derived from Google's own paper. The nearest independent corroboration is Mundt et al. naming left/right limb confusion as a *proposed mechanism* for a measured side-view detection collapse (section 4.4). **That is the honest state of the evidence and it should not be inflated.**

Search coverage, so the next person does not repeat it:

- Both official model card PDFs read end to end (ML Kit 8 pages, MediaPipe 9), grepped for back / rear / behind / facing / orient / viewpoint / angle / laterality / limitation. Zero hits.
- BlazePose (arXiv 2006.10204), BlazePose GHUM Holistic (arXiv 2206.11678) and BlazeFace (arXiv 1907.05047) extracted in full and grepped for the same terms. **The BlazePose paper never mentions back views, rear views, facing away, or left/right confusion. Not once.**
- `gh search issues` across `google-ai-edge/mediapipe`, `google-ai-edge/mediapipe-samples`, `googlesamples/mlkit` and `flutter-ml/google_ml_kit_flutter` over roughly 20 term sets (left right swap, mirrored landmarks, flipped, back view, facing away, laterality, rear view, person facing away, non-deterministic, same image different results, pose inconsistent, pose unstable, jitter, and variants), plus four global all-of-GitHub searches.
- Handedness-reversal reports do exist in this model family (mediapipe #4724, #4803, #4785, mediapipe-samples #450) but every one is a **hand** model image-mirroring convention issue, not the pose model.

**Two coverage gaps, stated so the conclusion is not overclaimed:**

1. **`issuetracker.google.com` could not be read.** The ML Kit component requires sign-in; pages render as "Sign in". **This is the one channel where a Google-side report of pose laterality failure could exist unseen.**
2. **Stack Overflow could not be fetched** from this environment. Coverage there is indirect, via search-result snippets only, which surfaced nothing beyond the flutter-ml issues in 5.2.

---

## 6. Dimension 3 - the z axis

**ML Kit does not use the phrase "least reliable".** It says something more specific and more useful. Two primary sources:

ML Kit product documentation:

> "The Z Coordinate is an **experimental** value that is calculated for every landmark. It is measured in 'image pixels' like the X and Y coordinates, but **it is not a true 3D value**. The Z axis is perpendicular to the camera and passes between a subject's hips. The origin of the Z axis is approximately the center point between the hips (left/right and front/back relative to the camera). Negative Z values are towards the camera; positive values are away from it. **The Z coordinate does not have an upper or lower bound.**"

**VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection>

Model card, the sharper statement:

> "Z coordinate is measured in 'image pixels' like the X and Y screen coordinates and represents the distance relative to the plane of the subject's hips, which is the origin of the Z axis. ... Z coordinate scale is similar with X, Y scales but has different nature as obtained not via human annotation, by fitting synthetic data (GHUM model) to the 2D annotation. **Note, that Z is not metric but up to scale.**"

**VERIFIED** - model card p.2. That last sentence is the quotable one.

And in OUT-OF-SCOPE APPLICATIONS: **"Applications requiring metric accurate depth."** **VERIFIED** - model card p.3.

Three consequences, all **VERIFIED** from the above:

1. **`z` is not metric.** It is "up to scale" and unbounded. You cannot compute a distance in centimetres from it.
2. **`z` was never annotated by a human.** It is the output of fitting a synthetic articulated body model (GHUM) to 2D annotations. It is a *model's opinion about depth given 2D*, propagated into a second model. The uncertainty is structurally larger than for x and y, and never quantified.
3. **Google's own accuracy evaluation excludes it.** *"The model is providing 3D coordinates, but the screen z-coordinate, as well as world 3D coordinates obtained from synthetic data, so for a fair comparison with human annotations, only 2D screen coordinates are employed."* **VERIFIED** - model card p.6. **Every published accuracy number for this model is a 2D number. `z` has no published accuracy at all.**

**The gap versus MediaPipe.** The model card documents a *second* output tensor that ML Kit does not expose: "33x3 tensor corresponding to 3D world metric scale coordinates (world x, world y, world z)", "measured in meters and normalized to center of subject hips and range from [-1.5, 1.5]" (model card pp. 1-2). **VERIFIED.** These are MediaPipe's world landmarks. **The ML Kit API surfaces only the screen-projected, non-metric `z`.** `PoseLandmark.getPosition3D()` returns the image-pixel triple; there is no world-landmark accessor. **VERIFIED** - <https://developers.google.com/android/reference/com/google/mlkit/vision/pose/PoseLandmark>.

**INFERRED, and this is the crisp statement of the difference the ticket asked for:** the model computes metric world landmarks; ML Kit discards them. Choosing ML Kit over MediaPipe is choosing to throw away the only metric channel the underlying model produces, for the same model at the same inference cost.

**INFERRED, for our use:** under self-referential scoring the non-metric `z` is not worthless. A monotone depth ordering ("is the left elbow in front of the hip plane?") is scale-free and comparable between a reference and a capture under matched framing, which is what map decision 6 gives us. Treat `z` as an ordinal cue, never as a length. Do not build any score term that subtracts two `z` values and calls the result a distance.

---

## 7. Dimensions 5 and 7 - iOS specifics and inference cost

### Binary size

**VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection/ios>:

| SDK | App size impact | Implementation |
|---|---|---|
| `GoogleMLKit/PoseDetection` | **Up to 29.6 MB** | "Assets for base detector are statically linked to your app at build time." |
| `GoogleMLKit/PoseDetectionAccurate` | **Up to 33.2 MB** | "Assets for accurate detector are statically linked to your app at build time." |

Models are **bundled, not downloaded.** No first-run network fetch, no cold-start model download - a real advantage for an offline gym-floor app.

**The number that actually applies to us is larger than either row.** The Flutter plugin's podspec declares **both** pods as unconditional dependencies (section 2). **INFERRED:** the app pays for the union, not the max. The two SDKs share the ML Kit runtime and vision common code, so the union is well below 62.8 MB, but it is above 33.2 MB. Exact figure: **not determinable from documentation; measure it.** A `google_mlkit_pose_detection`-only Flutter app, built for release, thinned, is the measurement - and it should be taken early, because it is cheap and it bounds nothing else in the evaluation.

Cross-check on the model sizes underneath: the model card gives "Lite (3MB size), Full (6MB size) and Heavy (26MB size)". **VERIFIED** - model card p.1. The base-to-accurate delta on iOS is 3.6 MB. **INFERRED:** ML Kit's **base ≈ BlazePose Lite** and **accurate ≈ BlazePose Full**, matching the ~3 MB model delta. Google publishes no mapping. **If that inference holds, ML Kit does not ship Heavy at all** - the 98.3% PDJ row in section 4.3 is a variant ML Kit does not expose, and the applicable rows are Lite (93.8%) and Full (96.6%). Verify this in the prototype before quoting 98.3% at anyone.

### Minimum iOS version and toolchain

- **Minimum iOS: 15.5.** **VERIFIED** - ML Kit release notes, 2024-09-30: *"On iOS, raised the minimum supported version of iOS to 15.5.0."* <https://developers.google.com/ml-kit/release-notes>. Matches the plugin podspec's `s.ios.deployment_target = '15.5'`.
- **Minimum Xcode: 16.0.0.** **VERIFIED** - release notes, 2025-03-25: *"On iOS, raised the minimum supported version of Xcode to 16.0.0."*
- **Acceleration:** ML Kit documents no CoreML or Neural Engine usage for pose detection, and exposes no delegate/backend selector. The BlazePose lineage runs on TFLite with XNNPACK (CPU) or a GPU delegate. **Not documented for ML Kit iOS at all.** **VERIFIED by absence** across the iOS guide and release notes.

### Free-team signing compatibility

**VERIFIED, cross-referenced with [`ios-signing-from-linux.md`](./ios-signing-from-linux.md):** ML Kit requires **no entitlements**. It is a statically-linked static framework (`s.static_framework = true`) with no App Groups, no push, no HealthKit, no capability from Apple's gated list. Camera and photo-library access are Info.plist usage strings, not entitlements, and work on a free Apple Account. **Nothing in ML Kit conflicts with free-team signing.**

The real iOS friction is CocoaPods dependency-graph pain, which is well attested in the plugin's tracker: **41 issues mention `Podfile`**, dominated by conflicts with Firebase / `GoogleDataTransport` / `GTMSessionFetcher` (#27, #34, #50, #59, #70, #333, #336, #357, #379, #408, #622, #643, #675, #676, #690, and open #866), plus a recent Apple Silicon / iOS 26 simulator arm64 cluster (#825, #849, #852, #854, #856, #860, open #861). **ANECDOTAL** (issue tracker) but a consistent, decade-long pattern. **INFERRED:** if PosePerfect ever adds Firebase, budget a day for pod resolution. If it never does, most of this class evaporates. The open SPM-migration issue (#875) suggests the ecosystem is mid-transition, which usually means more breakage before less.

### Single-image latency

Google's published figures, both **tracking-mode** and both for a **2017 phone**:

| SDK | iPhone X |
|---|---|
| `PoseDetection` (base) | **~45 FPS** (≈22 ms) |
| `PoseDetectionAccurate` | **~29 FPS** (≈34 ms) |

**VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection/ios>. The overview page gives the same numbers as "~30 and ~45 fps" for Pixel 4 and iPhone X respectively.

**These are stream-mode numbers and Google says so, indirectly but unambiguously.** From the iOS guide's own mode descriptions:

> **stream:** "In subsequent frames, **the person-detection step will not be conducted** unless the person becomes obscured or is no longer detected with high confidence. ... This reduces latency and smooths detection."
> **singleImage:** "The pose detector will detect a person and then run pose detection. **The person-detection step will run for every image, so latency will be higher**, and there is no person-tracking."

**VERIFIED** - <https://developers.google.com/ml-kit/vision/pose-detection/ios>. The iOS performance guide's optimisation advice is literally *"Use the base PoseDetection SDK and stream detection mode"* - the configuration we cannot use.

Google publishes **no `singleImage` latency figure for any device**. **VERIFIED by absence.**

**How much is the detector worth?** Bounded from the primary source: BlazeFace reports **0.6 ms on an iPhone XS GPU** (2.1 ms for the MobileNetV2-SSD baseline it replaces), on a 128x128 input. **VERIFIED** - Bazarevsky et al., *BlazeFace*, Table 1 and Table 2, <https://arxiv.org/abs/1907.05047>.

**INFERRED:** the detector *network* is cheap - low single-digit milliseconds. The `singleImage` penalty is therefore probably modest in absolute terms (order 10-30% on top of the tracking-mode figure, not 2x), and on 2026 iPhone-class silicon the whole single-image call is plausibly **well under 50 ms even for the accurate SDK**. For an app that scores one still on demand, **latency is a non-issue and should not carry weight in this decision.** Only the *accuracy* consequence of losing the tracking-mode crop matters, and that is section 4.3's point.

Also **VERIFIED** and worth stating for the prototype's benefit: the accuracy figures in section 4.3 and the latency figures here are both tracking-mode, so **both** understate our cost. Any prototype must set `.singleImage` and measure its own numbers; nothing published applies directly.

---

## 8. Dimension 6 - licensing for a closed-source app

**Cleared, with one disclosure obligation.**

| Layer | Licence | Source |
|---|---|---|
| Flutter plugin | **MIT** | pub.dev `license:mit`; repo `licenseInfo`. Note two copyright lines exist - published 0.15.0 archive says "Copyright (c) 2026 flutter-ml.dev", `master` says "Copyright (c) 2022 Francisco Bernal and Bharat Biradar". Immaterial: both MIT. |
| Model weights | **Apache License 2.0** | Model card p.2, "LICENSED UNDER: Apache License, Version 2.0" |
| ML Kit SDK | Google APIs ToS + ML Kit ToS | <https://developers.google.com/ml-kit/terms>, last modified 2025-05-14 |

**VERIFIED.** MIT and Apache-2.0 both permit closed-source commercial redistribution with attribution. There is **no separate restrictive model-weight licence** - unusually clean; contrast `ultralytics_yolo` on pub.dev, which is **AGPL-3.0** and would be a hard blocker.

Two obligations, both **VERIFIED** from the ML Kit ToS:

1. **No reverse engineering:** *"When using the ML Kit APIs, you may not reverse engineer or attempt to extract the source code or any related software"*, and *"machine learning models will be considered related software"*. Irrelevant to normal use; relevant if anyone ever considers extracting the `.tflite` to run it elsewhere. Don't.
2. **Telemetry, and an App Store disclosure duty.** Inference is on-device - *"processing of the input data (e.g. images, video, text) fully happens on-device, and ML Kit does not send that data and the resultant outputs to Google servers"* - **but**: *"The ML Kit APIs also send metrics about the performance and utilization of the APIs in your app to Google. ... **You are responsible for informing users of your app about Google's processing of ML Kit metrics data as required by applicable law.**"*

**INFERRED:** obligation 2 is a real, concrete cost for a closed-source App Store release - it forces a data-collection declaration in App Store Connect ("Diagnostics / Product Interaction" linked to a third party) that a fully self-contained TFLite or Apple Vision route would not require. Not a blocker, but it is the one thing in this section that is not free, and it distinguishes ML Kit from every alternative that ships its own weights.

---

## 9. Dimension 1, wider - the Flutter binding landscape for pose estimation

For context on what integration routes exist at all. All figures read from the pub.dev API on 2026-08-07. **VERIFIED.**

| Package | Version | Published | Likes | 30-day downloads | Platforms | Licence | Route |
|---|---|---|---|---|---|---|---|
| `google_mlkit_pose_detection` | 0.15.0 | 2026-07-07 | 79 | **18,966** | Android, iOS | MIT | Community wrapper over ML Kit |
| `pose_detection` | 3.6.0 | 2026-07-25 | 5 | 1,689 | all 6 | Apache-2.0 | Own pipeline over `flutter_litert` + `opencv_dart` |
| `flutter_litert` | 3.8.0 | 2026-08-06 | 23 | 6,285 | all 6 | Apache-2.0 | LiteRT runtime, bring your own model |
| `tflite_flutter` | 0.12.1 | 2025-10-28 | **901** | **58,868** | 5 | Apache-2.0 | TFLite runtime (publisher `tensorflow.org`), bring your own model |
| `onnxruntime` | 1.4.1 | **2024-03-27** | 73 | 13,299 | 5 | MIT | ONNX runtime, bring your own model |
| `apple_vision_pose` / `_pose_3d` | 0.1.0 | 2026-07-25 | 1 / 2 | 358 / 174 | iOS, macOS | MIT | Community wrapper over Apple Vision |
| `flutter_pose_detection` | 0.4.1 | 2026-01-01 | 1 | 258 | Android, iOS | MIT | Community wrapper over MediaPipe PoseLandmarker |
| `flutter_mp_pose_landmarker` | 0.1.8 | 2026-04-27 | 6 | 112 | Android, iOS | **unknown** | Community wrapper over MediaPipe + CameraX |
| `body_detection` | 0.0.3 | **2021-11-11** | 41 | 66 | Android, iOS | Apache-2.0 | MediaPipe wrapper, **abandoned** |
| `ultralytics_yolo` | 0.6.11 | 2026-07-28 | 78 | 2,401 | Android, iOS | **AGPL-3.0** | YOLO-pose; licence blocks closed source |
| `mediapipe` | 0.0.1 | **2022-08-07** | 3 | 22 | Android, iOS | MIT | `tensorflow.org` publisher, **single version, abandoned** |

Four structural observations, all **VERIFIED** from the table:

1. **There is no first-party Flutter binding for any pose engine.** Google's own `mediapipe` package on pub.dev has exactly one version, published 2022, and 22 downloads a month. Google publishes a Flutter *runtime* (`tflite_flutter`) and no Flutter *pose* plugin. Apple publishes nothing for Flutter.
2. **`google_mlkit_pose_detection` is, by an order of magnitude, the most-used pose binding that exists.** 18,966 monthly downloads against 1,689 for the runner-up and triple digits for everything else. Whatever its faults, it is the only one with a user base large enough to have surfaced its bugs.
3. **The MediaPipe wrappers are all one-person, sub-1.0, triple-digit-download projects**, and one of them has an unknown licence. Choosing MediaPipe over ML Kit in Flutter means accepting a materially less-proven binding, or writing the platform channel yourself.
4. **The bring-your-own-model route is well supported.** `tflite_flutter` (901 likes, 58,868 downloads, published by `tensorflow.org`) and `flutter_litert` are healthy. **INFERRED:** if the prototype finds every packaged engine fails on rear views, running a chosen `.tflite`/ONNX pose model directly through `tflite_flutter` is a viable fallback - and it would also recover the world-landmark tensor that ML Kit discards (section 6). The cost is writing the pre/post-processing (crop, align, decode) that ML Kit gives for free, which the BlazePose paper documents well enough to reimplement.

---

## 10. Summary for the prototype ticket

**Not a verdict.** What the evidence supports, and the cheapest experiments that would settle what it does not.

**Settled in ML Kit's favour:**
- Licensing is clean for a closed-source app (MIT + Apache-2.0, no restrictive weights licence). One App Store telemetry disclosure required.
- The Flutter binding is the most-used pose binding on pub.dev by 10x, shipped a real release a month ago, iOS is first-class, min iOS 15.5.
- Latency is a non-issue for still-image scoring. Do not let FPS numbers influence this decision.
- Models are bundled, so the app works offline with no first-run download.
- Landmark set covers every joint the ticket asks for.

**Settled against it:**
- **Google has an open, acknowledged model bug on rear-facing subjects** ([#5197](https://github.com/google-ai-edge/mediapipe/issues/5197)), unfixed for two years, whose signature is *confident output about landmarks that are not visible*. Three of our eight mandatories are rear-facing.
- The API discards the model's **metric world landmarks** and its **occlusion/visibility** channel. Both exist; MediaPipe exposes them; ML Kit does not. Same model, same cost, less output - and on rear views the visibility channel is broken anyway.
- **BlazePose is the fragile one of its peer group on viewpoint-varied footage**: 65.2% keypoint detection versus AlphaPose 98.4% and OpenPose 94.5% on identical frames (Mundt et al. 2022), with left/right limb confusion named by the authors as a mechanism.
- The upstream SDK is still beta after six years, with no SLA and an explicit backward-compatibility disclaimer. The Android artefact has not moved since 2024-08-07; the doc page since 2024-07-10. Google's own two model cards for this model disagree by 4-7 PDJ points.
- Both pods are pulled unconditionally by the plugin, so binary cost exceeds the published 33.2 MB.

**Unsettled, and decisive - in priority order:**

1. **Is the left/right assignment stable on rear and oblique views?** The architecture predicts a bimodal mirror ambiguity there (5.1), the model is trained never to abstain (5.3), an independent study proposes exactly this mechanism for side views (4.4), and **no one has ever measured it** (5.5). Perturb one rear capture within the model's own stated tolerance - 10% shift/scale, 8 degrees roll - and run it 20 times. **A flip inside that band disqualifies ML Kit for the rear mandatories no matter how good the frontal numbers are.** This is the experiment that decides.
2. **How wrong are the coordinates on a real rear capture?** Not "does it return something" - #5197 already tells us it will return 33 confident landmarks. Feed one rear-facing capture of the actual athlete and compare landmark by landmark against a human's judgement. Expect high `InFrameLikelihood` regardless; that is the point.
3. **Does the plugin's front-camera left/right swap ([#703](https://github.com/flutter-ml/google_ml_kit_flutter/issues/703)) survive 0.15.0's Objective-C-to-Swift rewrite?** Filed against the old implementation, never fixed, never re-tested, and no mirroring code exists in the shipped 0.15.0 source. Ten minutes to check. Independent of engine choice it implies a hard capture-UX constraint: **pin the camera between reference and capture, or normalise for it explicitly.**
4. **Actual iOS binary delta**, measured on a thinned release build, not read off a docs page.

**The single most important framing to carry forward:** every accuracy figure Google publishes for this model is a **frontal, tracking-mode, PDJ@0.2** number measured on an **AR-app capture corpus of people facing the phone**. Our hardest case - a heavily-muscled, oiled subject with his back to a phone taking one still - shares none of those four properties. The 98.3% headline is not evidence about our use case in either direction, and it should not be quoted as if it were.

**And the framing that matters most for the prototype's design:** ML Kit will never tell you it failed. It has no abstain path, its confidence field means "in frame" rather than "visible", and Google has confirmed that field reads 0.99 on landmarks a rear-facing subject physically cannot show. **Any evaluation of this engine that trusts its own confidence output will conclude it works.** The comparison must be against ground truth a human establishes, on the actual rear and side mandatories, or it will measure nothing.
