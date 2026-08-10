# Ticket #19 - person detector sweep

Cohort, crop and chirality test reused verbatim from `experiments/rear-view/` (ticket #18). CPU, IMAGE mode, no score threshold applied at record time.

## 0. Cohort

| orientation | n | facing_away_by_gt_shoulders | median_bbox_h |
|---|---|---|---|
| FRONT | 832 | 0.034 | 251.850 |
| OBLIQUE | 384 | 0.326 | 198.500 |
| PROFILE | 96 | 0.510 | 181.950 |
| REAR | 363 | 0.807 | 162.200 |

## 1. Does the detector find a person who is facing away?

Top-1 person detection matching the ground-truth box at IoU >= 0.5. Rate [95% Wilson CI] n.

| orientation | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|
| FRONT | 0.812 [0.785, 0.838] n=832 | 0.877 [0.853, 0.898] n=832 | 0.805 [0.777, 0.831] n=832 |
| OBLIQUE | 0.854 [0.815, 0.886] n=384 | 0.878 [0.841, 0.907] n=384 | 0.836 [0.796, 0.870] n=384 |
| PROFILE | 0.781 [0.689, 0.852] n=96 | 0.833 [0.746, 0.895] n=96 | 0.802 [0.711, 0.869] n=96 |
| REAR | 0.799 [0.755, 0.837] n=363 | 0.837 [0.796, 0.872] n=363 | 0.780 [0.734, 0.819] n=363 |

Any returned person detection matching at IoU >= 0.5 (upper bound on what a smarter selection rule could reach):

| orientation | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|
| FRONT | 0.999 [0.993, 1.000] n=832 | 0.998 [0.991, 0.999] n=832 | 1.000 [0.995, 1.000] n=832 |
| OBLIQUE | 0.995 [0.981, 0.999] n=384 | 0.997 [0.985, 1.000] n=384 | 1.000 [0.990, 1.000] n=384 |
| PROFILE | 1.000 [0.962, 1.000] n=96 | 1.000 [0.962, 1.000] n=96 | 1.000 [0.962, 1.000] n=96 |
| REAR | 1.000 [0.990, 1.000] n=363 | 1.000 [0.990, 1.000] n=363 | 1.000 [0.990, 1.000] n=363 |

Instances where the detector returned NO person detection at all - the failure mode that took BlazePose to 30.0% on rear views:

| orientation | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|
| FRONT | 0.000 [0.000, 0.005] n=832 | 0.000 [0.000, 0.005] n=832 | 0.000 [0.000, 0.005] n=832 |
| OBLIQUE | 0.000 [0.000, 0.010] n=384 | 0.000 [0.000, 0.010] n=384 | 0.000 [0.000, 0.010] n=384 |
| PROFILE | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.038] n=96 |
| REAR | 0.000 [0.000, 0.010] n=363 | 0.000 [0.000, 0.010] n=363 | 0.000 [0.000, 0.010] n=363 |

### 1b. Sensitivity to the detector score threshold

Top-1 hit rate at IoU >= 0.5 when the top-1 detection is additionally required to score at least `s`. Map constraint 3 forbids gating on engine confidence; this is here to show what a threshold would cost, not to pick one.

| score | rtmdet_ins_s FRONT | rtmdet_ins_s OBLIQUE | rtmdet_ins_s PROFILE | rtmdet_ins_s REAR | rtmdet_ins_tiny FRONT | rtmdet_ins_tiny OBLIQUE | rtmdet_ins_tiny PROFILE | rtmdet_ins_tiny REAR | rtmdet_nano_person FRONT | rtmdet_nano_person OBLIQUE | rtmdet_nano_person PROFILE | rtmdet_nano_person REAR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s>=0.0 | 0.812 | 0.854 | 0.781 | 0.799 | 0.877 | 0.878 | 0.833 | 0.837 | 0.805 | 0.836 | 0.802 | 0.780 |
| s>=0.05 | 0.812 | 0.854 | 0.781 | 0.799 | 0.877 | 0.878 | 0.833 | 0.837 | 0.805 | 0.836 | 0.802 | 0.780 |
| s>=0.1 | 0.812 | 0.854 | 0.781 | 0.799 | 0.877 | 0.878 | 0.833 | 0.835 | 0.805 | 0.836 | 0.802 | 0.780 |
| s>=0.3 | 0.811 | 0.854 | 0.781 | 0.788 | 0.875 | 0.872 | 0.833 | 0.829 | 0.804 | 0.836 | 0.802 | 0.780 |
| s>=0.5 | 0.808 | 0.839 | 0.771 | 0.782 | 0.869 | 0.857 | 0.812 | 0.807 | 0.792 | 0.812 | 0.792 | 0.725 |
| s>=0.7 | 0.782 | 0.807 | 0.729 | 0.708 | 0.794 | 0.763 | 0.740 | 0.689 | 0.698 | 0.677 | 0.667 | 0.540 |

