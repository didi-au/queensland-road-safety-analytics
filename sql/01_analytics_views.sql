-- Analytical views for the portable SQLite warehouse.
-- PostgreSQL equivalents use the same logic with minor DDL differences.

DROP VIEW IF EXISTS vw_state_yearly_burden;
CREATE VIEW vw_state_yearly_burden AS
SELECT
    f.year_key,
    y.is_complete_year,
    COUNT(*) AS crash_count,
    SUM(f.count_casualty_fatality) AS fatalities,
    SUM(f.count_casualty_hospitalised) AS hospitalisations,
    SUM(f.fatal_and_serious_casualties) AS fatal_and_serious_casualties,
    SUM(f.count_casualty_total) AS all_casualties,
    SUM(f.severity_weighted_burden) AS severity_weighted_burden,
    ROUND(100.0 * SUM(f.fatal_and_serious_casualties) / NULLIF(COUNT(*), 0), 2)
        AS fatal_and_serious_casualties_per_100_reported_crashes
FROM fact_crash f
JOIN dim_year y ON y.year_key = f.year_key
GROUP BY f.year_key, y.is_complete_year;

DROP VIEW IF EXISTS vw_lga_yearly_burden;
CREATE VIEW vw_lga_yearly_burden AS
SELECT
    f.year_key,
    l.loc_local_government_area AS lga,
    MAX(p.estimated_resident_population) AS estimated_resident_population,
    COUNT(*) AS crash_count,
    SUM(f.count_casualty_fatality) AS fatalities,
    SUM(f.count_casualty_hospitalised) AS hospitalisations,
    SUM(f.fatal_and_serious_casualties) AS fatal_and_serious_casualties,
    SUM(f.count_casualty_total) AS all_casualties,
    SUM(f.severity_weighted_burden) AS severity_weighted_burden,
    SUM(f.count_unit_motorcycle_moped + f.count_unit_bicycle + f.count_unit_pedestrian)
        AS vulnerable_road_user_units,
    SUM(f.count_unit_car + f.count_unit_motorcycle_moped + f.count_unit_truck
        + f.count_unit_bus + f.count_unit_bicycle + f.count_unit_pedestrian + f.count_unit_other)
        AS all_involved_units,
    ROUND(100.0 * SUM(f.fatal_and_serious_casualties) / NULLIF(COUNT(*), 0), 2)
        AS fatal_and_serious_casualties_per_100_reported_crashes,
    ROUND(
        100.0 * SUM(f.count_unit_motorcycle_moped + f.count_unit_bicycle + f.count_unit_pedestrian)
        / NULLIF(SUM(f.count_unit_car + f.count_unit_motorcycle_moped + f.count_unit_truck
            + f.count_unit_bus + f.count_unit_bicycle + f.count_unit_pedestrian + f.count_unit_other), 0),
        2
    ) AS vulnerable_road_user_unit_share_pct,
    ROUND(
        100000.0 * SUM(f.fatal_and_serious_casualties)
        / NULLIF(MAX(p.estimated_resident_population), 0),
        2
    ) AS fatal_and_serious_casualties_per_100k_residents
FROM fact_crash f
JOIN dim_location l ON l.location_key = f.location_key
JOIN dim_year y ON y.year_key = f.year_key AND y.is_complete_year = 1
LEFT JOIN bridge_lga_name b ON b.tmr_lga_name = l.loc_local_government_area
LEFT JOIN fact_lga_population p
  ON p.lga_match_name = b.lga_match_name
 AND p.population_year = f.year_key
WHERE l.loc_local_government_area IS NOT NULL
GROUP BY f.year_key, l.loc_local_government_area;

