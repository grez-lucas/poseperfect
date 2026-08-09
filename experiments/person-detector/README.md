# PROTOTYPE - person detector experiment (wayfinder #19)

**Throwaway code that answers one question.** It is not app code, it is not on
the route to the product, and nothing here should be imported by anything. It
exists to settle which person detector goes in front of RTMPose-m, offline,
before any iOS pipeline is built.

Findings and verdict: [`docs/research/person-detector.md`](../../docs/research/person-detector.md).

## Run it

```
./run.sh
```

Requires `experiments/rear-view/run.sh` to have been run first, because this
experiment **reuses that experiment's COCO cohort, crop construction and
chirality test verbatim** rather than rebuilding them. That reuse is the point:
it is what makes these numbers directly comparable to `rear-view-experiment.md`.

Nothing is installed outside `.venv310` and `~/.cache/poseperfect-detector`.

## What it does

Three questions, one sweep over the same 1,675-instance COCO val2017 cohort:

1. **Is the detector rear-view competent in its own right?** BlazePose's
   face-anchored detector returned nothing on 30.0% of rear instances under
   these exact conditions. That is the bar a replacement has to clear, and the
   whole reason BlazePose was rejected.
2. **What does RTMPose-m's chirality swap rate become with a real detector?**
   Ticket #18 ran RTMPose on ground-truth boxes, so its 1.0% rear swap rate is
   a pose-head upper bound. Here the identical pose model is re-run on the box
   the detector actually produced, against a `gt_box` baseline row recomputed
   in the same process.
3. **How good is the instance mask, specifically on rear views?** Mask IoU,
   precision and recall against the COCO ground-truth segmentation, bucketed by
   the #18 orientation proxy. Precision and recall are kept apart because a
   mask that *clips* a flared lat is a different failure from one that bleeds
   into the background, and only the first destroys a width measurement.

Detectors: **RTMDet-Ins-tiny** and **RTMDet-Ins-s** from MMDetection
(Apache-2.0, COCO-only training, mask-emitting), plus **RTMDet-nano-person**,
the box-only detector MMPose's own RTMPose project recommends - measured as the
comparison point, **not** as a shippable candidate, because it is trained on
Objects365 and Objects365 is academic-use-only. See the writeup.

## Files

| | |
|---|---|
| `bootstrap_mmdet.sh` | the Python 3.10 environment, kept apart from rear-view's 3.12 one |
| `fetch_weights.sh` | official OpenMMLab checkpoints, with SHA256s printed |
| `detectors.py` | one adapter per detector, returning every person detection with no score threshold |
| `run_experiment.py` | the sweep |
| `sweep.sh` | runs the sweep as concurrent shards and concatenates them |
| `run_fullimage.py` | the harder control - the whole source image instead of the crop |
| `analyse.py` | tables, Wilson intervals, two-proportion z-tests |
| `export_onnx.sh` | RTMDet-Ins to ONNX via MMDeploy's own deploy config for this model |
| `bench_onnx.py` | exported graph sizes and ONNX Runtime CPU latency |
| `results/per_instance.csv` | one row per (instance, detector), plus a `gt_box` baseline row |
| `results/summary.md`, `summary.json` | the computed tables |
| `results/onnx_cost.json` | sizes and latency |

## Three things to know before reading any of it

1. **Never validate by eye.** Map constraint 2. Nothing here renders an
   overlay, deliberately. Every number is scored against COCO ground truth -
   keypoints for the pose, boxes and instance masks for the detector.
2. **No score threshold is applied when recording.** Every person detection the
   model returns is written out with its score, and thresholds are swept in
   `analyse.py`. Map constraint 3 forbids gating on engine confidence; the
   honest treatment of a detector score is to measure how much the answer moves
   with it, not to pick one and hide the choice.
3. **The ONNX latency numbers are x86-64 Linux, not iOS.** They order the
   candidates and give an order of magnitude. They are not a device
   measurement, and the writeup says so in the same words.
