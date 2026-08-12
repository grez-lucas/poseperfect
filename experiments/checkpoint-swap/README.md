# PROTOTYPE - checkpoint swap experiment (wayfinder #20)

**Throwaway code that answers one question.** It is not app code, it is not on
the route to the product, and nothing here should be imported by anything. It
exists to price one swap: replacing RTMPose-m `body7`, which is trained on MPII
and therefore carries MPII's "Commercial use is not allowed", with RTMPose-m
`aic-coco`, which is not.

Findings and verdict: [`docs/research/checkpoint-licences.md`](../../docs/research/checkpoint-licences.md).

## Run it

```
./run.sh
```

Requires `experiments/rear-view/run.sh` to have been run first, because this
experiment **reuses that experiment's COCO cohort, crop construction and
chirality test verbatim**, and it shares ticket #19's Python 3.10 environment
(`experiments/person-detector/.venv310`) rather than building a second one.
That reuse is the point: it is what makes these numbers directly comparable to
`rear-view-experiment.md` and `person-detector.md`.

Nothing is installed outside `../person-detector/.venv310`,
`~/.cache/poseperfect-detector` and `~/.cache/poseperfect-checkpoint-swap`.

## What it does

`aic-coco` publishes 74.9 -> 75.8 AP on COCO against `body7`, so on paper the
swap is free. Published COCO AP is a whole-dataset average and says nothing
about rear views, which is the entire reason ticket #18 existed. This sweep
puts the two checkpoints on #18's 1,675-instance cohort and reports the
**chirality swap rate on rear-facing instances**, which is the number the
product actually depends on.

Four pose arms over that cohort, each run on two box sources:

| arm | where the graph came from | supervised pose training data |
|---|---|---|
| `body7_official` | the official ONNX bundle from `download.openmmlab.com/.../onnx_sdk/`, i.e. **the exact graph #18 and #19 ran** | AIC, COCO, CrowdPose, MPII, sub-JHMDB, Halpe, PoseTrack18 |
| `body7_self` | the same `body7` weights, exported to ONNX here by MMDeploy | same |
| `aic_coco_self` | the `aic-coco` weights, exported to ONNX here by MMDeploy | AIC + COCO |
| `coco_self` | the `simcc-coco` weights, exported to ONNX here by MMDeploy | **COCO alone** (backbone pretraining is `pt-aic-coco`) |

Box sources: `gt_box` (COCO's annotated box, #18's condition) and
`rtmdet_ins_tiny` (the detector #19 chose, #19's condition).

**`body7_self` is the control and it is not optional.** Neither `aic-coco` nor
`simcc-coco` ships an official ONNX, so their graphs have to be produced here;
without a self-exported `body7` arm there would be no way to tell a checkpoint
difference from an export artefact. If `body7_self` reproduces `body7_official`,
the other two arms' numbers are about their checkpoints.

**On `coco_self`, because the name is easy to misread.** MMPose's naming is
`simcc-<supervised pose training set>` and `pt-<backbone pretraining set>`. So
`rtmpose-m_simcc-coco_pt-aic-coco` is keypoint-supervised on COCO alone, with a
backbone pretrained on AIC+COCO. It is published in MMPose's MAIN COCO model
zoo (`configs/body_2d_keypoint/rtmpose/coco/rtmpose_coco.md`), not in
`projects/rtmpose/README.md`, which is why #19 concluded no COCO-only RTMPose-m
existed.

## How the committed results were produced

`run.sh` sweeps all four arms in one pass. The committed `results/` were
produced in **two** passes - three arms, then `coco_self` alone - and
concatenated. That is equivalent, and the equivalence is checkable rather than
asserted: the arms are independent per instance, and the detector runs once per
instance on a deterministic crop, so the second pass reproduces the identical
box. `analyse.py` verifies it and refuses to merge if the detector columns
disagree.

## Files

| | |
|---|---|
| `bootstrap.sh` | reuses #19's `bootstrap_mmdet.sh`, then adds mmpose and rtmlib |
| `fetch_weights.sh` | both official OpenMMLab checkpoints plus the official body7 ONNX bundle, with SHA256s printed |
| `export_onnx.sh` | both checkpoints to ONNX via MMDeploy, using the command MMPose's own README documents |
| `run_experiment.py` | the sweep |
| `sweep.sh` | runs the sweep as concurrent shards and concatenates them |
| `analyse.py` | tables, Wilson intervals, two-proportion z-tests |
| `bench_onnx.py` | exported graph sizes and ONNX Runtime CPU latency |
| `results/per_instance.csv` | one row per (instance, pose arm, box source) |
| `results/summary.md`, `summary.json` | the computed tables |
| `results/run_meta.json` | checkpoints, SHA256s, versions, cost |

## Three things to know before reading any of it

1. **Never validate by eye.** Map constraint 2. Nothing here renders an
   overlay, deliberately. Every number is scored against COCO ground truth.
2. **No score threshold is applied when recording.** Map constraint 3. Same
   discipline as #18 and #19.
3. **This experiment settles accuracy, not licensing.** Whether a dataset use
   restriction reaches a model trained on that dataset is explicitly out of
   scope for ticket #20 and is recorded as a risk, not resolved.
