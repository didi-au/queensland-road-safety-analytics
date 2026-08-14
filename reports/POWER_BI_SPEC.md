# Power BI implementation specification

> Scope note: this is a build-ready model, DAX and visual specification for importing the pipeline exports. The published portfolio deliverable is the interactive web dashboard; no `.pbix` file is claimed in this repository.

## Audience and decision

Audience: Queensland road-safety planning and regional program leaders.

Decision: where should limited investigation and intervention resources be prioritised, and which crash profiles should shape the next diagnostic step?

## Model

Use import mode with the generated files in `data/exports/`.

Relationships:

- `dim_year[year_key]` 1:* `fact_crash[year_key]`
- `dim_location[location_key]` 1:* `fact_crash[location_key]`
- `dim_lga[lga_key]` 1:* `fact_crash[lga_key]`
- `dim_lga[lga_key]` 1:* `fact_lga_population[lga_key]`
- `dim_year[year_key]` 1:* `fact_lga_population[year_key]`

Keep relationships single-direction from dimensions to facts. Do not join the five published aggregate profile facts to `fact_crash`; their grains differ.

## Explicit measures

```DAX
Reported Crashes =
COUNTROWS ( fact_crash )

Fatalities =
SUM ( fact_crash[count_casualty_fatality] )

Hospitalisations =
SUM ( fact_crash[count_casualty_hospitalised] )

Fatal and Serious Casualties =
[Fatalities] + [Hospitalisations]

All Casualties =
SUM ( fact_crash[count_casualty_total] )

Severity-Weighted Burden =
20 * [Fatalities]
    + 5 * [Hospitalisations]
    + 2 * SUM ( fact_crash[count_casualty_medically_treated] )
    + SUM ( fact_crash[count_casualty_minor_injury] )

Estimated Resident Population =
SUM ( fact_lga_population[estimated_resident_population] )

FSI per 100k Residents =
DIVIDE ( [Fatal and Serious Casualties] * 100000, [Estimated Resident Population] )

Vulnerable Road-User Units =
SUM ( fact_crash[count_unit_motorcycle_moped] )
    + SUM ( fact_crash[count_unit_bicycle] )
    + SUM ( fact_crash[count_unit_pedestrian] )

All Involved Units =
SUM ( fact_crash[count_unit_car] )
    + SUM ( fact_crash[count_unit_motorcycle_moped] )
    + SUM ( fact_crash[count_unit_truck] )
    + SUM ( fact_crash[count_unit_bus] )
    + SUM ( fact_crash[count_unit_bicycle] )
    + SUM ( fact_crash[count_unit_pedestrian] )
    + SUM ( fact_crash[count_unit_other] )

Vulnerable Road-User Unit Share =
DIVIDE ( [Vulnerable Road-User Units], [All Involved Units] )

Complete-Year Warning =
IF (
    SELECTEDVALUE ( dim_year[is_complete_year], 1 ) = 0,
    "Preliminary/incomplete year - do not compare with full years",
    BLANK ()
)
```

The severity weights are scenario parameters for prioritisation—not monetary valuations and not a validated road-safety severity index. Display the selected weights in an information tooltip.

## Report pages

### 1. Executive priorities

- KPI cards: five-year FSI, fatalities, hospitalisations and affected LGAs
- Ranked bar: absolute FSI burden by LGA
- Ranked dot plot: resident-normalised burden, filtering out fewer than 100 five-year FSI for ranking stability
- Two-axis quadrant: absolute burden against resident-normalised burden
- Recommendation panel: three prioritised investigation actions
- Persistent tooltip explaining why population is not traffic exposure

### 2. Geography and persistence

- Queensland point map using crash coordinates, aggregated before display
- LGA matrix for 2020-2024 with annual FSI and highest-quintile indicator
- Drill-through to selected LGA
- Slicers: complete year, remoteness, LGA and transport region

### 3. Crash profile

- Speed-limit band, lighting, surface and DCA group
- Vulnerable road-user involvement
- Small multiples comparing selected LGA with Queensland
- Dynamic narrative stating the largest differences, without causal wording

### 4. Recorded factors and demographics

- Police-region profiles for alcohol, speed and fatigue indicators
- Casualty age, gender and road-user type from the published aggregate fact
- Restraint/helmet use profile
- A visible grain note: these are published region/year aggregates and do not cross-filter individual crashes

### 5. Data quality and methodology

- Source lineage, retrieval date and record counts
- Complete versus incomplete years
- Reconciliation checks
- Definitions and limitations

## Visual standard

- Use a restrained colour system: navy for baseline, amber for investigation priority and red only for fatal outcomes.
- Do not use red/amber/green “risk” labels without accessible text.
- Every visual title should state the conclusion or question, not merely the metric name.
- Provide alt text, keyboard navigation order and colour-independent markers.