DROP VIEW IF EXISTS vw_lga_recent_priority;
CREATE VIEW vw_lga_recent_priority AS
WITH yearly_rank AS (
    SELECT
        b.*,
        NTILE(5) OVER (
            PARTITION BY b.year_key
            ORDER BY b.fatal_and_serious_casualties DESC
        ) AS burden_quintile
    FROM vw_lga_yearly_burden b
    WHERE b.year_key BETWEEN 2020 AND 2024
), five_year AS (
    SELECT
        lga,
        SUM(crash_count) AS crash_count,
        SUM(fatalities) AS fatalities,
        SUM(hospitalisations) AS hospitalisations,
        SUM(fatal_and_serious_casualties) AS fatal_and_serious_casualties,
        SUM(all_casualties) AS all_casualties,
        SUM(estimated_resident_population) AS population_person_years,
        SUM(severity_weighted_burden) AS severity_weighted_burden,
        SUM(vulnerable_road_user_units) AS vulnerable_road_user_units,
        SUM(all_involved_units) AS all_involved_units,
        SUM(CASE WHEN burden_quintile = 1 THEN 1 ELSE 0 END) AS years_in_highest_burden_quintile,
        COUNT(DISTINCT year_key) AS years_observed
    FROM yearly_rank
    GROUP BY lga
)
SELECT
    lga,
    crash_count,
    fatalities,
    hospitalisations,
    fatal_and_serious_casualties,
    all_casualties,
    population_person_years,
    severity_weighted_burden,
    years_in_highest_burden_quintile,
    years_observed,
    ROUND(100.0 * fatal_and_serious_casualties / NULLIF(crash_count, 0), 2)
        AS fatal_and_serious_casualties_per_100_reported_crashes,
    ROUND(100.0 * vulnerable_road_user_units / NULLIF(all_involved_units, 0), 2)
        AS vulnerable_road_user_unit_share_pct,
    ROUND(100000.0 * fatal_and_serious_casualties / NULLIF(population_person_years, 0), 2)
        AS annualised_fatal_and_serious_casualties_per_100k_residents,
    RANK() OVER (ORDER BY fatal_and_serious_casualties DESC) AS fatal_and_serious_burden_rank,
    RANK() OVER (ORDER BY severity_weighted_burden DESC) AS severity_weighted_burden_rank,
    RANK() OVER (
        ORDER BY 100000.0 * fatal_and_serious_casualties / NULLIF(population_person_years, 0) DESC
    ) AS population_normalised_rank
FROM five_year;

DROP VIEW IF EXISTS vw_police_region_factor_profile;
CREATE VIEW vw_police_region_factor_profile AS
SELECT
    CAST(crash_year AS INTEGER) AS year_key,
    crash_police_region AS police_region,
    SUM(count_crashes) AS crash_count,
    SUM(CASE WHEN involving_drink_driving = 'Yes' THEN count_crashes ELSE 0 END) AS drink_driving_crashes,
    SUM(CASE WHEN involving_driver_speed = 'Yes' THEN count_crashes ELSE 0 END) AS speed_crashes,
    SUM(CASE WHEN involving_fatigued_driver = 'Yes' THEN count_crashes ELSE 0 END) AS fatigue_crashes,
    SUM(CASE WHEN involving_defective_vehicle = 'Yes' THEN count_crashes ELSE 0 END) AS defective_vehicle_crashes,
    ROUND(100.0 * SUM(CASE WHEN involving_drink_driving = 'Yes' THEN count_crashes ELSE 0 END)
        / NULLIF(SUM(count_crashes), 0), 2) AS drink_driving_share_pct,
    ROUND(100.0 * SUM(CASE WHEN involving_driver_speed = 'Yes' THEN count_crashes ELSE 0 END)
        / NULLIF(SUM(count_crashes), 0), 2) AS speed_share_pct,
    ROUND(100.0 * SUM(CASE WHEN involving_fatigued_driver = 'Yes' THEN count_crashes ELSE 0 END)
        / NULLIF(SUM(count_crashes), 0), 2) AS fatigue_share_pct
FROM fact_crash_factor_profile
GROUP BY CAST(crash_year AS INTEGER), crash_police_region;

DROP VIEW IF EXISTS vw_recent_crash_context;
CREATE VIEW vw_recent_crash_context AS
SELECT
    l.loc_local_government_area AS lga,
    f.crash_lighting_condition,
    f.crash_speed_limit,
    f.crash_road_surface_condition,
    f.crash_dca_group_description,
    COUNT(*) AS crash_count,
    SUM(f.fatal_and_serious_casualties) AS fatal_and_serious_casualties,
    SUM(f.severity_weighted_burden) AS severity_weighted_burden
FROM fact_crash f
JOIN dim_location l ON l.location_key = f.location_key
WHERE f.year_key BETWEEN 2020 AND 2024
GROUP BY
    l.loc_local_government_area,
    f.crash_lighting_condition,
    f.crash_speed_limit,
    f.crash_road_surface_condition,
    f.crash_dca_group_description;
