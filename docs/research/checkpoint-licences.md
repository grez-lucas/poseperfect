# The RTMPose checkpoint's training-data licences, and which checkpoint ships

Resolution of [#20](https://github.com/grez-lucas/poseperfect/issues/20), 2026-08-10. Grading convention matches `pose-engines.md` and `person-detector.md`: **VERIFIED** = measured here or read from a primary source, **INFERRED** = reasoned from measurement, **ANECDOTAL** = reported by others.

**Written as a sibling of [`person-detector.md`](person-detector.md) rather than appended to it**, because it answers a different question about a different model. #19's file is the record of *which detector to put in front of RTMPose-m*; this one is the record of *which RTMPose-m weights to ship*. Appending would have buried a checkpoint decision inside a detector decision, and [#16](https://github.com/grez-lucas/poseperfect/issues/16)'s falsified prerequisite deserves its own findable document.

Code, raw per-instance results and the ONNX export recipe: `experiments/checkpoint-swap/`. It reuses [#18](https://github.com/grez-lucas/poseperfect/issues/18)'s cohort, crop construction and chirality test verbatim, and [#19](https://github.com/grez-lucas/poseperfect/issues/19)'s detector, pose scoring and statistics verbatim, so every number here sits on the same 1,675 COCO val2017 instances as `rear-view-experiment.md` and `person-detector.md`.

---

## 1. What `body7` actually contains

**VERIFIED, from MMPose's own definition.** [`projects/rtmpose/README.md`](https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose/README.md) states it in one line:

> "`*` denotes model trained on 7 public datasets:
>   - AI Challenger
>   - MS COCO
>   - CrowdPose
>   - MPII
>   - sub-JHMDB
>   - Halpe
>   - PoseTrack18"

The checkpoint [#16](https://github.com/grez-lucas/poseperfect/issues/16) chose is `rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504`, which carries that `*`. #19 opened three of the seven. This ticket opened the other four, each from its own distribution point, read separately from any paper or repo badge.

---
