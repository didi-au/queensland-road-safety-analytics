#!/usr/bin/env python3
"""Run warehouse integrity and analytical sanity checks."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from .common import PROJECT_ROOT


WAREHOUSE = PROJECT_ROOT / "data" / "warehouse" / "road_safety.db"
REPORT_JSON = PROJECT_ROOT / "reports" / "generated" / "data_quality.json"
REPORT_MD = PROJECT_ROOT / "reports" / "generated" / "data_quality.md"


CHECKS = [
    ("crash_row_count", "SELECT COUNT(*) = 415407, COUNT(*) FROM fact_crash", "Expected release row count"),
    ("crash_key_unique", "SELECT COUNT(*) = COUNT(DISTINCT crash_ref_number), COUNT(*) - COUNT(DISTINCT crash_ref_number) FROM fact_crash", "Crash reference is unique within release"),
    ("year_range", "SELECT MIN(year_key) = 2001 AND MAX(year_key) = 2025, CAST(MIN(year_key) AS TEXT) || '-' || CAST(MAX(year_key) AS TEXT) FROM fact_crash", "Expected release year range"),
    ("year_fk", "SELECT COUNT(*) = 0, COUNT(*) FROM fact_crash f LEFT JOIN dim_year y ON y.year_key=f.year_key WHERE y.year_key IS NULL", "Every crash resolves to year dimension"),
    ("location_fk", "SELECT COUNT(*) = 0, COUNT(*) FROM fact_crash f LEFT JOIN dim_location l ON l.location_key=f.location_key WHERE l.location_key IS NULL", "Every crash resolves to location dimension"),
    ("coordinate_range", "SELECT COUNT(*) = 0, COUNT(*) FROM fact_crash WHERE crash_longitude NOT BETWEEN 137 AND 154 OR crash_latitude NOT BETWEEN -30 AND -9", "Coordinates fall in a broad Queensland bounding box"),
    ("nonnegative_counts", "SELECT COUNT(*) = 0, COUNT(*) FROM fact_crash WHERE count_casualty_total < 0 OR count_casualty_fatality < 0 OR count_casualty_hospitalised < 0", "Casualty counts are non-negative"),
    ("casualty_component_reconciliation", "SELECT COUNT(*) = 0, COUNT(*) FROM fact_crash WHERE count_casualty_total <> count_casualty_fatality + count_casualty_hospitalised + count_casualty_medically_treated + count_casualty_minor_injury", "Total casualties equal published components"),
    ("partial_year_label", "SELECT is_complete_year = 0, is_complete_year FROM dim_year WHERE year_key=2025", "2025 is labelled incomplete/preliminary"),
    ("persistence_max_five", "SELECT COUNT(*) = 0, COUNT(*) FROM vw_lga_recent_priority WHERE years_in_highest_burden_quintile > 5 OR years_observed > 5", "Five-year persistence metrics cannot exceed five"),
    ("population_lga_match", "SELECT COUNT(*) = 0, COUNT(*) FROM bridge_lga_name b LEFT JOIN fact_lga_population p ON p.lga_match_name=b.lga_match_name AND p.population_year=2024 WHERE p.lga_match_name IS NULL", "Every known TMR LGA matches an ABS population record"),
]


def main() -> None:
    connection = sqlite3.connect(WAREHOUSE)
    results = []
    try:
        connection.executescript((PROJECT_ROOT / "sql" / "01_analytics_views.sql").read_text(encoding="utf-8"))
        for check_id, sql, description in CHECKS:
            passed, observed = connection.execute(sql).fetchone()
            results.append({"check_id": check_id, "description": description, "passed": bool(passed), "observed": observed})
        connection.commit()
    finally:
        connection.close()

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "warehouse": str(WAREHOUSE.relative_to(PROJECT_ROOT)),
        "passed": all(result["passed"] for result in results),
        "checks": results,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# Data-quality report", "", f"Overall result: **{'PASS' if payload['passed'] else 'FAIL'}**", "", "| Check | Result | Observed |", "|---|---|---:|"]
    for result in results:
        lines.append(f"| {result['description']} | {'PASS' if result['passed'] else 'FAIL'} | {result['observed']} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT_MD)
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
