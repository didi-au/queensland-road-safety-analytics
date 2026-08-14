#!/usr/bin/env python3
"""Profile source grains, schemas, nulls and key fields."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .common import PROJECT_ROOT, latest_raw_dir, read_manifest, snake_case


IMPORTANT_DISTINCT = {
    "crash_locations": [
        "crash_severity",
        "loc_local_government_area",
        "loc_police_region",
        "loc_queensland_transport_region",
        "loc_abs_remoteness",
        "crash_speed_limit",
        "crash_lighting_condition",
    ],
    "road_casualties": ["casualty_severity", "casualty_age_group", "casualty_gender", "casualty_road_user_type"],
    "restraint_helmet_use": ["casualty_road_user_type", "casualty_restraint_helmet_use"],
}


def profile_csv(path: Path, logical_name: str) -> dict:
    row_count = 0
    null_counts: pd.Series | None = None
    columns: list[str] = []
    year_min = None
    year_max = None
    observed_ids: set[str] = set()
    duplicate_ids = 0
    distinct_values: dict[str, set[str]] = {
        column: set() for column in IMPORTANT_DISTINCT.get(logical_name, [])
    }

    for chunk in pd.read_csv(path, chunksize=75_000, low_memory=False):
        chunk.columns = [snake_case(column) for column in chunk.columns]
        if not columns:
            columns = list(chunk.columns)
            null_counts = pd.Series(0, index=columns, dtype="int64")
        row_count += len(chunk)
        null_counts = null_counts.add(chunk.isna().sum(), fill_value=0)
        if "crash_year" in chunk:
            years = pd.to_numeric(chunk["crash_year"], errors="coerce")
            if years.notna().any():
                year_min = int(years.min()) if year_min is None else min(year_min, int(years.min()))
                year_max = int(years.max()) if year_max is None else max(year_max, int(years.max()))
        if logical_name == "crash_locations" and "crash_ref_number" in chunk:
            for value in chunk["crash_ref_number"].astype("string").dropna():
                if value in observed_ids:
                    duplicate_ids += 1
                observed_ids.add(str(value))
        for column, values in distinct_values.items():
            if column in chunk:
                values.update(str(value).strip() for value in chunk[column].dropna().unique())

    assert null_counts is not None
    return {
        "logical_name": logical_name,
        "file": path.name,
        "rows": row_count,
        "columns": columns,
        "column_count": len(columns),
        "year_min": year_min,
        "year_max": year_max,
        "duplicate_crash_reference_count": duplicate_ids if logical_name == "crash_locations" else None,
        "null_counts": {column: int(null_counts[column]) for column in columns},
        "distinct_values": {column: sorted(values) for column, values in distinct_values.items()},
    }


def markdown_report(profiles: list[dict], retrieval_id: str) -> str:
    lines = [
        "# Source profile",
        "",
        f"Retrieval: `{retrieval_id}`",
        "",
        "| Source | Rows | Columns | Years | Duplicate crash IDs |",
        "|---|---:|---:|---|---:|",
    ]
    for profile in profiles:
        duplicate = profile["duplicate_crash_reference_count"]
        lines.append(
            f"| {profile['logical_name']} | {profile['rows']:,} | {profile['column_count']} | "
            f"{profile['year_min']}-{profile['year_max']} | "
            f"{'' if duplicate is None else f'{duplicate:,}'} |"
        )
    lines.extend(
        [
            "",
            "## Grain warning",
            "",
            "`crash_locations` is crash-level. The other sources are published aggregates at combinations of year, "
            "police region, severity and category flags. They must not be joined to individual crash rows.",
            "",
            "## Machine-readable detail",
            "",
            "See `data/staging/source_profile.json` for column-level null counts and selected category values.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    raw_dir = latest_raw_dir()
    manifest = read_manifest(raw_dir)
    profiles = []
    for resource in manifest["resources"]:
        profiles.append(profile_csv(raw_dir / resource["local_file"], resource["logical_name"]))
    output_dir = PROJECT_ROOT / "data" / "staging"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"retrieval_id": manifest["retrieval_id"], "profiles": profiles}
    (output_dir / "source_profile.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (PROJECT_ROOT / "docs" / "SOURCE_PROFILE.md").write_text(
        markdown_report(profiles, manifest["retrieval_id"]), encoding="utf-8"
    )
    print(PROJECT_ROOT / "docs" / "SOURCE_PROFILE.md")


if __name__ == "__main__":
    main()
