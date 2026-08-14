# PROTOTYPE - real-subject validation (wayfinder #9)

**Throwaway code that answers one question.** Not app code, not on the route to
the product, and nothing here should be imported by anything.

Ticket: [#9 Validate RTMPose on the real subject](https://github.com/grez-lucas/poseperfect/issues/9).
The capture protocol Lucas follows is [`CAPTURE.md`](CAPTURE.md).

## The problem this directory exists to solve

#9 says to "re-run `experiments/checkpoint-swap/`'s chirality and positional
measures" against photographs of the real subject. **That instruction cannot be
followed as written.** Every measure in `experiments/rear-view/` and
`experiments/checkpoint-swap/` is a difference against COCO's annotated
keypoints:

```
experiments/rear-view/run_experiment.py:115
def chirality(pred_xy, gt_xy, vis, area, pairs):
    """... Scored only on ground-truth keypoints at v == 2 ..."""
```

`oks`, `pck` and `chirality` all take `gt_xy` and `vis`. Photographs of an
athlete in his own room have none. Map constraint 2 closes the obvious escape -
occluded joints are supervised toward a "best guess and default pose", so a
rear-view skeleton is smooth, stable and visually plausible while tracking a
learned average human. **Checking by eye would confirm exactly the failure being
hunted.**

So the instrument had to be built, and building it is most of this ticket.

## How ground truth is manufactured

Coloured tape, four limbs, two colours, one per anatomical side. Where the tape
sits in a photograph is a fact about the photograph, not a judgement about the
model's output, and reading it costs no human labour per frame.

Four limbs rather than two because #18 found **19% of rear skeletons internally
inconsistent** - transposed in the shoulder girdle but not the legs - and one
marker per side would score those as passes.

What this buys and what it does not: it labels four joints, which is enough for
chirality and nothing else. Absolute positional error is deliberately not
measured here. #18 already settled it (tolerable, architecture-independent,
corrected OKS drop 0.087 vs 0.078), and under self-referential scoring a
systematic bias cancels against the athlete's own reference. The bias that would
*not* cancel is one that moves with condition, and that is measurable as a
difference between two of his own captures with no annotation at all.

## The instrument is validated before it is used

`synthetic_check.py` paints synthetic tape onto #18's COCO cohort at the
annotated wrist and ankle positions and compares the tape verdict against #18's
annotation-based verdict on identical frames and identical predictions. This is
not optional: if the colour calibration, the blob finder, the wrist-versus-ankle
assignment or the nearest-keypoint rule were wrong, every downstream number
would be an artefact, and **nothing in the real capture set could reveal it.**

Because RTMPose-m swaps on only ~1% of rear COCO instances, real positives are
too scarce to test recall, so positives are **manufactured**: every instance is
scored twice, once on the real prediction and once with left and right
deliberately transposed, which is the exact failure the instrument exists to
catch, injected at a known 100% rate.

Measured over **681 instances**, at the chosen decisive margin of 0.20 torso
lengths:

| bucket | coverage | false alarm | injected recall |
|---|---|---|---|
| ALL | 90.6% | 1.0% | 99.4% |
| FRONT | 92.9% | 1.1% | 100.0% |
| OBLIQUE | 89.8% | 1.7% | 99.4% |
| PROFILE | 87.1% | 0.0% | 100.0% |
| REAR | 90.7% | 0.6% | 98.3% |

**The limit this leaves must be quoted with any rear result.** A 0.6% rear
false-alarm rate is the same order as the 1.0% rear swap rate #18 measured for
RTMPose-m on COCO. **This instrument cannot resolve a rate that small.** It can
resolve the pre-registered decision boundaries of 5% and 20%, which is what it
was built for, and it must not be asked for more.

The margin was chosen on COCO and never on the real captures - see the sweep
table in `markers.py`.

## Pre-registered before any photograph

Fixed in `analyse.py`, and the reason they are fixed in advance is that a
threshold chosen after the jitter is known is not a test, it is a
rationalisation.

| | |
|---|---|
| smallest correction the app must report | **5 cm** limb displacement, **3 deg** segment angle |
| rear chirality < 5% | RTMPose confirmed, #14 proceeds |
| rear chirality 5-20% | confirmed, but a session-script orientation prior becomes mandatory - a new ticket |
| rear chirality > 20% | rear mandatories cannot be scored on drift; #16's scope decision reopens |

**The 5 cm and 3 deg came from a gap this ticket exposed.** #9 says "if a
genuine posing correction produces a smaller change than that jitter, the metric
measures noise" - and nowhere on the map, across twenty tickets, was the size of
a genuine posing correction ever written down. It is now, by decision rather
than by default.

The floor is reported as **MDC95** = `1.96 * sqrt(2) * SEM`, the standard
test-retest form: `sqrt(2)` because the reference and the new capture each carry
the noise, 1.96 for two-sided 95%. Comparing a raw standard deviation against
5 cm would claim a sensitivity the pipeline does not have.

## Two noise floors, not one

`#9` asks for "the same pose five times without moving". That is the **sensor**
floor - the best the pipeline could ever do. It is not the number #11 and #12
inherit, because nobody re-hits a pose by not moving. The **human** floor -
break the pose, walk off, come back, hit it again - is strictly larger and is
what the product actually faces. Both are measured and reported separately.

## Run it

```
./bootstrap.sh                  # rebuilds ticket #20's shared venv, adds pillow
./run.sh                        # validates the instrument against COCO
./run.sh <photo directory>      # ...then measures the real captures
python dryrun.py                # fabricates a capture set and exercises the path
```

`dryrun.py` produces **no result about anything**. It fabricates a capture set
from one COCO person and checks the path completes and the tables populate. It
earned its place immediately: it found that the noise-floor grouping was
discarding every frame whose tape was unreadable, halving each group for no
reason, and that the tape-effect table excluded block E's unmarked frames by the
very property that defines them.

The environment is #20's, reused verbatim rather than rebuilt, so a chirality
number here decodes SimCC through the same rtmlib, onnxruntime and numpy that
produced #18's, #19's and #20's.

## Files

| | |
|---|---|
| `CAPTURE.md` | the capture protocol - the human half |
| `shotplan.py` | the canonical 115-frame shot plan; `python shotplan.py` prints it |
| `markers.py` | tape calibration, blob finding, the chirality rule |
| `synthetic_check.py` | validates the instrument against COCO ground truth |
| `ingest.py` | photographs to shot log, with a SHA256 manifest |
| `run_experiment.py` | the sweep: detector, pose, chirality, keypoints |
| `analyse.py` | tables, Wilson intervals, noise floors, the verdict |
| `dryrun.py` | fabricated end-to-end smoke test |

## Three things to know before reading any of it

1. **Never validate by eye.** Map constraint 2. Nothing here renders an overlay,
   deliberately - same discipline as #18, #19 and #20.
2. **No score threshold is applied when recording.** Map constraint 3.
3. **The photographs are not committed and never will be.** The repository is
   public by decision 11. `results/shotlog.csv` carries a SHA256 per file, which
   is what keeps a published number traceable to a file that was deliberately
   not published - the same arrangement the earlier tickets have with COCO.

## Scope, as agreed

**Oil is out.** Practice is dry, so the deployment condition is dry. The
consequence, recorded rather than buried: the competition-day condition stays
unmeasured, and a reference captured oiled is untested territory.

**The front camera is the product's camera.** Decision 7 puts a live guide
overlay on screen during the hold, and a screen pointing away from the athlete
cannot show it. The rear camera is a control, not a deployment option, so the
floor #11 and #12 inherit is the front camera's.
