#!/usr/bin/env python3
"""Build a verified local analytical warehouse from the latest raw retrieval."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from .common import PROJECT_ROOT, latest_raw_dir, read_manifest, snake_case
from .ingest_population import normalise_abs_lga_name, normalise_tmr_lga_name


WAREHOUSE = PROJECT_ROOT / "data" / "warehouse" / "road_safety.db"
LOCATION_COLUMNS = [
    "loc_suburb",
    "loc_local_government_area",
    "loc_post_code",
    "loc_police_division",
    "loc_police_district",
    "loc_police_region",
    "loc_queensland_transport_region",
    "loc_main_roads_region",
    "loc_abs_statistical_area_2",
    "loc_abs_statistical_area_3",
    "loc_abs_statistical_area_4",
    "loc_abs_remoteness",
    "loc_state_electorate",
    "loc_federal_electorate",
]


def clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [snake_case(column) for column in frame.columns]
    for column in frame.select_dtypes(include=["object"]).columns:
        frame[column] = frame[column].astype("string").str.strip().replace({"": pd.NA})
    return frame


def load_csv_chunks(connection: sqlite3.Connection, path: Path, table: str, chunk_size: int = 50_000) -> int:
    rows = 0
    first = True
    for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
        chunk = clean_frame(chunk)
        chunk.to_sql(table, connection, if_exists="replace" if first else "append", index=False, chunksize=2_000)
        first = False
        rows += len(chunk)
        print(f"{table}: {rows:,} rows", flush=True)
    return rows


def build() -> Path:
    raw_dir = latest_raw_dir()
    manifest = read_manifest(raw_dir)
    resources = {item["logical_name"]: raw_dir / item["local_file"] for item in manifest["resources"]}
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()

    connection = sqlite3.connect(WAREHOUSE)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        load_csv_chunks(connection, resources["crash_locations"], "stg_crash_locations")

        connection.executescript(
            """
            CREATE TABLE dim_year (
                year_key INTEGER PRIMARY KEY,
                is_complete_year INTEGER NOT NULL,
                completeness_note TEXT NOT NULL
            );

            INSERT INTO dim_year
            SELECT DISTINCT CAST(crash_year AS INTEGER),
                   CASE WHEN CAST(crash_year AS INTEGER) <= 2024 THEN 1 ELSE 0 END,
                   CASE WHEN CAST(crash_year AS INTEGER) <= 2024
                        THEN 'Complete reporting year in current release'
                        ELSE 'Incomplete/preliminary reporting year - exclude from like-for-like annual ranking' END
            FROM stg_crash_locations;

            CREATE TABLE dim_location (
                location_key INTEGER PRIMARY KEY,
                loc_suburb TEXT,
                loc_local_government_area TEXT,
                loc_post_code TEXT,
                loc_police_division TEXT,
                loc_police_district TEXT,
                loc_police_region TEXT,
                loc_queensland_transport_region TEXT,
                loc_main_roads_region TEXT,
                loc_abs_statistical_area_2 TEXT,
                loc_abs_statistical_area_3 TEXT,
                loc_abs_statistical_area_4 TEXT,
                loc_abs_remoteness TEXT,
                loc_state_electorate TEXT,
                loc_federal_electorate TEXT,
                UNIQUE (
                    loc_suburb, loc_local_government_area, loc_post_code,
                    loc_police_division, loc_police_district, loc_police_region,
                    loc_queensland_transport_region, loc_main_roads_region,
                    loc_abs_statistical_area_2, loc_abs_statistical_area_3,
                    loc_abs_statistical_area_4, loc_abs_remoteness,
                    loc_state_electorate, loc_federal_electorate
                )
            );

            INSERT INTO dim_location (
                loc_suburb, loc_local_government_area, loc_post_code,
                loc_police_division, loc_police_district, loc_police_region,
                loc_queensland_transport_region, loc_main_roads_region,
                loc_abs_statistical_area_2, loc_abs_statistical_area_3,
                loc_abs_statistical_area_4, loc_abs_remoteness,
                loc_state_electorate, loc_federal_electorate
            )
            SELECT DISTINCT
                loc_suburb, loc_local_government_area, CAST(loc_post_code AS TEXT),
                loc_police_division, loc_police_district, loc_police_region,
                loc_queensland_transport_region, loc_main_roads_region,
                loc_abs_statistical_area_2, loc_abs_statistical_area_3,
                loc_abs_statistical_area_4, loc_abs_remoteness,
                loc_state_electorate, loc_federal_electorate
            FROM stg_crash_locations;

            CREATE INDEX idx_dim_location_natural
            ON dim_location (
                loc_suburb, loc_local_government_area, loc_post_code,
                loc_police_division, loc_police_district, loc_police_region,
                loc_queensland_transport_region, loc_main_roads_region,
                loc_abs_statistical_area_2, loc_abs_statistical_area_3,
                loc_abs_statistical_area_4, loc_abs_remoteness,
                loc_state_electorate, loc_federal_electorate
            );

            CREATE TABLE fact_crash AS
            SELECT
                CAST(s.crash_ref_number AS TEXT) AS crash_ref_number,
                CAST(s.crash_year AS INTEGER) AS year_key,
                l.location_key,
                s.crash_severity,
                s.crash_month,
                s.crash_day_of_week,
                CAST(s.crash_hour AS INTEGER) AS crash_hour,
                s.crash_nature,
                s.crash_type,
                CAST(s.crash_longitude AS REAL) AS crash_longitude,
                CAST(s.crash_latitude AS REAL) AS crash_latitude,
                s.crash_street,
                s.crash_street_intersecting,
                s.state_road_name,
                s.crash_controlling_authority,
                s.crash_roadway_feature,
                s.crash_traffic_control,
                s.crash_speed_limit,
                s.crash_road_surface_condition,
                s.crash_atmospheric_condition,
                s.crash_lighting_condition,
                s.crash_road_horiz_align,
                s.crash_road_vert_align,
                CAST(s.crash_dca_code AS TEXT) AS crash_dca_code,
                s.crash_dca_description,
                s.crash_dca_group_description,
                s.dca_key_approach_dir,
                CAST(s.count_casualty_fatality AS INTEGER) AS count_casualty_fatality,
                CAST(s.count_casualty_hospitalised AS INTEGER) AS count_casualty_hospitalised,
                CAST(s.count_casualty_medically_treated AS INTEGER) AS count_casualty_medically_treated,
                CAST(s.count_casualty_minor_injury AS INTEGER) AS count_casualty_minor_injury,
                CAST(s.count_casualty_total AS INTEGER) AS count_casualty_total,
                CAST(s.count_unit_car AS INTEGER) AS count_unit_car,
                CAST(s.count_unit_motorcycle_moped AS INTEGER) AS count_unit_motorcycle_moped,
                CAST(s.count_unit_truck AS INTEGER) AS count_unit_truck,
                CAST(s.count_unit_bus AS INTEGER) AS count_unit_bus,
                CAST(s.count_unit_bicycle AS INTEGER) AS count_unit_bicycle,
                CAST(s.count_unit_pedestrian AS INTEGER) AS count_unit_pedestrian,
                CAST(s.count_unit_other AS INTEGER) AS count_unit_other,
                CAST(s.count_casualty_fatality AS INTEGER) + CAST(s.count_casualty_hospitalised AS INTEGER)
                    AS fatal_and_serious_casualties,
                20 * CAST(s.count_casualty_fatality AS INTEGER)
                  + 5 * CAST(s.count_casualty_hospitalised AS INTEGER)
                  + 2 * CAST(s.count_casualty_medically_treated AS INTEGER)
                  + CAST(s.count_casualty_minor_injury AS INTEGER) AS severity_weighted_burden
            FROM stg_crash_locations s
            JOIN dim_location l
              ON l.loc_suburb IS s.loc_suburb
             AND l.loc_local_government_area IS s.loc_local_government_area
             AND l.loc_post_code IS CAST(s.loc_post_code AS TEXT)
             AND l.loc_police_division IS s.loc_police_division
             AND l.loc_police_district IS s.loc_police_district
             AND l.loc_police_region IS s.loc_police_region
             AND l.loc_queensland_transport_region IS s.loc_queensland_transport_region
             AND l.loc_main_roads_region IS s.loc_main_roads_region
             AND l.loc_abs_statistical_area_2 IS s.loc_abs_statistical_area_2
             AND l.loc_abs_statistical_area_3 IS s.loc_abs_statistical_area_3
             AND l.loc_abs_statistical_area_4 IS s.loc_abs_statistical_area_4
             AND l.loc_abs_remoteness IS s.loc_abs_remoteness
             AND l.loc_state_electorate IS s.loc_state_electorate
             AND l.loc_federal_electorate IS s.loc_federal_electorate;

            CREATE UNIQUE INDEX idx_fact_crash_ref ON fact_crash(crash_ref_number);
            CREATE INDEX idx_fact_crash_year ON fact_crash(year_key);
            CREATE INDEX idx_fact_crash_location ON fact_crash(location_key);
            """
        )

        fact_names = {
            "road_casualties": "fact_road_casualty_profile",
            "driver_demographics": "fact_driver_profile",
            "restraint_helmet_use": "fact_restraint_helmet",
            "vehicle_types": "fact_vehicle_profile",
            "crash_factors": "fact_crash_factor_profile",
        }
        for logical_name, table in fact_names.items():
            load_csv_chunks(connection, resources[logical_name], table)
            connection.execute(f"CREATE INDEX idx_{table}_year ON {table}(crash_year)")

        population_path = raw_dir / "abs_lga_population.csv"
        if not population_path.exists():
            raise FileNotFoundError("Run `python -m src.ingest_population` before building the warehouse")
        population = pd.read_csv(population_path, dtype={"lga_code_2025": "string"})
        population["lga_match_name"] = population["lga_name_2025"].map(normalise_abs_lga_name)
        population_long = population.melt(
            id_vars=["lga_code_2025", "lga_name_2025", "lga_match_name"],
            value_vars=[f"erp_{year}" for year in range(2001, 2026)],
            var_name="population_year",
            value_name="estimated_resident_population",
        )
        population_long["population_year"] = population_long["population_year"].str.removeprefix("erp_").astype(int)
        population_long.to_sql("fact_lga_population", connection, if_exists="replace", index=False)
        connection.execute("CREATE UNIQUE INDEX idx_population_lga_year ON fact_lga_population(lga_match_name, population_year)")

        lga_names = pd.read_sql_query(
            "SELECT DISTINCT loc_local_government_area AS tmr_lga_name FROM dim_location WHERE loc_local_government_area IS NOT NULL AND loc_local_government_area <> 'Unknown'",
            connection,
        )
        lga_names["lga_match_name"] = lga_names["tmr_lga_name"].map(normalise_tmr_lga_name)
        lga_names.to_sql("bridge_lga_name", connection, if_exists="replace", index=False)
        connection.execute("CREATE UNIQUE INDEX idx_bridge_lga_name ON bridge_lga_name(tmr_lga_name)")

        connection.execute(
            "CREATE TABLE pipeline_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        metadata = {
            "retrieval_id": manifest["retrieval_id"],
            "retrieved_at_utc": manifest["retrieved_at_utc"],
            "source_metadata_modified": str(manifest.get("source_metadata_modified")),
            "severity_weight_scenario": json.dumps({"fatality": 20, "hospitalised": 5, "medical": 2, "minor": 1}),
        }
        connection.executemany("INSERT INTO pipeline_metadata VALUES (?, ?)", metadata.items())
        connection.execute("DROP TABLE stg_crash_locations")
        connection.commit()
    finally:
        connection.close()
    print(WAREHOUSE)
    return WAREHOUSE


if __name__ == "__main__":
    build()
