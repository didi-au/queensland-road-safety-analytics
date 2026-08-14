# Source profile

Retrieval: `20260424`

| Source | Rows | Columns | Years | Duplicate crash IDs |
|---|---:|---:|---|---:|
| crash_locations | 415,407 | 52 | 2001-2025 | 0 |
| road_casualties | 38,893 | 7 | 2001-2025 |  |
| driver_demographics | 22,699 | 16 | 2001-2025 |  |
| restraint_helmet_use | 42,787 | 8 | 2001-2025 |  |
| vehicle_types | 3,764 | 12 | 2001-2025 |  |
| crash_factors | 5,523 | 13 | 2001-2025 |  |

## Grain warning

`crash_locations` is crash-level. The other sources are published aggregates at combinations of year, police region, severity and category flags. They must not be joined to individual crash rows.

## Machine-readable detail

See `data/staging/source_profile.json` for column-level null counts and selected category values.
