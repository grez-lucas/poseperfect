## 0. Cohort and proxy validation

| orientation | n | facing_away_by_gt_shoulders | ears_visible_mean | median_bbox_h |
|---|---|---|---|---|
| FRONT | 832 | 0.034 | 1.256 | 251.850 |
| OBLIQUE | 384 | 0.326 | 0.979 | 198.500 |
| PROFILE | 96 | 0.510 | 0.979 | 181.950 |
| REAR | 363 | 0.807 | 1.014 | 162.200 |

`facing_away_by_gt_shoulders` is the fraction of instances whose ANNOTATED right shoulder lies to the viewer's right - a second, independent read on orientation from the same ground truth. It is what bounds contamination of the visibility-derived proxy.


## 1. Detection failure rate (the face-anchored-detector hypothesis)

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.073 | 0.069 | 0.000 | 0.000 |
| OBLIQUE | 0.188 | 0.169 | 0.000 | 0.000 |
| PROFILE | 0.198 | 0.188 | 0.000 | 0.000 |
| REAR | 0.311 | 0.300 | 0.000 | 0.000 |

## 2. Chirality error - swap rate (THE FATAL ONE)

An instance is `swapped` when the engine's output matches the ground truth better after transposing every left/right landmark label than it does as emitted. Scored on torso and limb pairs at GT v==2 only, normalised by sqrt(COCO area).

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.040 | 0.031 | 0.008 | 0.005 |
| OBLIQUE | 0.109 | 0.094 | 0.047 | 0.026 |
| PROFILE | 0.130 | 0.090 | 0.042 | 0.000 |
| REAR | 0.156 | 0.154 | 0.094 | 0.019 |

### 2b. Swap rate with 95% Wilson intervals, sign-confirmed buckets

| engine | bucket | n | swap rate | 95% CI |
|---|---|---|---|---|
| blazepose_full | FRONT (sign-confirmed) | 743 | 0.035 | 0.024 - 0.051 |
| blazepose_full | REAR (sign-confirmed) | 207 | 0.159 | 0.116 - 0.215 |
| blazepose_heavy | FRONT (sign-confirmed) | 747 | 0.027 | 0.017 - 0.041 |
| blazepose_heavy | REAR (sign-confirmed) | 209 | 0.144 | 0.102 - 0.198 |
| movenet_thunder | FRONT (sign-confirmed) | 804 | 0.006 | 0.003 - 0.014 |
| movenet_thunder | REAR (sign-confirmed) | 293 | 0.072 | 0.047 - 0.107 |
| rtmpose_m | FRONT (sign-confirmed) | 804 | 0.004 | 0.001 - 0.011 |
| rtmpose_m | REAR (sign-confirmed) | 293 | 0.010 | 0.003 - 0.030 |

### 2c. Decisive swaps only (|margin| > 0.05 sqrt-area units)

Guards against near-symmetric standing poses where the two hypotheses are all but tied and the label is noise.

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.010 | 0.007 | 0.005 | 0.001 |
| OBLIQUE | 0.026 | 0.025 | 0.017 | 0.017 |
| PROFILE | 0.067 | 0.034 | 0.012 | 0.000 |
| REAR | 0.065 | 0.048 | 0.046 | 0.017 |

Fraction of instances that are decisive at all:

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.869 | 0.877 | 0.976 | 0.990 |
| OBLIQUE | 0.740 | 0.765 | 0.896 | 0.932 |
| PROFILE | 0.779 | 0.756 | 0.875 | 0.979 |
| REAR | 0.744 | 0.740 | 0.890 | 0.964 |

## 3. Positional error, chirality-corrected (the tolerable one)

OKS over GT keypoints at v==2, computed AFTER applying the left/right correction, so this number is positional error with the chirality failure removed. This is the quantity that cancels when an athlete is scored against their own reference.

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.748 | 0.773 | 0.907 | 0.950 |
| OBLIQUE | 0.688 | 0.720 | 0.864 | 0.924 |
| PROFILE | 0.669 | 0.701 | 0.840 | 0.929 |
| REAR | 0.663 | 0.673 | 0.818 | 0.930 |

### 3b. OKS as emitted (chirality error left in)

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.746 | 0.771 | 0.906 | 0.950 |
| OBLIQUE | 0.683 | 0.717 | 0.862 | 0.924 |
| PROFILE | 0.646 | 0.687 | 0.838 | 0.929 |
| REAR | 0.649 | 0.665 | 0.802 | 0.921 |

