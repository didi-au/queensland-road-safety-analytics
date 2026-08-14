# KPI catalogue

| KPI | Definition | Grain/denominator | Decision use | Important limitation |
|---|---|---|---|---|
| Reported crashes | Count of crash-level source records | Crash | Workload and event volume | Source contains reportable crashes, not every road incident |
| Fatalities | Sum of published fatality counts | Crash/location/time | Highest-severity burden | Recent records can be preliminary |
| Hospitalisations | Sum of published hospitalised casualty counts | Crash/location/time | Serious-injury burden | Hospitalisation is a recorded outcome, not a cost estimate |
| Fatal and serious casualties (FSI) | Fatalities + hospitalisations | Crash/location/time | Primary harm-burden measure | A crash can have more than one casualty |
| FSI per 100 reported crashes | FSI ÷ reported crashes × 100 | Reported crashes | Severity mix among recorded crashes | Not a population or exposure risk rate; can exceed 100 |
| FSI per 100k residents | FSI ÷ ABS ERP × 100,000 | LGA-year resident population | Regional diagnostic screening | Residents are not road exposure; tourism, freight and through-traffic matter |
| Five-year annualised FSI per 100k | Five-year FSI ÷ sum of annual ERP × 100,000 | LGA, 2020-2024 person-years | Compare recent resident-normalised burden | Show only with count and uncertainty/low-count warning |
| Highest-burden persistence | Years in top LGA burden quintile | LGA, five complete years | Distinguish persistent from one-year burden | Quintile is relative to other LGAs |
| Vulnerable road-user unit share | Motorcycle/moped + bicycle + pedestrian units ÷ all involved units | Crash/location/time | Profile investigation needs | Unit involvement is not casualty rate or fault |
| Severity-weighted burden | 20×fatal + 5×hospitalised + 2×medical + 1×minor | Crash/location/time | Sensitivity/scenario prioritisation | Transparent scenario weights only; not validated or monetary |

## Required display rules

- Always show absolute FSI beside population-normalised FSI.
- Label incomplete/preliminary years visibly.
- Suppress league-table interpretation for low-count rate results; the lightweight dashboard uses a minimum of 100 five-year FSI.
- Refer to alcohol, speed, fatigue and defects as “recorded involvement” or “factor indicators,” not causes.
- Do not display the severity-weighted measure without its component weights.
