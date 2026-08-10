# Sourcing the person detector for RTMPose-m

Resolution of [#19](https://github.com/grez-lucas/poseperfect/issues/19), 2026-08-09. Grading convention matches `pose-engines.md`: **VERIFIED** = measured here or read from a primary source, **INFERRED** = reasoned from measurement, **ANECDOTAL** = reported by others.

Code, raw per-instance results and the ONNX export recipe: `experiments/person-detector/`. It reuses ticket [#18](https://github.com/grez-lucas/poseperfect/issues/18)'s cohort, crop construction and chirality test verbatim, so every number here sits on the same 1,675 COCO val2017 instances as `rear-view-experiment.md`.

---

## Verdict

*(written last - see the per-requirement sections below)*

---

## 1. Requirement 1 - licence-clean for a closed-source app, weights included

**This is the gate, and the honest finding is that nobody in this field grants you the weights in writing.** Reading the licences of nine candidate projects separately from their badges turned up exactly **one** project that states in words that its *model* is permissively licensed. It is not a person detector.

### 1.1 What each project actually says about its weights

**VERIFIED.** Code licence and weight licence read as two separate questions, from LICENSE files and READMEs rather than from package badges.

| Project | Code licence | Explicit statement covering the **weights**? |
|---|---|---|
| **Segment Anything** (Meta) | Apache-2.0 | **Yes, permissive.** "The model is licensed under the [Apache 2.0 license](LICENSE)." |
| **Detectron2** (Meta) | Apache-2.0 | **Yes, and it is copyleft.** "All models available for download through this document are licensed under the [Creative Commons Attribution-ShareAlike 3.0 license]" |
| **Ultralytics YOLO** | AGPL-3.0 | **Yes, and it is hostile.** "All Ultralytics YOLO trained models fall under the AGPL-3.0 License by default." |
| **torchvision** | BSD-3-Clause | **No - an explicit disclaimer.** "The pre-trained models provided in this library may have their own licenses or terms and conditions derived from the dataset used for training. It is your responsibility to determine whether you have permission to use the models for your use case." |
| **MMDetection** (RTMDet, RTMDet-Ins) | Apache-2.0 | No. Only "This project is released under the [Apache 2.0 license](LICENSE)." |
| **MMPose** (RTMPose) | Apache-2.0 | No. Same single sentence. |
| **YOLOX** (Megvii) | Apache-2.0 | No. The word "licence" does not appear in the README at all. |
| **MobileSAM** | Apache-2.0 | No. `weights/mobile_sam.pt` is committed in-tree, but the README has no licence section. |
| **PaddleSeg / PP-HumanSeg** | Apache-2.0 | No. Only marketing: "can be directly integrated into products at zero cost". |
| **YOLACT** | MIT | No. Weights re-hosted on HuggingFace with no stated terms. |

Sources: [ultralytics/LICENSE](https://raw.githubusercontent.com/ultralytics/ultralytics/main/LICENSE) and [ultralytics.com/license](https://www.ultralytics.com/license); [detectron2 MODEL_ZOO.md](https://github.com/facebookresearch/detectron2/blob/main/MODEL_ZOO.md); [segment-anything README](https://raw.githubusercontent.com/facebookresearch/segment-anything/main/README.md); [torchvision models.rst](https://raw.githubusercontent.com/pytorch/vision/main/docs/source/models.rst); [mmdetection README](https://raw.githubusercontent.com/open-mmlab/mmdetection/main/README.md) line 428; [mmpose README](https://raw.githubusercontent.com/open-mmlab/mmpose/main/README.md) line 328; [YOLOX LICENSE](https://raw.githubusercontent.com/Megvii-BaseDetection/YOLOX/main/LICENSE); [MobileSAM](https://github.com/ChaoningZhang/MobileSAM); [PP-HumanSeg README](https://raw.githubusercontent.com/PaddlePaddle/PaddleSeg/develop/contrib/PP-HumanSeg/README.md); [yolact README](https://raw.githubusercontent.com/dbolya/yolact/master/README.md).

**Two hard exclusions come straight out of that table.**

- **Ultralytics is confirmed blocked at the weight level, in Ultralytics' own words.** The map already treated YOLO as an AGPL blocker; this closes it. From [ultralytics.com/license](https://www.ultralytics.com/license): *"Are Ultralytics YOLO trained models licensed under the AGPL-3.0 license? Yes. All Ultralytics YOLO trained models fall under the AGPL-3.0 License by default. The AGPL-3.0 License covers the training code and the models produced by that training code."* And: *"An Enterprise License is required if you want to use Ultralytics YOLO without open-sourcing your entire project."*
- **Detectron2 is blocked for a reason nobody would guess from its badge.** The repo is Apache-2.0 and says so, but `MODEL_ZOO.md` grants the weights under **CC BY-SA 3.0**. ShareAlike on a shipped model is not compatible with a closed-source app without further legal work. This is the same shape of trap as the `pose_detection` 3.6.0 case in `pose-engines-flutter-routes.md`, inverted: there the permissive badge hid restrictive weights, here the permissive badge sits next to a restrictive weight grant *that the project states plainly* and that a badge-reader would never see.

### 1.2 Why the MMDetection silence is not the same defect as the `pose_detection` case

**VERIFIED, and this distinction is load-bearing.**

The ticket's precedent is `pose_detection` 3.6.0: an Apache-2.0 badge sitting on top of a 12.9 MB `yolov8n_float32.tflite` with no Ultralytics attribution and no AGPL mention. What made that bad was not the silence. It was that **the weights were produced by a different party whose own licence is known and incompatible**, and the packager's badge could not grant what the packager did not own.

RTMDet-Ins is not that. The relevant facts, each checked directly:

1. **The code is Apache-2.0.** [`mmdetection/LICENSE`](https://raw.githubusercontent.com/open-mmlab/mmdetection/main/LICENSE) line 1: *"Copyright 2018-2023 OpenMMLab. All rights reserved."*, followed by the Apache 2.0 text.
2. **The RTMDet source is OpenMMLab's own.** Every file on the RTMDet path - `models/backbones/cspnext.py`, `models/dense_heads/rtmdet_head.py`, `models/dense_heads/rtmdet_ins_head.py` - carries `# Copyright (c) OpenMMLab. All rights reserved.` The only reference to Ultralytics anywhere in the installed `mmdet` package is a comment in `models/dense_heads/yolo_head.py` (`# refer to https://github.com/ultralytics/yolov3`), which is the YOLOv3 head and is not on RTMDet's path.
3. **The weights are first-party.** `download.openmmlab.com/mmdetection/v3.0/rtmdet/...` is the same project that publishes the code. There is no third party whose licence could be being laundered.
4. **There is no separate weight grant, and that is a genuine gap.** Searched `README.md`, `docs/en/model_zoo.md` and `docs/en/notes/faq.md` in both MMDetection and MMPose. `grep -i licen` finds nothing but the badge and the one sentence. **State it plainly: OpenMMLab has never said in writing that its checkpoints are Apache-2.0.**

**INFERRED.** The residual risk is therefore "no express grant from a licensor who has no upstream obligation and publishes everything else permissively", not "a grant contradicted by a known incompatible upstream". That is a materially smaller risk than the `pose_detection` case, and it is identical in kind to the risk already accepted for RTMPose-m itself in [#16](https://github.com/grez-lucas/poseperfect/issues/16). **It is not zero, and it is Lucas's call to accept it, not mine.** Section 8 lists the options.

**One trap that would be easy to walk into.** RTMDet also ships in **MMYOLO**, and [MMYOLO is GPL-3.0](https://raw.githubusercontent.com/open-mmlab/mmyolo/main/LICENSE) - *"This project is released under the [GPL 3.0 license](LICENSE)."* Same model name, same organisation, different repository, copyleft licence. **Take RTMDet from `open-mmlab/mmdetection`, never from `open-mmlab/mmyolo`.** `experiments/person-detector/` uses MMDetection exclusively and records the checkpoint SHA256s.

### 1.3 The dataset layer, where the recommended detector actually fails

**VERIFIED, and this is the sharpest licence finding in the ticket.**

MMPose's RTMPose project recommends pairing RTMPose with `rtmdet_nano_8xb32-100e_coco-obj365-person`. That checkpoint's name states its training data: **COCO plus Objects365**. From the [Objects365 download page](https://www.objects365.org/download.html), verbatim:

> "The Objects365 dataset is available for the academic purpose only. Any researcher who uses the Objects365 dataset should obey the license as below: **Annotations & Website** The annotations in this dataset along with this website belong to the Objects365 Consortium and are licensed under a Creative Commons Attribution 4.0 License. **Images** The Objects365 Consortium does not own the copyright of the images. Use of images must abide by the Flickr Terms of Use."

**So the detector RTMPose's own documentation points you at is trained, in part, on a dataset whose publisher restricts it to academic purposes.** Whether that restriction reaches downstream model weights is unsettled law, but it is exactly the kind of unexamined inheritance this ticket exists to catch, and it is a strictly worse position than a COCO-only checkpoint.

**The RTMDet-Ins checkpoints do not have this problem.** [`rtmdet-ins_s_8xb32-300e_coco.py`](https://raw.githubusercontent.com/open-mmlab/mmdetection/main/configs/rtmdet/rtmdet-ins_s_8xb32-300e_coco.py) inherits `rtmdet-ins_l_8xb32-300e_coco.py`, whose dataset is COCO 2017 and nothing else. Its backbone is initialised from `cspnext-s_imagenet_600e.pth`, i.e. ImageNet - a restriction that attaches to essentially every vision model in existence, including the RTMPose-m the map has already committed to, and therefore not a discriminator between candidates.

**Bottom line on requirement 1.** No candidate passes a strict reading of "licence-clean, weights included", because only Segment Anything grants its weights at all and Segment Anything is not a person detector. Under the practical reading the map has already applied to RTMPose-m - first-party permissive project, first-party weights, no incompatible upstream, no restrictive training set beyond ImageNet - **RTMDet-Ins from MMDetection passes and is the best-positioned candidate in the field.** Ultralytics and Detectron2 fail outright. MMPose's own recommended detector fails on Objects365.

---

## 2. Requirement 2 - segmentation-capable

**VERIFIED. Yes, and from the same architecture family the pose model already comes from.**

**RTMDet-Ins** is RTMDet with an instance-segmentation head (`RTMDetInsSepBNHead`, a dynamic-kernel mask head with a Dice loss). It returns, per detection, a box, a score, a class and a binary instance mask. Published COCO numbers from [`configs/rtmdet/README.md`](https://raw.githubusercontent.com/open-mmlab/mmdetection/main/configs/rtmdet/README.md):

| Model | Box AP | Mask AP | Params (M) | FLOPs (G) |
|---|---|---|---|---|
| RTMDet-Ins-tiny | 40.5 | 35.4 | 5.6 | 11.8 |
| RTMDet-Ins-s | 44.0 | 38.7 | 10.18 | 21.5 |
| RTMDet-Ins-m | 48.8 | 42.1 | 27.58 | 54.13 |

That settles the *capability* question, which is what [#17](https://github.com/grez-lucas/poseperfect/issues/17) hangs on. Whether the masks are *good enough on a rear view* is a separate, measured question - section 5.

**What this means for the lat spreads.** [#16](https://github.com/grez-lucas/poseperfect/issues/16) decided the lat-spread silhouette should come from the detector rather than a second model, and that if nothing licence-clean emits a mask the lat spreads stay frame-only permanently and #17 resolves negative. A licence-clean, ONNX-exportable, mask-emitting detector exists, so **that branch does not trigger**.

---

## 3. Requirement 4 - ONNX on iOS via `flutter_onnxruntime`

Taken out of order because it constrains which variant is even worth measuring.

### 3.1 The export works, from the official checkpoint, with a first-party recipe

**VERIFIED by doing it.** MMDeploy ships a deploy config for this exact model: [`configs/mmdet/instance-seg/instance-seg_rtmdet-ins_onnxruntime_static-640x640.py`](https://github.com/open-mmlab/mmdeploy/blob/v1.3.1/configs/mmdet/instance-seg/instance-seg_rtmdet-ins_onnxruntime_static-640x640.py) - RTMDet-Ins, ONNX Runtime, static 640x640. `experiments/person-detector/export_onnx.sh` runs it against the checkpoint fetched from `download.openmmlab.com`, so nothing here depends on a third-party ONNX re-upload.

One upstream defect had to be worked around, and it is recorded in the script rather than hidden: **MMDeploy 1.3.1 cannot export RTMDet-Ins on a CPU-only machine.** Its mask head calls mmdet's `MlvlPointGenerator.single_level_grid_priors()` without a `device` argument, and that argument defaults to `'cuda'`, so the export aborts with `AssertionError: Torch not compiled with CUDA enabled`. A one-line patch passing `device=mask_feat.device` fixes it. MMDeploy's own verification stage then ran both the ONNX and the PyTorch model and reported `visualize onnxruntime model success` / `visualize pytorch model success`.

### 3.2 What lands in the IPA

**VERIFIED.** Exported fp32 graphs, measured on disk:

| File | Bytes | MiB |
|---|---|---|
| `rtmdet-ins_tiny` `end2end.onnx` (640x640) | 24,032,420 | **22.9** |
| `rtmdet-ins_s` `end2end.onnx` (640x640) | 43,237,040 | **41.2** |
| `rtmpose-m_simcc-body7_...onnx` (256x192) | 54,330,655 | **51.8** |

**So the shippable pair is roughly 75 MiB of fp32 weights** (RTMDet-Ins-tiny plus the RTMPose-m the map has already chosen), of which two thirds is the pose model that was already committed. Adding segmentation costs **22.9 MiB**, not a second model.

**Both graphs are stock ONNX and will load in any ORT build.** Read out of the exported files with `onnx`:

| | RTMDet-Ins-tiny | RTMPose-m |
|---|---|---|
| opset | `ai.onnx` 11 | `ai.onnx` 11 |
| operator domains | `''` only | `''` only |
| custom / contrib ops | none | none |
| input | `input` `[1, 3, 640, 640]` | `input` `[batch, 3, 256, 192]` |
| outputs | `dets [1, N, 5]`, `labels [1, N]`, `masks [N, 640, 640]` | `simcc_x`, `simcc_y` |

The detector graph is **end to end**: NMS is inside the graph (a single standard `NonMaxSuppression` node) and the masks come out at full 640x640 resolution already, so the Dart side thresholds a mask and does no decoding. That matters because `flutter_onnxruntime` is a thin binding - anything not expressible as an ORT graph would have to be reimplemented in Dart.

Runtime, from the CocoaPods specs, which are the authoritative source:

| | |
|---|---|
| `flutter_onnxruntime` licence | MIT |
| iOS deployment target | `s.platform = :ios, '16.0'` in the plugin's podspec; ONNX Runtime itself declares `"ios": "15.1"`. The **iOS 16 floor is the plugin's**, and it matches the map's constraint. |
| ORT pod | `s.dependency 'onnxruntime-objc', '1.23.0'` |
| ORT licence | MIT (`onnxruntime-c` and `onnxruntime-objc` podspecs both `"license": {"type": "MIT"}`) |
| ORT pod archive | `pod-archive-onnxruntime-c-1.23.0.zip`, 49,207,123 bytes |
| ORT device slice | `onnxruntime.xcframework/ios-arm64/onnxruntime.framework/onnxruntime`, **38,398,152 bytes** (36.6 MiB) |

The podspec was fetched from the CocoaPods CDN and the pod archive downloaded and unpacked rather than taken on trust. `onnxruntime-c` 1.23.0 declares `"license": {"type": "MIT"}`, `"platforms": {"ios": "15.1", "osx": "13.4"}`, `"static_framework": true` and `"weak_frameworks": ["CoreML"]`. `file` on the device slice reports *"Mach-O universal binary with 1 architecture: [arm64: current ar archive random library]"* - it is genuinely a static archive, not a dylib.

**Do not quote 36.6 MiB as IPA growth.** Because the framework is static, the linker keeps only what the app references. The honest statement is: the runtime contributes an undetermined fraction of a 36.6 MiB static archive, and the models contribute ~75 MiB that dead-stripping cannot touch. **The real linked size cannot be established from Linux** - it needs an actual iOS link, which needs the `ios-builder` pipeline. It is in section 11.

**Entitlements: none required.** Neither `onnxruntime-c` nor `onnxruntime-objc` declares an entitlement, and the only framework `onnxruntime-c` pulls in is a weak link against `CoreML`, which is not entitlement-gated. This clears the free-provisioning constraint from [#2](https://github.com/grez-lucas/poseperfect/issues/2), which established that camera and photo library are not entitlements either.

**One adjacent hazard, and it does not bite on our delivery path.** Unpacking the pod confirms it contains **no `PrivacyInfo.xcprivacy` anywhere**, and Apple's required-reason API check has flagged ORT for `NSPrivacyAccessedAPICategorySystemBootTime` ([microsoft/onnxruntime#20519](https://github.com/microsoft/onnxruntime/issues/20519)). `flutter_onnxruntime` ships its own privacy manifest (`s.resource_bundles = {'flutter_onnxruntime_privacy' => [...PrivacyInfo.xcprivacy]}`), but that declares the plugin's usage, not ORT's. **Privacy manifests are an App Store submission check.** Map decision 1 makes this a personal, side-loaded tool, so it does not gate this effort - but it would gate a future App Store release, and it belongs on the record now.

### 3.3 Latency

*(filled in after the sweep)*

---

## 5. Also establish - does RTMPose ship or recommend a paired detector, and under what licence?

**VERIFIED. It recommends three, and every single one is trained on a dataset whose publisher restricts it to non-commercial or academic use.**

RTMPose ships no detector in its own weights, but MMPose's RTMPose project README publishes explicit detector-plus-pose pairings with download links. Read straight off [`projects/rtmpose/README.md`](https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose/README.md):

| What MMPose pairs with RTMPose | Checkpoint | Training data | Dataset terms |
|---|---|---|---|
| **RTMDet-nano** (with RTMPose-t/s/**m**/l) | `rtmdet_nano_8xb32-100e_coco-obj365-person-05d8511e.pth` | COCO + **Objects365** | *"available for the academic purpose only"* |
| **RTMDet-m** (with RTMPose-m/l) | `rtmdet_m_8xb32-100e_coco-obj365-person-235e8209.pth` | COCO + **Objects365** | same |
| **RTMDet-tiny/s, YOLOX-nano..x** (Human-Art section) | `..._humanart-*.pth` | **Human-Art** | *"request authorization to use Human-Art for non-commercial purposes"* |

Sources: [Objects365 download page](https://www.objects365.org/download.html); [Human-Art README](https://raw.githubusercontent.com/IDEA-Research/HumanArt/main/README.md) - *"Under the CC-license, Human-Art is available for download. Fill out this form to request authorization to use Human-Art for non-commercial purposes."*

**And the community wrapper inherits the same problem.** `rtmlib`, the reference Python wrapper used by ticket #18's harness and by most RTMPose deployments, defaults its `Body` solution to `yolox_m_8xb8-300e_humanart-c2c7a14a.zip` - a Human-Art-trained YOLOX. Anyone who follows the obvious path from RTMPose's documentation to a working pipeline ends up with a non-commercially-licensed detector without ever being told.

**So the answer to the ticket's question is: yes, RTMPose recommends a paired detector, and no, none of the recommended pairings is licence-clean for a closed-source product.** The licence-clean option is a sibling model in the same Apache-2.0 codebase that MMPose does not point at: RTMDet-Ins, trained on COCO alone. That is a real finding, and it is the opposite of what "just use what upstream recommends" would have produced.

---

## 6. The finding this ticket did not go looking for: RTMPose-m's own weights carry a "commercial use is not allowed" dataset

**VERIFIED, from the dataset owner's own download page. This lands on [#16](https://github.com/grez-lucas/poseperfect/issues/16)'s engine choice, not on this ticket's detector choice, and it is the most consequential thing in this document.**

[#16](https://github.com/grez-lucas/poseperfect/issues/16) chose RTMPose-m and recorded a prerequisite: *"RTMPose weight licensing must verify clean."* Auditing the detector meant auditing the same layer for the pose model, and the pose model does not come out clean.

The weights the map committed to are `rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504`. MMPose defines `body7` verbatim in [`projects/rtmpose/README.md`](https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose/README.md):

> "`*` denotes model trained on 7 public datasets: AI Challenger, MS COCO, CrowdPose, **MPII**, sub-JHMDB, Halpe, PoseTrack18"

And MPII's [download page](https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/software-and-datasets/mpii-human-pose-dataset/download) says, verbatim:

> "MPII Human Pose Dataset, Version 1.0
> Copyright 2015 Max Planck Institute for Informatics
> Licensed under the Simplified BSD License [see bsd.txt]
> We are making the annotations and the corresponding code freely available for research purposes. **Commercial use is not allowed** due to the fact that the authors do not have the copyright for the images themselves."

**Which checkpoints this affects:** every RTMPose checkpoint whose name contains `body7` or `body8`, at every size, including the exact ONNX bundle this map plans to ship and the exact model ticket #18 measured. It does **not** affect the RTMDet-Ins detector recommended by this ticket, which trains on COCO alone.

**Now the limits of the claim, stated so this is not inflated.**

1. **The restriction is written over the dataset, not over models trained on it.** MPII restricts "the annotations and the corresponding code", and gives its reason plainly: the authors do not own the images. It says nothing explicit about model weights. Whether a dataset's use restriction reaches a model trained on it is genuinely unsettled, and this note is not the place to settle it.
2. **It is not a copyleft trap.** Nothing here obliges source disclosure. The exposure is a use restriction, not a licence-compatibility problem, so it does not interact with the closed-source requirement at all.
3. **On the map's current terms it is very likely moot.** Map decision 1 makes PosePerfect a **personal tool**, not distributed and not sold. Personal, non-commercial use sits inside what MPII permits. The exposure appears only if decision 1 is ever revisited and the app is sold or monetised - which decision 1 explicitly says the architecture should not have to be rewritten for.
4. **It is not unique to RTMPose.** Objects365 and Human-Art carry comparable restrictions (section 5), and this class of inheritance is endemic to the whole field.
5. **Three of the seven `body7` datasets are unaudited.** AI Challenger's terms could not be established at all: its host, `challenger.ai`, is defunct, and the surviving [GitHub repository](https://github.com/AIChallenger/AI_Challenger_2017) has no LICENSE file. CrowdPose, sub-JHMDB, Halpe and PoseTrack18 were not checked. See section 11.

**What this means procedurally.** It does not reverse #16, and this ticket has no standing to. What it does is falsify #16's stated prerequisite as written: RTMPose-m's weight licensing is **not** clean, on one of seven training datasets, in the dataset owner's own words. **That belongs in front of Lucas as an amendment to a settled decision, with the same "accept the risk or change the model" shape as section 9's detector question**, and it is flagged in the resolution comment on #19 rather than buried here.

**There is no drop-in remedy inside MMPose.** The only alternative published RTMPose-m body checkpoints are the `aic-coco` variants, which swap MPII for AI Challenger, whose terms could not be established. MMPose publishes no COCO-only RTMPose-m checkpoint. Retraining RTMPose-m on COCO alone is possible in principle and is not a research-ticket-sized job.

---

## 7. What this means for [#17](https://github.com/grez-lucas/poseperfect/issues/17)

*(stated after the measurement - see the Verdict)*

---

## 8. The decision this leaves for Lucas

Two questions here are not mine to settle, and both are of the "accept a stated risk or pay to avoid it" shape rather than the "which is better" shape.

**Question A: the detector's weight-grant gap (section 1.2).** OpenMMLab publishes Apache-2.0 code and first-party checkpoints, and has never written down that the checkpoints are Apache-2.0. Options:

| | Option | Cost | Residual risk |
|---|---|---|---|
| A1 | **Ship RTMDet-Ins from MMDetection** and accept the silence | none beyond this ticket | No express weight grant. Identical in kind to the risk already carried by RTMPose-m |
| A2 | Ask OpenMMLab to state the checkpoint licence in writing | an issue and an unknown wait | Removes the gap if they answer |
| A3 | Use **Segment Anything / MobileSAM** for the mask instead, the one project with an express permissive model grant | a second model, and it needs a box prompt so it does not replace the detector | Larger binary, more latency, more moving parts |
| A4 | Train a person detector ourselves on data we can point at | far outside this effort | none |

**Question B: MPII inside RTMPose-m's `body7` weights (section 6).** Options:

| | Option | Cost | Residual risk |
|---|---|---|---|
| B1 | **Accept it under map decision 1**, recording that the app is a personal tool and MPII permits that | none | Re-opens the moment the app is ever sold |
| B2 | Switch to an `aic-coco` RTMPose-m checkpoint | a re-run of #18's numbers on the new weights | AI Challenger's terms are unknown, so this may trade a known restriction for an unknown one |
| B3 | Retrain RTMPose-m on COCO alone | a training job well outside this effort | none |
| B4 | Change engine again | discards #16 | unknown |

**My recommendation, which is a recommendation and not a decision: A1 and B1.** Both risks are use-restriction risks that map decision 1 already sits inside, neither is a copyleft or source-disclosure risk, and both are cheap to revisit later precisely because the map committed to a portable reference format. The thing that must not happen is that either is left unrecorded and rediscovered at the point of shipping.

---

## 9. Caveats, stated plainly

1. **COCO is clothed people in everyday scenes.** The same caveat #18 carried applies without change: nobody has evaluated any of these models on heavily muscled, oiled, minimally clothed physique athletes holding extreme static poses. This experiment measures the viewpoint effect on a detector. **It does not measure our population.** For the mask specifically the direction is genuinely unclear: posing trunks against a dark backdrop could be easier than everyday clothing, or a flared lat could read as background to a model trained on ordinary body outlines.
2. **The rear-facing label is #18's visibility-derived proxy**, about 81% pure on REAR, and ordinal rather than angular. Every headline number is also reported on the sign-confirmed subset where the proxy and the annotated shoulder order agree.
3. **The crop is the friendliest realistic input.** A 1.25x square crop centred on the subject stands in for the product's constrained, frame-fit-gated capture (map decisions 8 and 14). Finding a person in a picture that is almost entirely one person is easy, which is exactly why the whole-image control exists.
4. **Nothing was validated by eye.** Map constraint 2. No overlay was rendered or inspected at any point. Boxes are scored against COCO ground-truth boxes, masks against COCO ground-truth instance segmentations, keypoints against COCO ground-truth keypoints.
5. **No score threshold was applied when recording.** Map constraint 3. Every detection is written out with its score and thresholds are swept in the analysis.
6. **The PyTorch latency numbers in `summary.md` are contended wall clock** from a five-way sharded run and are not a clean timing. Cost claims come from `results/onnx_cost.json`, which was measured with the box otherwise idle - and even that is x86-64 Linux, not iOS.
7. **The masks are scored against COCO polygon annotations**, which are themselves coarse. A predicted mask can be penalised for being more accurate than the ground truth. This biases the absolute mask IoU downward and is a reason to read the front-to-rear *difference* rather than the absolute level.

---

## 10. Not established

Listed so nobody mistakes silence for a clean bill.

**Licence**

1. **Whether OpenMMLab's checkpoints are covered by the Apache-2.0 licence on its code.** They have never said so in writing (section 1.2). Nobody asked them; asking is option A2 in section 8.
2. **Whether a dataset use restriction reaches a model trained on that dataset.** This is the crux of both the Objects365 finding and the MPII finding, it is unsettled generally, and a research ticket is the wrong instrument for settling it.
3. **AI Challenger's terms.** Its host `challenger.ai` is defunct and the surviving GitHub repository has no LICENSE file. This blocks any assessment of the `aic-coco` RTMPose checkpoints, which is option B2 in section 8.
4. **CrowdPose, sub-JHMDB, Halpe and PoseTrack18.** Four of the seven `body7` datasets were never opened. MPII was found on the first pass and the rest were not audited. **There may be a second MPII in there.**
5. **The RTMPose-m `body7` weights' full provenance chain** beyond the dataset list. Not attempted.

**iOS**

6. **The real added IPA size.** ONNX Runtime's iOS pod is a 36.6 MiB static archive, so the linked contribution depends on what the app references and cannot be determined from Linux. It needs a build through the `ios-builder` pipeline from [#2](https://github.com/grez-lucas/poseperfect/issues/2). The ~75 MiB of fp32 model weights is firm; the runtime's share is not.
7. **On-device latency.** Every latency figure here is x86-64 Linux under ONNX Runtime's CPU execution provider. No iPhone was involved, because there is no Mac and no device in this loop. **The ordering between models is meaningful; the absolute numbers are not the device numbers.**
8. **Whether the CoreML execution provider helps or works.** `onnxruntime-c` weak-links CoreML, and `flutter_onnxruntime` exposes execution-provider configuration, but neither was exercised. RTMDet-Ins's graph contains `NonMaxSuppression` and dynamic shapes, which CoreML commonly falls back to CPU for.
9. **fp16 or quantised variants.** MMDeploy ships an fp16 ONNX Runtime deploy config which would roughly halve the 22.9 MiB detector, and it was not exported or evaluated. No accuracy cost is known.

**Measurement**

10. **Anything about physique athletes.** Unchanged from #18 and still the largest gap on the map: muscularity, oil, posing trunks, stage lighting and extreme static poses are all outside COCO. This is now the second ticket to say so.
11. **Mask quality against a mask good enough to *score* a lat spread.** This experiment measures agreement with COCO's polygon ground truth. It does not establish what silhouette fidelity a lat-spread width metric actually needs, because that metric does not exist yet. That is [#17](https://github.com/grez-lucas/poseperfect/issues/17)'s job, and this ticket only clears its precondition.
12. **RTMDet-Ins-m and larger.** Only tiny and s were swept; the larger variants are outside a plausible mobile budget and were not measured.
13. **Any detector outside the MMDetection family.** Once Ultralytics and Detectron2 were excluded on licence and the remainder had no express weight grant either, RTMDet-Ins was the only candidate worth the compute. YOLACT, SOLOv2, MobileSAM and PP-HumanSeg were read but never run.
