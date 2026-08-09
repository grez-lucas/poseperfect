# The rear-view experiment: measured, not speculated

Resolution of [#18](https://github.com/grez-lucas/poseperfect/issues/18), 2026-08-07. Grading convention matches `pose-engines.md`: **VERIFIED** = measured or read from a primary source, **INFERRED** = reasoned from measurement, **ANECDOTAL** = reported by others.

Code, raw per-instance results and raw predicted keypoints: `experiments/rear-view/`. One command reproduces everything: `experiments/rear-view/run.sh`.

---

## Verdict

**BlazePose collapses from behind, and the collapse is worse than the map assumed - but the viewpoint is not the problem, the architecture is, and that is now measured rather than argued.**

Of rear-facing captures fed to MediaPipe BlazePose under the exact conditions our product will use (IMAGE mode, a well-framed single subject, ground-truth crop):

- **30.0%** return **no pose at all**. The failure is loud, not silent, and it is not a small-subject artefact - it holds at 23.7% even on subjects over 300 px tall, where the front-facing rate is 2.1%.
- Of the 70% that do return a pose, **14.4%** are **chirally transposed** - the model's `left_shoulder` is the athlete's right shoulder. Front-facing: 2.7%.
- Composite: **61.1% of rear-facing captures are usable.** Nearly two in five are not. Front-facing: 90.4%.

MoveNet Thunder, chosen as the control precisely because it has **no face anchor and no person detector**, never fails to return a pose and drops to a **7.2%** rear swap rate. RTMPose-m, a third architecture with a general detector, drops to **1.0%**. Same images, same crops, same IMAGE-mode discipline.

**The detector-swap hypothesis from #9 and #3 is confirmed.** Rear views are survivable. BlazePose is not.

**What this does not do:** it does not rescue the rear-facing mandatories on any engine we can currently ship to iOS, because ML Kit is BlazePose and MoveNet/RTMPose are not on the ML Kit or Apple Vision menu. It reframes [#16](https://github.com/grez-lucas/poseperfect/issues/16) from "are rear poses possible" to "which engine, and at what integration cost".

---

## 1. What was actually run

**VERIFIED.**

| | |
|---|---|
| Dataset | COCO val2017 person keypoints, 1,675-instance cohort |
| Mode | IMAGE / static single-image inference, every engine, no exceptions |
| Input | square crop at 1.25x the ground-truth bounding box, black-padded |
| Engines | MediaPipe BlazePose heavy + full (1.0.0), MoveNet SinglePose Thunder (TFLite fp16), RTMPose-m body7 (ONNX) |
| Hardware | CPU, Linux, Python 3.12.3. Whole sweep: 286 s |

The 1.25x ground-truth crop is deliberate. It stands in for the product's **constrained, frame-fit-gated capture** (map decisions 8 and 14), not for in-the-wild detection. It is the friendliest realistic input, which makes the failure rates below lower bounds rather than worst cases.

RTMPose is run with ground-truth boxes, so only its pose head is under test. Its numbers are an upper bound, not a deployable figure.

### COCO-MEBOW was gated, as the ticket anticipated

**VERIFIED.** `ChenyanWu/MEBOW`'s README: *"Please email czw390@psu.edu to get access to the human body orientation annotations... For academic researchers, please use your educational email address. For researchers in business companies, please send a formal letter (with the company name and your signature)."* Checked first, before any code was written. We fell back to the designated public alternative.

### The orientation proxy, and what it does and does not establish

**VERIFIED construction.** COCO carries per-keypoint visibility flags: `v=0` not labelled, `v=1` labelled but occluded, `v=2` visible. Define `face_visible` = how many of {nose, left_eye, right_eye} the annotator marked `v=2`:

| bucket | `face_visible` | n |
|---|---|---|
| FRONT | 3 | 832 |
| OBLIQUE | 2 | 384 |
| PROFILE | 1 | 96 |
| REAR | 0 | 363 |

Every instance additionally requires both shoulders and both hips at `v=2`, so the torso is fully annotated in every bucket and the chirality test always has ground truth to score against. Crowd annotations, instances under 100 px tall, instances with fewer than 8 labelled keypoints, and instances overlapping another annotated person by more than 35% are excluded.

**What it establishes.** A second, independent read of the same ground truth agrees with it. The annotated shoulder order - whether the human-labelled *right* shoulder lies to the viewer's right, which is what a person facing away looks like - splits cleanly along the proxy:

| bucket | fraction facing away by annotated shoulder order |
|---|---|
| FRONT | 0.034 |
| OBLIQUE | 0.326 |
| PROFILE | 0.510 |
| REAR | **0.807** |

Two unrelated annotator judgments - "can I see this person's eyes" and "where do I put their right shoulder" - agree 81% of the time on REAR and 97% on FRONT. That is what bounds contamination.

**What it does NOT establish.**

1. **It is ordinal, not angular.** There is no degree axis. The question "at what angle does degradation begin" cannot be answered in degrees from this data - only "as soon as the face starts to turn", which section 5 shows.
2. **REAR is ~81% pure, not 100%.** The other ~19% are front-facing people whose faces are occluded by an object, a hand, motion blur, or a hat. All headline numbers are therefore also reported on a **sign-confirmed** subset - proxy label AND annotated shoulder order agreeing - which is what the verdict quotes.
3. It says nothing about our population. See section 7.

---

## 2. Detection failure: the face-anchored detector, caught

**VERIFIED.** Fraction of instances where the engine returned **no pose at all**:

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.073 | 0.069 | 0.000 | 0.000 |
| OBLIQUE | 0.188 | 0.169 | 0.000 | 0.000 |
| PROFILE | 0.198 | 0.188 | 0.000 | 0.000 |
| **REAR** | **0.311** | **0.300** | **0.000** | **0.000** |

BlazePose's failure rate rises monotonically as the face turns away, and quadruples from front to rear. MoveNet and RTMPose never fail, because neither has a face-anchored gate to fail at.

**This is not a size artefact.** REAR instances are smaller in COCO (median bbox height 162 px vs 252 px for FRONT), so the comparison is repeated inside size bands:

| size band | blazepose_heavy FRONT | blazepose_heavy REAR | n FRONT | n REAR |
|---|---|---|---|---|
| 100-200px | 0.140 | 0.293 | 308 | 198 |
| 200-300px | 0.044 | 0.298 | 159 | 57 |
| >300px | **0.021** | **0.237** | 337 | 38 |

The gap *widens* with size, from 2.1x to 11.3x. Controlling for scale makes BlazePose look worse, not better.

**INFERRED, and the mechanism matches the binary evidence already on record** (`pose-engines-flutter-routes.md`: Google's shipped `pose_detector.tflite` metadata describes its person detector as "Full Range Face Detection"): the detector fires on faces, so no face means no ROI means no pose. Google's own statement in [#5641](https://github.com/google-ai-edge/mediapipe/issues/5641) - *"our current Pose Landmarker is unable to detect individuals facing backward"* - is a 30% failure rate on a friendly crop, not a total one.

**One correction to the map's pessimism.** The map recorded the rear-view failure as *silent*. The dominant BlazePose failure is not silent at all - it returns nothing, which an app can detect trivially. The *silent* failure is the second one, below, and it is smaller but unfixable.

---

## 3. Chirality error: the fatal one, measured

**VERIFIED.** An instance is scored as **swapped** when the engine's output matches the ground truth better after transposing every left/right landmark label than it does as emitted. Scored on torso and limb pairs at ground-truth `v=2` only, both sides of a pair required, distances normalised by `sqrt(COCO area)`. Only instances where a pose was returned are eligible.

Sign-confirmed buckets, with 95% Wilson intervals:

| engine | bucket | n | swap rate | 95% CI |
|---|---|---|---|---|
| blazepose_full | FRONT | 743 | 0.035 | 0.024 - 0.051 |
| blazepose_full | **REAR** | 207 | **0.159** | 0.116 - 0.215 |
| blazepose_heavy | FRONT | 747 | 0.027 | 0.017 - 0.041 |
| blazepose_heavy | **REAR** | 209 | **0.144** | 0.102 - 0.198 |
| movenet_thunder | FRONT | 804 | 0.006 | 0.003 - 0.014 |
| movenet_thunder | **REAR** | 293 | **0.072** | 0.047 - 0.107 |
| rtmpose_m | FRONT | 804 | 0.004 | 0.001 - 0.011 |
| rtmpose_m | **REAR** | 293 | **0.010** | 0.003 - 0.030 |

**Is the architecture ordering real, or noise?** blazepose_heavy's REAR interval and movenet_thunder's overlap slightly (0.102-0.198 against 0.047-0.107), so overlapping intervals are not sufficient here and the differences were tested directly. Two-proportion z-tests on sign-confirmed REAR:

| comparison | rate 1 | rate 2 | z | two-sided p |
|---|---|---|---|---|
| blazepose_heavy vs movenet_thunder | 0.144 (n=209) | 0.072 (n=293) | 2.63 | **0.0086** |
| blazepose_full vs movenet_thunder | 0.159 (n=207) | 0.072 (n=293) | 3.11 | **0.0018** |
| movenet_thunder vs rtmpose_m | 0.072 (n=293) | 0.010 (n=293) | 3.75 | **0.0002** |
| blazepose_heavy vs rtmpose_m | 0.144 (n=209) | 0.010 (n=293) | 5.94 | **<0.0001** |

The ordering is real, not noise, at every step.

This also survives size control - in the >300 px band, blazepose_heavy swaps 17.2% of REAR against 2.1% of FRONT.

### The swap is not a clean global flip, and that matters

**VERIFIED, and this is the most consequential single result in the experiment.**

The obvious mitigation is: detect that the athlete is facing away, then transpose every label back. That only works if the failure is a **coherent** front/back reflection. It is not. Chirality was decided independently for four limb groups - shoulders, hips, arms, legs - on instances where all four could be decided:

| engine | bucket | n | all four groups agree | all four swapped | **mixed (incoherent)** |
|---|---|---|---|---|---|
| blazepose_heavy | FRONT | 503 | 0.897 | 0.004 | 0.103 |
| blazepose_heavy | **REAR** | 121 | 0.810 | 0.033 | **0.190** |
| movenet_thunder | REAR | 154 | 0.896 | 0.019 | 0.104 |
| rtmpose_m | REAR | 154 | 0.974 | 0.006 | **0.026** |

On rear-facing input, **19% of BlazePose skeletons are internally inconsistent** - the shoulders are read one way and the legs the other. Only 3.3% are the clean global mirror that a relabelling fix could recover.

**INFERRED, strongly:** no downstream orientation gate, however accurate, can repair this. A facing-direction flag fixes coherent flips. It cannot fix a skeleton whose upper and lower body disagree with each other. Per-group rear swap rates for blazepose_heavy are shoulders 0.148, hips 0.153, arms 0.115, legs 0.136 - each group failing at a similar rate, largely independently.

---

## 4. Positional error: the tolerable one, and it really is tolerable

**VERIFIED.** OKS over ground-truth keypoints at `v=2`, computed **after** applying the chirality correction, so this is positional error with the chirality failure removed. This is the quantity that cancels when an athlete is scored against their own earlier reference under matched framing.

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.748 | 0.773 | 0.907 | 0.950 |
| OBLIQUE | 0.688 | 0.720 | 0.864 | 0.924 |
| PROFILE | 0.669 | 0.701 | 0.840 | 0.929 |
| REAR | 0.663 | 0.673 | 0.818 | 0.930 |

PCK@0.2·sqrt(area), same correction, blazepose_heavy: 0.840 FRONT to 0.727 REAR.

Sign-confirmed front-to-rear deltas in corrected OKS: blazepose_heavy **-0.087**, movenet_thunder **-0.078**, rtmpose_m **-0.018**.

**INFERRED.** Two readings, and they point the same way:

1. **Positional degradation is real but modest, and nearly identical for BlazePose and MoveNet** (-0.087 vs -0.078). Turning around costs both architectures about the same in raw landmark placement. That is the viewpoint effect, and it is the kind of smooth, largely systematic loss that self-referential scoring is designed to absorb.
2. **What separates the architectures is chirality, not position** - a 14.4% vs 7.2% vs 1.0% spread, against a positional spread of 0.087 vs 0.078 vs 0.018.

The map was right to insist these be reported separately. Merged into one accuracy number, BlazePose REAR reads as "OKS 0.67, a bit worse than 0.77 front", which is a completely misleading description of an engine that returns nothing 30% of the time and transposes the athlete 14% of the rest.

**Caveat on the BlazePose positional numbers: survivor bias.** They are computed only on the 70% of rear instances BlazePose deigned to detect. The hard 30% is missing from that average. MoveNet and RTMPose numbers have no such exclusion.

---

## 5. Where degradation begins

**VERIFIED.** By `face_visible` (3 = both eyes and nose visible, 0 = none):

**Chirality swap rate**

| face_visible | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| 3 | 0.040 | 0.031 | 0.008 | 0.005 |
| 2 | 0.109 | 0.094 | 0.047 | 0.026 |
| 1 | 0.130 | 0.090 | 0.042 | 0.000 |
| 0 | 0.156 | 0.154 | 0.094 | 0.019 |

**Detection failure rate**

| face_visible | blazepose_heavy |
|---|---|
| 3 | 0.069 |
| 2 | 0.169 |
| 1 | 0.188 |
| 0 | 0.300 |

**There is no cliff at 180 degrees. The largest single step is the first one.** Going from a fully visible face to a partially visible one - which is a modest turn, not a rear view - triples BlazePose's swap rate (0.031 to 0.094) and multiplies its detection failure rate by 2.4 (0.069 to 0.169). The remaining turn to full rear roughly doubles it again.

**INFERRED, and directly relevant to the product.** Degradation is not confined to the three rear mandatories. **Quarter turns and the side poses are already in the degraded regime**, because as soon as the head rotates far enough to hide one eye, BlazePose has lost most of the signal it relies on. This is consistent with, and sharpens, `pose-engines-failure-modes.md` section 5's finding that side poses are less safe than first recorded.

The precise angle at which this happens is **not established** by this experiment. That needs COCO-MEBOW's 5-degree labels, and MEBOW is gated.

---

## 6. The two questions the ticket asked to settle for #12

### 6a. The shoulder-sign heuristic: 84.6% on rear, and it cannot catch its own failure

**VERIFIED.** `sign(RIGHT_SHOULDER.x - LEFT_SHOULDER.x)` computed on the predicted landmarks, scored against the same sign computed on the annotated shoulders. Unconditioned on the full proxy buckets, so this is not circular.

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.970 | 0.977 | 0.982 | 0.989 |
| OBLIQUE | 0.869 | 0.893 | 0.898 | 0.938 |
| PROFILE | 0.818 | 0.821 | 0.844 | 0.927 |
| **REAR** | 0.836 | **0.846** | 0.895 | 0.956 |

Overall accuracy: blazepose_heavy **0.926**, movenet_thunder 0.936, rtmpose_m 0.967.

**As a facing-direction reporter it works about as well as the engine underneath it.** On BlazePose, 84.6% on rear views is a 1-in-6.5 error rate. That is not a gate.

**And the deeper problem, VERIFIED:** the heuristic reads facing direction off the *same predicted landmarks that are transposed*. Treated as a detector of the chirality swap, on blazepose_heavy it catches **63.0%** of swaps at a **40.0%** false alarm rate. It is not an independent check. It is the failure, restated.

**INFERRED for [#12](https://github.com/grez-lucas/poseperfect/issues/12): the heuristic does not give #12 its gate for free.** What survives is the weaker use already written into `pose-engines-failure-modes.md` section 4 - use it as a **consistency check across repeated captures of the same held pose**, and discard the sample when the sign is unstable. That is a stability test, not a correctness test, and it needs repeated captures to work at all.

### 6b. Confidence is useless on BlazePose, and this is now first-party evidence

**VERIFIED. Google's open bug [#5197](https://github.com/google-ai-edge/mediapipe/issues/5197) reproduces exactly.**

Mean per-landmark `visibility` for BlazePose against a keypoint score for the others:

**nose**

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.999 | 0.995 | 0.560 | 0.970 |
| **REAR** | **0.993** | **0.985** | **0.251** | 0.700 |

**eyes**

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.998 | 0.994 | 0.579 | 0.999 |
| **REAR** | **0.992** | **0.983** | **0.252** | 0.681 |

BlazePose reports **0.985 visibility for the nose of a person whose nose is pointing away from the camera**, across 363 instances. MoveNet, on the identical crops, drops to 0.251. The signal exists in the image; BlazePose's head simply does not report it.

Worse, on the instances BlazePose got **chirally wrong**, mean nose visibility is still ~0.98. As a detector of its own chirality failure on rear input, blazepose_heavy's confidence has an **AUC of 0.564** (mean confidence) and **0.528** (nose confidence) - 0.50 is a coin flip. MoveNet's reaches 0.759.

**This confirms the map's existing conclusion with our own data and refutes the kabe-tech claim already flagged as wrong.** No confidence threshold on BlazePose catches the rear-view failure. Any prototype that gates on `visibility` or ML Kit's `inFrameLikelihood` will conclude the engine works.

**INFERRED, and it strengthens the case against ML Kit specifically.** `pose-engines-mlkit.md` records that ML Kit exposes only `inFrameLikelihood`, not even `visibility`. It is strictly less instrumented than the engine measured here, whose instrumentation is already worthless on this input.

---

## 7. Caveats, stated plainly

1. **This is MediaPipe, not ML Kit.** ML Kit cannot run on Linux and was not tested. MediaPipe is a legitimate proxy because both are BlazePose-derived and share the face-anchored person detector - confirmed at the binary level in `pose-engines-flutter-routes.md` - but they are not the same binary, and the numbers here are MediaPipe's. **Apple Vision is entirely untested by this ticket. Full stop.** Nothing here says anything about it.

2. **COCO is clothed people in everyday scenes.** Our subject is a heavily muscled, oiled, minimally clothed physique athlete holding a static, extreme, deliberately symmetric pose. **This experiment measures the viewpoint effect. It does not measure our population.** Nobody has ever evaluated any of these engines on physique athletes, and this ticket does not close that gap. Muscularity could plausibly go either way: more surface definition might help a bottom-up model, or a lat spread's silhouette might confuse a model trained on "yoga/fitness/dance".

3. **The rear-facing label is a proxy, ~81% pure, and ordinal rather than angular.** See section 1. No degree axis exists without MEBOW, and MEBOW is gated.

4. **Nothing here was validated by eye**, in accordance with the model card's admission that occluded points are annotated with a "best guess and default pose". Every number is scored against ground-truth keypoints. No skeleton overlay was rendered or inspected at any point.

5. **No filtering on engine confidence anywhere.** Section 6b is why.

6. **RTMPose ran with ground-truth boxes**, so its numbers isolate the pose head and are an upper bound. It is also not on the shippable menu today.

7. **BlazePose's positional numbers carry survivor bias** - conditioned on the 70% it detected.

---

## Bottom line for the map

**VERIFIED:**

1. **BlazePose is disqualified for rear-facing mandatories on measured evidence, not inference.** 61.1% usable rear captures against 90.4% front. The detector-swap hypothesis on #9 is confirmed: the failure lives in the face-anchored person detector and does not transfer to architectures without one.
2. **The dominant failure is loud (30% no detection), not silent.** The map should be corrected on this. The silent failure - chirality - is smaller at 14.4%, and it is the unfixable one.
3. **The chirality failure is piecewise, not a coherent global flip.** 19% of rear BlazePose skeletons are internally inconsistent. No orientation gate repairs that.
4. **Positional error is modest and comparable across architectures (~-0.08 OKS front to rear).** The map's premise that positional bias is tolerable under self-referential scoring survives intact. The problem was never the pixels.
5. **Confidence is worthless on BlazePose**, AUC 0.53-0.56 for detecting its own chirality failure, with 0.985 nose visibility on people facing away. #5197 reproduced.
6. **The shoulder-sign heuristic is 84.6% accurate on rear BlazePose output and cannot detect the swap** (63% recall, 40% false alarms). #12 does not get its gate for free.
7. **Degradation begins at the first partial head turn, not at 180 degrees.** Quarter turns and side poses are already affected.

**NOT ESTABLISHED, and needing separate work:**

- Anything about **Apple Vision**, which is the other half of the field #3 narrowed to.
- Anything about **ML Kit's specific binary**, as opposed to BlazePose generally.
- Anything about **physique athletes**, muscularity, oil, or posing trunks.
- **The angle at which degradation begins**, in degrees. Gated behind MEBOW.
- Whether MoveNet or RTMPose can be **shipped to iOS through Flutter** at acceptable cost, which is the question this result now makes worth asking.

**For [#16](https://github.com/grez-lucas/poseperfect/issues/16):** the choice is no longer "drop rear poses or accept a broken engine". It is "change engine, or drop rear poses". A control architecture reaching 92.8% usable rear captures on the same images says the poses are recoverable; it just is not BlazePose that recovers them.
