# PROTOTYPE - rear-view experiment (wayfinder #18)

**Throwaway code that answers one question.** It is not app code, it is not on the
route to the product, and nothing here should be imported by anything. It exists
to settle whether landmark quality collapses on rear-facing poses, offline,
before any iOS pipeline is built.

Findings and verdict: [`docs/research/rear-view-experiment.md`](../../docs/research/rear-view-experiment.md).

## Run it

```
./run.sh
```

Bootstraps a venv (this box has no `pip` and no `ensurepip`, so pip comes from
`get-pip.py`), downloads COCO val2017 and three engines' weights into
`~/.cache/poseperfect-rearview`, runs the sweep, writes `results/`. CPU only,
about 5 minutes for the sweep after the ~1 GB of downloads.

Nothing is installed outside `.venv` and `~/.cache/poseperfect-rearview`.

## What it does

Four engines over a 1,675-instance COCO val2017 cohort, bucketed by a
visibility-derived orientation proxy, scoring **two separate failure modes**
that are never merged into one accuracy number:

- **positional error** - OKS / PCK against ground-truth keypoints, measured
  after correcting chirality. Tolerable if systematic, because it cancels when
  an athlete is scored against their own earlier reference.
- **chirality error** - whether the engine's `left_shoulder` is the athlete's
  anatomical left shoulder. Fatal, because it is bimodal rather than systematic.

Engines: MediaPipe BlazePose heavy and full (the suspect - face-anchored person
detector), MoveNet SinglePose Thunder (the control - no face anchor, no
detector), RTMPose-m (third architecture, general detector).

**IMAGE mode / static single-image inference throughout.** VIDEO and
LIVE_STREAM are non-deterministic and let a wrong front/back interpretation
latch through the ROI feedback loop; IMAGE mode is what the product will use.

## Files

| | |
|---|---|
| `cohort.py` | cohort construction and the orientation proxy, with its limits documented |
| `engines.py` | one adapter per engine, each remapping to the COCO 17-keypoint schema |
| `run_experiment.py` | the sweep and the metrics |
| `analyse.py` | tables, confidence intervals, robustness checks |
| `results/per_instance.csv` | one row per (instance, engine) - the raw result |
| `results/predictions.jsonl` | raw predicted keypoints, so every number can be rechecked without re-running |
| `results/summary.md`, `summary.json`, `summary_extra.json` | the computed tables |

## Two things to know before reading any of it

1. **Never validate by eye.** The BlazePose model card states occluded points
   are annotated with a "best guess and default pose", so failures are smooth,
   stable and visually plausible. A rear-view skeleton overlay looks completely
   reasonable while tracking a learned average human. Nothing here renders an
   overlay, deliberately. Every number is scored against ground truth.
2. **Never filter on engine confidence.** It is a known-broken signal on
   exactly these inputs, and the experiment measures how broken rather than
   relying on it.
