# The RTMPose checkpoint's training-data licences, and which checkpoint ships

Resolution of [#20](https://github.com/grez-lucas/poseperfect/issues/20), 2026-08-10. Grading convention matches `pose-engines.md` and `person-detector.md`: **VERIFIED** = measured here or read from a primary source, **INFERRED** = reasoned from measurement, **ANECDOTAL** = reported by others.

**Written as a sibling of [`person-detector.md`](person-detector.md) rather than appended to it**, because it answers a different question about a different model. #19's file is the record of *which detector to put in front of RTMPose-m*; this one is the record of *which RTMPose-m weights to ship*. Appending would have buried a checkpoint decision inside a detector decision, and [#16](https://github.com/grez-lucas/poseperfect/issues/16)'s falsified prerequisite deserves its own findable document.

Code, raw per-instance results and the ONNX export recipe: `experiments/checkpoint-swap/`. It reuses [#18](https://github.com/grez-lucas/poseperfect/issues/18)'s cohort, crop construction and chirality test verbatim, and [#19](https://github.com/grez-lucas/poseperfect/issues/19)'s detector, pose scoring and statistics verbatim, so every number here sits on the same 1,675 COCO val2017 instances as `rear-view-experiment.md` and `person-detector.md`.

---

## Verdict

**Ship `rtmpose-m_simcc-coco_pt-aic-coco_420e-256x192-d8dd5ca4_20230127`. It is supervised on COCO alone, it measures the same as `body7` on the rear view, and it costs nothing in size or latency. This is a recommendation, not a decision, and section 5 lays out the alternatives.**

| | Question | Answer |
|---|---|---|
| 1 | **The four unaudited `body7` datasets** | **All four are problems.** PoseTrack18 is **CC BY-NC 4.0** *and* is built from MPII's raw video, so **MPII is in `body7` twice**. CrowdPose has **no licence at all** and its images are sampled from MSCOCO + MPII + AI Challenger. Halpe has **no licence at all**, at any layer it owns. sub-JHMDB has **no licence statement in the entire archived history of its site**; upstream HMDB51 is CC BY 4.0, applied to clips from commercial movies |
| 2 | **AI Challenger** | **Not unknowable after all.** The origin site is dead, but an archived copy of the owner's own agreement survives and restricts the data to *"non-commercial purposes such as scientific research or classroom teaching"*. **The dataset-download agreement that expressly overrides it was never archived and is unrecoverable** |
| 3 | **The `aic-coco` rear swap rate** | **1.0% (3/293) on ground-truth boxes and 0.4% (1/251) on real detector boxes**, against `body7`'s 1.0% and 1.2%. p = 1.00 and p = 0.32. **No measurable cost**, zero size cost, zero latency cost |
| 4 | **Is there a clean option?** | **No, and the field has none.** But there is a cleaner one than #19 knew about: **MMPose does publish a COCO-supervised RTMPose-m**, in its main model zoo rather than the RTMPose project README. It measures 1.4% / 1.2% rear swap, also indistinguishable from `body7` |

**The single most useful result is a negative one: the checkpoints are statistically indistinguishable on rear chirality swap, so this is a licensing choice and not an accuracy choice.** All three sit inside each other's confidence intervals on the failure mode #18, #19 and #20 all exist to control, and all three are 51.8 MiB, opset 11, and within 4 ms of each other.

**Two corrections to `person-detector.md`, section 7.** #19 wrote that no COCO-only RTMPose-m exists; one does. #19 wrote that swapping to `aic-coco` trades a known restriction for an unknown one; AI Challenger's restriction is now known.

---

## 1. What `body7` actually contains

**VERIFIED, from MMPose's own definition.** [`projects/rtmpose/README.md`](https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose/README.md) states it in one line:

> "`*` denotes model trained on 7 public datasets:
>   - AI Challenger
>   - MS COCO
>   - CrowdPose
>   - MPII
>   - sub-JHMDB
>   - Halpe
>   - PoseTrack18"

The checkpoint [#16](https://github.com/grez-lucas/poseperfect/issues/16) chose is `rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504`, which carries that `*`. #19 opened three of the seven. This ticket opened the other four, each from its own distribution point, read separately from any paper or repo badge.

---

## 2. The four unaudited datasets

**VERIFIED, each from its own distribution point.** #19's operating assumption was that there might be a second MPII in there. **There is, and it is worse than that: two of the four carry an explicit non-commercial term, and the other two carry no licence at all.**

| Dataset | Owner's own terms | Verdict |
|---|---|---|
| **CrowdPose** | **No LICENSE file, no terms anywhere.** But its images are sampled from MSCOCO + **MPII** + AI Challenger, by the authors' own account | **Unlicensed, and inherits MPII** |
| **sub-JHMDB** | **No licence statement of any kind**, on any page the site ever had. Upstream HMDB51 is **CC BY 4.0** | **Unlicensed at the J-HMDB layer; permissive upstream** |
| **Halpe** | **No LICENSE file, no terms.** Images are HICO-DET (no terms either, Flickr-sourced) plus COCO val2017 | **Unlicensed at every layer it owns** |
| **PoseTrack18** | **CC BY-NC 4.0**, declared by the owner. Imagery is **MPII Human Pose's raw video**, by the authors' own words | **Express non-commercial, and a second MPII** |

### 2.1 CrowdPose - no licence, and MPII underneath

**VERIFIED.** There is no `LICENSE` on `master` or `main`, GitHub's licence API returns 404, and a recursive listing of [`Jeff-sjtu/CrowdPose`](https://github.com/Jeff-sjtu/CrowdPose) contains only `.gitignore`, `README.md`, `crowdpose-api/` and `crowdpose.gif`. The README has no terms section; its only obligation-flavoured sentence is *"If you find our works useful in your reasearch, please consider citing:"* (typo in the original), which is a request, not a grant. Both download links are bare Google Drive URLs with no click-through agreement.

**The README is silent on where the images come from**, so provenance had to come from the authors' own CVPR 2019 paper ([arXiv:1812.00324](https://arxiv.org/abs/1812.00324)). Verbatim, from the dataset-construction section:

> "To build a dataset of crowded human pose, we need to define a Crowd Index first... To achieve that, we first analyze three public benchmarks [19, 2, 30] and divide their images into 20 groups according to Crowd Index, ranging from 0 to 1."

> "To evaluate the performance of multi-person pose estimation algorithms, several public benchmarks were established, such as MSCOCO [19], MPII [2] and AI Challenger [30]."

Resolved against the paper's own bibliography, `[2]` is Andriluka et al. CVPR 2014, i.e. **MPII Human Pose**. **So CrowdPose's images are partly MPII's images**, and the CrowdPose authors annotated them rather than captured them: *"use 14 keypoints definition and annotate keypoints and full-body bounding boxes for persons in 30,000 images"*.

**The consequence is asymmetric and worth stating plainly: "no licence found" is not "permissively licensed".** Absent a grant, nothing is conveyed. Combine that with a provable MPII fraction, and CrowdPose is not clean.

### 2.2 sub-JHMDB - no licence at any point in the site's history

**VERIFIED, including a strong negative result.** The J-HMDB distribution site `jhmdb.is.tue.mpg.de` is dead: every path 302s to `crichton.is.tue.mpg.de/404.html`, a page whose `Last-Modified` is 2014, served by Apache 2.2.22.

The archived owner pages were read instead (Internet Archive snapshots of the owner's own site, 2019-12-18 to 2019-12-23). The home page and `/dataset` page carry no licence text - the only obligation-like heading is *"Referencing the dataset in your work"* followed by a BibTeX block. The download page `/challenge/JHMDB/datasets` redirects to `/login`, and the `/signup` form collects only email and password with **no terms checkbox**.

**And this is the part that makes it a finding rather than a failed search.** Enumerating every URL the Internet Archive ever captured on the domain (`web.archive.org/cdx/search/cdx?url=jhmdb.is.tue.mpg.de&matchType=domain`) yields the complete page list: `/`, `/about`, `/algorithms`, `/challenge/JHMDB`, `/challenge/JHMDB/datasets`, `/dataset`, `/hero`, `/imprint`, `/login`, `/password_resets/new`, `/puppet_model`, `/puppet_tool`, `/robots.txt`, three `/show_file` PDFs, `/signup`, and an account-confirm route. **There is no `/license`, `/licence`, `/terms`, `/tos`, `/eula`, `/agreement` or `/copyright` page in the entire archived history of the site.**

**Specifically checked and not found: the MPII formula.** J-HMDB is a Max Planck dataset, so the obvious hazard was the same *"Commercial use is not allowed"* sentence. It does not appear on any reachable J-HMDB page, in any form.

**The upstream is the surprise, and it is good news.** J-HMDB's clips come from HMDB51, and the J-HMDB home page links to it under "Resources" (*"HMDB dataset Project page at Brown University"*). HMDB51's own page carries a formal, machine-readable CC declaration:

> "HMDB by H. Kuehne, H. Jhuang, E. Garrote, T. Poggio, T. Serre is licensed under a Creative Commons Attribution 4.0 International License."

That is **CC BY 4.0 - permissive, commercial use allowed with attribution**. Quoted from the Serre Lab's own page via archived snapshots dated 2020-01-10 and re-confirmed identical at 2025-08-19; the live `serre-lab.clps.brown.edu` URL now cross-redirects to the lab's new site and the resource page is gone.

**But do not read that as a clearance.** The same page says, verbatim: *"Here we introduce HMDB collected from various sources, mostly from movies, and a small proportion from public databases such as the Prelinger archive, YouTube and Google videos."* and *"Because HMDB51 video sequences are extracted from commercial movies as well as YouTube..."*. The word "copyright" does not appear on the page at all. **The Serre Lab applied CC BY 4.0 to footage it clipped from commercial films, and never stated that it holds rights in that footage.** A permissive badge from a party that may not hold the copyright is worth less than it looks.

### 2.3 Halpe - unlicensed at every layer, and an adjacent trap in AlphaPose

**VERIFIED.** [`Fang-Haoshu/Halpe-FullBody`](https://github.com/Fang-Haoshu/Halpe-FullBody) has no `LICENSE`: the raw URL 404s, GitHub's licence API 404s, the repo root contains only `HalpeCOCOAPI/`, `README.md`, `docs/` and `vis.py`, and `master` is the only branch. The README's sole obligation is *"If the data helps your research, please cite the following paper:"*.

**Halpe distributes only annotations; it never redistributes an image.** From its own download section, verbatim:

> "Train annotations [Baidu | Google]"
> "Val annotations [Baidu | Google]"
> "Train images from [HICO-DET]"
> "Val images from [COCO]"

MMPose corroborates the split independently: *"The images of the training set are from HICO-Det and those of the validation set are from COCO."*

**HICO-DET, the source of the training images, also has no terms.** Its live official site is [`umich-ywchao-hico.github.io`](https://umich-ywchao-hico.github.io/), which states its own provenance - *"2024/06/01: This is the official project site migrated from http://www.umich.edu/~ywchao/hico/. That address was originally printed in the ICCV'15 and WACV'18 publications but can no longer host the site."* The entire Dataset section reads:

> "HICO-DET version 20160224 7.5GB
> Images and annotations for the HOI detection task."

No licence, no terms of use, no copyright notice, no attribution requirement. The owners' ICCV 2015 paper says where the images came from:

> "To collect images for the HOI categories, we use Creative Common images from Flickr as the source of candidate images."

with their own caveat: *"In addition to our automatic pipeline, we also manually collected some images for categories with very few images."*

**"Creative Common" is not a licence.** On Flickr that label spans CC BY, BY-SA, BY-ND, **BY-NC, BY-NC-SA, BY-NC-ND** and CC0. Three of the seven are NonCommercial, the authors never state that NC was excluded, and no per-image licence manifest is published, so the attribution every CC licence except CC0 requires is not shipped either.

**The adjacent trap, which is sharper than the dataset question.** Halpe comes from the AlphaPose team, and [`MVIG-SJTU/AlphaPose`'s LICENSE](https://raw.githubusercontent.com/MVIG-SJTU/AlphaPose/master/LICENSE) opens:

> "ALPHAPOSE: MULTIPERSON KEYPOINT DETECTION
> SOFTWARE LICENSE AGREEMENT
> ACADEMIC OR NON-PROFIT ORGANIZATION NONCOMMERCIAL RESEARCH USE ONLY"

with the licensor named as Shanghai Jiao Tong University, and the README adding *"AlphaPose is freely available for free non-commercial use... For commercial queries, please drop an e-mail at mvig.alphapose[at]gmail[dot]com."*

**Read the scope carefully, because it is easy to overstate.** The Agreement defines its own subject exhaustively as *"(i) the actual copy of all or any portion of code for program routines... including all or any file structures, programming instructions, user interfaces and screen formats and sequences as well as any and all documentation and instructions related to it, and (ii) all or any derivatives and/or modifications created or made by You"*. The words data, dataset, images, annotations, labels and models **appear nowhere in it**, and the Halpe repo never adopts or links it. **Textually the AlphaPose licence covers the code, not the Halpe dataset.** What it does cover unambiguously is anything taken from the AlphaPose repo, including the Halpe-26 and Halpe-136 pretrained weights its model zoo hosts. **That is a trap this project does not walk into - RTMPose-m comes from MMPose, not from AlphaPose - but it is why "Halpe" reads as non-commercial in most people's heads.**

### 2.4 PoseTrack18 - the second MPII, and an express CC BY-NC 4.0

**VERIFIED, and this is the sharpest finding in the ticket.**

`posetrack.net` is dead as of 2026-08-10: DNS delegation itself fails, with the zone's own nameservers returning REFUSED and SERVFAIL. MMPose still instructs users to *"download from PoseTrack18"* at `https://posetrack.net/users/download.php`, which cannot be reached. The site was read from Internet Archive snapshots of the owner's own pages.

**PoseTrack declares CC BY-NC 4.0.** From `posetrack.net/about.php`, archived 2019-07-19, the entire licence section is:

```html
<h3>License</h3>
<a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank"><img src="/img/by-nc.png" width="100px"></a>
```

**The whole grant is a badge and a link. There is no prose licence text anywhere on the site**, nothing saying whether it covers annotations only or annotations plus imagery, and the badge appears on the About page only - not on the download page, the Rules page, the homepage or the ECCV'18 workshop page. A user could complete the entire registration-and-download flow having accepted only generic website boilerplate (*"Welcome to our website. If you continue to browse and use this website, you are agreeing to comply with and be bound by the following terms and conditions of use..."*) and never having been shown the NC term.

**And the imagery is MPII's.** From the PoseTrack authors' own paper, section 3, verified in both the [official CVF camera-ready PDF](https://openaccess.thecvf.com/content_cvpr_2018/papers/Andriluka_PoseTrack_A_Benchmark_CVPR_2018_paper.pdf) via `pdftotext` and the arXiv source rendering of [arXiv:1710.10000](https://arxiv.org/abs/1710.10000), with identical wording:

> "We build on and extend the newly introduced datasets for pose tracking in the wild [17, 22]. To that end, we use the raw videos provided by the popular MPII Human Pose dataset. For each frame in MPII Human Pose dataset we include 41-298 neighboring frames from the corresponding raw videos, and then select sequences that represent crowded scenes with multiple articulated people engaging in various dynamic activities."

**Source-strength caveat, stated rather than glossed: that is the owner's own statement, but it lives in a paper, not on a distribution page.** The paper was used because posetrack.net is dead and none of its archived pages ever stated provenance. It is corroborated by a non-paper, owner-authored artefact - the official evaluation code's documented data layout in [`poseval`'s README](https://raw.githubusercontent.com/leonid-pishchulin/poseval/master/README.md), whose worked example contains the image path `"images/bonn_5sec/000342_mpii/00000001.jpg"`. **PoseTrack's sequence directories are literally named `*_mpii`.**

The chain closes on primary sources at both ends. MPII's own [download page](https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/software-and-datasets/mpii-human-pose-dataset/download) says *"Commercial use is not allowed due to the fact that the authors do not have the copyright for the images themselves."*, says *"Each image was extracted from a YouTube video"*, and separately publishes exactly the artefact PoseTrack consumed: *"Below you can download short videos including preceding and following frames for each image."*

**So MPII is in `body7` twice: once directly, and once as the raw material of PoseTrack18.** The two restrictions agree rather than conflict, which means removing MPII alone would not have removed the restriction.

### 2.5 What COCO says, for contrast

**VERIFIED, and it is the only dataset in the mixture that grants anything.** From [COCO's terms of use](https://github.com/cocodataset/cocodataset.github.io/blob/master/dataset/termsofuse.htm): the annotations are *"licensed under a Creative Commons Attribution 4.0 License"*, and *"Use of the images must abide by the Flickr Terms of Use."* **No academic-only clause, no non-commercial clause.** COCO carries the same third-party-image caveat as everything else here, but unlike MPII it does not convert that caveat into a use restriction.

---

## 3. AI Challenger - the one #19 could not establish at all

**#19 recorded AI Challenger as unknowable. It is not. An archived copy of the owner's own agreement survives, and it contains an express non-commercial clause.**

### 3.1 What is dead, and what is not

**VERIFIED.** `challenger.ai` still resolves - `47.92.70.128`, served by `ns1.alidns.com` / `ns2.alidns.com`, i.e. Alibaba Cloud - but nothing answers. Both `http://challenger.ai/` and `https://challenger.ai/` time out at the TCP layer with `time_connect=0.000000`, meaning the socket never opens. This is not a 404 and not a parked page; the host silently drops traffic. The registration is alive, the service is gone.

The surviving repository [`AIChallenger/AI_Challenger_2017`](https://github.com/AIChallenger/AI_Challenger_2017) confirms #19's reading: `https://api.github.com/repos/AIChallenger/AI_Challenger_2017/license` returns 404, the repo root holds only `Baselines/`, `Evaluation/` and `README.md`, and the 12-line README contains no terms at all - it points at the dead site: *"AI Challenger is a platform for open datasets and programming competitions to artificial intelligence (AI) talents around the world. To participate, please visit https://challenger.ai/."*

### 3.2 The archived agreement, which #19 did not reach

**VERIFIED, from an Internet Archive snapshot of the owner's own `challenger.ai/terms` page, dated 2018-08-11** (`web.archive.org/web/20180811180623id_/https://challenger.ai/terms`). The page is the competition entrant agreement, 竞赛选手报名协议. Article 3, 知识产权 (Intellectual Property), item 3, in the original Chinese:

> "除非举办方和选手另有约定，选手应保证其仅在科学研究或课堂教学等非商业性目的范围内使用基础数据，并对基础数据的使用自行承担全部责任，以保证举办方及其关联方免受任何因基础数据使用导致的索赔或诉讼。"

**My translation, labelled as mine:** *"Unless otherwise agreed between the organiser and the contestant, the contestant shall ensure that they use the Base Data only within the scope of non-commercial purposes such as scientific research or classroom teaching, and shall bear full responsibility for their use of the Base Data, so as to hold the organiser and its affiliates harmless from any claim or litigation arising from that use."*

"基础数据" (Base Data) is defined in item 2 of the same article as the images, videos and data supplied by the organiser. Item 2 adds, in the original: *"选手如在使用该等成果过程中使用了举办方及其关联方享有知识产权或其他合法权利的基础数据，应向举办方及其关联方支付使用费用"* - **my translation:** *"if the contestant uses, in the course of using such results, Base Data in which the organiser or its affiliates hold intellectual property or other lawful rights, the contestant shall pay the organiser and its affiliates a usage fee."*

**That is an express non-commercial restriction over the data, written by the dataset's own publisher.**

### 3.3 What still cannot be established, and why it matters

**Two limits, stated plainly rather than buried.**

1. **The instrument that would actually govern a dataset download was never archived.** Article 3 item 1 opens *"除数据集下载协议另有约定外"* (*"except as otherwise agreed in the Dataset Download Agreement"*), and Article 5 item 1 directs the reader to the 《数据集下载协议》. That document lived at `challenger.ai/terms/data`. Querying the full Wayback index for the path (`web.archive.org/cdx/search/cdx?url=challenger.ai/terms*`) returns **exactly one row: `https://challenger.ai/terms 20180811180623 200`.** `/terms/data`, `/terms/copyright` and `/terms/user` were **never captured**. So the agreement that expressly overrides the one quoted above is unrecoverable, and it could in principle be either stricter or looser.
2. **The agreement quoted is a competition entrant agreement, not a dataset licence.** It binds people who clicked "register" for the 2017 competition. Whether it reaches someone who obtained the dataset years later from a mirror is a different question, and not one this ticket can settle.

The dataset's own page, `challenger.ai/dataset/keypoint` (archived 2019-06-23), carries download links with SHA1 sums and **no terms text of any kind** - only a takedown contact: *"如果发现本网站存在侵犯自身合法权益的内容，请及时与 hi@challenger.ai 取得联系。"*

### 3.4 The verdict, and how it changes the picture

**PARTIALLY ESTABLISHED, and it resolves against AI Challenger rather than for it.**

#19 wrote that "unknowable" is worse than a known restriction. That framing still holds, and AI Challenger now sits in both categories at once: **there is a recoverable, owner-written non-commercial term over the data, and the document that would supersede it is permanently unrecoverable.** Practically, that is the same posture as MPII with worse paperwork - a restriction you can read, sitting under an agreement you cannot.

**The consequence for the checkpoint choice is direct: `aic-coco` does not escape the problem, it relocates it.** Swapping `body7` for `aic-coco` drops MPII, PoseTrack18, CrowdPose, sub-JHMDB and Halpe, and keeps AI Challenger, whose own entrant agreement restricts the data to *"non-commercial purposes such as scientific research or classroom teaching"*. That is a smaller surface, not a clean one.

---

## 4. Pricing the swap: what `aic-coco` actually costs on rear views

`aic-coco` publishes **75.8 AP on COCO against `body7`'s 74.9**, so on paper the swap is free. **Published COCO AP is a whole-dataset average over a cohort that is mostly front-facing, and #18 exists precisely because that average hides the rear view.** Nobody had measured the swap candidate on the failure mode the product depends on. This does.

Everything below is `experiments/checkpoint-swap/`, on #18's 1,675-instance COCO val2017 cohort, with the crop, the orientation proxy and the chirality test reused verbatim, and the detector, pose scoring and statistics reused verbatim from #19.

### 4.1 The export, and why a control was mandatory

**VERIFIED by doing it.** `aic-coco` ships `.pth` only - MMPose's `projects/rtmpose/README.md` shows an `onnx` link for every `body7` row and none for any `aic-coco` row. So the graph had to be produced here, with MMDeploy, following the invocation MMPose itself documents:

```
python tools/deploy.py \
    configs/mmpose/pose-detection_simcc_onnxruntime_dynamic.py \
    ../mmpose/projects/rtmpose/rtmpose/body_2d_keypoint/rtmpose-m_8xb256-420e_coco-256x192.py \
    https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192-63eb25f7_20230126.pth \
    demo/resources/human-pose.jpg \
    --work-dir rtmpose-ort/rtmpose-m --device cpu --show --dump-info
```

That is upstream's own worked example, and upstream's own worked example happens to use the `aic-coco` checkpoint. Same MMDeploy v1.3.1 clone `experiments/person-detector/export_onnx.sh` used for #19.

**A self-exported graph is not automatically the published graph, so `body7` was exported the same way and run as a third arm.** `body7` ships both a `.pth` and an official ONNX bundle, which makes it the control:

| | |
|---|---|
| rows compared | 3,350 |
| max abs difference in corrected OKS | 2.264e-03 |
| mean abs difference in corrected OKS | 7.788e-07 |
| instances where the chirality verdict differs | **0** |

**The self-exported `body7` graph is the published `body7` graph.** So any difference `aic-coco` shows is a property of its weights, not of the export. The reverse check rules out the other failure mode: `aic_coco_self` differs from `body7_official` by mean 1.405e-02 and max 8.860e-01 corrected OKS, so these are genuinely two different sets of weights and not one file under two names.

**And the anchor holds.** `body7_official` reproduces #18 and #19 exactly on the same instances: sign-confirmed REAR swap **3/293 = 1.0%** on ground-truth boxes, **3/251 = 1.2%** on RTMDet-Ins-tiny boxes. Identical to `rear-view-experiment.md` and `person-detector.md`. That is the check that makes this sweep commensurable with theirs.

### 4.1a A third candidate, which #19 said did not exist

**VERIFIED, and it corrects a factual error in `person-detector.md`.** #19 wrote: *"MMPose publishes exactly two 2D body training mixtures for RTMPose, and no others... There is no COCO-only RTMPose-m checkpoint."* That was read off `projects/rtmpose/README.md`, whose section headers are indeed `AIC+COCO` and `Body8`.

**MMPose's main model zoo publishes a third.** [`configs/body_2d_keypoint/rtmpose/coco/rtmpose_coco.md`](https://raw.githubusercontent.com/open-mmlab/mmpose/main/configs/body_2d_keypoint/rtmpose/coco/rtmpose_coco.md) lists `rtmpose-m` at **0.746 AP** on COCO val2017 with the checkpoint `rtmpose-m_simcc-coco_pt-aic-coco_420e-256x192-d8dd5ca4_20230127.pth`.

**Read the name, because it is the whole point.** MMPose's convention is `simcc-<supervised pose training set>` and `pt-<backbone pretraining set>`. So this checkpoint is **keypoint-supervised on COCO alone**, with a backbone pretrained on AIC+COCO. MPII, PoseTrack18, CrowdPose, sub-JHMDB and Halpe are absent entirely; AI Challenger appears only in pretraining. It is a materially different position from `aic-coco`, and it was measured here as a fourth arm.

### 4.2 The number the ticket asked for

**VERIFIED. There is no measurable rear-view cost. On the deployable condition `aic-coco` is nominally better, and the difference is not significant.**

Chirality swap rate, sign-confirmed instances only - the subset #18's and #19's verdicts quoted:

| condition | orientation | `body7` (#18/#19) | `aic-coco` | z, p | `simcc-coco` | z, p |
|---|---|---|---|---|---|---|
| ground-truth box | **REAR** | **1.0% (3/293)** | **1.0% (3/293)** | 0.000, 1.000 | 1.4% (4/293) | 0.380, 0.704 |
| ground-truth box | FRONT | 0.4% (3/804) | 0.1% (1/804) | -1.001, 0.317 | 0.2% (2/804) | -0.448, 0.654 |
| RTMDet-Ins-tiny box | **REAR** | **1.2% (3/251)** | **0.4% (1/251)** | -1.004, 0.315 | **1.2% (3/251)** | 0.000, 1.000 |
| RTMDet-Ins-tiny box | FRONT | 0.3% (2/706) | 0.3% (2/706) | 0.000, 1.000 | 0.3% (2/706) | 0.000, 1.000 |

**So the headline is: 1.0% -> 1.0% on ground-truth boxes and 1.2% -> 0.4% on real detector boxes for `aic-coco`, and 1.0% -> 1.4% / 1.2% -> 1.2% for `simcc-coco`.** Every one of those is null. The FRONT rows are shown so a rear-specific claim is not being made from a whole-cohort effect; they are null too.

**The useful form of this result is not "the swap is safe", it is "the choice is not an accuracy choice".** All three checkpoints sit inside each other's confidence intervals on the failure mode the product depends on. That means the decision in section 6 can be made on licensing grounds without trading anything measurable away.

**The honest counterweight, reported because cherry-picking the confirmed subset would be exactly the wrong move.** On the *full* REAR bucket, which includes instances where the visibility proxy and the annotated shoulder order disagree, the direction is not uniform:

| orientation | `body7_official` | `body7_self` | `aic_coco_self` | `coco_self` |
|---|---|---|---|---|
| FRONT | 0.005 [0.002, 0.012] n=832 | 0.005 [0.002, 0.012] n=832 | 0.001 [0.000, 0.007] n=832 | 0.004 [0.001, 0.011] n=832 |
| OBLIQUE | 0.026 [0.014, 0.047] n=384 | 0.026 [0.014, 0.047] n=384 | 0.031 [0.018, 0.054] n=384 | 0.031 [0.018, 0.054] n=384 |
| PROFILE | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.038] n=96 | 0.000 [0.000, 0.038] n=96 | 0.010 [0.002, 0.057] n=96 |
| **REAR** | **0.019 [0.009, 0.039] n=363** | 0.019 [0.009, 0.039] n=363 | **0.028 [0.015, 0.050] n=363** | **0.036 [0.021, 0.060] n=363** |

On ground-truth boxes and the unfiltered REAR bucket, `aic-coco` is 2.8% and `simcc-coco` 3.6% against `body7`'s 1.9%. **Every interval in that table overlaps, and the same comparison on the detector boxes runs the other way for `aic-coco` (1.6% vs 2.0%).** The defensible statement is that the checkpoints are indistinguishable on rear chirality at this cohort size, not that any of them is better. **Anyone quoting only the sign-confirmed table is quoting the half that flatters the swap.**

### 4.3 Positional error, kept separate as the map requires

**VERIFIED. `aic-coco` is marginally better at every orientation on both box sources; `simcc-coco` is a wash with `body7`.** Mean OKS after correcting chirality:

| orientation | gt box, `body7` | gt box, `aic-coco` | gt box, `simcc-coco` | det box, `body7` | det box, `aic-coco` | det box, `simcc-coco` |
|---|---|---|---|---|---|---|
| FRONT | 0.9500 | **0.9555** | 0.9512 | 0.9536 | **0.9576** | 0.9540 |
| OBLIQUE | 0.9249 | **0.9315** | 0.9243 | 0.9256 | **0.9345** | 0.9270 |
| PROFILE | 0.9292 | **0.9320** | 0.9268 | 0.9300 | **0.9340** | 0.9253 |
| REAR | 0.9297 | **0.9325** | 0.9264 | 0.9357 | **0.9388** | 0.9327 |

PCK@0.2 moves the same way (REAR 0.9765 for `body7`, 0.9798 for `aic-coco`, 0.9737 for `simcc-coco`, on ground-truth boxes). **This is consistent with the published 74.9 / 75.8 / 74.6 AP ordering, and it extends that ordering to the rear view, which the published numbers could not.**

Composite usable-capture rate, #18's definition, over the whole detector arm without conditioning on correct selection: REAR 0.821 `body7`, 0.824 `aic-coco`, 0.818 `simcc-coco`. Unchanged.

### 4.4 The costs that are not accuracy

**VERIFIED.** All three self-exported graphs are byte-identical in size, because they are the same architecture:

| graph | bytes | MiB | 1 thread | 2 threads | 4 threads |
|---|---|---|---|---|---|
| `body7` official bundle (what #19 measured) | 54,330,655 | 51.81 | 44.0 ms | 24.7 ms | 14.6 ms |
| `body7` self-exported | 54,369,767 | 51.85 | 45.9 ms | 23.6 ms | 16.1 ms |
| `aic-coco` self-exported | 54,369,767 | 51.85 | 34.1 ms | 22.8 ms | 15.5 ms |
| `simcc-coco` self-exported | 54,369,767 | 51.85 | 34.1 ms | 21.1 ms | 14.4 ms |

**So the swap costs nothing in IPA size and nothing in latency.** All graphs are `ai.onnx` opset 11, domain `''` only, no custom ops, input `input [batch, 3, 256, 192]`, outputs `simcc_x` and `simcc_y` - the same signature #19 recorded for the official bundle, so nothing changes for `flutter_onnxruntime`. Median of 20 runs after 3 warmups, x86-64 Linux under ONNX Runtime 1.19.2's CPU execution provider, box otherwise idle. **Same caveat as #19, unchanged: this is not an iOS measurement.** The single-thread spread across identical architectures is measurement noise, not a real difference.

**One provenance oddity, recorded rather than smoothed over.** OpenMMLab tags its checkpoint filenames with an 8-hex digest. `body7`'s matches the file served: SHA256 `e48f03d0cfe1285ee8b6d3457ac3ce33a4594a92b080053ab1ec4a7e300975f2` under a name saying `e48f03d0`. **`aic-coco`'s does not**: the served file is `5e55be2a03f6e5dcd14d088afc4ae5afe94a4f9de93c22e5deb725ad0eee899d` under a name saying `63eb25f7`, its `Last-Modified` is 2023-04-18 although the name says `20230126`, and `Content-Length` matches the download exactly so it is not a truncated fetch. **The `aic-coco` file currently served is not the file that was published under that name.** It works, it exports, and it measures as above - but anyone relying on the filename as an integrity check should know it does not hold. The `simcc-coco` checkpoint has the same defect (`929f00f2...` under a name saying `d8dd5ca4`). All SHA256s are recorded in `results/run_meta.json`.

---

## 5. Is there a genuinely clean option at all?

**No. Not in this field, and not from any publisher.** Here is the full set of options with their costs. **This is not a decision, and it is not mine to make.**

### 5.1 The four candidates, side by side

| | `body7` (current) | `aic-coco` | `simcc-coco` | retrain / other engine |
|---|---|---|---|---|
| Checkpoint | `rtmpose-m_simcc-body7_pt-body7_420e-256x192` | `rtmpose-m_simcc-aic-coco_pt-aic-coco_420e-256x192` | `rtmpose-m_simcc-coco_pt-aic-coco_420e-256x192` | none exists |
| Supervised pose data | AIC, COCO, CrowdPose, **MPII**, sub-JHMDB, Halpe, **PoseTrack18** | **AIC**, COCO | **COCO alone** | - |
| Backbone pretraining | body7 | AIC+COCO | **AIC+COCO** | - |
| Datasets carrying an express non-commercial term | **MPII, PoseTrack18, AI Challenger** | **AI Challenger** | **AI Challenger, in pretraining only** | - |
| Datasets carrying no licence at all | CrowdPose, sub-JHMDB, Halpe | - | - | - |
| Published COCO AP | 74.9 | **75.8** | 74.6 | - |
| Rear swap, gt box (sign-confirmed) | **1.0%** | **1.0%** (p = 1.00) | 1.4% (p = 0.70) | - |
| Rear swap, detector box (sign-confirmed) | **1.2%** | **0.4%** (p = 0.32) | **1.2%** (p = 1.00) | - |
| Official ONNX published? | yes | no, export it | no, export it | - |
| Graph size / latency | 51.8 MiB / 24.7 ms | 51.8 MiB / 22.8 ms | 51.8 MiB / 21.1 ms | - |

### 5.2 The options, with costs

| | Option | Cost | Residual exposure |
|---|---|---|---|
| **O1** | **Keep `body7`, record the exposure** | Nothing. It ships today and it is the only one with an official ONNX | **Three express non-commercial terms** (MPII, PoseTrack18 CC BY-NC 4.0, AI Challenger) plus **three datasets with no grant at all** (CrowdPose, sub-JHMDB, Halpe). The widest surface of the four |
| **O2** | **Swap to `aic-coco`** | An MMDeploy export, already done and committed here, plus re-running #18's and #19's numbers, also already done | **One express non-commercial term** (AI Challenger), whose superseding data agreement is unrecoverable. Best measured accuracy of the four |
| **O3** | **Swap to `simcc-coco`** | Same export, same re-measurement, both done here | **AI Challenger in backbone pretraining only.** Supervised pose data is COCO alone, and COCO is the one dataset in the field with a real grant (CC BY 4.0 annotations, no NC clause) |
| **O4** | Train an RTMPose-m on COCO alone, from an ImageNet-only backbone | A real training job: 420 epochs, 8-GPU config, far outside this effort. No published checkpoint to start from | Only ImageNet, which attaches to essentially every vision model including the RTMDet-Ins detector #19 chose. Not a discriminator |
| **O5** | Drop to a fallback engine | Discards [#16](https://github.com/grez-lucas/poseperfect/issues/16) and #18's measured result. BlazePose is 14.4% rear swap, MoveNet Thunder 7.2%, against RTMPose's 1.0% | Unknown, and #18 already established the accuracy cost is severe |
| **O6** | Ask the rights holders | Free, slow, and partly impossible: `challenger.ai` is dead, `posetrack.net`'s DNS delegation is broken, `jhmdb.is.tue.mpg.de` is a 2014-era 404. MPII and HICO-DET have live contacts | Would resolve MPII and HICO-DET only |

**Two things that are true of every option and should not be used to discriminate between them.**

1. **ImageNet is in all of them**, via the CSPNeXt backbone, and it is in the RTMDet-Ins detector #19 chose too. It is not a differentiator.
2. **OpenMMLab has never stated in writing that its checkpoints are Apache-2.0.** #19 established that and it is unchanged here. It applies identically to all four RTMPose candidates and to the detector.

**And one thing that is out of bounds for this ticket, per the issue: whether a dataset use restriction legally reaches a model trained on that dataset.** It is unsettled generally, it is the crux of every row above, and a research ticket is the wrong instrument for it. **Recorded as a risk. Not resolved.**

---

## 6. Recommendation

**Ship `simcc-coco` - `rtmpose-m_simcc-coco_pt-aic-coco_420e-256x192-d8dd5ca4_20230127` - option O3. This is a recommendation, not a decision.**

The reasoning is short because the measurement made it short. **The three candidates are statistically indistinguishable on rear chirality swap, which is the failure mode this whole product line of tickets exists to control**, and they are identical in graph size, opset and latency. So there is nothing to trade. Given nothing to trade, take the checkpoint with the smallest licensing surface.

`simcc-coco` is the only option whose **supervised pose training data is a single dataset that actually grants something**: COCO's annotations are CC BY 4.0 with no non-commercial clause. It removes MPII, PoseTrack18 (and therefore MPII a second time), CrowdPose, sub-JHMDB and Halpe outright, and demotes AI Challenger from supervised training data to backbone pretraining. **That last distinction is a real reduction in exposure and it is also the weakest link in the recommendation** - it is a narrower claim than "AI Challenger is gone", and section 5's out-of-bounds question applies to pretraining exactly as it does to training.

**If Lucas prefers to weight measured accuracy over licensing surface, O2 (`aic-coco`) is the defensible alternative**: it is the best of the four on positional error at every orientation and the best on detector-box rear swap, at the cost of keeping AI Challenger as supervised training data. **What is not defensible is O1**, keeping `body7`, now that the audit is complete: it carries the widest surface, it is not more accurate, and the swap has been shown to cost nothing.

### 6.1 The residual risk, in one paragraph

PosePerfect's pose model is trained on photographs that neither the model's publisher nor the dataset's publisher owns. Every dataset in this field is assembled from other people's pictures - YouTube frames, Flickr uploads, clips from commercial films - and the labs that assembled them say so plainly and then disclaim holding the copyright. `simcc-coco` narrows this to COCO, whose publisher grants the *annotations* under CC BY 4.0 and states that use of the *images* "must abide by the Flickr Terms of Use", plus AI Challenger in the backbone, whose publisher wrote a non-commercial clause on a website that no longer exists. **What that means in practice: as a personal tool that is not sold and not distributed, per map decision 1, there is no realistic exposure at all, and nothing here needs acting on today.** The exposure appears only if PosePerfect is ever sold, subscribed, ad-supported or otherwise commercialised. At that moment the open question is not a licence-compatibility problem - **nothing here obliges anyone to open-source anything** - it is whether a use restriction written over a dataset follows the model trained on it, which is unsettled law that this ticket was explicitly told not to try to settle. **The practical action is therefore not legal work now; it is to make the checkpoint a one-line configuration rather than an assumption baked into the pipeline, so that if the answer ever arrives, swapping is an afternoon.** This ticket has already proved that swapping is an afternoon: the export, the re-measurement and the comparison are committed in `experiments/checkpoint-swap/`.

---

## 7. What this means for `person-detector.md` and #16

**Two corrections to the record, both mine to report and neither mine to apply.**

1. **#19's section 6.1 says "There is no COCO-only RTMPose-m checkpoint."** That is wrong. `rtmpose-m_simcc-coco_pt-aic-coco` is keypoint-supervised on COCO alone and is published in MMPose's main COCO model zoo. The error came from reading `projects/rtmpose/README.md` and not `configs/body_2d_keypoint/rtmpose/coco/`.
2. **#19's option B2 says swapping to `aic-coco` "may trade a known restriction for an unknown one".** AI Challenger's restriction is no longer unknown: section 3 recovers an express non-commercial clause from the owner's own archived agreement. The trade is now known in both directions.

**[#16](https://github.com/grez-lucas/poseperfect/issues/16)'s stated prerequisite that "RTMPose weight licensing must verify clean" does not hold for any published RTMPose-m checkpoint**, and #19 was right that it does not hold for `body7`. It holds least badly for `simcc-coco`. **That is an amendment to a settled decision and it belongs in front of Lucas, which is what the resolution comment on #20 is for.**

---

## 8. Caveats, stated plainly

1. **COCO is clothed people in everyday scenes.** Unchanged from #18 and #19 and still the largest gap on the map: nobody has evaluated any of these checkpoints on heavily muscled, oiled, minimally clothed physique athletes holding extreme static poses. This experiment measures a checkpoint difference. **It does not measure our population.**
2. **The rear-facing label is #18's visibility-derived proxy**, about 81% pure on REAR, and ordinal rather than angular. Every headline number is also reported on the sign-confirmed subset, and section 4.2 reports the unfiltered bucket too, where the direction is less flattering.
3. **The cohort is too small to resolve a difference this size.** Three swaps out of 293 is three events. A null two-proportion z-test at n=293 rules out a large difference, not a small one. **"Indistinguishable" is the claim; "equivalent" is not.**
4. **Nothing was validated by eye.** Map constraint 2. No overlay was rendered at any point.
5. **No score threshold was applied when recording.** Map constraint 3.
6. **Latency is x86-64 Linux under ONNX Runtime's CPU execution provider.** Not iOS. The ordering is meaningful, the absolute numbers are not the device numbers.
7. **Three of the seven dataset owners' sites are dead**, so their terms are quoted from Internet Archive snapshots of the owners' own pages, labelled as archived with their dates. An archived owner page is a primary source; a third-party summary is not, and none was used.
8. **The AI Challenger translation is mine.** The original Chinese is quoted alongside it in section 3 so it can be checked.
9. **This document does not establish that any option is legally safe.** It establishes what each dataset's publisher wrote down, and what each checkpoint measures. The step from there to a legal conclusion is out of bounds for this ticket by the ticket's own terms.

---

## 9. Not established

Listed so nobody mistakes silence for a clean bill.

**Licence**

1. **Whether a dataset use restriction reaches a model trained on that dataset.** Out of bounds by the ticket's own terms, unsettled generally, and the crux of everything above.
2. **AI Challenger's 《数据集下载协议》 (Dataset Download Agreement).** The one instrument that expressly overrides the clause quoted in section 3, at `challenger.ai/terms/data`. The Internet Archive never captured it, `challenger.ai` no longer serves, and the full Wayback index for `challenger.ai/terms*` returns exactly one row. **Permanently unrecoverable as far as this ticket can tell.**
3. **Whether OpenMMLab's checkpoints are covered by the Apache-2.0 licence on its code.** Unchanged from #19. Never stated in writing. Nobody has asked.
4. **Which Creative Commons licences HICO-DET's Flickr images actually carry.** "Creative Common images from Flickr" spans seven licences, three of them NonCommercial, and no per-image manifest is published.
5. **The `README` inside HICO-DET's 7.5 GB `hico_20160224_det` tarball.** Its existence is confirmed by both the `hico_benchmark` repo and MMPose's expected directory layout. It is the one place HICO-DET terms could still be written down, and it was not downloaded.
6. **What terms, if any, J-HMDB's login-gated download page carried.** The Internet Archive crawler was never logged in, and the site is dead.
7. **What fraction of CrowdPose's 20,000 images came from MPII.** The paper gives no per-source breakdown.
8. **Whether PoseTrack18's doubling of PoseTrack17 drew on the same MPII pool.** The ECCV'18 page says the videos are "similar to" PoseTrack17's and the `*_mpii` naming persists in the 2018 format, but no owner statement says so explicitly, and none contradicts it.

**Measurement**

9. **Anything about physique athletes.** Third ticket in a row to say so.
10. **On-device latency and real linked IPA size.** Same gap #19 recorded. Needs the `ios-builder` pipeline from [#2](https://github.com/grez-lucas/poseperfect/issues/2).
11. **Whether the swap changes anything for the segmentation half of [#17](https://github.com/grez-lucas/poseperfect/issues/17).** It cannot: the mask comes from RTMDet-Ins, which this ticket did not touch.
12. **fp16 or quantised variants of any of the four checkpoints.** Not exported, not evaluated.
13. **RTMPose-m at 384x288, and RTMPose-l/x.** The `aic-coco` 384x288 checkpoint publishes 77.0 AP. Out of scope here, which fixed the size and input resolution #16 chose.
