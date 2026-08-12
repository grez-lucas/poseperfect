"""PROTOTYPE - throwaway. Concatenates a second sweep pass into results/.

Wayfinder ticket #20. `run.sh` sweeps all four arms in one pass and does not
need this. The committed results were produced in two passes - three arms, then
`coco_self` alone - because the first pass was already most of the way done
when the fourth checkpoint was discovered, and discarding it would have cost an
hour of CPU for nothing.

The merge is only legitimate if every arm saw the identical detector box for a
given instance. That is checked by `analyse.py`, which exits rather than merge
if the detector columns disagree - not asserted here.

Run:  ../person-detector/.venv310/bin/python merge_pass.py <other-results-dir>
"""

from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    extra = sys.argv[1]

    rows, fields = [], None
    for p in (os.path.join(RES, "per_instance.csv"),
              os.path.join(extra, "per_instance.csv")):
        with open(p, newline="") as f:
            r = csv.DictReader(f)
            fields = r.fieldnames
            rows.extend(list(r))
    rows.sort(key=lambda x: (int(x["ann_id"]), x["pose_model"], x["box_source"]))
    with open(os.path.join(RES, "per_instance.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    m = json.load(open(os.path.join(RES, "run_meta.json")))
    m2 = json.load(open(os.path.join(extra, "run_meta.json")))
    passes = m.get("passes", [{"arms": sorted(m["pose_arms"]),
                               "seconds": m.get("seconds")}])
    passes.append({"arms": sorted(m2["pose_arms"]), "seconds": m2.get("seconds")})
    m["pose_arms"].update(m2["pose_arms"])
    m["passes"] = passes
    m["merge_note"] = (
        "produced in more than one pass and concatenated; analyse.py verifies "
        "that every arm saw the identical detector box before reporting")
    json.dump(m, open(os.path.join(RES, "run_meta.json"), "w"), indent=2)
    print(f"{len(rows)} rows, {len(m['pose_arms'])} arms")


if __name__ == "__main__":
    main()
