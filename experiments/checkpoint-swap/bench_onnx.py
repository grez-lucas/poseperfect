"""PROTOTYPE - throwaway. ONNX Runtime cost of the two checkpoints, ticket #20.

The swap has to be priced on three axes, and accuracy is only one of them. This
file settles the other two:

  - on-disk size of the .onnx file, which is what lands in the IPA
  - single-image latency under ONNX Runtime's CPU execution provider, at
    several `intra_op_num_threads` settings

Three graphs are measured: the official `body7` bundle #18 and #19 actually
ran, the self-exported `body7`, and the self-exported `aic-coco`. The middle one
is the control - if the self-export changed the cost of `body7`, the cost of
`aic-coco` would say nothing about the checkpoint.

The bench function is #19's, imported from ../person-detector/bench_onnx.py
rather than copied, so warmups, iteration count and session options match.

CAVEAT, stated here because it is the most load-bearing limitation of this
file, and it is unchanged from #19: this is x86-64 Linux. It is NOT an iOS
measurement. Treat these as an ordering and an order of magnitude.

Run:  ../person-detector/.venv310/bin/python bench_onnx.py
"""

from __future__ import annotations

import importlib.util
import json
import os

import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
DETECTOR = os.path.join(os.path.dirname(HERE), "person-detector")
CACHE = os.path.expanduser("~/.cache/poseperfect-checkpoint-swap")
OFFICIAL_ONNX = os.path.expanduser(
    "~/.cache/rtmlib/hub/checkpoints/"
    "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.onnx")

_spec = importlib.util.spec_from_file_location(
    "pd_bench", os.path.join(DETECTOR, "bench_onnx.py"))
_pd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pd)
bench = _pd.bench


def main():
    targets = {
        "body7_official": OFFICIAL_ONNX,
        "body7_self": os.path.join(CACHE, "onnx", "body7", "end2end.onnx"),
        "aic_coco_self": os.path.join(CACHE, "onnx", "aic-coco", "end2end.onnx"),
    }

    report = {"note": "x86-64 Linux CPU, ONNX Runtime "
                      f"{ort.__version__}. NOT an iOS measurement.",
              "models": {}}
    for key, p in targets.items():
        if not os.path.exists(p):
            print("missing", p, "- skipped", flush=True)
            continue
        entry = {"path": p, "bytes": os.path.getsize(p),
                 "mib": round(os.path.getsize(p) / 1024 / 1024, 2),
                 "threads": {}}
        for th in (1, 2, 4):
            entry["threads"][str(th)] = bench(p, th)
        report["models"][key] = entry
        print(key, entry["mib"], "MiB",
              {t: entry["threads"][t]["median_ms"] for t in entry["threads"]},
              flush=True)

    out = os.path.join(HERE, "results", "onnx_cost.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
