#!/usr/bin/env python3
"""
Download training data from Azure Blob Storage if configured.

This script is used by the GitHub Actions training workflow. To keep the pipeline
usable in forks/local runs (without Azure secrets), it gracefully falls back to
creating/downloading a local dataset via `scripts/download_dataset.py`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _fallback(local_path: str) -> int:
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

    # Use the repo's existing dataset helper (downloads or generates).
    cmd = [sys.executable, "scripts/download_dataset.py"]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        return result.returncode

    # Ensure we end up with the expected file name.
    default_csv = Path("data/transactions.csv")
    if default_csv.exists() and str(default_csv) != local_path:
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        default_csv.replace(local_path)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage-account", default=os.getenv("AZURE_STORAGE_ACCOUNT", ""))
    parser.add_argument("--container", default="ml-data")
    parser.add_argument("--blob-path", default="datasets/transactions.csv")
    parser.add_argument("--local-path", default="data/transactions.csv")
    args = parser.parse_args()

    # If Azure isn't configured, don't fail the workflow.
    if not args.storage_account:
        print("AZURE_STORAGE_ACCOUNT not set. Falling back to local dataset.")
        return _fallback(args.local_path)

    try:
        from azure.storage.blob import BlobServiceClient  # type: ignore
    except Exception as e:
        print(f"azure-storage-blob not available ({e}). Falling back to local dataset.")
        return _fallback(args.local_path)

    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    if not conn_str:
        print("AZURE_STORAGE_CONNECTION_STRING not set. Falling back to local dataset.")
        return _fallback(args.local_path)

    local_path = Path(args.local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        service = BlobServiceClient.from_connection_string(conn_str)
        blob_client = service.get_blob_client(container=args.container, blob=args.blob_path)
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())
        print(f"Downloaded dataset to {local_path}")
        return 0
    except Exception as e:
        print(f"Azure blob download failed ({e}). Falling back to local dataset.")
        return _fallback(args.local_path)


if __name__ == "__main__":
    raise SystemExit(main())

