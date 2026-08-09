"""PROTOTYPE - throwaway. ONNX Runtime cost of the candidate pair, ticket #19.

Reports, for the exported RTMDet-Ins graphs and for the RTMPose-m graph the app
already plans to ship:

  - on-disk size of the .onnx file, which is what lands in the IPA
  - single-image latency under ONNX Runtime's CPU execution provider, at
    several `intra_op_num_threads` settings

CAVEAT, stated here because it is the single most load-bearing limitation of
this file: this is x86-64 Linux. It is NOT an iOS measurement. A phone has
different cores, a different memory system and a different ORT build. Treat
these as an ordering and an order of magnitude, not as the device figure. The
writeup says the same thing in plainer words.

Run:  .venv310/bin/python bench_onnx.py
"""

from __future__ import annotations

import glob
import json
import os
import time

import numpy as np
import onnxruntime as ort

CACHE = os.path.expanduser("~/.cache/poseperfect-detector")
RTMPOSE_ONNX = os.path.expanduser(
    "~/.cache/rtmlib/hub/checkpoints/"
    "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.onnx")
WARMUP, ITERS = 3, 20


def bench(path, threads):
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])

    feeds = {}
    for i in sess.get_inputs():
        shape = [1 if not isinstance(s, int) else s for s in i.shape]
        feeds[i.name] = np.random.rand(*shape).astype(np.float32)

    for _ in range(WARMUP):
        sess.run(None, feeds)
    ts = []
    for _ in range(ITERS):
        t = time.perf_counter()
        sess.run(None, feeds)
        ts.append((time.perf_counter() - t) * 1000.0)
    return {
        "input_shapes": {i.name: list(i.shape) for i in sess.get_inputs()},
        "output_names": [o.name for o in sess.get_outputs()],
        "median_ms": round(float(np.median(ts)), 1),
        "p90_ms": round(float(np.percentile(ts, 90)), 1),
    }


def main():
    targets = sorted(glob.glob(os.path.join(CACHE, "onnx", "*", "*.onnx")))
    if os.path.exists(RTMPOSE_ONNX):
        targets.append(RTMPOSE_ONNX)

    report = {"note": "x86-64 Linux CPU, ONNX Runtime "
                      f"{ort.__version__}. NOT an iOS measurement.",
              "models": {}}
    for p in targets:
        entry = {"path": p, "bytes": os.path.getsize(p),
                 "mib": round(os.path.getsize(p) / 1024 / 1024, 2),
                 "threads": {}}
        for th in (1, 2, 4):
            entry["threads"][str(th)] = bench(p, th)
        report["models"][os.path.basename(p)] = entry
        print(json.dumps({os.path.basename(p): entry}, indent=2), flush=True)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "results", "onnx_cost.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
