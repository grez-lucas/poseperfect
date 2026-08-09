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

**Adjacent, and it belongs on the record because [#16](https://github.com/grez-lucas/poseperfect/issues/16) made "RTMPose weight licensing must verify clean" a prerequisite.** RTMPose-m's shipped weights are the `body7` variant, and MMPose defines `body7` verbatim as *"model trained on 7 public datasets: AI Challenger, MS COCO, CrowdPose, MPII, sub-JHMDB, Halpe, PoseTrack18"*. That is seven dataset licences riding on the pose model this map has already committed to, and this ticket did not audit them. It is listed in section 11 as unfinished work, not silently assumed clean.
