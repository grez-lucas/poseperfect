# BlazePose rear-view, oblique-view and non-determinism failure modes

Supplementary note to [#3](https://github.com/grez-lucas/poseperfect/issues/3), 2026-08-07. The most decision-relevant of the engine research. Grading convention matches `pose-engines.md`.

**Verdict: the fatal failure mode is real, documented, and has a documented mitigation that our architecture already happens to satisfy.**

---

## 1. The bimodal front/back flip is confirmed, in the user's own words

**ANECDOTAL but exact.** [mediapipe#3500](https://github.com/google-ai-edge/mediapipe/issues/3500), closed stale:

> "I am experiencing **random horizontal flips in the body joints (between the front angle and the back angle)**. Because the **faces in my video dataset are blurred**, MediaPipe has difficulty detecting the angle of the body joints and **alternates between front and back angles**."

Note the causal detail the reporter supplies unprompted: the flips correlate with the face being unavailable. Google's only reply pointed at an unrelated thread; closed stale, no fix, no acknowledgement.

This is precisely the bimodal error identified as fatal to self-referential scoring. Systematic bias cancels between reference and capture; a coin-flip between two interpretations does not.

**And Google says it outright.** [mediapipe#5641](https://github.com/google-ai-edge/mediapipe/issues/5641), Google staff:

> "**Our current Pose Landmarker is unable to detect individuals facing backward.** While customization for specific tasks is possible using MediaPipe Model Maker, this feature is not available for the Pose Landmarker at this time."

The architectural reason, from the BlazePose paper (arXiv:2006.10204):

> "**the strongest signal to the neural network about the position of the torso is the person's face**"
> "**the head of the person should always be visible for our single-person use case**"

They train "a face detector... **as a proxy for a pose detector**". The entire ROI, scale and rotation for the landmark network is anchored on a face detection.

---

## 2. The mitigation we already have by accident

**VERIFIED, and this is the good news.**

| Mode | Deterministic | Smoothing | Detector re-runs |
|---|---|---|---|
| **IMAGE / `static_image_mode=True`** | **Yes** | No | **Every frame** |
| VIDEO | **No** | One Euro, timestamp-dependent | Only when tracking lost |
| LIVE_STREAM | **No** | One Euro, timestamp-dependent | Only when tracking lost |

Confirmed in Google's own graph source (`pose_landmarker_graph.cc`: "While in stream mode, skip pose detector graph when we successfully track the poses from the last frame"), in [#4509](https://github.com/google-ai-edge/mediapipe/issues/4509) (same image, same process, different numbers - x/y drift at the 6th decimal, **z at the 4th**), [#3945](https://github.com/google-ai-edge/mediapipe/issues/3945) and [#5253](https://github.com/google-ai-edge/mediapipe/issues/5253).

In VIDEO/LIVE_STREAM the 256x256 crop fed to the network on frame N is an affine transform derived from frame N-1's landmarks. **Feed identical pixels twice and the network sees two different inputs.** This is the mechanism that lets a wrong front/back interpretation **latch and persist** - the ROI feedback loop reinforces it, and the detector only re-runs when tracking is lost entirely.

Smoothing compounds it: filtering is a **One Euro filter**, whose gain is computed as `1.0 / (new_timestamp - last_time_)`. Identical frames at different pacing give different output.

**Map decision 7 - live guide overlay with no scoring, rigorous scoring on capture - already puts us in IMAGE mode by construction.** That decision was made for UX reasons (a number jittering at 30fps is unreadable while holding a pose). It turns out to also eliminate an entire class of non-determinism and to remove the latching behaviour. Keep it, and now for two reasons.

Caveat: [#4981](https://github.com/google-ai-edge/mediapipe/issues/4981) shows unexplained input-order sensitivity even in IMAGE mode (shuffling a 24k-image folder changed detection failures from 305 to 320). Never explained.

---

## 3. Do not validate by eye - this corrects an earlier instruction

**VERIFIED, model card, BIAS section:**

> "This model was trained and evaluated both on visible and hidden points. **For cases that the point location is present but hard to define by humans annotator, it is annotated with a 'best guess' and default pose.**"

Under heavy self-occlusion the supervision target is a canonical prior, not truth. **Errors will be smooth, stable, and visually plausible rather than obviously broken.**

This directly contradicts the instruction previously written into [#9](https://github.com/grez-lucas/poseperfect/issues/9), which said rear-view validation should be done "by eye against the photograph". That was wrong. A rear-view skeleton overlay will look fine while being a learned average human. Validation must be **geometric and comparative**, never visual.

`visibility` is equally useless as a guard: [#5197](https://github.com/google-ai-edge/mediapipe/issues/5197), Google-confirmed bug, still open - visibility and presence stay at ~0.99 for the nose and eyes on a subject filmed from behind, across lite, full and heavy.

A third-party blog (kabe-tech.com) claims rear views produce "reduced confidence in all joints on the hidden side". **That is contradicted by the empirical evidence in #5197. Treat it as wrong.**

---

## 4. A concrete orientation heuristic

**From a Google engineer in [#2221](https://github.com/google-ai-edge/mediapipe/issues/2221):** use the sign of `RIGHT_SHOULDER.x - LEFT_SHOULDER.x` to determine facing direction.

This is the geometric, non-confidence-based check [#12](https://github.com/grez-lucas/poseperfect/issues/12) needs. Use it as a consistency check across repeated captures: if the sign is not stable for the same held pose, discard the sample rather than score it.

---

## 5. Side poses are less safe than previously recorded

`pose-engines.md` concluded that side views are the safer case because the sagittal plane is the best-measured plane. That holds for **near-side** joints only. **The far-side limb collapses.**

**VERIFIED**, Ryu et al., *Bioengineering* 11(2):141, 2024, MediaPipe vs OptiTrack Prime 41 (9 cameras, 120fps, 39 markers). Pearson r, near-side vs far-side:

| Joint | Near side | Far side |
|---|---|---|
| Hip | 0.94 - 0.97 | 0.91 - 0.96 |
| Knee | 0.98 | 0.96 - 0.98 |
| **Ankle** | 0.73 - 0.84 | **0.45 - 0.53** |

Corroborated on OpenPose (PLOS ONE 18(11):e0293917, vs 15-camera Qualisys): "**SD of bias and limits of agreement for the occluded-side hip and knee joint angles in the sagittal plane were double that of the camera-side**". Frontal-plane ankle: "too high across the whole stride and therefore should not currently be used in clinical or sporting applications."

**And the model is not left/right symmetric.** [#4917](https://github.com/google-ai-edge/mediapipe/issues/4917): mirror-image leg positions produced x values of +0.21 and -0.09, and a second user reported "when a person facing right and left showed different tracking results... the model does not involve some fundamental symmetries, such as left-right symmetry".

**Consequence: side chest and side triceps must always be performed facing the same direction**, or the reference comparison is invalid. That is a new domain invariant, alongside camera identity.

---

## 6. Rear views are not intrinsically bad - BlazePose is

**VERIFIED counterweight**, *Sensors* 25(3):799, 2025 - **OpenPose**, four cameras at 45 degrees vs 12-camera Vicon:

> "**The back-viewing cameras demonstrate lower deviations, indicating that the back views are most suitable for this type of exercise estimation.**"

Knee RMSE: back-right 15.50, back-left 16.66 against front-right 18.23, front-left 29.44 degrees.

**Do not transfer this number to BlazePose.** OpenPose is bottom-up with part-affinity fields and **no face-anchored ROI** - the exact mechanism that breaks BlazePose from behind does not exist in it.

What it does prove: **the viewpoint is not the problem, the architecture is.** This independently supports the YOLOv8n-detector hypothesis already on #9, and suggests that if BlazePose flips, a bottom-up model is the architecture to test next.

---

## 7. Depth, for completeness

Google **never evaluated z**. Model card: "the z-coordinate is obtained from synthetic data, so for a fair comparison with human annotations, **only 2D coordinates are employed**" and "Z is not metric but up to scale". ML Kit says the same: "it is not a true 3D value".

Independent numbers: MediaPipe monocular 3D at **56.3 mm median RMSE** (*Sensors* 24(23):7772), and depth-axis error running **6-7x** in-plane error even with two cameras (*Sensors* 25(10):3122).

**A sign-convention trap:** the model card says negative z is "between the hips and the camera"; the TensorFlow blog says world-landmark z "is positive if moving closer to the camera". **These are opposite.** Code assuming one convention across both outputs is inverted for one of them.

And a note on the depth-reflection ambiguity: human depth-order annotation "helped to reduce the depth ordering errors for the fitted GHUM reconstructions **from 25% to 3%**". INFERRED but strong - 3% of the depth supervision is still wrong, and that residual *is* the front/back reflection ambiguity, baked into the training signal.

This all reinforces the existing conclusion: build no metric on depth from any engine.

---

## 8. What nobody has measured

**VERIFIED negative.** Systematic search of PubMed/PMC, arXiv and publisher records found **zero** marker-based validations of MediaPipe/BlazePose from a posterior camera. The one group that tried it printed the result (Ryu et al.): "**Preliminary experiments with smartphone cameras in front of and behind the subject showed that it was difficult to obtain reliable datasets for gait analysis.**" They dropped both placements.

Equally, **no study evaluates muscularity, physique-sport athletes, or minimal clothing.** BlazePose's training corpus is "yoga/fitness/dance" and the model card's fairness axes are geography, skin tone and gender only - **no viewpoint axis at all**.

We are measuring this ourselves or not at all.

---

## Bottom line for the map

**Tolerable** (systematic, cancels against the athlete's own reference): the forward-lean world-landmark bias ([#2918](https://github.com/google-ai-edge/mediapipe/issues/2918)), the non-metric z scale, per-view constant offsets.

**Fatal and confirmed present:**

1. VIDEO/LIVE_STREAM non-determinism. **Already mitigated by decision 7.**
2. The front/back flip, mechanism identified as face-anchored ROI. IMAGE mode removes the latching but not the per-frame ambiguity.
3. `visibility` is unusable as a guard. Use the shoulder-sign heuristic instead.
4. Side poses require a fixed facing direction; far-side limbs degrade badly regardless.
5. Failures look plausible. Never validate by eye.
