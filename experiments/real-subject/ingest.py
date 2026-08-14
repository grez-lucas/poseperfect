"""PROTOTYPE - throwaway. Wayfinder ticket #9: photographs in, shot log out.

Turns a directory of iPhone frames into a checkable mapping from file to
(block, pose, camera, condition, rep), plus a SHA256 manifest.

The manifest matters more than it looks. Ticket #9's photographs are of Lucas in
posing trunks and the repository is public by decision 11, so the images never
enter git - only derived numbers do. That is the same arrangement #18, #19 and
#20 have with COCO's 1 GB. The manifest is what keeps a published number
traceable to a file that was never published.

The proposed mapping is a PROPOSAL. It aligns EXIF capture order against
`shotplan.sequence()`, which is correct only if nothing was re-shot, and
something always is. Lucas confirms or corrects `results/shotlog.csv` before
anything is measured. Two independent signals are printed to make that cheap:
the camera read out of EXIF is cross-checked against the camera the plan
expects, and unusually long gaps between frames are flagged as likely block
boundaries.

    python ingest.py --photos ~/poseperfect-captures/2026-08-xx

Run:  ./run.sh
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os

from PIL import Image, ExifTags

import shotplan

EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}
EXTS = (".jpg", ".jpeg", ".heic", ".png")

# Long gap between consecutive frames => the athlete was walking back to the
# tripod, changing camera, or taking tape off. Used only to draw the operator's
# eye, never to decide anything.
GAP_HINT_S = 45.0


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def exif_of(path):
    """Capture time, lens and body, straight out of the file.

    Camera identity is a domain invariant (map constraint 5), so it is read from
    the file rather than trusted to the shot log. Apple writes the lens into
    LensModel as e.g. "iPhone 15 Pro front camera 2.69mm f/1.9", which is the
    only place front-versus-rear is recorded unambiguously.
    """
    out = {"exif_time": "", "lens": "", "body": "", "w": 0, "h": 0,
           "camera_exif": "unknown"}
    try:
        with Image.open(path) as im:
            out["w"], out["h"] = im.size
            ex = im.getexif()
            if ex:
                out["body"] = str(ex.get(EXIF_TAGS.get("Model"), "") or "")
                out["exif_time"] = str(ex.get(EXIF_TAGS.get("DateTime"), "") or "")
                ifd = ex.get_ifd(ExifTags.IFD.Exif) if hasattr(ExifTags, "IFD") else {}
                out["lens"] = str(ifd.get(EXIF_TAGS.get("LensModel"), "") or "")
                dto = ifd.get(EXIF_TAGS.get("DateTimeOriginal"), "")
                if dto:
                    out["exif_time"] = str(dto)
    except Exception as exc:                       # keep the ingest alive
        out["error"] = repr(exc)
    lens = out["lens"].lower()
    if "front" in lens:
        out["camera_exif"] = "front"
    elif "back" in lens or "rear" in lens:
        out["camera_exif"] = "rear"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photos", required=True)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "results"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    files = sorted(f for f in os.listdir(args.photos)
                   if f.lower().endswith(EXTS))
    if not files:
        raise SystemExit(f"no images in {args.photos}")

    rows = []
    for f in files:
        p = os.path.join(args.photos, f)
        rows.append(dict(file=f, sha256=sha256(p), bytes=os.path.getsize(p),
                         **exif_of(p)))

    # EXIF DateTimeOriginal has one-second resolution, so a burst can tie.
    # Falling back to filename keeps a burst in the order the camera wrote it,
    # which is the order the plan expects.
    rows.sort(key=lambda r: (r["exif_time"], r["file"]))

    plan = shotplan.sequence()
    if len(rows) != len(plan):
        print(f"!! {len(rows)} photographs against {len(plan)} planned frames. "
              f"The proposed mapping below is offset from the first extra or "
              f"missing frame onward - fix shotlog.csv by hand.")

    prev = None
    out_rows = []
    for i, r in enumerate(rows):
        p = plan[i] if i < len(plan) else {"block": "?", "pose": "?",
                                           "camera": "?", "condition": "?",
                                           "rep": 0}
        gap = ""
        if prev and r["exif_time"] and prev["exif_time"]:
            try:
                from datetime import datetime
                fmt = "%Y:%m:%d %H:%M:%S"
                gap = (datetime.strptime(r["exif_time"], fmt)
                       - datetime.strptime(prev["exif_time"], fmt)).total_seconds()
            except Exception:
                gap = ""
        mismatch = (p["camera"] != r["camera_exif"]
                    and r["camera_exif"] != "unknown"
                    and p["condition"] != "calibration")
        out_rows.append({
            "n": i + 1, "file": r["file"], "sha256": r["sha256"],
            "bytes": r["bytes"], "exif_time": r["exif_time"],
            "gap_s": gap, "lens": r["lens"], "body": r["body"],
            "w": r["w"], "h": r["h"],
            "camera_exif": r["camera_exif"],
            "block": p["block"], "pose": p["pose"], "camera": p["camera"],
            "condition": p["condition"], "rep": p["rep"],
            "facing": "", "subject_hint": "", "confirmed": "",
            "flag": ("CAMERA_MISMATCH" if mismatch else
                     ("LONG_GAP" if isinstance(gap, float) and gap > GAP_HINT_S
                      else "")),
        })
        prev = r

    path = os.path.join(args.out, "shotlog.csv")
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        wr.writeheader()
        wr.writerows(out_rows)

    flagged = [r for r in out_rows if r["flag"]]
    print(f"wrote {path}: {len(out_rows)} frames, {len(flagged)} flagged")
    for r in flagged:
        print(f"  {r['n']:4d} {r['file']:24s} {r['flag']:16s} "
              f"plan={r['camera']:5s} exif={r['camera_exif']}")
    print("\nNEXT: open shotlog.csv, fix any wrong row, and put 'y' in the "
          "`confirmed` column of every row you want measured.")
    print("Side Chest, Side Triceps and the left/right quarter turns also need "
          "`facing` set to L or R - map constraint 5 makes comparing across "
          "facing directions invalid, not merely noisy.")
    print("Block F needs `subject_hint`: how far across the frame YOU are, as a "
          "fraction from 0 at the left edge to 1 at the right. Your reflection "
          "wears the same tape on the same limbs, so nothing in the image can "
          "tell you apart from it - this is the one fact only you can supply, "
          "and it is four numbers.")


if __name__ == "__main__":
    main()
