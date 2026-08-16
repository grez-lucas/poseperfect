# Capture protocol - wayfinder ticket #9

**This is the human half of the experiment.** Nothing in `experiments/real-subject/`
can produce a number until this session has been shot. Read it once end to end
before you start; several steps cannot be repaired afterwards.

Print `python shotplan.py` and keep it beside you - it is the numbered sequence,
115 frames, and it is the authority. This file explains the parts of it that
would otherwise look arbitrary.

---

## Why the tape

Every measurement in `experiments/rear-view/` and `experiments/checkpoint-swap/`
is a difference against COCO's annotated keypoints. Your photographs have no
annotation, so none of those functions can be pointed at them, and map
constraint 2 rules out the obvious substitute: occluded joints are supervised
toward a "best guess and default pose", so a rear-view skeleton looks entirely
plausible while tracking a learned average human. **Checking it by eye would
confirm exactly the failure this ticket is hunting.**

So the ground truth is physical. Tape of a known colour on a known side is a
fact about the photograph, not a judgement about the model's output.

The instrument was validated before you shoot anything - see
`results/synthetic_check.json`, which paints synthetic tape onto ticket #18's
COCO cohort and checks the tape verdict against the annotation verdict on the
same frames.

---

## Before you shoot

**1. Tape.** Four pieces. Two colours, one per anatomical side:

| | |
|---|---|
| **Colour 1** | left wrist **and** left ankle |
| **Colour 2** | right wrist **and** right ankle |

Both colours must be strongly saturated and appear nowhere else in the room or
on you - not white, not black, not skin-adjacent, not the colour of your trunks
or the floor. Green and magenta are a safe pair. **The code learns each colour
from your actual roll**, so any two distant colours work, and it will refuse to
run if the two are too close to tell apart rather than quietly guessing.

Four limbs and not two, because #18 found 19% of rear skeletons transposed in
the shoulders but not the legs. One marker per side would score those as passes.

**2. Camera settings.** Set these and do not change them mid-session:

- **Settings > Camera > Formats > Most Compatible.** Writes JPEG directly. HEIC
  gets transcoded on the way to Linux, and a recompression in the middle of the
  measurement is one variable nobody needs.
- **Settings > Photos > Transfer to Mac or PC > Keep Originals.**
- **Note down whether Settings > Camera > Mirror Front Camera is on or off, and
  do not touch it afterwards.** This is not bookkeeping. It decides whether the
  saved front-camera pixels match what you saw, and a marker on your anatomical
  left is what will detect it - a known-sign flip is the one case where we
  already know the right answer, so it is the strongest single check that the
  whole instrument works.
- Live Photos off, flash off, HDR left alone but not changed between blocks.

**3. The room.** Tripod or phone stand, far enough back to frame you head to
foot with your arms up. Tape your standing position on the floor **in a colour
that is neither marker colour** - plain masking tape - so the analysis never
mistakes it for a marker.

**4. The scale marks.** Two pieces of **colour 1** tape on the floor, exactly
**1.00 m apart**, left-to-right across the frame, on your standing line. These
are what let the noise floor be quoted in centimetres instead of pixels, and
centimetres are the only unit in which the pre-registered threshold means
anything. **Shoot frame CAL-S, then take them up** - if they stay down they will
be found as markers in every later frame.

**5. The tripod does not move again.** Not between blocks, not between cameras,
not when you switch the tape off for block E. If it moves, say so in the shot
log rather than trying to compensate.

---

## The blocks, and why they are in this order

**C and D come first, while you are freshest.** They are the noise floor, and
tickets #11 and #12 both inherit that number. A tired eighth rep inflates it,
and an inflated floor is not conservative - it would wrongly condemn a metric
that works.

| block | what | frames |
|---|---|---|
| CAL | tape colour close-ups and the 1 m floor scale | 3 |
| **C** | **sensor floor** - Front Double Biceps and Back Double Biceps, burst of 10, **do not move between frames**, both cameras | 40 |
| **D** | **human floor** - the same two poses, break the pose completely and re-hit it, 8 times, front camera | 16 |
| A | chirality sweep - all 12 poses x 2 reps, front camera | 24 |
| B | chirality sweep - all 12 poses x 2 reps, rear camera | 24 |
| E | marker control - 4 poses with **the tape removed**, rear camera | 4 |
| F | mirror arm - 4 poses with **your reflection visible in frame**, front camera | 4 |

**Block C is a burst.** Hold the pose and let the camera fire ten times. The
point is what the pipeline does when *nothing changes*, so any movement you add
is contamination rather than realism.

**Block D is the opposite.** Break the pose all the way - drop your arms, step
off the mark, shake it out - then step back on and hit it again. Eight times.
This is the floor the product actually faces, because in real use you re-hit the
pose every session, and it is strictly larger than block C's.

**Block D is front camera only.** The camera comparison belongs to block C,
where it costs nothing; sixteen rear double biceps holds per camera would have
measured your fatigue rather than your repeatability.

**Block E: take the tape off.** Same four poses, rear camera. This prices what
the tape itself does to the landmarks it is meant to label - without it, the
marker method is an assumption rather than a measurement.

**Block F needs your reflection in the frame**, not just a mirror on the wall.
Stand so the camera sees both you and your reflection. #19 found that picking
the highest-scoring detection finds the target only 83.7% of the time, and a
mirror is not a contrived test case for a posing room - it is the deployment
condition. If your reflection is not in frame, block F measures nothing.

**Side Chest, Side Triceps, Quarter Turn Right and Quarter Turn Left have a
facing direction.** Keep it the same for both reps and write it down. Map
constraint 5 makes comparing across facing directions invalid, not merely
noisy - pose models are not left/right symmetric.

---

## After the session

1. Plug the iPhone into the Linux box and copy the whole `DCIM` folder off. Do
   not let anything resize, rotate or re-encode on the way.
2. `python ingest.py --photos <that directory>` writes `results/shotlog.csv`
   with a SHA256 per file and a **proposed** mapping from file to block, pose
   and camera, aligned by EXIF capture time against the shot plan.
3. **Open `shotlog.csv` and fix it.** The proposal assumes nothing was re-shot,
   and something always is. Rows flagged `CAMERA_MISMATCH` or `LONG_GAP` are
   where to look first. Put `y` in `confirmed` on every row you want measured,
   and fill `facing` with L or R on the four poses that have one.
4. `./run.sh` does the rest.

**The photographs never enter git.** The repository is public by decision 11.
`shotlog.csv` carries a SHA256 per file, which is what keeps a published number
traceable to a file that was deliberately not published - the same arrangement
tickets #18, #19 and #20 have with COCO's 1 GB.

---

## What was agreed and will not be revisited quietly

- **Oil is out of scope.** Practice is dry, so the deployment condition is dry.
  The consequence, recorded rather than buried: the competition-day condition
  stays unmeasured, and a reference captured oiled would be untested territory.
- **Never validate by eye**, at any point, including when a result looks wrong.
- **Never gate on engine confidence** - measured at AUC 0.53-0.56 for detecting
  its own chirality failure.
- **Positional and chirality error stay two separate numbers.**
- **IMAGE mode only.**
