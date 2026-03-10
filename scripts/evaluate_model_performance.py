#!/usr/bin/env python3
"""
Evaluate model metrics against configured thresholds.

Used by GitHub Actions workflow. If metrics are missing (e.g., no labels), it
doesn't fail the pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _get(d: dict, path: str):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-file", required=True)
    parser.add_argument("--threshold-file", required=True)
    args = parser.parse_args()

    metrics_path = Path(args.metrics_file)
    if not metrics_path.exists():
        print(f"Metrics file not found: {metrics_path}. Skipping gate.")
        return 0

    thresholds_path = Path(args.threshold_file)
    if not thresholds_path.exists():
        print(f"Threshold file not found: {thresholds_path}. Skipping gate.")
        return 0

    metrics = json.loads(metrics_path.read_text())
    thresholds = json.loads(thresholds_path.read_text())

    # If evaluation didn't run (no labels), don't fail.
    if not metrics:
        print("No metrics present. Skipping gate.")
        return 0

    failures = []
    for section_name, section_thresholds in thresholds.items():
        for metric_name, min_val in section_thresholds.items():
            if not metric_name.endswith("_min"):
                continue
            metric_key = metric_name[: -len("_min")]
            actual = _get(metrics, f"{section_name}.{metric_key}")
            if actual is None:
                continue
            try:
                actual_f = float(actual)
                min_f = float(min_val)
            except Exception:
                continue
            if actual_f < min_f:
                failures.append((section_name, metric_key, actual_f, min_f))

    if failures:
        print("Model performance gate failed:")
        for section, key, actual, minimum in failures:
            print(f"- {section}.{key}: {actual:.4f} < {minimum:.4f}")
        return 1

    print("Model performance gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

