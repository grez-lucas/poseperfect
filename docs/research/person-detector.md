# Sourcing the person detector for RTMPose-m

Resolution of [#19](https://github.com/grez-lucas/poseperfect/issues/19), 2026-08-10. Grading convention matches `pose-engines.md`: **VERIFIED** = measured here or read from a primary source, **INFERRED** = reasoned from measurement, **ANECDOTAL** = reported by others.

Code, raw per-instance results and the ONNX export recipe: `experiments/person-detector/`. It reuses ticket [#18](https://github.com/grez-lucas/poseperfect/issues/18)'s cohort, crop construction and chirality test verbatim, so every number here sits on the same 1,675 COCO val2017 instances as `rear-view-experiment.md`.

> **CORRECTED IN TWO PLACES by [#20](https://github.com/grez-lucas/poseperfect/issues/20).** This
> document's detector findings stand unchanged. Two of its statements about the
> *pose* checkpoint do not, and both are marked `CORRECTION (#20)` inline below:
> a COCO-only RTMPose-m checkpoint **does** exist (section 9.1), and AI
> Challenger's terms **are** establishable (section 9.2). The checkpoint
> decision itself now lives in
> [`checkpoint-licences.md`](checkpoint-licences.md), which ships
> `simcc-coco`, not the `body7` this document assumed.

---

## Verdict

**Ship RTMDet-Ins-tiny from MMDetection, exported to ONNX with MMDeploy's own recipe. It clears all four requirements, and it is the only candidate in the field that does.**

| | Requirement | Result |
|---|---|---|
| 1 | **Licence-clean for a closed-source app, weights included** | **Passes, with one recorded gap.** Apache-2.0 code, first-party weights from the same project, COCO-only training, no upstream copyleft owner. But OpenMMLab has never written down that its checkpoints are Apache-2.0. **Nobody in this field grants their weights except Segment Anything**, which is not a person detector. Ultralytics is confirmed AGPL over weights in its own words; Detectron2's model zoo is CC BY-SA 3.0. The gap is Lucas's to accept, section 8 |
| 2 | **Segmentation-capable** | **Yes.** RTMDet-Ins emits a binary instance mask per detection, 35.4 mask AP for the tiny variant, and the exported graph returns masks at full 640x640 with NMS inside the graph |
| 3 | **Rear-view competent in its own right** | **Yes, emphatically. 363 of 363 rear-facing people found. Zero no-detection failures at any orientation.** BlazePose returned nothing on 30.0% of the same crops |
| 4 | **ONNX on iOS via `flutter_onnxruntime`** | **Yes.** Stock `ai.onnx` opset 11, no custom ops. **22.9 MiB** added weights, **~185 ms** at two threads on x86 CPU. No entitlement required, iOS 16 floor honoured. Real linked IPA size and on-device latency remain unmeasured |

**The three "also establish" items:**

- **Does RTMPose ship or recommend a paired detector?** Yes, three of them, and **not one is licence-clean**. RTMDet-nano-person and RTMDet-m-person are trained on Objects365 (*"available for the academic purpose only"*); the RTMDet and YOLOX Human-Art detectors, including the one `rtmlib` uses by default, are trained on Human-Art (*"non-commercial purposes"*). **Following upstream's recommendation would have produced a licensing problem.** The clean option is a sibling model in the same repository that MMPose never points at.
- **RTMPose-m's rear swap rate with a real detector?** **1.2% (3/251) sign-confirmed, against 1.0% (3/293) on ground-truth boxes, p = 0.85.** #18's headline was not an artefact of ground-truth boxes. Positional error does not degrade either (OKS 0.936 vs 0.930 on rear).
- **Segmentation quality on rear views?** **Holds.** Mask IoU 0.846 rear vs 0.878 front; mask *recall*, the failure mode that would clip a flared lat, 91.4% vs 93.3%; 92.8% of rear masks clear IoU 0.7 against 97.8% front.

**[#17](https://github.com/grez-lucas/poseperfect/issues/17) resolves POSITIVE.** [#16](https://github.com/grez-lucas/poseperfect/issues/16) set the condition plainly: the lat spreads get silhouette scoring if a licence-clean, segmentation-capable detector exists, and stay frame-only permanently if not. One exists, it costs 22.9 MiB rather than a second model, and its masks survive the rear view. **The Back Lat Spread is the pose that had both problems at once, and the silhouette half of it is now available.** What #17 still has to do is establish what silhouette fidelity a lat-spread width metric actually needs, which this ticket deliberately did not assume.

**One finding outside this ticket's scope, and it is the most consequential thing here.** Auditing the detector's training data meant auditing the pose model's, and **MPII's own download page says "Commercial use is not allowed"** - MPII is one of the seven datasets in `body7`, which is exactly the RTMPose-m checkpoint [#16](https://github.com/grez-lucas/poseperfect/issues/16) chose. That falsifies #16's stated prerequisite that RTMPose weight licensing verify clean. Scoped honestly in section 6: it is a use restriction rather than copyleft, it is written over the dataset rather than over models trained on it, and map decision 1 keeps this a personal tool where it is very likely moot. **And avoiding it is nearly free** - the `aic-coco` checkpoint drops MPII and is 0.9 AP *higher* on COCO - except that it keeps AI Challenger, whose terms could not be established at all. **That is Lucas's call, and it needs to be an explicit one rather than an omission.**

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

**Do not quote 36.6 MiB as IPA growth.** Because the framework is static, the linker keeps only what the app references. The honest statement is: the runtime contributes an undetermined fraction of a 36.6 MiB static archive, and the models contribute ~75 MiB that dead-stripping cannot touch. **The real linked size cannot be established from Linux** - it needs an actual iOS link, which needs the `ios-builder` pipeline. It is in section 10.

**Entitlements: none required.** Neither `onnxruntime-c` nor `onnxruntime-objc` declares an entitlement, and the only framework `onnxruntime-c` pulls in is a weak link against `CoreML`, which is not entitlement-gated. This clears the free-provisioning constraint from [#2](https://github.com/grez-lucas/poseperfect/issues/2), which established that camera and photo library are not entitlements either.

**One adjacent hazard, and it does not bite on our delivery path.** Unpacking the pod confirms it contains **no `PrivacyInfo.xcprivacy` anywhere**, and Apple's required-reason API check has flagged ORT for `NSPrivacyAccessedAPICategorySystemBootTime` ([microsoft/onnxruntime#20519](https://github.com/microsoft/onnxruntime/issues/20519)). `flutter_onnxruntime` ships its own privacy manifest (`s.resource_bundles = {'flutter_onnxruntime_privacy' => [...PrivacyInfo.xcprivacy]}`), but that declares the plugin's usage, not ORT's. **Privacy manifests are an App Store submission check.** Map decision 1 makes this a personal, side-loaded tool, so it does not gate this effort - but it would gate a future App Store release, and it belongs on the record now.

### 3.3 Latency

**VERIFIED, on x86-64 Linux under ONNX Runtime 1.19.2's CPU execution provider, with the box otherwise idle. This is not an iOS measurement** - see caveat 6 and section 10. Median of 20 runs after 3 warmups, at several `intra_op_num_threads` settings because a phone gives you two useful cores, not twenty.

| Graph | Size | 1 thread | 2 threads | 4 threads |
|---|---|---|---|---|
| RTMDet-Ins-tiny 640x640 | 22.9 MiB | 353.6 ms | **184.6 ms** | 98.7 ms |
| RTMDet-Ins-s 640x640 | 41.2 MiB | 693.8 ms | 181.9 ms | 118.8 ms |
| RTMPose-m 256x192 | 51.8 MiB | 57.0 ms | **31.8 ms** | 17.3 ms |

**The shippable pair costs about 215 ms per capture at two threads on this hardware.** Raw numbers in `results/onnx_cost.json`.

That is comfortably inside what the map needs. Map decision 7 already moved rigorous scoring off the live path and onto capture, and decision 20 says scoring must not block the session, so the budget is "a second or two in the background", not "30 fps". Even if a phone were three times slower than this desktop core, the pair stays under a second.

**RTMDet-Ins-s is not worth its cost.** It is 18 MiB larger, no faster in the regime that matters, and section 4 shows it is not better on any metric the product cares about. **RTMDet-Ins-tiny is the variant to ship.**

---

## 4. Measured on COCO: requirement 3, and the two numbers the ticket asked for

### 4.1 What was run

**VERIFIED.** Full sweep, `experiments/person-detector/`, results in `results/`.

| | |
|---|---|
| Cohort | ticket #18's 1,675-instance COCO val2017 cohort, reused verbatim |
| Input | the same 1.25x square crop, black-padded, as #18 |
| Mode | IMAGE / static single-image inference throughout |
| Detectors | RTMDet-Ins-tiny, RTMDet-Ins-s (mask-emitting, COCO-only, Apache-2.0), RTMDet-nano-person (box-only, Objects365, the pairing MMPose recommends) |
| Pose | RTMPose-m body7 ONNX, the same weights and the same rtmlib decode path as #18 |
| Baseline | a `gt_box` row per instance, RTMPose-m on the ground-truth box, recomputed in-process |
| Scoring | boxes against COCO ground-truth boxes, masks against COCO ground-truth instance segmentations, keypoints against COCO ground-truth keypoints |
| Threshold | none applied at record time; swept in the analysis |
| Cost | 6,701 rows, 935 s over five shards, CPU |

**The `gt_box` baseline reproduces #18 exactly**, which is the check that the two experiments are commensurable: sign-confirmed REAR chirality swap **3/293 = 1.0%**, FRONT **3/804 = 0.4%**. Identical to the numbers in `rear-view-experiment.md`.

### 4.2 Requirement 3 - is the detector rear-view competent in its own right?

**VERIFIED. Yes, completely, and it is not close.**

The failure that disqualified BlazePose was that its face-anchored person detector returns *nothing* on 30.0% of rear-facing subjects. Under the identical conditions:

**Instances where the detector returned no person detection at all:**

| orientation | RTMDet-Ins-tiny | RTMDet-Ins-s | RTMDet-nano-person | BlazePose heavy (#18) |
|---|---|---|---|---|
| FRONT | 0.000 | 0.000 | 0.000 | 0.069 |
| OBLIQUE | 0.000 | 0.000 | 0.000 | - |
| PROFILE | 0.000 | 0.000 | 0.000 | - |
| **REAR** | **0.000** | **0.000** | **0.000** | **0.300** |

**Instances where the target person was among the returned detections at IoU >= 0.5:**

| orientation | RTMDet-Ins-tiny | RTMDet-Ins-s | RTMDet-nano-person |
|---|---|---|---|
| FRONT | 0.998 [0.991, 0.999] n=832 | 0.999 [0.993, 1.000] n=832 | 1.000 [0.995, 1.000] n=832 |
| OBLIQUE | 0.997 [0.985, 1.000] n=384 | 0.995 [0.981, 0.999] n=384 | 1.000 [0.990, 1.000] n=384 |
| PROFILE | 1.000 [0.962, 1.000] n=96 | 1.000 [0.962, 1.000] n=96 | 1.000 [0.962, 1.000] n=96 |
| **REAR** | **1.000 [0.990, 1.000] n=363** | **1.000 [0.990, 1.000] n=363** | **1.000 [0.990, 1.000] n=363** |

**RTMDet-Ins found every single rear-facing person in the cohort. 363 of 363.** There is no rear-view detection deficit to report, at any orientation, for any of the three detectors. The architecture hypothesis #18 confirmed holds up from the other side: it was never the viewpoint, it was the face anchor, and a general object detector does not have one.

**And box quality does not degrade either.** Mean IoU of the selected box against ground truth, on hits: 0.912 FRONT and 0.896 REAR for RTMDet-Ins-tiny. A 1.6-point drop across the whole viewpoint range.

**One thing this measurement is NOT saying, and it matters.** Picking the *highest-scoring* detection finds the target only 83.7% of the time on REAR, not 100%. That gap is **not** a detection failure - the target is always in the list. It is the naive selection rule choosing a different person, because the 1.25x crop pulls in neighbours and #18's cohort tolerates up to 35% overlap with another annotated person. **Selecting the subject is a product design problem** (most central, or largest, or nearest the frame-fit gate's expected box), not a detector property, and this ticket does not settle it. Everything downstream is therefore reported both ways.

**Sensitivity to the score threshold**, since map constraint 3 forbids gating on confidence and the honest treatment is to show what a threshold would cost rather than to pick one. Top-1 hit rate on REAR for RTMDet-Ins-tiny: 0.837 at any score, 0.835 at s>=0.1, 0.829 at s>=0.3, 0.807 at s>=0.5, **0.689 at s>=0.7**. The answer is flat until 0.5 and then falls off a cliff. **Do not threshold above 0.3**, and there is no reason to threshold at all.

### 4.3 Also establish - what does RTMPose-m's rear swap rate become with a real detector?

**VERIFIED. It stays at 1%. The pose-head upper bound from #18 survives contact with a real detector.**

This is the number the ticket said nobody had. Restricted to instances where the pipeline selected the right person, so it measures the cost of *a real box instead of a ground-truth box* rather than the cost of a bad selection rule:

| orientation | `gt_box` (#18's condition) | RTMDet-Ins-tiny | RTMDet-Ins-s | RTMDet-nano-person |
|---|---|---|---|---|
| FRONT | 0.005 n=832 | 0.003 n=730 | 0.003 n=676 | 0.003 n=670 |
| OBLIQUE | 0.026 n=384 | 0.033 n=337 | 0.034 n=328 | 0.034 n=321 |
| PROFILE | 0.000 n=96 | 0.000 n=80 | 0.000 n=75 | 0.000 n=77 |
| **REAR** | **0.019 n=363** | **0.020 n=304** | 0.024 n=290 | 0.021 n=283 |

Sign-confirmed, which is the subset #18's verdict quoted:

| orientation | `gt_box` | RTMDet-Ins-tiny | RTMDet-Ins-s | RTMDet-nano-person |
|---|---|---|---|---|
| FRONT | 0.004 (3/804) | 0.003 (2/706) | 0.003 (2/656) | 0.003 (2/647) |
| **REAR** | **0.010 (3/293)** | **0.012 (3/251)** | 0.008 (2/239) | 0.017 (4/238) |

Two-proportion z-tests against the ground-truth box on sign-confirmed REAR: RTMDet-Ins-tiny **p = 0.85**, RTMDet-Ins-s p = 0.82, RTMDet-nano-person p = 0.51. **No detector is distinguishable from a ground-truth box.**

**Positional error, kept separate as map constraint 4 requires.** Mean OKS after chirality correction, same conditioning:

| orientation | `gt_box` | RTMDet-Ins-tiny |
|---|---|---|
| FRONT | 0.950 | 0.954 |
| OBLIQUE | 0.925 | 0.926 |
| PROFILE | 0.929 | 0.930 |
| REAR | 0.930 | **0.936** |

The detector's box is, if anything, marginally *better* for RTMPose than COCO's annotated box - unsurprising, since RTMDet was trained to produce the kind of box a detector-fed pose model expects.

**So the deployable figure the ticket asked for is ~1.2% rear chirality swap, and #18's 1.0% was not an artefact of ground-truth boxes.** Against BlazePose's 14.4% and MoveNet Thunder's 7.2%, on the same images.

**The honest caveat, stated rather than buried.** Under a naive highest-score selection rule in a crowded crop, the same pipeline reports 5.1% rear swap and a composite usable rate of 82.1% instead of 99%. That entire gap is subject selection, not pose or detection, and it is a real engineering task the product has to do properly. The frame-fit gate (map decisions 8 and 14) exists precisely to make this a non-problem, and the 100% any-detection recall above proves a correct rule is always achievable. But **a careless implementation will throw away most of the margin RTMPose bought**, and that is worth recording as a design constraint rather than discovering later.

### 4.4 Also establish - segmentation quality, and specifically on rear views

**VERIFIED. The mask holds up on rear views. It is 3 points of IoU worse than front, not a collapse.**

Mask IoU against the COCO ground-truth instance segmentation, on hits:

| orientation | RTMDet-Ins-tiny | RTMDet-Ins-s |
|---|---|---|
| FRONT | 0.878 | 0.883 |
| OBLIQUE | 0.861 | 0.868 |
| PROFILE | 0.845 | 0.849 |
| **REAR** | **0.846** | 0.855 |

Precision and recall kept separate, because for a lat spread the damaging failure is the mask **clipping** the flared silhouette (a recall failure), while bleeding into the background costs a width measurement far less:

| orientation | tiny recall | tiny precision |
|---|---|---|
| FRONT | 0.933 | 0.938 |
| OBLIQUE | 0.919 | 0.932 |
| PROFILE | 0.920 | 0.915 |
| **REAR** | **0.914** | 0.922 |

**Rear-view mask recall is 91.4% against 93.3% front. A 1.9-point drop.** The failure mode that would actually hurt a lat spread barely moves with viewpoint.

Fraction of masks clearing IoU 0.7, a rough "the silhouette is usable" bar:

| orientation | RTMDet-Ins-tiny | RTMDet-Ins-s |
|---|---|---|
| FRONT | 0.978 [0.965, 0.986] n=730 | 0.981 [0.967, 0.989] n=676 |
| OBLIQUE | 0.947 [0.917, 0.966] n=337 | 0.960 [0.933, 0.977] n=328 |
| PROFILE | 0.938 [0.862, 0.973] n=80 | 0.947 [0.871, 0.979] n=75 |
| **REAR** | **0.928 [0.893, 0.952] n=304** | 0.945 [0.912, 0.966] n=290 |

**92.8% of rear-view masks clear IoU 0.7 against 97.8% of front-view masks.** A back lat spread gets a usable silhouette about as often as a front one.

Two things this does not establish, both in section 10: COCO's polygon ground truth is itself coarse, so the absolute level is pessimistic and the front-to-rear *difference* is the trustworthy part; and nobody has measured any of this on an oiled, muscled athlete in posing trunks, where a flared lat is exactly the structure a COCO-trained model has never been asked to outline.

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
5. **Three of the seven `body7` datasets are unaudited.** AI Challenger's terms could not be established at all: its host, `challenger.ai`, is defunct, and the surviving [GitHub repository](https://github.com/AIChallenger/AI_Challenger_2017) has no LICENSE file. CrowdPose, sub-JHMDB, Halpe and PoseTrack18 were not checked. See section 10.

**What this means procedurally.** It does not reverse #16, and this ticket has no standing to. What it does is falsify #16's stated prerequisite as written: RTMPose-m's weight licensing is **not** clean, on one of seven training datasets, in the dataset owner's own words. **That belongs in front of Lucas as an amendment to a settled decision, with the same "accept the risk or change the model" shape as section 8's detector question**, and it is flagged in the resolution comment on #19 rather than buried here.

### 6.1 What avoiding MPII would cost

**VERIFIED from the model zoo, because a blocker without a price tag is not actionable.**

MMPose publishes exactly **two** 2D body training mixtures for RTMPose, and no others. The section headers in `projects/rtmpose/README.md` are `AIC+COCO` and `Body8`. **There is no COCO-only RTMPose-m checkpoint.**

> **CORRECTION (#20): the last sentence is wrong.** A COCO-supervised RTMPose-m
> checkpoint does exist, `rtmpose-m_simcc-coco_pt-aic-coco_420e-256x192-d8dd5ca4`,
> at 74.6 AP. This section read only `projects/rtmpose/README.md`; the main
> MMPose model zoo carries more mixtures than that file's two section headers
> suggest. **That checkpoint is what now ships**, because #20's audit found
> `body7` carries three express non-commercial terms plus three datasets with no
> grant at all. See [`checkpoint-licences.md`](checkpoint-licences.md).

| | `body7` (current choice) | `aic-coco` (the alternative) |
|---|---|---|
| Checkpoint | `rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504` | `rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126` |
| Training mixture | AI Challenger, MS COCO, CrowdPose, **MPII**, sub-JHMDB, Halpe, PoseTrack18 | AI Challenger, MS COCO |
| **AP (COCO)** | 74.9 | **75.8** |
| PCK@0.1 (Body8) | 94.25 | 94.13 |
| AUC (Body8) | 68.59 | 68.53 |
| Params / FLOPs | 13.59 M / 1.93 G | 13.59 M / 1.93 G |
| ONNX bundle published? | **yes** | **no, `.pth` only** |

**The accuracy question answers itself: there is no accuracy cost.** The `aic-coco` checkpoint is **0.9 AP higher on COCO** and 0.12 PCK lower on Body8. Same architecture, same size, same speed. On the published numbers this is a wash, and if anything the MPII-free checkpoint is the better one on the benchmark that matters most for a single-person top-down pipeline.

**But it does not clear the licence question, it relocates it.** `aic-coco` drops MPII and keeps AI Challenger, and **AI Challenger's terms could not be established at all**: its host `challenger.ai` is defunct, the surviving [GitHub repository](https://github.com/AIChallenger/AI_Challenger_2017) has no LICENSE file and no terms in its README, and web search was unavailable during this session. **Swapping to `aic-coco` trades a known restriction for an unknown one.** That is not obviously an improvement, and it should not be presented as one.

> **CORRECTION (#20): AI Challenger's terms are not unknown.** Giving up here
> was premature. The Internet Archive holds the owner's own `/terms` page
> (2018-08-11): *"选手应保证其仅在科学研究或课堂教学等非商业性目的范围内使用基础数据"* -
> use the base data only for non-commercial purposes such as scientific research
> or classroom teaching. So AIC is an **express non-commercial term**, quotable,
> not an unknown. The trade is therefore known-for-known, and the argument above
> no longer holds. What remains genuinely unrecoverable is AIC's separate
> 《数据集下载协议》, which was never archived.

**COCO itself is clean, and that is worth stating because it is the one dataset here that is.** From [COCO's terms of use](https://github.com/cocodataset/cocodataset.github.io/blob/master/dataset/termsofuse.htm), verbatim: *"The annotations in this dataset along with this website belong to the COCO Consortium and are licensed under a Creative Commons Attribution 4.0 License."* and *"The COCO Consortium does not own the copyright of the images. Use of the images must abide by the Flickr Terms of Use. The users of the images accept full responsibility for the use of the dataset."* **There is no academic-only clause and no non-commercial clause.** COCO carries the same Flickr-image caveat that Objects365 and MPII do, but unlike them it does not convert that caveat into a use restriction. This is exactly why the RTMDet-Ins detector recommended by this ticket, trained on COCO alone, is in a better position than the pose model it will feed.

**Two costs of the swap that are real but small:** the `aic-coco` variant ships no ONNX bundle, so it would have to be converted with MMDeploy - which `experiments/person-detector/export_onnx.sh` now demonstrates is a solved problem in this repo - and #18's rear-view numbers were measured on the `body7` weights, so they would need re-running on the new ones. Both are hours, not weeks.

**Not measured:** the `aic-coco` checkpoint's actual rear chirality swap rate on our cohort. The published AP is a COCO-average and says nothing about rear views specifically, which is the whole reason #18 existed. Running it is a contained job with the harness now in place, and it is listed in section 10.

---

## 7. What this means for [#17](https://github.com/grez-lucas/poseperfect/issues/17)

**#17 resolves POSITIVE. The silhouette is available.**

[#16](https://github.com/grez-lucas/poseperfect/issues/16) wrote the condition without ambiguity: the two lat spreads get *"framing and arm position, plus silhouette if [#19](https://github.com/grez-lucas/poseperfect/issues/19) finds a segmentation-capable detector; frame-only permanently if not"*. All three clauses of that condition are met:

1. **Segmentation-capable** - RTMDet-Ins emits an instance mask (section 2).
2. **Licence-clean on the same terms the map has already accepted elsewhere** - Apache-2.0 project, first-party weights, COCO-only training, and COCO is the one dataset in this whole document with no use restriction (sections 1 and 6.1).
3. **Good enough on a rear view** - 92.8% of rear-view masks clear IoU 0.7, and mask recall, the failure that would clip a flared lat, drops only 1.9 points from front to rear (section 4.4).

And #16's other constraint is satisfied too: the mask comes from **the detector the pipeline needed anyway**, not from a second model. The marginal cost of the silhouette over a box-only detector is zero inference passes and about 19 MiB of weights against RTMDet-nano-person.

**What #17 must not inherit from this.** This ticket establishes that a mask exists and that the viewpoint does not destroy it. It does **not** establish that the mask is good enough to *score* a lat spread, because the metric that would consume it does not exist yet. A V-taper measurement may need boundary precision at the lat margin specifically, which mean IoU does not report and COCO's coarse polygon ground truth cannot validate. **#17 starts from "the input exists" and still has to prove "the input is sufficient".**

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
| B2 | Switch to an `aic-coco` RTMPose-m checkpoint | a re-run of #18's numbers on the new weights | ~~AI Challenger's terms are unknown, so this may trade a known restriction for an unknown one~~ **CORRECTION (#20): AIC's terms are established (express non-commercial), and the re-run was done - all candidates are statistically indistinguishable on rear chirality. `simcc-coco` ships.** |
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