### 3c. PCK@0.2 sqrt(area), chirality-corrected

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.827 | 0.840 | 0.964 | 0.992 |
| OBLIQUE | 0.779 | 0.794 | 0.933 | 0.980 |
| PROFILE | 0.756 | 0.777 | 0.910 | 0.983 |
| REAR | 0.723 | 0.727 | 0.871 | 0.977 |

### 3d. Degradation with facing-away, sign-confirmed FRONT vs REAR

| engine | OKS corr FRONT | OKS corr REAR | delta | OKS raw FRONT | OKS raw REAR | delta |
|---|---|---|---|---|---|---|
| blazepose_full | 0.753 | 0.674 | -0.079 | 0.751 | 0.661 | -0.090 |
| blazepose_heavy | 0.777 | 0.690 | -0.087 | 0.776 | 0.685 | -0.091 |
| movenet_thunder | 0.910 | 0.832 | -0.078 | 0.909 | 0.820 | -0.089 |
| rtmpose_m | 0.952 | 0.934 | -0.018 | 0.952 | 0.930 | -0.021 |

## 4. The shoulder-sign heuristic

`sign(RIGHT_SHOULDER.x - LEFT_SHOULDER.x)` on the PREDICTED landmarks, scored against the same sign computed on the ANNOTATED shoulders. Unconditioned - full proxy buckets, no sign filtering, so this is not circular.

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.970 | 0.977 | 0.982 | 0.989 |
| OBLIQUE | 0.869 | 0.893 | 0.898 | 0.938 |
| PROFILE | 0.818 | 0.821 | 0.844 | 0.927 |
| REAR | 0.836 | 0.846 | 0.895 | 0.956 |

### 4b. Overall accuracy and rear recall

| engine | overall acc | REAR acc | n REAR | FRONT acc | n FRONT |
|---|---|---|---|---|---|
| blazepose_full | 0.916 | 0.836 | 250 | 0.970 | 771 |
| blazepose_heavy | 0.926 | 0.846 | 254 | 0.977 | 775 |
| movenet_thunder | 0.936 | 0.895 | 363 | 0.982 | 832 |
| rtmpose_m | 0.967 | 0.956 | 363 | 0.989 | 832 |

## 5. Is confidence usable as a self-check?

Mean per-landmark confidence. BlazePose reports `visibility`; MoveNet and RTMPose report a keypoint score. The question is whether any of them falls on the inputs where the engine is wrong.


**nose**

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.999 | 0.995 | 0.560 | 0.970 |
| OBLIQUE | 0.997 | 0.996 | 0.503 | 0.902 |
| PROFILE | 0.994 | 0.998 | 0.438 | 0.857 |
| REAR | 0.993 | 0.985 | 0.251 | 0.700 |

**eyes**

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.998 | 0.994 | 0.579 | 0.999 |
| OBLIQUE | 0.996 | 0.995 | 0.465 | 0.901 |
| PROFILE | 0.993 | 0.998 | 0.412 | 0.838 |
| REAR | 0.992 | 0.983 | 0.252 | 0.681 |

**shoulders**

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.999 | 0.999 | 0.643 | 0.792 |
| OBLIQUE | 0.999 | 0.999 | 0.573 | 0.745 |
| PROFILE | 0.998 | 0.997 | 0.524 | 0.747 |
| REAR | 0.991 | 0.992 | 0.552 | 0.747 |

**all 17**

| orientation | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| FRONT | 0.873 | 0.831 | 0.538 | 0.799 |
| OBLIQUE | 0.844 | 0.810 | 0.473 | 0.742 |
| PROFILE | 0.837 | 0.796 | 0.449 | 0.729 |
| REAR | 0.833 | 0.782 | 0.428 | 0.693 |

### 5b. Confidence on the instances the engine got CHIRALLY WRONG

| engine | n swapped | mean conf (all 17) on swapped | mean conf on correct | conf_nose on swapped |
|---|---|---|---|---|
| blazepose_full | 114 | 0.803 | 0.862 | 0.993 |
| blazepose_heavy | 100 | 0.744 | 0.821 | 0.978 |
| movenet_thunder | 63 | 0.356 | 0.499 | 0.340 |
| rtmpose_m | 21 | 0.631 | 0.760 | 0.768 |

## 6. Where degradation begins

The proxy is ordinal, not angular: `face_visible` counts how many of {nose, left_eye, right_eye} the annotator marked v==2. It is a monotone stand-in for turning away from the camera. There is no degree axis without MEBOW.

**OKS, chirality-corrected, by face_visible (3 = fully frontal face, 0 = no face keypoint visible)**

