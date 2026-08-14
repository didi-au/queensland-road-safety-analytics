#!/usr/bin/env python3
"""Generate downstream BI tables and the public dashboard dataset."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from .common import PROJECT_ROOT


WAREHOUSE = PROJECT_ROOT / "data" / "warehouse" / "road_safety.db"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
DASHBOARD_DATA = PROJECT_ROOT / "dashboard" / "data" / "summary.json"


POWER_BI_QUERIES = {
    "dim_year.csv": "SELECT * FROM dim_year ORDER BY year_key",
    "dim_location.csv": "SELECT * FROM dim_location ORDER BY location_key",
    "dim_lga.csv": """
        SELECT ROW_NUMBER() OVER (ORDER BY b.tmr_lga_name) AS lga_key,
               b.tmr_lga_name AS lga,
               MIN(p.lga_code_2025) AS abs_lga_code_2025,
               MIN(p.lga_name_2025) AS abs_lga_name_2025
        FROM bridge_lga_name b
        JOIN fact_lga_population p ON p.lga_match_name=b.lga_match_name
        GROUP BY b.tmr_lga_name
        ORDER BY lga_key
    """,
    "fact_crash.csv": """
        WITH lga AS (
            SELECT ROW_NUMBER() OVER (ORDER BY b.tmr_lga_name) AS lga_key, b.tmr_lga_name
            FROM bridge_lga_name b
        )
        SELECT f.*, g.lga_key
        FROM fact_crash f
        LEFT JOIN dim_location l ON l.location_key=f.location_key
        LEFT JOIN lga g ON g.tmr_lga_name=l.loc_local_government_area
    """,
    "fact_lga_population.csv": """
        WITH lga AS (
            SELECT ROW_NUMBER() OVER (ORDER BY b.tmr_lga_name) AS lga_key,
                   b.lga_match_name
            FROM bridge_lga_name b
        )
        SELECT g.lga_key, p.population_year AS year_key, p.estimated_resident_population
        FROM fact_lga_population p
        JOIN lga g ON g.lga_match_name=p.lga_match_name
        ORDER BY g.lga_key, p.population_year
    """,
    "fact_road_casualty_profile.csv": "SELECT * FROM fact_road_casualty_profile",
    "fact_driver_profile.csv": "SELECT * FROM fact_driver_profile",
    "fact_restraint_helmet.csv": "SELECT * FROM fact_restraint_helmet",
    "fact_vehicle_profile.csv": "SELECT * FROM fact_vehicle_profile",
    "fact_crash_factor_profile.csv": "SELECT * FROM fact_crash_factor_profile",
}


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(WAREHOUSE)
    try:
        for filename, query in POWER_BI_QUERIES.items():
            frame = pd.read_sql_query(query, connection)
            frame.to_csv(EXPORT_DIR / filename, index=False)
            print(f"{filename}: {len(frame):,} rows")

        statewide = pd.read_sql_query(
            "SELECT * FROM vw_state_yearly_burden WHERE year_key BETWEEN 2015 AND 2024 ORDER BY year_key",
            connection,
        )
        burden = pd.read_sql_query(
            """SELECT lga, fatalities, hospitalisations, fatal_and_serious_casualties,
                      annualised_fatal_and_serious_casualties_per_100k_residents,
                      years_in_highest_burden_quintile
                 FROM vw_lga_recent_priority
                ORDER BY fatal_and_serious_burden_rank LIMIT 20""",
            connection,
        )
        rate = pd.read_sql_query(
            """SELECT lga, fatal_and_serious_casualties,
                      annualised_fatal_and_serious_casualties_per_100k_residents,
                      fatal_and_serious_burden_rank
                 FROM vw_lga_recent_priority
                WHERE fatal_and_serious_casualties >= 100
                ORDER BY annualised_fatal_and_serious_casualties_per_100k_residents DESC LIMIT 20""",
            connection,
        )
        factors = pd.read_sql_query(
            """SELECT police_region, SUM(crash_count) AS crash_count,
                      ROUND(100.0*SUM(drink_driving_crashes)/SUM(crash_count),2) AS drink_driving_share_pct,
                      ROUND(100.0*SUM(speed_crashes)/SUM(crash_count),2) AS speed_share_pct,
                      ROUND(100.0*SUM(fatigue_crashes)/SUM(crash_count),2) AS fatigue_share_pct
                 FROM vw_police_region_factor_profile
                WHERE year_key BETWEEN 2020 AND 2024
                GROUP BY police_region ORDER BY crash_count DESC""",
            connection,
        )
        payload = {
            "metadata": {
                "analysis_period": "2020-2024 complete years",
                "population_denominator": "ABS estimated resident population; rate is per 100,000 person-years",
                "rate_caveat": "Population is not traffic exposure. Rates describe resident-normalised burden, not road-user risk.",
                "low_count_rule": "Rate ranking shown only where five-year fatal-and-serious casualties >= 100.",
            },
            "statewide_trend": records(statewide),
            "top_burden_lgas": records(burden),
            "top_rate_lgas_min_100_fsi": records(rate),
            "police_region_factor_profile": records(factors),
        }
    finally:
        connection.close()

    DASHBOARD_DATA.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DATA.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(DASHBOARD_DATA)


if __name__ == "__main__":
    main()
