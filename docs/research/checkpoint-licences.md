# The RTMPose checkpoint's training-data licences, and which checkpoint ships

Resolution of [#20](https://github.com/grez-lucas/poseperfect/issues/20), 2026-08-10. Grading convention matches `pose-engines.md` and `person-detector.md`: **VERIFIED** = measured here or read from a primary source, **INFERRED** = reasoned from measurement, **ANECDOTAL** = reported by others.

**Written as a sibling of [`person-detector.md`](person-detector.md) rather than appended to it**, because it answers a different question about a different model. #19's file is the record of *which detector to put in front of RTMPose-m*; this one is the record of *which RTMPose-m weights to ship*. Appending would have buried a checkpoint decision inside a detector decision, and [#16](https://github.com/grez-lucas/poseperfect/issues/16)'s falsified prerequisite deserves its own findable document.

Code, raw per-instance results and the ONNX export recipe: `experiments/checkpoint-swap/`. It reuses [#18](https://github.com/grez-lucas/poseperfect/issues/18)'s cohort, crop construction and chirality test verbatim, and [#19](https://github.com/grez-lucas/poseperfect/issues/19)'s detector, pose scoring and statistics verbatim, so every number here sits on the same 1,675 COCO val2017 instances as `rear-view-experiment.md` and `person-detector.md`.

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
