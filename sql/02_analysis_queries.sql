-- 1. Complete-year statewide trend. Never compare partial 2025 with a full year.
SELECT *
FROM vw_state_yearly_burden
WHERE is_complete_year = 1
ORDER BY year_key;

-- 2. Recent LGA investigation priorities. Counts are burden, not population/traffic risk rates.
SELECT *
FROM vw_lga_recent_priority
ORDER BY fatal_and_serious_burden_rank
LIMIT 20;

-- 3. Locations with persistently high burden in all five recent complete years.
SELECT *
FROM vw_lga_recent_priority
WHERE years_in_highest_burden_quintile = 5
ORDER BY fatal_and_serious_casualties DESC;

-- 4. Context profile for a selected LGA. Replace the parameter in Power BI or the SQL client.
SELECT
    crash_lighting_condition,
    crash_speed_limit,
    crash_road_surface_condition,
    crash_dca_group_description,
    SUM(crash_count) AS crash_count,
    SUM(fatal_and_serious_casualties) AS fatal_and_serious_casualties
FROM vw_recent_crash_context
WHERE lga = 'Rockhampton Region'
GROUP BY 1, 2, 3, 4
ORDER BY fatal_and_serious_casualties DESC
LIMIT 20;

-- 5. Police-region factor shares for recent complete years.
SELECT
    police_region,
    SUM(crash_count) AS crash_count,
    ROUND(100.0 * SUM(drink_driving_crashes) / NULLIF(SUM(crash_count), 0), 2) AS drink_driving_share_pct,
    ROUND(100.0 * SUM(speed_crashes) / NULLIF(SUM(crash_count), 0), 2) AS speed_share_pct,
    ROUND(100.0 * SUM(fatigue_crashes) / NULLIF(SUM(crash_count), 0), 2) AS fatigue_share_pct
FROM vw_police_region_factor_profile
WHERE year_key BETWEEN 2020 AND 2024
GROUP BY police_region
ORDER BY crash_count DESC;