| face_visible | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| 3 | 0.748 | 0.773 | 0.907 | 0.950 |
| 2 | 0.688 | 0.720 | 0.864 | 0.924 |
| 1 | 0.669 | 0.701 | 0.840 | 0.929 |
| 0 | 0.663 | 0.673 | 0.818 | 0.930 |

**Chirality swap rate by face_visible**

| face_visible | blazepose_full | blazepose_heavy | movenet_thunder | rtmpose_m |
|---|---|---|---|---|
| 3 | 0.040 | 0.031 | 0.008 | 0.005 |
| 2 | 0.109 | 0.094 | 0.047 | 0.026 |
| 1 | 0.130 | 0.090 | 0.042 | 0.000 |
| 0 | 0.156 | 0.154 | 0.094 | 0.019 |

## 7. Robustness checks and the product-level composite

### 7a. Size confound control

REAR instances are smaller than FRONT in COCO, so the raw comparison confounds viewpoint with scale. Repeated inside size bands.


**detection failure rate, FRONT vs REAR within size band**

| size band | engine | FRONT | REAR | n FRONT | n REAR |
|---|---|---|---|---|---|
| 100-200px | blazepose_full | 0.136 | 0.298 | 308 | 198 |
| 100-200px | blazepose_heavy | 0.140 | 0.293 | 308 | 198 |
| 100-200px | movenet_thunder | 0.000 | 0.000 | 308 | 198 |
| 100-200px | rtmpose_m | 0.000 | 0.000 | 308 | 198 |
| 200-300px | blazepose_full | 0.050 | 0.316 | 159 | 57 |
| 200-300px | blazepose_heavy | 0.044 | 0.298 | 159 | 57 |
| 200-300px | movenet_thunder | 0.000 | 0.000 | 159 | 57 |
| 200-300px | rtmpose_m | 0.000 | 0.000 | 159 | 57 |
| >300px | blazepose_full | 0.033 | 0.237 | 337 | 38 |
| >300px | blazepose_heavy | 0.021 | 0.237 | 337 | 38 |
| >300px | movenet_thunder | 0.000 | 0.000 | 337 | 38 |
| >300px | rtmpose_m | 0.000 | 0.000 | 337 | 38 |

**chirality swap rate, FRONT vs REAR within size band**

| size band | engine | FRONT | REAR | n FRONT | n REAR |
|---|---|---|---|---|---|
| 100-200px | blazepose_full | 0.053 | 0.151 | 266 | 139 |
| 100-200px | blazepose_heavy | 0.034 | 0.143 | 265 | 140 |
| 100-200px | movenet_thunder | 0.013 | 0.081 | 308 | 198 |
| 100-200px | rtmpose_m | 0.006 | 0.015 | 308 | 198 |
| 200-300px | blazepose_full | 0.026 | 0.128 | 151 | 39 |
| 200-300px | blazepose_heavy | 0.026 | 0.100 | 152 | 40 |
| 200-300px | movenet_thunder | 0.006 | 0.088 | 159 | 57 |
| 200-300px | rtmpose_m | 0.000 | 0.000 | 159 | 57 |
| >300px | blazepose_full | 0.025 | 0.241 | 326 | 29 |
| >300px | blazepose_heavy | 0.021 | 0.207 | 330 | 29 |
| >300px | movenet_thunder | 0.000 | 0.000 | 337 | 38 |
| >300px | rtmpose_m | 0.003 | 0.000 | 337 | 38 |

**OKS (chirality-corrected), FRONT vs REAR within size band**

| size band | engine | FRONT | REAR | n FRONT | n REAR |
|---|---|---|---|---|---|
| 100-200px | blazepose_full | 0.677 | 0.659 | 266 | 139 |
| 100-200px | blazepose_heavy | 0.704 | 0.674 | 265 | 140 |
| 100-200px | movenet_thunder | 0.880 | 0.821 | 308 | 198 |
| 100-200px | rtmpose_m | 0.940 | 0.932 | 308 | 198 |
| 200-300px | blazepose_full | 0.744 | 0.743 | 151 | 39 |
| 200-300px | blazepose_heavy | 0.782 | 0.740 | 152 | 40 |
| 200-300px | movenet_thunder | 0.918 | 0.832 | 159 | 57 |
| 200-300px | rtmpose_m | 0.958 | 0.935 | 159 | 57 |
| >300px | blazepose_full | 0.819 | 0.656 | 326 | 29 |
| >300px | blazepose_heavy | 0.833 | 0.699 | 330 | 29 |
| >300px | movenet_thunder | 0.934 | 0.890 | 337 | 38 |
| >300px | rtmpose_m | 0.960 | 0.940 | 337 | 38 |

