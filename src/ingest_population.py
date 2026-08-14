#!/usr/bin/env python3
"""Retrieve official ABS LGA population estimates for Queensland."""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .common import latest_raw_dir


LAYER_URL = "https://geo.abs.gov.au/arcgis/rest/services/Hosted/LGA_Regional_Population_2025/FeatureServer/1"


def normalise_abs_lga_name(name: str) -> str:
    return name.replace(" (Qld)", "").strip().casefold()


def normalise_tmr_lga_name(name: str) -> str:
    cleaned = name.strip()
    for suffix in (" Aboriginal Shire", " Region", " Shire", " City", " Town"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned.casefold()


def retrieve() -> Path:
    raw_dir = latest_raw_dir()
    fields = ["lga_code_2025", "lga_name_2025"] + [f"erp_{year}" for year in range(2001, 2026)]
    params = urllib.parse.urlencode(
        {
            "where": "state_code_2021=3",
            "outFields": ",".join(fields),
            "returnGeometry": "false",
            "f": "json",
        }
    )
    query_url = f"{LAYER_URL}/query?{params}"
    request = urllib.request.Request(query_url, headers={"User-Agent": "qld-road-safety-portfolio/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if "error" in payload:
        raise RuntimeError(payload["error"])
    records = [feature["attributes"] for feature in payload["features"]]
    records.sort(key=lambda row: row["lga_code_2025"])

    csv_path = raw_dir / "abs_lga_population.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    manifest = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "publisher": "Australian Bureau of Statistics",
        "dataset": "Regional Population 2024-25 - LGA estimated resident population",
        "layer_url": LAYER_URL,
        "query": "state_code_2021=3; returnGeometry=false",
        "license_note": "Use subject to ABS website copyright and attribution conditions",
        "local_file": csv_path.name,
        "rows": len(records),
        "bytes": csv_path.stat().st_size,
        "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    (raw_dir / "population_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(csv_path)
    return csv_path


if __name__ == "__main__":
    retrieve()
