# Discarded documents

These are kept for provenance only. **They are not authoritative and must not be used as input to any implementation or planning work.**

The governing artifact is the wayfinder map, [issue #1](https://github.com/grez-lucas/poseperfect/issues/1).

## `FUNCTIONAL_REQUIREMENTS.md`

Discarded during the charting session on 2026-08-07 (map decision 4).

Two independent reasons:

1. **Wrong platform.** It specifies Android, Kotlin, Jetpack Compose and CameraX. This project is Flutter, with iOS as the acceptance target.
2. **Wrong product.** Its core premise is real-time bilateral symmetry analysis, with a `SymmetryAssessment` model carrying `shoulderTiltDeg`, `elbowDiffPx` and `isCenterBalanced`, and a non-functional requirement of "30+ FPS symmetry calculations".

That premise was rejected on the evidence. Map decision 6 established that scoring measures **drift and consistency against the athlete's own reference**, not left-right symmetry, because structural asymmetry is largely skeletal and hypertrophic and posing practice does not fix it. Decision 7 moved scoring off the live preview and onto the capture, which voids the FPS requirement entirely. Decision 16 forbids the absolute percentage scores this document assumes throughout.

Its four-peer-screen bottom-navigation architecture was also discarded (decision 13): the guided session is the app's spine, because you cannot tap a shutter during a back double biceps.

The only salvageable content was the user stories, and even those assume the rejected scoring model.

## `STYLE_CONTEXT.md`

Not present in this directory. It was removed from the repository root during the charting session, before the discard was formalised.

It was a light-themed CSS design system for "Kriptome", a crypto onboarding and payment product, written in Spanish, containing bundle pricing tiers and OTP input components. It was pasted into this repository by mistake and has no relationship to this project. `STYLE_GUIDE.md` at the repository root is the authoritative style document.
