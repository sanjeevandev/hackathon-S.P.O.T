# Held-out Evaluation & Benchmark Methodology

> **Superseded by `docs/AI_ARCHITECTURE_AND_EVALUATION.md`** (single source of
> truth). This file remains as a breadcrumb.

The canonical evaluation document is now **`docs/AI_ARCHITECTURE_AND_EVALUATION.md`**,
covering:

- current AI architecture and model inventory,
- confidence → grading → REVIEW_REQUIRED flow,
- datasets + held-out split + leakage check,
- the **committed** 15-image held-out set (`evaluation/v1_eval/`),
- measured old-vs-new benchmark, latency, model size,
- ONNX export verification,
- limitations, and exact reproduction commands.

Run the benchmark with:

```bash
.venv/bin/python scripts/evaluate_models.py \
    --images evaluation/v1_eval/images \
    --manifest evaluation/v1_eval/manifest.csv \
    --out evaluation/v1_eval/results.json
```

The script enforces checksum-verified labels, a leakage check against committed
split/pilot identifiers, and scores **both** models on the **same** images with
**no hard-coded results** and **no cherry-picking**.
