#!/usr/bin/env python3
"""
Register trained models in Azure ML (optional).

The GitHub Actions workflow calls this script. In repos/forks without Azure ML
configured, this script should no-op successfully instead of failing fast.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-name", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--model-path", required=True)
    args = parser.parse_args()

    model_dir = Path(args.model_path)
    if not model_dir.exists():
        print(f"Model directory not found: {model_dir}. Skipping registration.")
        return 0

    # If Azure ML env isn't configured, skip gracefully.
    if not os.getenv("AZURE_SUBSCRIPTION_ID"):
        print("AZURE_SUBSCRIPTION_ID not set. Skipping Azure ML registration.")
        return 0

    try:
        from azure.ai.ml import MLClient  # type: ignore
        from azure.identity import DefaultAzureCredential  # type: ignore
    except Exception as e:
        print(f"Azure ML SDK not available ({e}). Skipping registration.")
        return 0

    # Best-effort: register each .pkl as a model asset.
    try:
        cred = DefaultAzureCredential()
        client = MLClient(
            cred,
            subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
            resource_group_name=args.resource_group,
            workspace_name=args.workspace_name,
        )
    except Exception as e:
        print(f"Could not create Azure ML client ({e}). Skipping registration.")
        return 0

    pkl_files = sorted(model_dir.glob("*.pkl"))
    if not pkl_files:
        print(f"No .pkl models found under {model_dir}. Skipping registration.")
        return 0

    registered = 0
    for p in pkl_files:
        name = p.stem.replace(" ", "_").lower()
        try:
            # Avoid importing the full Model entity to keep compatibility across SDK versions.
            model_kwargs = {"name": name, "path": str(p), "type": "custom_model"}
            model = client.models.create_or_update(model_kwargs)  # type: ignore[arg-type]
            print(f"Registered model: {name} (version: {getattr(model, 'version', 'unknown')})")
            registered += 1
        except Exception as e:
            print(f"Failed to register {p.name} ({e}). Continuing.")

    print(f"Azure ML registration complete. Registered: {registered}/{len(pkl_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

