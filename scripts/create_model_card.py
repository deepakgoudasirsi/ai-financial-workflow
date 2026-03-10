#!/usr/bin/env python3
"""
Create a simple model card markdown from training artifacts.

Used by GitHub Actions. Works even if some artifacts are missing.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-card-path", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = out_dir / "evaluation_metrics.json"
    diagnostics_path = out_dir / "model_diagnostics.json"
    stats_path = out_dir / "detection_statistics.json"

    def read_json(p: Path):
        try:
            if p.exists():
                return json.loads(p.read_text())
        except Exception:
            pass
        return None

    metrics = read_json(metrics_path)
    diagnostics = read_json(diagnostics_path)
    stats = read_json(stats_path)

    generated_at = datetime.now(timezone.utc).isoformat()

    lines = []
    lines.append("# Model Card")
    lines.append("")
    lines.append(f"- Generated at (UTC): {generated_at}")
    lines.append("")
    lines.append("## Overview")
    lines.append("This repository trains an AML / fraud transaction anomaly detection ensemble.")
    lines.append("")

    lines.append("## Artifacts")
    model_dir = out_dir / "models"
    if model_dir.exists():
        pkls = sorted(model_dir.glob("*.pkl"))
        if pkls:
            lines.append(f"- Models: {len(pkls)} pickle files under `output/models/`")
        else:
            lines.append("- Models: none found under `output/models/`")
    else:
        lines.append("- Models: `output/models/` not found")
    lines.append("")

    lines.append("## Metrics")
    if isinstance(metrics, dict) and metrics:
        combined = metrics.get("combined_system", {})
        auc = combined.get("auc")
        f1 = combined.get("f1_score") or combined.get("f1")
        lines.append(f"- Combined AUC: {auc}")
        lines.append(f"- Combined F1: {f1}")
    else:
        lines.append("- No evaluation metrics available (likely missing labels).")
    lines.append("")

    lines.append("## Diagnostics")
    if isinstance(diagnostics, dict) and diagnostics:
        lines.append("- Model diagnostics available in `output/model_diagnostics.json`.")
    else:
        lines.append("- No model diagnostics found.")
    lines.append("")

    lines.append("## Detection statistics")
    if isinstance(stats, dict) and stats:
        lines.append("- Detection statistics available in `output/detection_statistics.json`.")
    else:
        lines.append("- No detection statistics found.")
    lines.append("")

    card_path = Path(args.model_card_path)
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote model card to {card_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

