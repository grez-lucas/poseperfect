# Men's Open mandatory poses: canonical definitions, cues and observable checkpoints

Research resolving [issue #4](https://github.com/grez-lucas/poseperfect/issues/4).
Date: 2026-08-07.

Feeds two consumers: the in-app pose reference guide, and the shipped canonical reference
poses used for cold-start scoring (map decision 12).

**Reading convention.** Every claim is tagged:

- **[VERIFIED]** - quoted or directly paraphrased from a primary federation document, with URL.
- **[COACHING]** - execution guidance from a named coach or publication. Legitimate for the
  pose guide, but it is not rule and must not be presented as rule.
- **[INFERRED]** - my own derivation, mostly the geometric work in section 4. Sound reasoning,
  but not sourced, and in several places explicitly flagged as needing prototype validation.

---

## Executive summary

Five things came out of this that change what the app can claim.

1. **There is no single "8 IFBB mandatory poses".** The IFBB Pro League (US-based, the
   Olympia/Arnold circuit) mandates **eight** poses. The international IFBB (Madrid, the
   amateur and world-championship body) is a **legally distinct federation** and mandates
   **seven**, with Most Muscular appearing nowhere in its Men's Bodybuilding rulebook. See
   section 1. Getting this wrong in the app's copy - saying "the IFBB mandatory poses" without
   qualifying which IFBB - would be a factual error in the domain's own ubiquitous language.

2. **Most Muscular has no official definition in any primary source found.** The IFBB Pro
   League lists it as mandatory pose 8 and never describes it. The international IFBB omits
   it and, in Classic Physique, explicitly *forbids* it. Every description of how to perform
   it is coaching content. This is a decision for Lucas, not for research - options in
   section 4.8.

3. **No federation rulebook defines the bodybuilding quarter turn** - checked across nine of
   them. The IFBB Pro League and NPC reference "the quarter turns" repeatedly without ever
   defining them; the international IFBB Men's Bodybuilding rulebook does not contain the word
   "quarter" at all. A usable definition does exist one level down, in **NPC promoter
   documents**, word-for-word identical across three independent promoters. See sections 1.4
   and 1.4b. That is the source the app should use, labelled as promoter guidance.

4. **The two lat spreads are the app's blind spot.** Shoulder landmarks sit at the joint
   centre. Flaring the lats does not move them. A landmark-only system can verify that a
   competitor is *in the frame of* a lat spread (hands on waist, elbows wide, feet together)
   and is completely blind to whether the lat spread is any good - which is the entire judged
   content of the pose. Section 4 is explicit about this.

5. **Quarter turns are the most reliably verifiable items in the whole set**, because they are
   about gross body orientation and gross body orientation is exactly what a skeleton encodes.

**Count for the record: 7 of the 8 poses have rule-derived observable checkpoints.** Of those,
5 have checkpoints that both identify the pose and partially verify its execution
(Front Double Biceps, Side Chest, Back Double Biceps, Side Triceps, Abdominals and Thighs);
2 verify only the frame and are blind to the judged quality (Front Lat Spread, Back Lat
Spread); 1 has no checkpoints derivable from any primary source (Most Muscular).

---

## Primary sources used

| Source | What it is | URL |
|---|---|---|
| IFBB Federation Rules, Section 2: Men's Bodybuilding, 2026 Edition | The international IFBB (Madrid) rulebook. **The only primary source found that describes how each pose is performed.** | <https://ifbb.com/wp-content/uploads/2025/07/Mens-Bodybuilding-Rules-2026-1.pdf> |
| IFBB Pro League Pro Competition Rules | The Pro League (US) rulebook. Procedural only - lists poses, never describes them. | <https://www.ifbbpro.com/rules/> |
| IFBB Pro League, NPC Worldwide Rules | NPC Worldwide amateur rules hosted by the Pro League. | <https://www.ifbbpro.com/npc-worldwide/rules/> |
| NPC Official Bodybuilding Rules | The NPC amateur ruleset. Contains the only published judging-criteria sentence in the US pipeline. Last modified 2026-02-15. | <https://npcnewsonline.com/official-bodybuilding-rules/> |
| NPC IFBB Pro League Qualifier Rules | **Superseded** (last modified 2019-11-07). Retained here only as evidence of variance. | <https://npcnewsonline.com/ifbb-pro-league-rules/> |
| IFBB Federation Rules, Men's Physique 2024 | Contains the only official IFBB quarter-turn description. Different division. | <https://ifbb.com/wp-content/uploads/2025/04/Mens-Physique-2024.pdf> |
| IFBB Federation Rules, Men's Classic Physique 2024 | Useful contrast: same pose descriptions, different mandatory list, explicit Most Muscular prohibition. | <https://ifbb.com/wp-content/uploads/2024/02/Mens-Classic-Physique-2024.pdf> |
| NABBA USA Rules and Regulations | A divergent federation ruleset. Affiliate-published. | <https://nabbausa.wordpress.com/rules-and-regulations/> |
| NPC promoter "Relaxed" definition | The only bodybuilding-specific quarter-turn stance definition found. Promoter-level, identical across three promoters. | <https://www.timgardnerproductions.com/rules> |
| WNBF Australia bodybuilding poses | The most complete quarter-turn description found, and it contradicts the NPC one. Affiliate-published. | <https://www.wnbfaustralia.com/poses/bodybuilding> |
| Google MediaPipe Pose Landmarker | The 33-landmark model whose output the checkpoints in section 4 are written against. | <https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker> |

Index of the IFBB rulebook file directory, used to confirm no newer Men's Bodybuilding edition
exists: <https://ifbb.com/rules/>

---

## 1. Official names and federation variance

### 1.1 IFBB Pro League - eight poses [VERIFIED]

From <https://www.ifbbpro.com/rules/>, Men's Open Bodybuilding, Judging, rule 1, verbatim:

> Each competitor is called onstage individually in numerical order and has up to a maximum of
> 60 seconds to perform the following eight mandatory poses in the order shown:
> Front double biceps / Front lat spread / Side chest / Back double biceps / Back lat spread /
> Side triceps / Abdominals and thighs / Most muscular

Rules 3 and 4 then add, verbatim:

> The head judge then directs groups of competitors in numerical order through the quarter
> turns and mandatory poses. The size of the groups is at the discretion of the head judge.
>
> The head judge then directs selected competitors through the callouts, where the selected
> competitors are compared against each other in the quarter turns and mandatory poses.

The identical eight-pose list and order applies to Men's 212 Bodybuilding on the same page.

**The Pro League rulebook contains no description of any pose and no definition of a quarter
turn.** It is a procedural document. This was verified by reading the full page text, not by
skimming. Confirmed negatives across the whole page: `relaxed` 0 hits, `criteria` 0 hits,
`symmetry` 0 hits, `crab` 0 hits. There is no judging-criteria page anywhere on ifbbpro.com
(verified by enumerating the site's 32 pages via `page-sitemap.xml`).

### 1.1b NPC - the same eight, plus the only published criteria sentence [VERIFIED]

From <https://npcnewsonline.com/official-bodybuilding-rules/> (last modified 2026-02-15),
Contest Format (Judging), verbatim:

> Each competitor shall have a maximum of 60 seconds to complete the mandatory poses.
>
> The mandatory poses are:
> Front Double Biceps / Front Lat Spread / Side Chest / Back Double Biceps / Back Lat Spread /
> Side Triceps / Abdominals and Thighs / Most Muscular
>
> The head judge shall call the competitors, in small groups and in numerical order, to center
> stage to perform the quarter turns and mandatory poses.
>
> **Judges shall score competitors according to the "total package", which is a balance of
> size, symmetry, and muscularity.**

That bolded sentence is **the entire published judging criteria of the NPC / IFBB Pro League
pipeline**. It also appears verbatim on <https://www.ifbbpro.com/npc-worldwide/rules/>, whose
Bodybuilding section otherwise duplicates the NPC page. Nothing more detailed is published.

Two NPC rules bear directly on the poses:

> Competitors must not alter the fit of the posing suit by hiking it up in the back, or by
> pulling up the sides during Front and Rear Lat Spreads.

> "Moon pose" (any competitor performing this pose will be disqualified)

Note NPC's own name for the pose in that first rule - "Rear Lat Spread", not "Back Lat Spread"
- inside the same document that lists it as "Back Lat Spread". Minor, but worth knowing that
even a single federation is not internally consistent on naming.

**Most Muscular is unambiguously mandatory, not optional and not judge's choice**, in both the
Pro League and NPC lists. Neither publishes any rule about which variant is permitted:
`crab`, `hands on hips` and `hands clasped` return zero hits across all four US rules pages.

### 1.1c Variance inside the NPC's own site [VERIFIED]

<https://npcnewsonline.com/ifbb-pro-league-rules/> ("IFBB Pro League Qualifier Rules", last
modified 2019-11-07, headed "*THESE RULES ARE SUBJECT TO CHANGE") lists **seven** mandatory
poses and omits Most Muscular entirely. Other staleness markers on the page ("Posing music must
be on a CD or USB stick"; number worn on the left side only) and its dead PDF links
(`ProQualifierRules_MBB.pdf` 404s) confirm it is superseded rather than a live alternative.

Recorded because it is a live page a user could reach, and because it shows the eight-pose list
is a relatively recent settlement even within the US pipeline. Follow the 2026 page, not this.

### 1.2 International IFBB - seven poses, no Most Muscular [VERIFIED]

From the IFBB Federation Rules, Section 2: Men's Bodybuilding, 2026 Edition, Article 8.1
point 5, verbatim:

> In Round 1 individual comparisons, formulated by the IFBB Chief Judge, competitors are
> directed to perform the following seven Mandatory Poses:
> a. Front double biceps / b. Front lat spread / c. Side chest / d. Back double biceps /
> e. Back lat spread / f. Side triceps / g. Abdominals and thighs

Appendix 1 of that document is titled "DETAILED DESCRIPTION OF THE SEVEN MANDATORY POSES".
Article 12.1 point 2 has the finalists perform "the 7 Mandatory Poses" twice.

**Most Muscular does not appear in the international IFBB Men's Bodybuilding rulebook at
all.** I confirmed this by searching the extracted full text of the PDF: the strings
`most muscular`, `quarter` and `relaxed` return zero matches outside the header block.

The international IFBB also uses a **reduced four-pose set** for the elimination round and for
the initial grouping of Round 1 (Articles 5.2 point 3 and 8.1 point 2), verbatim:

> a. Front double biceps; b. Side chest; c. Back double biceps; d. Abdominals and thighs.

That four-pose subset is a genuinely useful artefact for the app: it is the federation's own
answer to "if you only have time for four, which four", and is a natural preset routine.

For contrast, the same federation's Classic Physique rules mandate a *different* seven and
explicitly exclude Most Muscular
(<https://ifbb.com/wp-content/uploads/2024/02/Mens-Classic-Physique-2024.pdf>, Appendix 1):
Front Double Biceps, Side Chest, Back Double Biceps, Side Triceps, **Vacuum Pose**,
Abdominals and Thighs, and "Classic Pose of Athlete's choice ... but not the 'Most Muscular'
one".

### 1.3 NABBA - eight mandatories, but starting with abdominals [VERIFIED, affiliate sources]

NABBA USA (<https://nabbausa.wordpress.com/rules-and-regulations/>) publishes **eight mandatory
poses plus seven optional**, in an order that begins with abdominals and thighs rather than
front double biceps:

1. Abdominal and thighs - hands behind head
2. Front lat spread with thighs flexed (heels together, toes at 45 degrees)
3. Front double biceps
4. Side chest (lifted ribcage) - favorite side
5. Side triceps - favorite side (leg flexed, calf spiked)
6. Back lat spread with one calf spiked
7. Back double biceps
8. Most muscular (Men Only) - favorite

Optional: double calf raise, hands on hips most muscular, thigh flex, hands behind back most
muscular, serratus/intercostal twisted crunch, hamstring flex, overhead victory.

Note the document is internally inconsistent: its prose says the head judge calls "each of the
thirteen mandatory poses in order" while the published list is 8 mandatory and 7 optional.

NABBA UK, South Africa and Northern Ireland publish the **same eight in the same order** but
invert the round structure - individual routine at Round 2, comparisons at Round 3, the reverse
of NABBA USA (<https://nabbaofficial.com/products/men-juniors>,
<http://www.nabbasouthafrica.co.za/mens_bodybuilding.html>).

Two things worth extracting even though we will not follow NABBA. First, "most muscular" is
explicitly an *umbrella* here, covering at least three distinct poses (mandatory 8 plus
optionals 10 and 12), which is why no federation can describe it in one paragraph. Second,
Round 1 is a quarter-turn round from a "semi-relaxed stance" - one of the few federation-level
acknowledgements that the bodybuilding relaxed round has a defined stance at all, though NABBA
never specifies it anatomically.

Caveat: these are national affiliate sites, not a NABBA International rulebook PDF. Indicative
of NABBA practice, not authoritative NABBA text.

### 1.3b The wider federation landscape [VERIFIED]

Eleven federations checked. The disagreement is broader than IFBB versus NPC.

| Federation | Quarter turns in men's BB? | Mandatories | Most Muscular? | Order signature |
|---|---|---|---|---|
| IFBB international (2026) | **No** | 7 | **No** | FDB, FLS, SC, BDB, BLS, ST, Abs |
| IFBB Pro League | Yes (undefined) | 8 | Yes | FDB, FLS, SC, BDB, BLS, ST, Abs, MM |
| NPC | Yes (undefined) | 8 | Yes | identical to Pro League |
| NABBA USA | Yes, Round 1 | 8 (+7 optional) | Yes | **Abs first**, MM last |
| NABBA UK/SA/NI | Yes, Round 1 | 8 | Yes | Abs first, MM last; routine before comparisons |
| WNBF Australia | Yes, "Round 1 Symmetry" | 9 | Yes, **two** (hands-on-hips and crab) | FDB, FLS, SC, ST, RDB, RLS, Abs, MM, MM |
| WNBF Germany | Yes | 8 | Yes ("Hands on Hips or crab") | **alternating** FDB, RDB, FLS, RLS, SC, ST, Abs, MM |
| NANBF | Yes | 11 | Yes (crab) | **both sides** of chest and triceps; adds Single Quadriceps |
| OCB | Yes | 11, "not necessarily in this order" | Yes, two | both sides |
| ICN | Yes | 8 | Yes, "of your choosing" | FDB, FLS, SC, ST, RDB, RLS, Abs, MM |
| PCA | not found - domains parked or 404 | - | - | - |

Sources: <https://www.wnbfaustralia.com/divisions/bodybuilding>,
<https://wnbf-germany.de/media/34/download/Rules%20Bodybuilding.pdf?v=1>,
<https://nanbf.net/nansite/mens-bodybuilding/>, <https://ocbonline.com/mens-bodybuilding/>,
<https://posingcoach.com.au/wp-content/uploads/2024/07/ICN-Handbook-2020.pdf> (ICN handbook
hosted on an affiliated coach's site, not an ICN domain).

Three observations that matter for the app:

1. **Pose *order* is the least stable thing in the sport.** Four distinct orderings appear
   above, including WNBF Germany's front/rear alternation, which is a deliberately different
   design (it minimises turning). The app should treat pose order as **configuration, not a
   constant** - which map decision 17's "preset routines plus custom" already anticipates.
2. **Several federations mandate both sides** of side chest and side triceps (NANBF, OCB).
   That is a strong independent argument for the side-pinning recommendation in section 5.2:
   the sport itself treats left and right as separate items to be judged.
3. **Most Muscular is a set, not a pose.** WNBF Australia and OCB mandate two of them
   separately. This reinforces option C in section 4.8.

### 1.4 The quarter-turn gap [VERIFIED as a negative finding]

- IFBB Pro League: references "the quarter turns" four times for Men's Open, defines them zero
  times.
- NPC: references them twice, defines them zero times.
- Neither the Pro League nor NPC uses the term **"relaxed round"** at all - zero occurrences
  across every US rules page checked. The relaxed-round framing in issue #4 is real-world
  bodybuilding vocabulary, but it is not federation vocabulary in this pipeline. The app's copy
  should say "quarter turns", which every federation does use.
- International IFBB Men's Bodybuilding 2026: the word "quarter" does not occur.
- International IFBB Men's Physique 2024: **does** define them, in Appendix 1. Verbatim,
  Front position:

  > Erect, tense stance, head and eyes facing the same direction as the body, one hand resting
  > on the hip, with four fingers at the front of the body, and one leg slightly moved to the
  > side. Second hand hanging down along the body, slightly out of to the side, elbow slightly
  > bent, with open palm and straight, aesthetically configured fingers. Knees unbent,
  > abdominal and latissimus dorsi muscles slightly contracted, head up.

  and Quarter Turn Right:

  > Competitors will perform the first quarter turn to the right. They will stand left side to
  > the judges, with upper body slightly turned toward the judges and face looking at the
  > judges. Left hand resting on the left hip, right arm hold down and slightly to the front
  > from the centerline of the body, elbow slightly bent, with open palm and straight,
  > aesthetically configured fingers. Left leg (nearest the judges) slightly bent in the knee,
  > resting flat on the floor. Right leg (farthest to the judges) bent in the knee, with foot
  > moved back and resting on the toes.

  The sequence is Front, Quarter Turn Right, Quarter Turn Back, Quarter Turn Right, Quarter
  Turn Front (Article 5, points 3 to 5).

**Do not ship the Men's Physique stance as a bodybuilding quarter turn.** The hand-on-hip,
"aesthetically configured fingers" presentation is a Physique convention. A bodybuilder in a
relaxed round stands with arms hanging slightly away from the body and lats flared, not with a
hand on the hip.

### 1.4b Where a bodybuilding relaxed-stance definition *does* exist [VERIFIED, promoter-level]

The search for a rulebook definition failed across IFBB international, IFBB Pro League, NPC,
NABBA, WNBF world, NANBF, OCB and ICN. But it turned up something nearly as good: a definition
that appears **word-for-word identical across three independent NPC / IFBB Pro League
promoters**, which strongly suggests a shared NPC judging handout that is simply not published
on npcnewsonline.com.

> **Relaxed**
> Keep your feet flat
> Keep your heels together
> Hold your arms at your side
> No twisting
> Your head must be facing the same direction as your feet

Appearing at <https://www.timgardnerproductions.com/rules>,
<https://www.musclesportproductions.com/rules-bodybuilding>, and
<https://www.2bpevents.com/division-rules/>, the last of which points readers back to the
official NPC rules page. A fourth promoter expands it into prose and names the round:

> **Symmetry Round:** ... You should perform quarter turns with heels touching, arms at your
> side and your head facing in the direction of your feet. You should be in a "semi relaxed"
> pose, meaning you are not performing any mandatory poses, but you should not be totally
> relaxed either. Do not distort your body by twisting your torso or placing one arm further in
> front of you than the other.
> - <https://www.idahostatebodybuilding.com/mens-bodybuilding-competition-guidelines.html>

**Status: promoter-authored, federation-affiliated, not traceable to a federation-published
rulebook.** Label it that way in the app. It is nonetheless the best bodybuilding-specific
quarter-turn source found, it is fully positional, and it converges with what an IFBB pro says
independently (section 3.3).

The most complete definition of all comes from a WNBF affiliate
(<https://www.wnbfaustralia.com/poses/bodybuilding>), which specifies arms, lats, hands, feet
and gaze for all four turns - for example Front Relaxed: "Stand tall with feet slightly apart
and toes pointing outwards ... Position arms by the sides with lats flared, maintaining a
slight bend at the elbows. Keep hands closed in a fist."

**And these two contradict each other**, which is exactly the sort of thing that must not be
silently averaged:

| | NPC promoter "Relaxed" | WNBF Australia "Front Relaxed" |
|---|---|---|
| Feet | "Keep your heels together" | "feet slightly apart and toes pointing outwards" |
| Arms | "Hold your arms at your side", "No twisting" | "arms by the sides **with lats flared**", fists closed |
| Lat flare | not mentioned; "not performing any mandatory poses" | explicitly required |

**Resolution for the app:** we follow the IFBB Pro League / NPC ruleset (section 1.5), so
follow the NPC promoter wording, and mark the heels-together predicate as **contested** rather
than settled. Section 4.9 does this. WNBF Germany, incidentally, constrains the stance only
negatively - "Feet are never allowed to be placed further than shoulder width apart", "Arms are
never allowed to be exaggeratedly spread", "The line of vision has to be aligned with the foot
positioning" - which is compatible with both and is a useful loose bound.

### 1.5 Recommendation: follow the IFBB Pro League list, annotate with international IFBB text

Follow the **IFBB Pro League** eight-pose list and order:

> Front Double Biceps, Front Lat Spread, Side Chest, Back Double Biceps, Back Lat Spread,
> Side Triceps, Abdominals and Thighs, Most Muscular

Reasons, in order of weight:

1. **It matches map decision 9**, which already committed the app to all eight mandatories
   plus quarter turns. Following the international IFBB would silently drop Most Muscular and
   contradict an accepted decision.
2. **It is the ruleset the target user trains against.** Men's Open, Olympia and Arnold
   lineage, and the NPC amateur pipeline that feeds it, all run the Pro League eight.
   NPC Worldwide carries the identical list.
3. **It is the only list that includes quarter turns for bodybuilding**, which map decision 9
   also requires.

But **source the pose *descriptions* from the international IFBB 2026 rulebook**, because the
Pro League publishes none. This is a defensible hybrid and it must be stated as such in the
app's reference guide: the list is Pro League, the execution definitions are international
IFBB. Six of the eight poses are described word-for-word in the IFBB Appendix 1. Front Lat
Spread and Back Lat Spread are described there too. Only Most Muscular has no primary source
at all.

Recorded as a decision candidate, not a decision - it is Lucas's call whether the hybrid is
acceptable or whether the app should present the international IFBB seven as the canonical
set.

---

## 2. Judged criteria

### 2.0 The federation we are following publishes one sentence [VERIFIED]

Worth stating before the detail, because it sets expectations. The complete published judging
criteria of the IFBB Pro League / NPC pipeline - the ruleset section 1.5 recommends following -
is this:

> Judges shall score competitors according to the "total package", which is a balance of size,
> symmetry, and muscularity.

That is all of it (<https://npcnewsonline.com/official-bodybuilding-rules/>,
<https://www.ifbbpro.com/npc-worldwide/rules/>). The IFBB Pro League publishes no criteria text
at all under its own domain.

So the detailed criteria below come from the **international IFBB** rulebook, which is the only
body in this space publishing a real rubric. Same hybrid caveat as section 1.5: the list we
follow is Pro League, the substance we quote is international IFBB, and the app must say so.

### 2.1 General assessment procedure [VERIFIED]

IFBB Men's Bodybuilding 2026, Article 10.1, verbatim:

> When assessing a competitor's physique, a judge should follow a routine procedure which will
> allow a comprehensive assessment of the physique as a whole. During the comparisons of the
> mandatory poses, the judge should first look at the primary muscle group being displayed.
> The judge should then survey the whole physique, starting from the head, and looking at
> every part of the physique in a downward sequence, beginning with general impressions, and
> looking for muscular bulk, balanced development, muscular density and definition.
>
> The downward survey should take in the head, neck, shoulders, chest, all of the arm muscles,
> front of the trunk for pectorals, pec-delt tie-in, abdominals, waist, thighs, legs and calves
> and feet. The same procedure for back poses will also take in the upper and lower trapezius,
> teres and infraspinatus, erector spinae, the gluteus group, the leg biceps group at the back
> of the thighs and calves and feet.

Article 10.2:

> In assessing prejudging, overall shape and that of the various muscle groups is important.
> The judge should favour competitors with a harmonious, classical physique. The judge should
> look for good posture and athletic bearing, correct anatomical structure (including body
> framework, broad shoulders, high chest, correct spinal curves, limbs and trunk in good
> proportion, straight legs, not bandy or knock-kneed).

Article 7.1:

> the judges will be assessing the overall physique for the degree of proportion, symmetry,
> muscle size and quality (density, separation, definition) as well as skin tone.

**Read that list and notice what is on it.** Proportion, symmetry, size, density, separation,
definition, skin tone, muscular bulk. Not one of those is a landmark quantity. The *only*
judged criterion in the entire IFBB assessment text that a skeleton touches is "good posture"
and "correct spinal curves", and even those are marginal in 2D.

This is the strongest possible support for map decision 6 and decision 16: the app cannot
compute an absolute grade because the app cannot observe a single thing the judge actually
scores. What it can observe is whether the athlete put their body in the same *configuration*
they did last week. That is a real and useful thing, and it is a different thing.

### 2.2 Per-pose primary muscle group [VERIFIED]

From IFBB Appendix 1, what the judge looks at *first* in each pose. This is what the app's
reference guide should say the pose is *for*.

| Pose | Primary focus, per the rulebook |
|---|---|
| Front Double Biceps | Biceps: "full, peaked development ... whether or not there is a defined split between the anterior and posterior sections of the biceps", then forearms, deltoids, pectorals, pec-delt tie-ins, abdominals, thighs, calves |
| Front Lat Spread | "a good spread of the latissimus muscles, thereby creating a V-shaped torso" |
| Side Chest | "the pectoral muscles and the arch of the rib cage, the biceps, the leg biceps and the calves"; thigh and calf in profile |
| Back Double Biceps | Arms first, then "more muscle groups to look at than in all of the other poses": neck, deltoids, biceps, triceps, forearm, trapezius, teres, infraspinatus, erector spinae, external obliques, latissimus dorsi, gluteus, thigh biceps, calves |
| Back Lat Spread | "a good spread of the latissimus dorsi, but also for good muscle density" |
| Side Triceps | Triceps first, then thigh and calf in profile |
| Abdominals and Thighs | "the abdominal and thigh muscles" |
| Most Muscular | No primary source |

---

## 3. Execution cues

### 3.1 Rule-level execution text [VERIFIED]

These are the official descriptions, quoted from IFBB Men's Bodybuilding 2026, Appendix 1.
They are the *only* execution text with rule status found in this research, and they are what
the app's pose guide should quote.

**Front Double Biceps.**
> Standing face front to the judges, with one leg 40-50 cm forward and to the side, the
> competitor will raise both arms to shoulder level and bend them at the elbows. The hands
> should be clenched and turned down so as to cause a contraction of the biceps and forearm
> muscles.

**Front Lat Spread.**
> Standing face front to the judges, with the legs and feet in-line and up to 15 cm apart, the
> competitor will place the open hands, or clenched fists, against, or gripping, the lower
> waist or obliques and will expand the latissimus muscles. At the same time, the competitor
> should attempt to contract as many other frontal muscles as possible. It shall be strictly
> forbidden for the competitor to pull up on the posing trunks so as to show the top inside of
> the quadriceps.

**Side Chest.**
> The competitor may choose either side for this pose, in order to display the "better" arm.
> He will stand with his left or right side towards the judges and will bend the arm nearest
> the judges to a right-angle position, with the fist clenched and, with the other hand, will
> grasp the wrist. The leg nearest the judges will be bent at the knee and will rest on the
> toes. The competitor will then expand the chest and by upward pressure of the front bent arm
> and contract the biceps as much as possible. He will also contract the thigh muscles, in
> particular, the biceps femoris group, and by downward pressure on his toes, will display the
> contracted calf muscles.

**Back Double Biceps.**
> Standing with his back to the judges, the competitor will bend the arms and wrists as in the
> Front Double Biceps pose, and will place one foot back, resting on the toes. He will then
> contract the arm muscles as well as the muscles of the shoulders, upper and lower back,
> thigh and calf muscles.

**Back Lat Spread.**
> Standing with his back to the judges, the competitor will place his hands on his waist with
> his elbows kept wide, with the legs and feet in-line and up to 15 cm apart. He will then
> contract the latissimus dorsi as wide as possible. The competitor should make an effort to
> display the opposite calf to that which was displayed during the back double biceps pose so
> the judge may assess both calf muscles equally. It shall be strictly forbidden for the
> competitor to pull up on the posing trunks so as to show the gluteus maximus muscles.

**Side Triceps.**
> The competitor may choose either side for this pose so as to show the "better" arm. He will
> stand with his left or right side towards the judges and will place both arms behind his
> back, either linking his fingers or grasping the front arm by the wrist with his rear hand.
> The leg nearest the judges will be bent at the knee and the foot will rest flat on the floor.
> The leg farthest to the judges will be bent at the knee and the foot resting on the toes.
> The competitor will exert pressure against his front arm, thereby causing the triceps muscle
> to contract. He will also raise the chest and contract the abdominal muscles as well as the
> thigh and calf muscles.

**Abdominals and Thighs.**
> Standing face front to the judges, the competitor will place both arms behind the head and
> will place one leg forward. He will then contract the abdominal muscles by "crunching" the
> trunk slightly forward. At the same time, he will contract the thigh muscles of the front leg.

**Most Muscular.** No rule text exists. See section 4.8.

### 3.2 Quantities the rulebook actually specifies [VERIFIED]

These are the only numbers in the entire corpus, and they matter because they are the only
place a *shipped canonical reference* can claim rule backing rather than opinion:

| Quantity | Value | Pose |
|---|---|---|
| Forward-and-side stagger of the lead leg | 40-50 cm | Front Double Biceps |
| Maximum foot separation | up to 15 cm, feet in-line | Front Lat Spread, Back Lat Spread |
| Front arm elbow angle | "right-angle position" | Side Chest |
| Arm height | "to shoulder level" | Front Double Biceps (and Back Double Biceps by reference) |
| Elbow position | "kept wide" | Back Lat Spread |
| Near foot | "rest flat on the floor" | Side Triceps |
| Far foot | "resting on the toes" | Side Triceps |
| Near foot | "rest on the toes" | Side Chest |
| One foot | "back, resting on the toes" | Back Double Biceps |

### 3.3 Coaching cues [COACHING]

**Everything in this subsection is coaching guidance, not rule.** It is legitimate for the pose
guide and it must be visually distinguished from section 3.1 in the UI. Sources are named
inline. Where coaches contradict each other, that is recorded rather than smoothed over,
because a contradiction is a signal that the cue is athlete-dependent and should not be encoded
as a checkpoint.

Principal sources: Andre Adams (IFBB Pro League athlete, NASM Master Trainer,
<https://blog.nasm.org/how-to-nail-bodybuilding-poses>); Andreas Abelsson
(<https://www.strengthlog.com/bodybuilding-poses/>); Bradley Grunner MS RD, ANBF pro
(<https://breakingmuscle.com/bodybuilding-poses/>); Philip M. Ricardo Jr., PNBA pro
(<https://www.ironmanmagazine.com/everything-you-need-to-know-and-more-about-posing-from-an-pnba-pro/>);
Fitschen and Wilson, *Bodybuilding*, Human Kinetics
(<https://us.humankinetics.com/blogs/excerpt/back-or-rear-double-biceps-pose>); Israetel,
Feather and Guevarra, *Bodybuilding Anatomy*, Human Kinetics
(<https://us.humankinetics.com/blogs/excerpt/bodybuilding-posing-tips>); Greg Merritt
(<https://thebarbell.com/most-muscular-pose/>); Andrew Heffernan CSCS
(<https://barbend.com/how-to-lat-spread/>); Dr. Andrew Chappell, WNBF Pro World Champion and
former WNBF UK President
(<https://www.naturalbodybuildingcoach.com/articles/how-bodybuilding-judging-works-and-the-poses>).

#### Cross-cutting

- **Position first, contract last.** Set the limbs, then the core, then flare, then contract,
  working "muscle by muscle from the feet up" (Israetel/Feather/Guevarra). This is directly
  relevant to capture timing: the pose is not fully formed at the instant it is assumed, which
  supports map decision 17's capture at *hold midpoint* rather than hold start.
- **Shrug down, not up.** Shrugging up narrows the physique (Israetel et al.). Named as the
  number one error in both lat spreads by three independent sources.
- **Breathe shallow.** A deep inhale pushes the stomach out and reads as poor conditioning
  (Israetel et al.); exhale slowly after locking the pose (Abelsson).
- **Do not over-contract.** Minimal tension is enough; over-contracting causes cramping and
  breathing failure across a long callout (Israetel et al.).
- **Judges sit below stage level**, which is the stated reason for the slight backward torso
  tilt in the rear poses (Adams, Ricardo).

#### Per-pose highlights, and where coaches disagree

**Front Double Biceps.** Feet shoulder-width, toes turned out into a "V" (consensus); Grunner
specifies 45 degrees. **Supinate the wrists** to enhance the peak (Adams, Abelsson). Upper arms
slightly above horizontal with elbows aimed 10-20 degrees forward of the body (Grunner);
"push the elbows forward to pop the lats" (Adams). *Disagreement:* the midsection. Grunner
says draw the abdomen in and **avoid** aggressive ab flexion because it makes you look shorter
and narrower; Saini says suck the stomach in to elevate the ribcage; Abelsson says flex
naturally without crunching. No consensus - do not encode.

**Front Lat Spread.** The hand cue is the most concretely specified detail in the whole
literature and three sources phrase it near-identically: **pinch the sides of the waist between
thumb and index finger** (Heffernan, Saini), or hook the thumbs behind the waist and bring them
forward (Ricardo). Drive elbows forward and outward. **Protract the scapulae** - "separate the
shoulder blades" (Abelsson, Heffernan, Reid). *Disagreement:* Saini's lat-spread article says
pull the shoulder blades **back and down**, contradicting everyone including his own other
article. Treat protraction as consensus.

**Side Chest.** Turn 90 degrees on the stronger side. Legs jammed together, no daylight
(Adams, Abelsson). Far arm reaches across and grips the near wrist; near arm bent to about 90
degrees (Ricardo, Grunner) - **this matches the rulebook's "right-angle position" exactly**,
which is a rare case of coaching and rule converging on a measurable number.
*Disagreement resolved by rule:* Abelsson alone says front foot flat and back foot on toes,
against five sources saying the front heel is raised. **The IFBB rule settles it** - "The leg
nearest the judges will be bent at the knee and will rest on the toes." Follow the rule.
*Disagreement unresolved:* Grunner says do **not** flex the near hamstring, just press it
against the other leg; Abelsson says flex it. Invisible to landmarks either way.

**Back Double Biceps.** The most precisely quantified pose in the coaching literature:
Fitschen and Wilson give the rear foot placement as **10 to 15 inches (25-38 cm) behind the
other foot**, knees turned slightly outward. Compare the IFBB rule, which says only "one foot
back, resting on the toes" - the coaching number is a usable refinement of a rule that gives
none. Flex both hamstrings "as if trying to perform a leg curl" (Fitschen and Wilson). **Do not
pinch the shoulder blades together** - unanimous across six sources. Lean the torso back
slightly toward the seated judges. *Disagreement:* elbow direction - forward (Adams, Grunner,
Fitschen and Wilson, Reid) versus down and back "like a lat pulldown" (Saini, who then
contradicts himself in the next line). *Disagreement:* elbow height - above the shoulders
(Ricardo, BarBend) versus at or just above parallel to avoid trap dominance (Abelsson). The
IFBB rule says only "as in the Front Double Biceps pose", i.e. "to shoulder level". **This
matters for the checkpoint in 4.4** and is why the elbow-height predicate there is written as
at-or-above shoulder rather than strictly above.

**Back Lat Spread.** Adams gives the clearest sequence: "pull back like a row, then turn those
elbows out as you open up the lats." Step one leg back with the heel raised and that calf
spiked (Heffernan) - which is the coaching form of the rulebook's "display the opposite calf"
requirement. *Disagreement, and it changes spine geometry:* Heffernan, Grunner and Sheehan all
say round the chest slightly forward for the "cobra hood" look; Abelsson lists hunching forward
as a mistake and Adams, Ricardo and Saini all say lean back slightly. This is a genuine
unresolved split and it is a good reason **not** to put a torso-lean checkpoint on this pose.

**Side Triceps.** Near arm straight, pressed hard against the side, **triceps locked down with
full elbow extension** (Adams) - again converging with the rule's "arms behind his back ...
exert pressure against his front arm". Grip variants: interlocked fingers, wrist-to-wrist hook,
or hand on hip (Abelsson) - matching the rule's "either linking his fingers or grasping the
front arm by the wrist". Press hamstrings together, no daylight. Notable subtle cue nobody else
gives: **smashing the triceps too hard flattens the muscle instead of popping it** (Abelsson).
*Minor disagreement:* Saini says bend forward slightly to accentuate the obliques; Abelsson
lists crunching forward as a fault.

**Abdominals and Thighs.** The key cue, and it is a genuinely useful one because it is
counter-intuitive: **push the head back into the fists "as if you were on a decline sit-up"**
(Adams). Abelsson states the matching error: pulling the head down with the hands "makes the
entire pose look sloppy and breaks your posture." Elbows out at roughly 45 degrees (Adams);
forward just enough to flare the lats, not so wide it stretches the abs flat (Abelsson). Front
leg extended with the ankle extended and toe pointed (Grunner). A posing coach flags putting
the front leg **too far forward** as throwing the whole silhouette off. Crunch slowly and with
control on a sharp exhale. *Disagreement:* Grunner says round the entire back; Adams and
Abelsson both say avoid compression. Grunner is the outlier.

**Most Muscular.** Greg Merritt is the only source that systematically separates the variants
and says which physique each suits:
- *Crab:* one leg slightly forward for a stronger base, knees pointed out, **lean forward
  considerably**, fists balled with a few inches between them, traps/delts/pecs/arms maxed.
  Suits wide clavicles with heavy trap and delt mass. Adjust the lean based on whether
  shoulders or chest is the stronger point.
- *Hands on hips:* **stand upright, no forward lean**, knees slightly out, shoulders rolled
  slightly forward. Suits excellent conditioning or lighter bodyweights - it sells aesthetics
  over raw size.
- *Hands in front:* hands together at waist level, grabbing a wrist or pressing fists together,
  with isometric pull or push.

  *Disagreement:* forward lean. Adams says hip-hinge forward; Merritt says the lean belongs to
  the crab and explicitly not to the hands-on-hips variant; Abelsson and Reid both warn that too
  much lean makes you look smaller. Grunner wants the shoulders **down** while Abelsson wants
  traps lifted and shoulders rounded forward. This is exactly the picture you would expect for a
  pose with no rule behind it, and it is the strongest practical argument for option B or C in
  section 4.8.

**Quarter turns.** Adams, an IFBB pro, gives three flat rules: "**Keep your feet flat. Keep your
heels together.** Head must be facing the same direction as your feet." No excessive twisting.
An NPC guidelines summary (<https://www.idahostatebodybuilding.com/mens-bodybuilding-competition-guidelines.html>,
self-described as a summary and **not** the complete rules) adds the same and one more:

> Perform quarter turns with heels touching, arms at your side and your head facing in the
> direction of your feet. ... Do not distort your body by twisting your torso or placing one
> arm further in front of you than the other.

That last clause is the most useful sentence found in the entire coaching corpus, because it is
the only cue anywhere that describes a fault in **purely positional terms** - and it is
therefore directly checkable. See section 4.9. *Disagreement:* Sheehan says the head faces
forward throughout the turns, against Adams and the NPC summary. Sheehan is very likely wrong;
if the app encoded his version, quarter-turn head yaw would be wrong by 90 degrees. Flagged
because it is exactly the kind of error the "invented cues are worse than no cues" concern is
about.

---

## 4. Observable checkpoints

This is the section that matters for the reference-encoding ticket. Everything here is
**[INFERRED]** unless it quotes a rule; the derivation is mine, the rule text it derives from
is cited.

### 4.0 Conventions, and two honest caveats up front

Written against **MediaPipe Pose Landmarker**, 33 landmarks, normalized image coordinates
(<https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker>). Indices
used: 0 nose, 7/8 ears, 11/12 shoulders, 13/14 elbows, 15/16 wrists, 17-22 pinky/index/thumb,
23/24 hips, 25/26 knees, 27/28 ankles, 29/30 heels, 31/32 foot index. **y increases downward**,
so "above" means smaller y.

Two derived scalars do most of the work:

- **Torso scale `S` = |midpoint(11,12) - midpoint(23,24)|.** Used as the unit for every length
  predicate, which makes them invariant to subject-camera distance. Chosen over shoulder width
  because torso length foreshortens only under pitch, not under yaw, so it stays stable as the
  athlete turns. This directly answers the map's "cannot recover subject-camera distance"
  constraint: every predicate below is a ratio or an angle, never a pixel count.
- **Orientation ratio `r` = |x(11) - x(12)| / S.** Apparent shoulder width over torso length.
  Maximal front-on and back-on, minimal in profile. This is the app's yaw proxy.

**Caveat 1: `r` is not a clean rotation measurement.** It conflates yaw with individual build,
and it is corrupted by *scapular protraction* - rolling the shoulders forward in a most
muscular or a crab reduces apparent shoulder width with zero yaw. So `r` is trustworthy as a
**relative** signal compared against the same athlete's own reference for the same pose
(exactly what map decision 6 already commits to), and untrustworthy as an absolute claim like
"you are rotated 43 degrees". **The app must never print a rotation angle in degrees.** That
number cannot be recovered from 2D without camera intrinsics and subject depth. Where the
ticket asked for "torso rotated roughly 45 degrees from camera", the honest implementation is
"`r` within tolerance of your reference's `r`".

**Caveat 2: front/back discrimination rests on a model inference, not on geometry.** MediaPipe
labels landmarks anatomically (left shoulder is the subject's left). So for a front-facing
subject in a non-mirrored image the anatomical left shoulder appears on the image right, and
that sign flips when the subject turns around. That gives a facing predicate,
`sign(x(11) - x(12))`, but it is only as reliable as the model's own front/back call, which is
a known weak point for a turned-away subject. A second, more robust signal is the mean
visibility of the face landmarks 0-10, which collapses when the athlete faces away.
**Recommend the prototype ticket validate both empirically before either is trusted** - this is
the single highest-risk assumption in this document.

Notation: `L`/`R` are the subject's anatomical left and right. `ang(a,b,c)` is the interior
angle at `b`. "near"/"far" are relative to the camera in profile poses.

---

### 4.1 Front Double Biceps

Camera: front.

**Verifiable [INFERRED, from the rule text quoted in 3.1]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Facing the camera | `r` within tolerance of the front-on reference; face landmarks 0-10 high visibility | "Standing face front to the judges" |
| Head square | `abs(x(0) - x_midshoulder) < 0.15 * S` | "face front" |
| Elbows at or above shoulder height | `y(13) <= y(11)` and `y(14) <= y(12)` | "raise both arms to shoulder level" |
| Elbows outside shoulders | `abs(x(13) - x(11)) > 0` outward, both sides; elbow separation > shoulder separation | implied by arms raised and bent |
| Wrists above elbows | `y(15) < y(13)` and `y(16) < y(14)` | "bend them at the elbows" |
| Elbow flexion acute | `ang(11,13,15)` and `ang(12,14,16)` both in roughly 45-100 degrees | "bend them at the elbows" |
| Wrists inboard of elbows | `abs(x(15) - x_mid) < abs(x(13) - x_mid)`, both sides | hands drawn in over the head |
| Arms level with each other | `abs(y(13) - y(14)) < 0.10 * S` | bilateral, implied |
| Arms matched in flexion | `abs(ang(11,13,15) - ang(12,14,16)) < 15 degrees` | bilateral, implied |
| Stance wider than hips | `abs(x(27) - x(28)) > abs(x(23) - x(24))` | "one leg forward **and to the side**" |
| Fists closed | landmarks 17-22 clustered within `0.10 * S` of their wrist | "The hands should be clenched" - marginal, see below |

**Invisible**

- **The 40-50 cm forward stagger.** The rule's most specific number is a *depth* displacement
  and the camera is head-on to it. Essentially unobservable. Only the "to the side" component
  survives into 2D. This is worth stating plainly in the pose guide rather than pretending.
- Biceps peak, and "whether or not there is a defined split between the anterior and posterior
  sections of the biceps" - the literal first thing the judge looks at.
- Forearm, deltoid, pectoral development; pec-delt tie-in; abdominal definition; quad sweep;
  calf development; density; definition; overall balance.
- "turned down" wrist rotation. The pinky/index/thumb landmarks can weakly indicate a closed
  fist but cannot recover forearm pronation. Treat the fist check as advisory at best.

---

### 4.2 Front Lat Spread

Camera: front.

**Verifiable [INFERRED]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Feet close together | `abs(x(27) - x(28)) <= 0.30 * S`, cross-checked against `<= abs(x(23) - x(24))` | "up to 15 cm apart" |
| Feet in-line, both flat | `abs(y(27) - y(28)) < 0.05 * S`; both heels down, `y(29) >= y(31)` and `y(30) >= y(32)` | "legs and feet in-line" |
| Hands at the waist | `abs(y(15) - y(23)) < 0.15 * S`, same for `16`/`24` | "against, or gripping, the lower waist or obliques" |
| Hands on the body, not out from it | `abs(x(15) - x(23)) < 0.30 * S`, same for `16`/`24` | "against, or gripping" |
| Elbows flared wide | elbow separation `abs(x(13) - x(14))` > shoulder separation `abs(x(11) - x(12))` | "expand the latissimus muscles" (the arm frame that enables it) |
| Elbows below shoulder, above hip | `y(11) < y(13) < y(23)`, same on the other side | implied by hands at waist |
| Facing the camera | `r` near the front-on reference; face landmarks visible | "Standing face front to the judges" |

The feet-together / feet-flat pair is a strong discriminator: it is the geometric opposite of
Front Double Biceps' staggered stance, so the two front poses separate cleanly on the lower
body even though their upper bodies both face camera.

**Invisible - and this is the important part**

- **The lat spread itself.** Landmarks 11 and 12 sit at the shoulder joint centre. Flaring the
  latissimus dorsi changes the *silhouette* of the torso and moves the joint centres barely at
  all. The V-taper that the rulebook says the judge looks for first - "a good spread of the
  latissimus muscles, thereby creating a V-shaped torso" - produces almost no landmark signal.
  A landmark-only engine cannot tell a world-class lat spread from an athlete standing in the
  same arm position with no lats flared whatsoever.
- Consequence for the product: for this pose the app can honestly say "you are in the right
  frame" and must not say "your lat spread is better than last week". If a lat-width metric is
  ever wanted it needs silhouette segmentation, not landmarks - which is a different engine and
  outside the current scope.
- Also invisible: torso width, waist taper, serratus, frontal muscle contraction, conditioning.
- The rulebook's explicit prohibition ("strictly forbidden ... to pull up on the posing trunks")
  is unobservable and irrelevant to the app.

---

### 4.3 Side Chest

Camera: side. The athlete chooses which side.

**Verifiable [INFERRED]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Turned to profile | `r` substantially below the front-on value and within tolerance of the reference | "stand with his left or right side towards the judges" |
| Far shoulder occluded | visibility of the far shoulder landmark drops; far-shoulder x converges on near-shoulder x | same |
| Near arm at a right angle | `ang(near shoulder, near elbow, near wrist)` in 70-110 degrees | "bend the arm nearest the judges to a **right-angle position**" |
| Hands joined | `abs(p(15) - p(16)) < 0.20 * S` (Euclidean, both axes) | "with the other hand, will grasp the wrist" |
| Hands in front of the body | wrist x lies on the same side of the hip x as the nose x | distinguishes from Side Triceps |
| Hands at waist-to-mid-torso height | `y(23) > y_wrist > y_midtorso` | implied |
| Near knee flexed | `ang(near hip, near knee, near ankle) < 170 degrees` | "The leg nearest the judges will be bent at the knee" |
| Near heel raised | `y(near heel) < y(near foot index)` | "will rest on the toes" |

The pair *(near elbow at 90 degrees, hands joined in front)* is the cleanest single signature
in the whole set. Side Chest and Side Triceps are the two poses most likely to be confused
from a silhouette, and they separate perfectly on near-elbow angle (90 vs near-straight) and
hand position (front vs behind).

**Invisible**

- Chest expansion and "the arch of the rib cage" - the rulebook's first-priority item.
- Pectoral development, biceps contraction, "upward pressure of the front bent arm" (an
  isometric with no positional consequence), leg biceps, calf contraction.
- Which side is the athlete's "better" arm and why.

**Product implication, flagged for the session model:** because the athlete chooses a side and
because a left-side and a right-side Side Chest are not comparable captures, the session must
**pin the chosen side per athlete and hold it constant across sessions**, or drift scoring on
this pose is meaningless. Same for Side Triceps. This is not currently in the map's decision
list and probably should be.

---

### 4.4 Back Double Biceps

Camera: back.

**Verifiable [INFERRED]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Facing away | mean visibility of landmarks 0-10 low; `sign(x(11) - x(12))` inverted relative to front poses | "Standing with his back to the judges" |
| Arm geometry as Front Double Biceps | all of 4.1's arm predicates: elbows at/above shoulders, wrists above elbows, elbow flexion acute, elbows wide, arms matched | "bend the arms and wrists as in the Front Double Biceps pose" |
| Exactly one heel raised | `y(29) < y(31)` XOR `y(30) < y(32)` | "will place one foot back, resting on the toes" |
| The raised-heel leg is trailing | that ankle's y is slightly above the planted ankle's y | "one foot back" |

**Not** verifiable, and worth recording because it is tempting: Fitschen and Wilson's
**[COACHING]** figure of 10-15 inches (25-38 cm) for how far the rear foot goes back. Like the
Front Double Biceps 40-50 cm stagger, this is a displacement along the **depth** axis with the
camera square to it. The trailing ankle appears marginally higher in frame through perspective,
but that shift also fires on camera pitch and on a simple weight shift, so it cannot carry a
tolerance band. Do not encode it as a checkpoint; it belongs in the pose guide as text.

The one-heel-raised check is what separates Back Double Biceps from Front Double Biceps on the
lower body, and it is the safety net for when the facing inference is unreliable.

**Invisible - almost everything the pose exists for**

The rulebook says this pose has "more muscle groups to look at than in all of the other poses"
and then lists them: neck, deltoids, biceps, triceps, forearm, trapezius, teres, infraspinatus,
erector spinae, external obliques, latissimus dorsi, gluteus, thigh biceps, calves. **Not one
of those fourteen is a landmark quantity.** The rulebook goes on: "This pose, probably more
than the others, will help the judge to determine the quality of the competitor's muscle
density, definition, and overall balance" - all three invisible.

The app can verify the athlete assumed the pose. It cannot evaluate the pose. For this one
above all, the reference guide should say so.

---

### 4.5 Back Lat Spread

Camera: back.

**Verifiable [INFERRED]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Facing away | as 4.4 | "Standing with his back to the judges" |
| Hands on the waist | `abs(y(15) - y(23)) < 0.15 * S` and `abs(x(15) - x(23)) < 0.30 * S`, mirrored | "place his hands on his waist" |
| Elbows kept wide | elbow separation > shoulder separation | "with his elbows kept wide" - verbatim rule, directly measurable |
| Feet close and in-line | `abs(x(27) - x(28)) <= abs(x(23) - x(24))`, `abs(y(27) - y(28)) < 0.05 * S` | "legs and feet in-line and up to 15 cm apart" |
| **Opposite calf to Back Double Biceps** | across the session: the side with the raised heel here differs from the side with the raised heel in the Back Double Biceps capture | "should make an effort to display the opposite calf to that which was displayed during the back double biceps pose" |

That last one is worth dwelling on. It is a **session-level checkpoint**, not a frame-level one:
it can only be evaluated by comparing two captures from the same session. The app is uniquely
placed to check it, because map decision 10 already made sessions structured and decision 17
already fixed one capture per pose. No live overlay could do this. It is a genuine, rule-backed,
fully-observable coaching cue that the app can deliver and a mirror cannot, and it costs almost
nothing to implement. Recommend it explicitly to the reference-encoding ticket.

Note the tension in the rule itself: "feet in-line and up to 15 cm apart" and "display the
opposite calf" pull in different directions, since displaying a calf usually means spiking it
onto the toes. Treat the feet-together predicate as the looser of the two.

**Invisible**

- The lat spread, for the same reason as 4.2 - and here it is the whole pose.
- Back thickness, erector spinae detail, muscle density, glute and hamstring conditioning.

---

### 4.6 Side Triceps

Camera: side. The athlete chooses which side.

**Verifiable [INFERRED]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Turned to profile | `r` below front-on and within tolerance of reference; far shoulder occluded | "stand with his left or right side towards the judges" |
| Near arm near-straight | `ang(near shoulder, near elbow, near wrist) > 150 degrees` | "exert pressure against his front arm" with the arm extended behind |
| Hands joined | `abs(p(15) - p(16)) < 0.20 * S` | "either linking his fingers or grasping the front arm by the wrist" |
| Hands **behind** the body | wrist x lies on the opposite side of hip x from nose x | "place both arms behind his back" |
| Near knee flexed | `ang(near hip, near knee, near ankle) < 170 degrees` | "The leg nearest the judges will be bent at the knee" |
| Near foot flat | `abs(y(near heel) - y(near foot index)) < 0.03 * S` | "the foot will rest flat on the floor" |
| Far foot on toes | `y(far heel) < y(far foot index)` | "the foot resting on the toes" |

The near-arm-straight plus hands-behind pair is the mirror image of Side Chest's
right-angle-plus-hands-in-front. Together they make the two side poses trivially separable,
which is a good result for the classifier.

Caveat on the far foot: in a true profile the far leg is frequently occluded by the near leg,
so the far-heel predicate will be low-confidence. Gate it on landmark visibility rather than
scoring it blind.

**Invisible**

- Triceps development, the horseshoe, the isometric "pressure against his front arm".
- Chest raise, abdominal contraction, thigh and calf development and separation.

---

### 4.7 Abdominals and Thighs

Camera: front.

**Verifiable [INFERRED]**

| Checkpoint | Predicate | Rule it encodes |
|---|---|---|
| Hands behind the head | `y(15) < y(7)` and `y(16) < y(8)` (wrists above ear level), and `abs(x(15) - x(7)) < 0.25 * S` mirrored | "place both arms behind the head" |
| Elbows wide, at head height | elbow separation > shoulder separation; `y(13) <= y(11)`, `y(14) <= y(12)` | implied by hands behind head |
| Facing the camera | `r` near front-on reference | "Standing face front to the judges" |
| Trunk shortened by the crunch | `S` reduced by a tolerance band vs the athlete's standing-neutral `S` | "'crunching' the trunk slightly forward" - weak, see below |
| Front knee extended | `ang(hip, knee, ankle)` near straight on the lead leg | "contract the thigh muscles of the front leg" (positional part only) |

Hands-above-ear-level is the most distinctive single predicate in the entire eight: no other
mandatory pose puts the wrists above the head. Pose identification for this one is close to
trivial.

**Invisible**

- **Abdominal definition, separation and "control"** - the pose's entire purpose.
- **The crunch depth.** Forward trunk flexion is motion along the depth axis and the camera is
  head-on to it. The `S` shortening predicate captures a little of it, but it also fires on a
  simple forward lean and on any pitch of the camera, so it is low-confidence. Do not present
  it as a crunch measurement.
- Serratus, intercostals, obliques, thigh separation, striations, quad sweep, conditioning.

---

### 4.8 Most Muscular

Camera: front.

**There is no primary source. Nothing in this subsection is rule-backed.** The IFBB Pro League
and the NPC both mandate the pose and neither describes it; the international IFBB omits it
entirely; NABBA treats it as three separate poses (crab, hands on hips, hands behind back);
IFBB Classic Physique explicitly forbids it.

Verified negative: searching all four US rules pages (`ifbbpro.com/rules/`,
`ifbbpro.com/npc-worldwide/rules/`, `npcnewsonline.com/official-bodybuilding-rules/`,
`npcnewsonline.com/ifbb-pro-league-rules/`) for `crab`, `hands on hips`, `hands clasped` and
`variant` returns **zero hits in all four**. Variant choice is unregulated. Any app copy
asserting that a particular variant is the Most Muscular would be inventing a rule.

This has a hard consequence: **the shipped canonical reference for Most Muscular cannot be
sourced from a rulebook.** That is an architectural choice about what the app ships, so per
standing preference it goes back to Lucas rather than being settled here. Concrete options:

- **A. Ship the crab variant as the canonical reference, labelled as one variant among several.**
  Pro: the app ships a complete set of eight, matching decision 9 and the Pro League list.
  Con: the app asserts a specific execution with no rule behind it, which is exactly the
  "invented cues are worse than no cues" failure this ticket exists to avoid. Mitigated if the
  guide names it as a variant rather than as the pose.
- **B. Ship no canonical reference for Most Muscular; make it user-reference-only.** The pose
  is still in the routine and still timed and captured, but cold-start scoring is unavailable
  until the user promotes their own gold rep. Pro: honest, and the rest of decision 12 is
  untouched. Con: one pose behaves differently from the other seven, which needs UI.
- **C. Let the user pick their variant at first run** (crab / hands on hips / hands behind
  back), and ship a canonical reference per variant. Pro: matches how the pose is actually
  competed; the variant is pinned so drift scoring stays valid. Con: three references to build
  instead of one, and the references are still coaching-derived, not rule-derived.

My reading: **B is the most defensible and C is the most useful.** A is the one to avoid,
because it hides an unsourced assertion inside something the app presents as canonical.

**If a variant is shipped, these are the checkpoints [INFERRED from coaching descriptions, not
rule]:**

*Crab / hands clasped in front:* hands joined near the midline
(`abs(p(15) - p(16)) < 0.25 * S`, `x_wrist` near `x_midhip`); wrists between chest and waist
height; elbows wide and forward, elbow separation > shoulder separation; elbows below shoulder
level, `y(13) > y(11)`; trunk flexed, `S` reduced vs neutral; head forward and down, `y(0)`
close to `y_midshoulder`.

*Hands on hips:* wrists at hip landmarks, elbows wide, facing front.

**A collision worth flagging to the reference-encoding ticket:** the hands-on-hips Most
Muscular is, in landmark space, nearly identical to the Front Lat Spread. Both are front-on,
both put the wrists at the hips, both flare the elbows. What separates them for a judge is
shoulder protraction and trapezius contraction - soft-tissue changes with almost no landmark
signature. **A landmark-only classifier should not be expected to separate these two.** If the
app ever needs to auto-detect which pose it is looking at rather than trusting the routine
timer, that is a known-unresolvable pair. Since map decision 13 makes the timer drive capture,
the app knows which pose it asked for and this is survivable - but it must not be forgotten if
auto-detection is ever added.

**Invisible:** everything the pose is for. Trapezius, pectoral striations, deltoid separation,
overall density, "the most muscular" impression itself.

---

### 4.9 Quarter turns

Camera: fixed. The athlete rotates through four positions.

**These are the most reliably verifiable items in the entire set**, which is a pleasant
inversion of expectations. Quarter turns are about gross body orientation, and gross body
orientation is precisely what a skeleton encodes well. The poses whose judged content is soft
tissue are the ones the app is blind to; the quarter turns' judged content includes actual
body position.

**Verifiable [INFERRED]**

The four positions separate on a 2x2 of two independent signals:

| Position | `r` (orientation ratio) | Facing signal |
|---|---|---|
| Front | near maximum | face landmarks 0-10 highly visible |
| Quarter turn right (left side to judges) | near minimum | left-side landmarks nearer camera, higher visibility |
| Back | near maximum | face landmarks 0-10 poorly visible |
| Quarter turn right again (right side to judges) | near minimum | right-side landmarks nearer camera |

Additional per-position predicates. The four marked **[cue-backed]** encode named coaching
cues rather than my own derivation, which makes them the safest ones in this document to
surface as user-facing feedback:

| Checkpoint | Predicate | Origin |
|---|---|---|
| **Heels together** - *contested* | `abs(x(29) - x(30)) < 0.10 * S` | [cue-backed] Adams and three NPC promoters say heels touching; WNBF Australia says "feet slightly apart". See 1.4b. Ship it as a cue, not a scored checkpoint |
| **Feet flat** | `abs(y(29) - y(31)) < 0.03 * S` and `abs(y(30) - y(32)) < 0.03 * S` - neither heel raised | [cue-backed] Adams "keep your feet flat" |
| **Head faces the same direction as the feet** | nose-to-ear-midpoint offset agrees in sign and rough magnitude with the foot-index-to-heel offset | [cue-backed] Adams; NPC summary. Note Sheehan contradicts this - see 3.3 |
| **Arms even, neither one further forward** | in the front and back positions, `abs(x(15) - x(23))` and `abs(x(16) - x(24))` match within tolerance; in profile, both wrists at the same depth-axis x | [cue-backed] NPC summary "placing one arm further in front of you than the other" |
| Arms down at the sides | `y(15) > y(23)` and `y(16) > y(24)` - wrists below hip level | derived |
| Arms slightly away from the body | `abs(x(15) - x(23))` in roughly `0.15-0.40 * S` | derived |
| Elbows slightly bent, not locked | `ang(11,13,15)` in roughly 150-175 degrees | derived |
| Knees straight in the front position | `ang(23,25,27)` near straight | derived |
| No torso twist | shoulder-line and hip-line orientation agree: `abs(r_shoulders - r_hips)` small | [cue-backed] NPC summary "Do not distort your body by twisting your torso" |
| Turn is a full quarter, not a half | `r` at the side positions is at its per-athlete minimum, not intermediate | derived |
| Consistent turn direction | across the four captures, the facing signal advances in one rotational direction | derived, session-level |

The torso-twist check deserves a note: comparing shoulder-line orientation against hip-line
orientation is one of the few things a 2D skeleton does genuinely well, because it is a
*relative* measurement between two segments of the same body and so cancels out most of the
camera-distance and scale problems. It is the closest this app gets to measuring rotation
honestly, and it is worth preferring over any absolute `r` threshold wherever a cue can be
expressed as "these two lines should agree".

That last one is another **session-level checkpoint**, like the Back Lat Spread calf rule: it
can only be evaluated across the four captures of the quarter-turn sequence, and it catches a
real and common error (turning the wrong way, or over/under-rotating one turn).

**Invisible**

- **Lat flare in the relaxed round.** In bodybuilding the "relaxed" round is not relaxed - the
  athlete holds a flared, tensed presentation throughout. That flare is the same soft-tissue
  quantity the lat spreads depend on, and it is equally invisible.
- Posture quality beyond gross joint positions, "athletic bearing", skin tone, conditioning,
  the "total package".
- Muscle presentation of any kind: trap and delt fullness, hamstring and calf display, the
  glute and lower-back detail the rear turn exists to show.

**On the styling question.** There is still **no federation rule** defining the bodybuilding
quarter-turn stance (section 1.4). What section 3.3 turned up is the next best thing: an IFBB
pro and an NPC guidelines summary independently giving the same three positional requirements -
heels together, feet flat, head facing the same direction as the feet - plus the explicit fault
"do not distort your body by twisting your torso or placing one arm further in front of you
than the other". Those are cited, positional, and checkable, so the app can surface them
**attributed as coaching guidance**. What it must not do is present them as rule, and it must
not go beyond them into arm styling, hand shape or presentation, for which no citable standard
exists in bodybuilding.

---

### 4.10 Summary: what the camera can and cannot do

| Pose | Checkpoint strength | Judged quality observable? |
|---|---|---|
| Front Double Biceps | Strong - 11 predicates, several rule-quantified | No |
| Front Lat Spread | Frame only - 7 predicates, all about arm and foot placement | **No - the lat spread itself is invisible** |
| Side Chest | Strong - highly distinctive signature | No |
| Back Double Biceps | Strong - arm geometry plus heel discriminator | No - 14 named muscle groups, none visible |
| Back Lat Spread | Frame only, plus one excellent session-level checkpoint | **No - the lat spread itself is invisible** |
| Side Triceps | Strong - cleanly separable from Side Chest | No |
| Abdominals and Thighs | Strong for the upper body, weak for the crunch | No |
| Most Muscular | **None derivable from any primary source** | No |
| Quarter turns | **Strongest of all** - orientation is what skeletons do well, and 5 of the predicates are cue-backed rather than derived | Partially: orientation and stance yes, muscle presentation no |

A note on confidence. The checkpoints in this section come in three grades, and the app should
treat them differently:

1. **Rule-quantified** - the rule states a number or a named geometry. Side Chest's right angle,
   Back Lat Spread's "elbows kept wide", the 15 cm foot separation, the on-toes and flat-foot
   distinctions. Highest confidence; safe to score.
2. **Cue-backed** - no rule, but a named coach or federation summary states it in positional
   terms. The quarter-turn set in 4.9. Safe to surface as feedback, attributed.
3. **Derived** - my geometric reading of a prose rule. Most of section 4. Sound, but each one
   should earn its place against real captures in the metric prototype before it drives a score.

**The honest boundary, stated once, for the app to reuse verbatim:**

> PosePerfect measures where your joints are. It does not measure how your muscles look.
> It can tell you that your elbows dropped below shoulder height, that your feet drifted
> wider than last week, or that you under-rotated a quarter turn. It cannot tell you
> anything about conditioning, muscle separation, density, vascularity, lat width or
> abdominal control - the things a judge actually scores. Those are invisible to the
> landmarks this app is built on.

This is also the load-bearing argument for map decisions 6 and 16. The app is not a weak
approximation of a judge; it is a precise instrument for a different and complementary
question - *did you hit the same position you hit last time.*

---

## 5. Camera-facing direction and framing implications

### 5.1 Facing per pose [VERIFIED from the rule text]

| Pose | Facing | Rule phrase |
|---|---|---|
| Front Double Biceps | Front | "Standing face front to the judges" |
| Front Lat Spread | Front | "Standing face front to the judges" |
| Side Chest | Side, athlete's choice | "stand with his left or right side towards the judges" |
| Back Double Biceps | Back | "Standing with his back to the judges" |
| Back Lat Spread | Back | "Standing with his back to the judges" |
| Side Triceps | Side, athlete's choice | "stand with his left or right side towards the judges" |
| Abdominals and Thighs | Front | "Standing face front to the judges" |
| Most Muscular | Front | No rule; universal in practice |
| Quarter turns | All four in sequence | Front, right, back, right |

Four front, two back, two side.

### 5.2 Framing implications [INFERRED]

1. **One fixed camera, rotating subject.** This is how a stage works - the judges do not move,
   the competitor turns. The app should mirror it exactly. It means a single tripod position
   serves all eight poses plus the quarter turns, which is what makes map decision 8's
   constrained capture practical at all.

2. **The frame-fit gate needs a per-facing bounding box, not one box.** A subject in profile is
   much narrower in frame than the same subject front-on with elbows flared in a double biceps.
   A single width tolerance will either reject valid side poses or fail to catch badly framed
   front poses. Recommend the gate carry a per-pose expected aspect, derived from the reference.

3. **Back poses mean the athlete cannot see the screen.** This is independent confirmation of
   map decisions 13 (timer drives capture, not a shutter tap) and 18 (audio cues for pose names
   and timing beats). For a quarter of the routine, visual feedback is physically unavailable.

4. **The chosen side for Side Chest and Side Triceps must be pinned and persisted.** A left-side
   Side Chest and a right-side Side Chest are different captures. If the athlete switches sides
   between sessions the drift score is comparing two different things. Recommend the side becomes
   part of the session configuration and is surfaced in the guide overlay. **Not currently
   covered by any map decision.**

5. **Full body must be in frame, feet included.** Half the checkpoints in section 4 use the
   heel and foot-index landmarks (29-32) - the on-toes / flat-footed distinctions carry real
   rule weight. A framing that crops at the knee discards them. The frame-fit gate should
   require ankle and foot landmarks present with adequate visibility.

6. **Camera height matters more than it looks.** `S`, the torso scale that normalizes every
   predicate, foreshortens under camera pitch. A phone propped at chest height and a phone on
   the floor produce different `S` for the same pose, which shifts every ratio. The gate should
   constrain camera height, or the reference should record it.

---

## 6. Hold duration

### 6.1 What the rules actually say [VERIFIED]

**No federation document found states a per-pose hold time.** What exists:

| Quantity | Value | Source |
|---|---|---|
| All eight mandatory poses, individual presentation | "up to a maximum of 60 seconds" | IFBB Pro League Men's Open, Judging rule 1; identical in NPC and NPC Worldwide |
| Ten-second warning before the 60 s expires | "A warning will be given when 10 seconds remain" | NPC IFBB Pro League Qualifier Rules (superseded page, but a real practice detail) |
| Competitors need not use the full minute | "Competitors are not required to use the full 60 seconds" | same |
| Individual posing routine, Finals | "up to a maximum of three minutes" | IFBB Pro League Men's Open, Finals rule 5 |
| Individual posing routine, Finals | "a maximum of 60 seconds" | NPC, Contest Format (Finals) - **differs from the Pro League** |
| Posedown | "60-second posedown to music of the promoter's choice" | IFBB Pro League Men's Open, Finals rule 8 |
| Posedown | "30- to 60-second Posedown" | IFBB Men's Bodybuilding 2026, Article 12.1 point 3 |
| Per-pose hold in comparisons | **not specified anywhere** | all sources |
| Number of comparisons | "will be decided by the IFBB Chief Judge" | IFBB Men's Bodybuilding 2026, Article 8.1 point 3 |
| Comparison group size | "no less than three and no more than ten" | IFBB Men's Bodybuilding 2026, Article 8.1 point 3 |

The ten-second warning is a useful detail for the app even though its source page is stale: it
confirms that a *timed, audibly cued* pose sequence is how the sport itself runs, which supports
map decisions 13 and 18 rather than being an app invention.

The international IFBB rulebook states **no time limit at all** for the individual mandatory
pose presentation.

**This was checked across nine federations and the negative is firm.** Every numeric time in
every document found is for a *routine*, a *posedown*, or a *whole set of mandatories performed
solo* - never for holding a single pose in a comparison. The closest any federation comes is
deliberately non-numeric:

> giving the competitors a sufficient number of seconds to hold the pose for the judge's
> determination and ample time for the athletes to rest between each pose
> - NABBA USA, <https://nabbausa.wordpress.com/rules-and-regulations/>

> Competitors are urged to get into their poses as quickly as possible. Competitors doing
> lengthy transitions and wind-ups risk having the next pose called before they are in the pose.
> - OCB, <https://ocbonline.com/mens-bodybuilding/>

Other routine timings, for completeness: NABBA UK 45 s minimum; WNBF Australia 45 s or shorter;
WNBF Germany 30-60 s; NANBF 60 s.

**A warning about numbers that circulate online.** Search-engine summaries readily offer
figures like "hold each pose 30-60 seconds", "beginners 10 to 15 seconds", and "pro lineups can
hold a pose for 30+ seconds". When the underlying pages were fetched, **those sentences were not
present in the page text**. They appear to be summarizer confabulations. They are recorded here
only so that nobody re-finds them later and mistakes them for sourced. Do not use them.

The one verifiable coaching statement on posing endurance, from Dr. Andrew Chappell (WNBF Pro
World Champion, judge of 100+ events), is about stamina rather than per-pose hold: "Be sure you
can pose for at least 20 minutes straight without a break before you get to the stage"
(<https://www.naturalbodybuildingcoach.com/articles/how-bodybuilding-judging-works-and-the-poses>).
That is a useful data point for total session length, not for a hold timer.

### 6.2 The one defensible derivation [INFERRED]

The Pro League's 60 seconds for 8 poses is the only hard number tied to mandatory poses. It
gives **7.5 seconds per pose including transition**, which for a working default splits
naturally into roughly a **5 second hold with a 2-3 second transition**.

That is a ceiling, not a typical. It describes the *individual* presentation, where the athlete
moves briskly through all eight. In callouts, where the head judge holds a comparison while
nine judges survey a whole lineup head to toe, holds are longer. But no primary source
quantifies that, so the app should not claim one.

**Recommendation for default routine timings:** ground the default on the rule that exists.
Default to a 5 second hold plus 3 second transition, cite it as derived from the Pro League's
60-second / 8-pose allowance, and make hold duration user-configurable. Note that map decision
17 fixes *one capture per pose at hold midpoint* and deliberately does not make capture count
configurable - hold *duration* is a different knob and configuring it does not fragment the
history, since the capture is still a single frame at the midpoint.

Anything longer than 7.5 seconds per pose in a shipped default is a training choice, not a
rule-derived one, and should be labelled that way in the UI if offered.

One caveat worth carrying into the routine design: OCB's warning that "competitors doing lengthy
transitions and wind-ups risk having the next pose called before they are in the pose" means the
transition budget is not free time. A default that gives a generous transition is training the
athlete to be slow. If anything, a tight transition is the more faithful simulation, and
Chappell's 20-minute endurance benchmark suggests total session length matters more than
per-pose generosity.

---

## 7. Reference imagery and licensing

Relevant because a later ticket may want to derive landmark templates from images.

### 7.1 The federation figures are not usable [VERIFIED]

The IFBB Men's Bodybuilding 2026 rulebook contains "APPENDIX 2: PICTURES OF THE SEVEN MANDATORY
POSES" and Appendix 1 references "see Figure 1" through "see Figure 7". **These are the single
best reference images that exist** - they are the federation's own illustration of its own rule
text.

They are also **all rights reserved**. The PDF carries no licence grant, no Creative Commons
mark, and no permission statement. IFBB is a private federation and the images are competition
photography. Deriving landmark templates from them and shipping those templates is a derivative
use that we have no licence for. **Do not use them without written permission from IFBB
headquarters** (headquarters@ifbb.com, listed on the rulebook cover). Asking is cheap and may
well succeed for a non-commercial personal tool, but it must be asked.

Note that landmark *coordinates* extracted from a photograph are a thin, factual derivative and
the copyright position on them is genuinely unsettled. That is not a defence to rely on for
something the repo is public about (map decision 11). Treat the figures as off-limits pending
permission.

### 7.2 Openly licensed alternatives on Wikimedia Commons [VERIFIED]

Commons has **no category for bodybuilding poses** - I enumerated the subcategories of
`Category:Bodybuilding` and there is no pose-organised collection, and `incategory` searches for
pose terms return zero results. So there is no ready-made licensed reference set. Individual
usable files exist but coverage is sparse and unsystematic:

| File | Licence | URL |
|---|---|---|
| SRD Posing Bodybuilder.svg | **CC0** | <https://commons.wikimedia.org/wiki/File:SRD_Posing_Bodybuilder.svg> |
| Bodybuilder John Quinlan On Stage 1998.jpg | **Public domain** | <https://commons.wikimedia.org/wiki/File:Bodybuilder_John_Quinlan_On_Stage_1998.jpg> |
| Elite American bodybuilder posing in yellow shorts.png | CC BY-SA 4.0 | <https://commons.wikimedia.org/wiki/File:Elite_American_bodybuilder_posing_in_yellow_shorts.png> |
| Hitman hart on front double biceps pose..jpg | CC BY-SA 3.0 | <https://commons.wikimedia.org/wiki/File:Hitman_hart_on_front_double_biceps_pose..jpg> |
| African american bodybuilder tony pearson posing.jpg | CC BY-SA 3.0 | <https://commons.wikimedia.org/wiki/File:African_american_bodybuilder_tony_pearson_posing.jpg> |
| David Henry, bodybuilder (15 October 2005).jpg | CC BY-SA 3.0 | <https://commons.wikimedia.org/wiki/File:David_Henry,_bodybuilder_(15_October_2005).jpg> |
| Charalambos Sarakinis.jpg | CC BY-SA 3.0 | <https://commons.wikimedia.org/wiki/File:Charalambos_Sarakinis.jpg> |
| FBB fromt double bicep.jpg | CC BY-SA 2.0 | <https://commons.wikimedia.org/wiki/File:FBB_fromt_double_bicep.jpg> |

Licences confirmed via the Commons API `extmetadata` field, not by reading the file pages.

**Bulk sets, which are a better yield than individual files:**

| Commons category | Files | Licence | Photographer | Note |
|---|---|---|---|---|
| [Championship of the Kaliningrad area on bodybuilding-2019](https://commons.wikimedia.org/wiki/Category:Championship_of_the_Kaliningrad_area_on_bodybuilding-2019) | 46 | CC BY-SA 4.0 | A. Podgorchuk / "Klops" | The best coherent men's stage set on Commons |
| [2012 Hong Kong Bodybuilding Championships](https://commons.wikimedia.org/wiki/Category:2012_Hong_Kong_Bodybuilding_Championships) | 39 | **CC BY 2.0** (no share-alike) | istolethetv | Mixed divisions, several clear mandatories |
| [2006 NPC Junior National Championships](https://commons.wikimedia.org/wiki/Category:2006_NPC_Junior_National_Championships) | 107 | CC BY-SA 2.0 | petechons | Predominantly female competitors |
| US military bodybuilding competition photography (multiple DVIDS files) | ~10 | **Public domain** | US Army / DoD staff photographers | No attribution obligation at all |

The CC BY 2.0 Hong Kong set and the public-domain military images are the licensing-cleanest
photographic material available: BY 2.0 has no share-alike clause, and US federal works have no
copyright restriction.

**The share-alike problem.** CC BY-SA is copyleft. If landmark templates derived from a CC BY-SA
photograph count as a derivative work, the templates - and arguably anything they are embedded
in - inherit BY-SA. For a public repo (decision 11) that is probably tolerable, but it is a
licensing commitment that should be made deliberately, not stumbled into. The CC0 and public
domain files carry no such condition and are the safe subset.

**Coverage is the real blocker regardless of licence.** There is **no openly licensed,
systematic photo set of one male competitor hitting all eight mandatories**. The contest-gallery
categories above are candid stage photography: many frames, arbitrary poses, arbitrary camera
angles, arbitrary subjects. Every high-quality systematic reference that does exist - Muscular
Development, Muscle and Fitness, Generation Iron, NPC News Online contest galleries, and the
IFBB pro posing tutorial series - is all-rights-reserved editorial content.

There is a deeper problem than licensing, and it applies even to a perfectly licensed image.
Section 4 normalizes every predicate by torso scale `S` and reads angles off joint positions.
A photograph taken from an unknown camera height, at an unknown distance, of an athlete with
unknown proportions, gives landmark coordinates that bake in all three unknowns. A template
derived from it encodes *that photograph's camera setup and that athlete's build*, not the pose.
For the shipped canonical set that is the wrong artefact regardless of who owns the copyright.

### 7.3 Recommendation for the canonical reference set

Image-derived canonical references look worse the closer you get to them: the best images are
unlicensed, the licensed images are copyleft and do not cover the poses, and a template derived
from one photograph of one athlete encodes that athlete's proportions rather than the pose.
Two alternatives are worth putting in front of Lucas when the reference-encoding ticket opens:

- **Synthesise the references from the rule text.** Section 3.2 lists the quantities the
  rulebook actually specifies, and section 4 turns them into predicates. A canonical reference
  could be a *set of predicate tolerance bands* rather than a landmark template - which is
  arguably the more honest artefact anyway, since it encodes the rule rather than one person's
  interpretation of it, and it sidesteps copyright entirely.
- **Capture them.** Lucas poses, the app records, those become the shipped references, clearly
  labelled as a starting point to be replaced by the user's own gold rep. Zero licensing risk,
  and decision 12 already anticipates the user promoting their own reference.

Either way the licensing answer is: **do not build the shipped reference set from third-party
photographs**, and ask IFBB for permission if their figures are ever genuinely wanted.

---

## 8. Open questions handed onward

1. **Most Muscular canonical reference** - options A/B/C in section 4.8. Needs Lucas's call.
2. **Hybrid ruleset acceptance** - Pro League list plus international IFBB descriptions
   (section 1.5). Needs Lucas's call.
3. **Side selection for Side Chest and Side Triceps must be pinned per athlete** (section 5.2
   point 4). Not covered by any current map decision. Recommend a new decision.
4. **Front/back facing discrimination is the highest-risk assumption in this document**
   (section 4.0, caveat 2). Recommend the metric prototype validate it empirically before any
   scoring depends on it.
5. **Session-level checkpoints** - the Back Lat Spread opposite-calf rule (4.5) and quarter-turn
   rotation consistency (4.9) are cheap, rule-backed, and only possible because sessions are
   structured. Recommend they reach the reference-encoding ticket.
6. **Camera height constrains `S`** (section 5.2 point 6), which normalizes every predicate.
   Interacts with the frame-fit gate design.
7. **Pose order should be configuration, not a constant** (section 1.3b). Four distinct orders
   exist across federations. Map decision 17 already allows custom routines, so this may be free
   - but the *shipped presets* should be named after their federation rather than presented as
   "the" order. Recommend shipping at least the Pro League eight and the international IFBB
   four-pose elimination subset (section 1.2) as presets.

## 9. What could not be established

Recorded so nobody re-runs it. All of these were searched for and not found, rather than
skipped:

- **A per-pose hold duration.** Does not exist in any of nine federations' rules (section 6.1).
- **A federation rulebook definition of the bodybuilding quarter turn.** Does not exist; only
  promoter and affiliate documents have one (section 1.4b).
- **Any official description of Most Muscular.** Does not exist in any federation document found
  (section 4.8).
- **Any IFBB Pro League judging criteria.** There is no criteria page on ifbbpro.com; verified by
  enumerating all 32 pages in its sitemap. The NPC's one-sentence "total package" formula is the
  whole published rubric for this pipeline (section 2.0).
- **PCA rules.** pcauk.com is a parked domain for sale; pcaofficial.com/rules 404s;
  pcaofficial.co.uk does not connect.
- **The WNBF world "Full Criteria Document".** Linked from
  <https://worldnaturalbb.com/competition-category/bodybuilding/> but the href is absent from the
  served HTML.
- **Historical rulebook editions.** web.archive.org was unreachable from this environment, so it
  was not possible to check when the Pro League list settled at eight, beyond the evidence of the
  superseded 2019 NPC page in section 1.1c.