### 1c. Box quality where the detector did hit

Mean IoU of the top-1 box against the ground-truth box, hits only:

| orientation | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|
| FRONT | 0.913 | 0.912 | 0.916 |
| OBLIQUE | 0.906 | 0.903 | 0.907 |
| PROFILE | 0.893 | 0.885 | 0.898 |
| REAR | 0.899 | 0.896 | 0.892 |

## 2. RTMPose-m with a real detector instead of ground-truth boxes

Chirality swap rate - the fatal error, because it is bimodal rather than systematic. `gt_box` is ticket #18's condition, recomputed here on the identical instances.

| orientation | gt_box | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|---|
| FRONT | 0.005 [0.002, 0.012] n=832 | 0.058 [0.044, 0.076] n=832 | 0.026 [0.018, 0.040] n=832 | 0.049 [0.037, 0.066] n=832 |
| OBLIQUE | 0.026 [0.014, 0.047] n=384 | 0.076 [0.053, 0.106] n=384 | 0.076 [0.053, 0.106] n=384 | 0.091 [0.066, 0.124] n=384 |
| PROFILE | 0.000 [0.000, 0.038] n=96 | 0.073 [0.036, 0.143] n=96 | 0.094 [0.050, 0.169] n=96 | 0.062 [0.029, 0.130] n=96 |
| REAR | 0.019 [0.009, 0.039] n=363 | 0.094 [0.068, 0.128] n=363 | 0.063 [0.043, 0.093] n=363 | 0.099 [0.072, 0.134] n=363 |

Same, restricted to **sign-confirmed** instances (proxy label and annotated shoulder order agree) - the subset ticket #18 quoted in its verdict:

| orientation | gt_box | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|---|
| FRONT | 0.004 [0.001, 0.011] n=804 | 0.055 [0.041, 0.073] n=804 | 0.025 [0.016, 0.038] n=804 | 0.049 [0.036, 0.066] n=804 |
| REAR | 0.010 [0.003, 0.030] n=293 | 0.082 [0.056, 0.119] n=293 | 0.051 [0.031, 0.083] n=293 | 0.089 [0.061, 0.127] n=293 |

Two-proportion z-tests, ground-truth box vs each detector, on sign-confirmed REAR:

```json
{
  "rtmdet_ins_s": {
    "gt_box": "3/293",
    "detector": "24/293",
    "z": 4.138,
    "p": 0.0
  },
  "rtmdet_ins_tiny": {
    "gt_box": "3/293",
    "detector": "15/293",
    "z": 2.873,
    "p": 0.0041
  },
  "rtmdet_nano_person": {
    "gt_box": "3/293",
    "detector": "26/293",
    "z": 4.381,
    "p": 0.0
  }
}
```

### 2b. The deployable number: swap rate given the pipeline selected the right person

Restricted to instances where the top-1 detection matched the target at IoU >= 0.5. This isolates the cost of a real box from the cost of a naive highest-score selection rule in a crowded crop.

| orientation | gt_box | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|---|
| FRONT | 0.005 [0.002, 0.012] n=832 | 0.003 [0.001, 0.011] n=676 | 0.003 [0.001, 0.010] n=730 | 0.003 [0.001, 0.011] n=670 |
| OBLIQUE | 0.026 [0.014, 0.047] n=384 | 0.034 [0.019, 0.059] n=328 | 0.033 [0.018, 0.057] n=337 | 0.034 [0.019, 0.060] n=321 |
| PROFILE | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.049] n=75 | 0.000 [-0.000, 0.046] n=80 | 0.000 [0.000, 0.048] n=77 |
| REAR | 0.019 [0.009, 0.039] n=363 | 0.024 [0.012, 0.049] n=290 | 0.020 [0.009, 0.042] n=304 | 0.021 [0.010, 0.045] n=283 |

Same, sign-confirmed only:

| orientation | gt_box | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|---|
| FRONT | 0.004 [0.001, 0.011] n=804 | 0.003 [0.001, 0.011] n=656 | 0.003 [0.001, 0.010] n=706 | 0.003 [0.001, 0.011] n=647 |
| REAR | 0.010 [0.003, 0.030] n=293 | 0.008 [0.002, 0.030] n=239 | 0.012 [0.004, 0.035] n=251 | 0.017 [0.007, 0.042] n=238 |

Two-proportion z-tests against the ground-truth box, sign-confirmed REAR:

