#!/usr/bin/env python3
"""Discover and download the versioned Queensland road-crash source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "sources.json"


def read_json(url: str, attempts: int = 3) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "qld-road-safety-portfolio/1.0"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def sha256(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path, attempts: int = 3) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "qld-road-safety-portfolio/1.0"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            partial.replace(destination)
            return
        except (urllib.error.URLError, TimeoutError, OSError):
            if partial.exists():
                partial.unlink()
            if attempt == attempts:
                raise
            time.sleep(2**attempt)


def run(config_path: Path, raw_root: Path, retrieval_id: str | None = None) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    expected: dict[str, str] = config["expected_resources"]
    package = read_json(config["package_api"])
    if not package.get("success"):
        raise RuntimeError("Queensland Open Data API returned success=false")

    resources = {resource["id"]: resource for resource in package["result"]["resources"]}
    missing = sorted(set(expected) - set(resources))
    if missing:
        raise RuntimeError(f"Expected resource IDs are missing: {missing}")

    retrieval_id = retrieval_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = raw_root / retrieval_id
    destination.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "retrieval_id": retrieval_id,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_id": config["dataset_id"],
        "package_api": config["package_api"],
        "publisher": config["publisher"],
        "license": config["license"],
        "source_metadata_modified": package["result"].get("metadata_modified"),
        "resources": [],
    }

    for resource_id, logical_name in expected.items():
        resource = resources[resource_id]
        suffix = Path(urllib.parse.urlparse(resource["url"]).path).suffix or ".csv"
        target = destination / f"{logical_name}{suffix.lower()}"
        if not target.exists():
            print(f"Downloading {logical_name} ...", flush=True)
            download(resource["url"], target)
        manifest["resources"].append(
            {
                "logical_name": logical_name,
                "resource_id": resource_id,
                "source_name": resource.get("name"),
                "format": resource.get("format"),
                "url": resource["url"],
                "source_last_modified": resource.get("last_modified"),
                "local_file": target.name,
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )

    manifest_path = destination / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (raw_root / "LATEST").write_text(retrieval_id + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")
    return manifest_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--raw-root", type=Path, default=PROJECT_ROOT / "data" / "raw")
    parser.add_argument("--retrieval-id", help="Stable ID for a repeatable or test retrieval")
    return parser.parse_args(argv)


if __name__ == "__main__":
    arguments = parse_args(sys.argv[1:])
    run(arguments.config, arguments.raw_root, arguments.retrieval_id)
