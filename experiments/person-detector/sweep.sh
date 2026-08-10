#!/usr/bin/env bash
# PROTOTYPE - throwaway. Runs the ticket #19 sweep as N concurrent shards and
# concatenates them into results/per_instance.csv.
#
# The sweep is embarrassingly parallel over instances and CPU-bound, so a
# single process leaves most of the box idle. Sharding costs one thing and it
# is recorded rather than hidden: det_latency_ms becomes contended wall clock
# and is not a clean timing. Cost claims come from bench_onnx.py, which runs
# alone.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${HERE}/.venv310/bin/python"
RES="${HERE}/results"
N="${1:-5}"
THREADS="${2:-4}"

mkdir -p "${RES}"
# Shard CSVs are NOT deleted: run_experiment.py resumes from them.
rm -f "${RES}"/run_meta.shard*.json

pids=()
for i in $(seq 0 $((N - 1))); do
  OMP_NUM_THREADS="${THREADS}" MKL_NUM_THREADS="${THREADS}" \
    "${PY}" "${HERE}/run_experiment.py" --shard "${i}" --nshards "${N}" \
    > "${RES}/shard${i}.log" 2>&1 &
  pids+=($!)
done
echo "launched ${N} shards: ${pids[*]}"
for p in "${pids[@]}"; do wait "${p}"; done

echo "==> concatenating"
"${PY}" - "${RES}" "${N}" <<'PY'
import csv, glob, json, os, sys
res, n = sys.argv[1], int(sys.argv[2])
rows, fields = [], None
for i in range(n):
    with open(os.path.join(res, f"per_instance.shard{i}.csv")) as f:
        r = csv.DictReader(f)
        fields = r.fieldnames
        rows.extend(list(r))
rows.sort(key=lambda x: (int(x["ann_id"]), x["detector"]))
with open(os.path.join(res, "per_instance.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

metas = [json.load(open(os.path.join(res, f"run_meta.shard{i}.json")))
         for i in range(n)]
meta = dict(metas[0])
meta["cohort_size"] = sum(m["cohort_size"] for m in metas)
meta["shards"] = n
meta["seconds"] = max(m["seconds"] for m in metas)
meta["detector_latency_ms_median"] = {
    "note": "contended wall clock under a sharded run, not a clean timing; "
            "see results/onnx_cost.json for cost claims"}
json.dump(meta, open(os.path.join(res, "run_meta.json"), "w"), indent=2)
print(f"{len(rows)} rows over {meta['cohort_size']} instances")
PY

rm -f "${RES}"/per_instance.shard*.csv "${RES}"/run_meta.shard*.json "${RES}"/shard*.log