```json
{
  "rtmdet_ins_s": {
    "gt_box": "3/293",
    "detector": "2/239",
    "z": -0.222,
    "p": 0.824
  },
  "rtmdet_ins_tiny": {
    "gt_box": "3/293",
    "detector": "3/251",
    "z": 0.191,
    "p": 0.8487
  },
  "rtmdet_nano_person": {
    "gt_box": "3/293",
    "detector": "4/238",
    "z": 0.66,
    "p": 0.5093
  }
}
```

And the same conditioning applied to positional error:

| orientation | gt_box | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|---|
| FRONT | 0.950 | 0.953 | 0.954 | 0.953 |
| OBLIQUE | 0.925 | 0.927 | 0.926 | 0.931 |
| PROFILE | 0.929 | 0.932 | 0.930 | 0.931 |
| REAR | 0.930 | 0.935 | 0.936 | 0.936 |

Positional error, kept separate as the map requires. Mean OKS after correcting chirality:

| orientation | gt_box | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|---|
| FRONT | 0.950 | 0.781 | 0.844 | 0.773 |
| OBLIQUE | 0.925 | 0.795 | 0.818 | 0.787 |
| PROFILE | 0.929 | 0.729 | 0.778 | 0.748 |
| REAR | 0.930 | 0.754 | 0.798 | 0.743 |

Composite usable-capture rate, using ticket #18's definition - the detector found the subject (IoU >= 0.5) AND the resulting pose is not chirally transposed:

| orientation | rtmdet_ins_s | rtmdet_ins_tiny | rtmdet_nano_person |
|---|---|---|---|
| FRONT | 0.810 [0.782, 0.835] n=832 | 0.875 [0.851, 0.896] n=832 | 0.803 [0.774, 0.828] n=832 |
| OBLIQUE | 0.826 [0.784, 0.860] n=384 | 0.849 [0.810, 0.881] n=384 | 0.807 [0.765, 0.844] n=384 |
| PROFILE | 0.781 [0.689, 0.852] n=96 | 0.833 [0.746, 0.895] n=96 | 0.802 [0.711, 0.869] n=96 |
| REAR | 0.780 [0.734, 0.819] n=363 | 0.821 [0.778, 0.857] n=363 | 0.763 [0.717, 0.804] n=363 |

## 3. Segmentation quality, and specifically on rear views

Mask IoU of the top-1 detection's mask against the COCO ground-truth instance segmentation, hits only:

| orientation | rtmdet_ins_s | rtmdet_ins_tiny |
|---|---|---|
| FRONT | 0.883 | 0.878 |
| OBLIQUE | 0.868 | 0.861 |
| PROFILE | 0.849 | 0.845 |
| REAR | 0.855 | 0.846 |

Mask precision and recall, kept separate. For a lat spread the damaging failure is the mask CLIPPING the flared silhouette, which is a recall failure; bleeding into the background is a precision failure and costs a width measurement far less.

Mask recall (fraction of the true silhouette captured):

| orientation | rtmdet_ins_s | rtmdet_ins_tiny |
|---|---|---|
| FRONT | 0.937 | 0.933 |
| OBLIQUE | 0.925 | 0.919 |
| PROFILE | 0.922 | 0.920 |
| REAR | 0.917 | 0.914 |

Mask precision:

| orientation | rtmdet_ins_s | rtmdet_ins_tiny |
|---|---|---|
| FRONT | 0.939 | 0.938 |
| OBLIQUE | 0.936 | 0.932 |
| PROFILE | 0.918 | 0.915 |
| REAR | 0.929 | 0.922 |

Fraction of hits whose mask IoU clears 0.7, a rough 'silhouette is usable' bar:

| orientation | rtmdet_ins_s | rtmdet_ins_tiny |
|---|---|---|
| FRONT | 0.981 [0.967, 0.989] n=676 | 0.978 [0.965, 0.986] n=730 |
| OBLIQUE | 0.960 [0.933, 0.977] n=328 | 0.947 [0.917, 0.966] n=337 |
| PROFILE | 0.947 [0.871, 0.979] n=75 | 0.938 [0.862, 0.973] n=80 |
| REAR | 0.945 [0.912, 0.966] n=290 | 0.928 [0.893, 0.952] n=304 |

## 4. Detector cost on this box (CPU, PyTorch, not the shipped runtime)

| detector | median_ms | p90_ms |
|---|---|---|
| rtmdet_ins_s | 1742.9 | 2806.7 |
| rtmdet_ins_tiny | 1209.2 | 2005.8 |
| rtmdet_nano_person | 255.8 | 630.1 |

These are PyTorch-on-x86 numbers and are NOT an iOS estimate. The ONNX Runtime figures are in the writeup.

