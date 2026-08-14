# Data model and grains

## Why this is a fact constellation

The source package contains one crash-level file and five published aggregate files. A single flattened table would create many-to-many joins and multiply measures. The warehouse therefore uses conformed year, location/LGA and police-region labels across separate facts.

| Table | Grain | Key/use |
|---|---|---|
| `fact_crash` | One reported crash | Unique `crash_ref_number`; crash circumstances, coordinates, casualty and involved-unit counts |
| `dim_year` | One calendar year | Complete/preliminary reporting flag |
| `dim_location` | One unique published location hierarchy | Suburb, LGA, police/transport regions, ABS areas, remoteness and electorates |
| `fact_lga_population` | One ABS LGA and year | Estimated resident population denominator |
| `fact_road_casualty_profile` | Year × police region × casualty attributes | Published casualty counts by severity, age, gender and road-user type |
| `fact_driver_profile` | Year × police region × severity × driver flags | Published crash/casualty counts for driver demographic combinations |
| `fact_restraint_helmet` | Year × police region × casualty attributes × restraint status | Published casualty counts |
| `fact_vehicle_profile` | Year × police region × severity × vehicle flags | Published crash/casualty counts |
| `fact_crash_factor_profile` | Year × police region × severity × factor flags | Published crash/casualty counts for alcohol, speed, fatigue and vehicle-defect combinations |

## Join safety

- `fact_crash` may join to `dim_year` and `dim_location` using many-to-one relationships.
- Population may join through the conformed LGA name and year.
- Aggregate profile facts may be analysed at their published grain only.
- Aggregate facts must not join to individual crashes. Their measures are not additive across arbitrary factor columns unless their exact published combination grain is retained.

## Geographic name bridge

TMR labels include local-government type suffixes such as `City`, `Region`, `Shire`, `Aboriginal Shire` and `Town`. ABS regional-population names omit these suffixes and use `(Qld)` qualifiers for ambiguous names. The pipeline normalises both systems into a controlled matching value and validates that all 78 known TMR LGAs match an ABS record. `Unknown` is retained in the crash source but excluded from the bridge.

## Incomplete year handling

The current source contains partial 2025 records. `dim_year.is_complete_year` is false for 2025, and the five-year prioritisation views explicitly use 2020-2024. The underlying partial records remain available for transparent source reconciliation.