### 7b. Product-level composite: fraction of captures that are USABLE

A capture is usable only if the engine returns a pose AND that pose is not chirally transposed. Non-detections count as failures - the app cannot score what it did not get. This is the number that matters to a rear-facing mandatory pose.

| engine | FRONT usable | REAR usable | n FRONT | n REAR |
|---|---|---|---|---|
| blazepose_full | 0.892 | 0.594 | 804 | 293 |
| blazepose_heavy | 0.904 | 0.611 | 804 | 293 |
| movenet_thunder | 0.994 | 0.928 | 804 | 293 |
| rtmpose_m | 0.996 | 0.990 | 804 | 293 |

### 7c. Can the shoulder-sign heuristic DETECT the chirality swap?

The heuristic reads facing direction off the same predicted landmarks that are swapped. If the two agree almost perfectly, the heuristic is not an independent check - it is the failure, restated.

| engine | agreement(sign wrong == swapped) | swaps caught (recall) | false alarms | n |
|---|---|---|---|---|
| blazepose_full | 0.928 | 0.579 | 0.445 | 1410 |
| blazepose_heavy | 0.945 | 0.630 | 0.400 | 1426 |
| movenet_thunder | 0.952 | 0.714 | 0.579 | 1675 |
| rtmpose_m | 0.971 | 0.667 | 0.750 | 1675 |

### 7d. AUC of confidence as a detector of the chirality swap

0.50 = the confidence signal carries no information about whether the engine got chirality right. Computed on REAR instances only.

| engine | AUC conf_mean | AUC conf_nose | n swapped | n correct |
|---|---|---|---|---|
| blazepose_full | 0.570 | 0.655 | 39 | 211 |
| blazepose_heavy | 0.564 | 0.528 | 39 | 215 |
| movenet_thunder | 0.759 | 0.486 | 34 | 329 |
| rtmpose_m | 0.756 | 0.642 | 7 | 356 |

### 7e. Is the chirality failure a COHERENT global mirror, or piecewise?

Chirality is decided independently for four limb groups (shoulders, hips, arms, legs). If a rear-view failure were a clean global front/back flip, every group would agree, and a downstream fix could recover it by transposing all labels. If groups disagree, the output is internally inconsistent and no relabelling recovers it.

| engine | bucket | n with 4 groups decided | all-4 agree | all-4 swapped | mixed (incoherent) |
|---|---|---|---|---|---|
| blazepose_full | FRONT | 498 | 0.890 | 0.008 | 0.110 |
| blazepose_full | REAR | 121 | 0.843 | 0.074 | 0.157 |
| blazepose_heavy | FRONT | 503 | 0.897 | 0.004 | 0.103 |
| blazepose_heavy | REAR | 121 | 0.810 | 0.033 | 0.190 |
| movenet_thunder | FRONT | 538 | 0.959 | 0.004 | 0.041 |
| movenet_thunder | REAR | 154 | 0.896 | 0.019 | 0.104 |
| rtmpose_m | FRONT | 538 | 0.974 | 0.000 | 0.026 |
| rtmpose_m | REAR | 154 | 0.974 | 0.006 | 0.026 |

**Per-group swap rate, sign-confirmed REAR**

| engine | shoulders | hips | arms | legs |
|---|---|---|---|---|
| blazepose_full | 0.155 | 0.164 | 0.129 | 0.176 |
| blazepose_heavy | 0.148 | 0.153 | 0.115 | 0.136 |
| movenet_thunder | 0.085 | 0.075 | 0.049 | 0.100 |
| rtmpose_m | 0.027 | 0.020 | 0.011 | 0.025 |

### 7f. Two-proportion z-tests on the REAR swap rate

Wilson intervals for two proportions can overlap while the difference is still significant, so the comparison is tested directly. Sign-confirmed REAR only.

| comparison | p1 | p2 | z | two-sided p |
|---|---|---|---|---|
| blazepose_heavy vs movenet_thunder | 0.144 (n=209) | 0.072 (n=293) | 2.63 | 0.0086 |
| blazepose_full vs movenet_thunder | 0.159 (n=207) | 0.072 (n=293) | 3.11 | 0.0018 |
| movenet_thunder vs rtmpose_m | 0.072 (n=293) | 0.010 (n=293) | 3.75 | 0.0002 |
| blazepose_heavy vs rtmpose_m | 0.144 (n=209) | 0.010 (n=293) | 5.94 | 0.0000 |
