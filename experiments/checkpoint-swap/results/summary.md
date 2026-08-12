# Ticket #20 - checkpoint swap sweep

Cohort, crop and chirality test reused verbatim from `experiments/rear-view/` (#18). Detector and pose scoring reused verbatim from `experiments/person-detector/` (#19). CPU, IMAGE mode, no score threshold applied at record time.

Arms: body7_official, body7_self, aic_coco_self.

Merge check: every arm saw the same detector box on all 1675 instances, across all 5 detector columns. The committed results were produced in two passes and concatenated; this is the check that makes that legitimate.

## 0. Cohort

| orientation | n | facing_away_by_gt_shoulders | median_bbox_h |
|---|---|---|---|
| FRONT | 832 | 0.034 | 251.850 |
| OBLIQUE | 384 | 0.326 | 198.500 |
| PROFILE | 96 | 0.510 | 181.950 |
| REAR | 363 | 0.807 | 162.200 |

## 1. The control: does the self-exported graph reproduce the official one?

`aic-coco` ships no official ONNX, so its graph had to be exported here. Without this check, any difference it shows could be an export artefact rather than a property of the weights. `body7` ships BOTH, so exporting it too gives a direct answer.

| | |
|---|---|
| rows compared | 3350 |
| max abs difference in corrected OKS | 2.264e-03 |
| mean abs difference in corrected OKS | 7.788e-07 |
| instances where the chirality verdict differs | 0 |

Sanity check in the other direction, so a null result cannot be a mislabelled file: `aic_coco_self` vs `body7_official` differ by mean 1.405e-02 and max 8.860e-01 corrected OKS. The two arms are genuinely different weights.


## 2. Chirality swap rate - the number this ticket exists for

Fatal failure mode, kept separate from positional error throughout. The engine's `left_shoulder` is not the athlete's left shoulder.

### 2a. On ground-truth boxes - #18's condition

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.005 [0.002, 0.012] n=832 | 0.005 [0.002, 0.012] n=832 | 0.001 [0.000, 0.007] n=832 |
| OBLIQUE | 0.026 [0.014, 0.047] n=384 | 0.026 [0.014, 0.047] n=384 | 0.031 [0.018, 0.054] n=384 |
| PROFILE | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.038] n=96 |
| REAR | 0.019 [0.009, 0.039] n=363 | 0.019 [0.009, 0.039] n=363 | 0.028 [0.015, 0.050] n=363 |

Sign-confirmed only (proxy label and annotated shoulder order agree) - the subset #18's verdict quoted:

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.004 [0.001, 0.011] n=804 | 0.004 [0.001, 0.011] n=804 | 0.001 [0.000, 0.007] n=804 |
| REAR | 0.010 [0.003, 0.030] n=293 | 0.010 [0.003, 0.030] n=293 | 0.010 [0.003, 0.030] n=293 |

### 2b. On RTMDet-Ins-tiny boxes, given correct selection - #19's condition, and the deployable one

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.003 [0.001, 0.010] n=730 | 0.003 [0.001, 0.010] n=730 | 0.003 [0.001, 0.010] n=730 |
| OBLIQUE | 0.033 [0.018, 0.057] n=337 | 0.033 [0.018, 0.057] n=337 | 0.030 [0.016, 0.054] n=337 |
| PROFILE | 0.000 [-0.000, 0.046] n=80 | 0.000 [-0.000, 0.046] n=80 | 0.000 [-0.000, 0.046] n=80 |
| REAR | 0.020 [0.009, 0.042] n=304 | 0.020 [0.009, 0.042] n=304 | 0.016 [0.007, 0.038] n=304 |

Sign-confirmed only:

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.003 [0.001, 0.010] n=706 | 0.003 [0.001, 0.010] n=706 | 0.003 [0.001, 0.010] n=706 |
| REAR | 0.012 [0.004, 0.035] n=251 | 0.012 [0.004, 0.035] n=251 | 0.004 [0.001, 0.022] n=251 |

### 2c. Two-proportion z-tests, each candidate against `body7_official`, on sign-confirmed instances

This is the test the swap decision rests on. A null result means the swap costs nothing measurable on the failure mode the product cares about; it does NOT mean the checkpoints are identical.


**REAR:**

```json
{
  "gt_box": {
    "body7_official": "3/293",
    "aic_coco_self": {
      "swaps": "3/293",
      "z": 0.0,
      "p": 1.0
    }
  },
  "rtmdet_ins_tiny": {
    "body7_official": "3/251",
    "aic_coco_self": {
      "swaps": "1/251",
      "z": -1.004,
      "p": 0.3154
    }
  }
}
```

**FRONT:**

```json
{
  "gt_box": {
    "body7_official": "3/804",
    "aic_coco_self": {
      "swaps": "1/804",
      "z": -1.001,
      "p": 0.3167
    }
  },
  "rtmdet_ins_tiny": {
    "body7_official": "2/706",
    "aic_coco_self": {
      "swaps": "2/706",
      "z": 0.0,
      "p": 1.0
    }
  }
}
```

FRONT is reported alongside REAR so a rear-specific claim is not made from a whole-cohort effect.


## 3. Positional error, kept separate as the map requires

Mean OKS after correcting chirality. Tolerable if systematic, because it cancels when an athlete is scored against their own earlier reference.

On ground-truth boxes:

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.9500 | 0.9500 | 0.9555 |
| OBLIQUE | 0.9249 | 0.9249 | 0.9315 |
| PROFILE | 0.9292 | 0.9292 | 0.9320 |
| REAR | 0.9297 | 0.9297 | 0.9325 |

On RTMDet-Ins-tiny boxes, given correct selection:

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.9536 | 0.9536 | 0.9576 |
| OBLIQUE | 0.9256 | 0.9256 | 0.9345 |
| PROFILE | 0.9300 | 0.9300 | 0.9340 |
| REAR | 0.9357 | 0.9357 | 0.9388 |

PCK@0.2 after correcting chirality, ground-truth boxes:

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.9919 | 0.9919 | 0.9938 |
| OBLIQUE | 0.9804 | 0.9804 | 0.9850 |
| PROFILE | 0.9828 | 0.9828 | 0.9825 |
| REAR | 0.9765 | 0.9765 | 0.9798 |

Raw OKS, i.e. before chirality correction. This is the number a single accuracy figure would report, and it merges the two failure modes the map insists on separating. Recorded, not headlined:

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.9501 | 0.9501 | 0.9552 |
| OBLIQUE | 0.9241 | 0.9241 | 0.9293 |
| PROFILE | 0.9292 | 0.9292 | 0.9320 |
| REAR | 0.9206 | 0.9206 | 0.9246 |

## 4. Composite usable-capture rate

#18's definition: the detector found the subject (IoU >= 0.5) AND the resulting pose is not chirally transposed. Over the whole detector arm, without conditioning on correct selection.

| orientation | body7_official | body7_self | aic_coco_self |
|---|---|---|---|
| FRONT | 0.875 [0.851, 0.896] n=832 | 0.875 [0.851, 0.896] n=832 | 0.875 [0.851, 0.896] n=832 |
| OBLIQUE | 0.849 [0.810, 0.881] n=384 | 0.849 [0.810, 0.881] n=384 | 0.852 [0.813, 0.884] n=384 |
| PROFILE | 0.833 [0.746, 0.895] n=96 | 0.833 [0.746, 0.895] n=96 | 0.833 [0.746, 0.895] n=96 |
| REAR | 0.821 [0.778, 0.857] n=363 | 0.821 [0.778, 0.857] n=363 | 0.824 [0.781, 0.859] n=363 |
