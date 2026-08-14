# Project brief

## Sponsor scenario

The stakeholder is a Queensland road-safety planning team preparing an evidence pack for prioritising limited investigation and intervention resources. The team needs a repeatable view of crash burden, severity and associated risk profiles across local government areas and transport regions.

## Primary decision

Which geographic areas and crash profiles warrant priority investigation, and which intervention categories are supported by the available evidence?

## Supporting questions

1. Where is the greatest recent burden of fatal and serious-injury crashes?
2. Which locations remain persistently high priority rather than appearing high in a single period?
3. Which crash circumstances and road-user groups are over-represented within each priority area?
4. How do alcohol, speed, fatigue, restraint use, vehicle type, lighting and road conditions differ across segments?
5. Which findings are robust enough to support a recommendation, and which require exposure data or further investigation?

## Published analytical grain

- Core fact: one row per reported crash.
- Related published facts: aggregated casualty, driver, vehicle, restraint and crash-factor profiles at their documented geographic and demographic grains.
- The supplementary facts are deliberately not joined to individual crashes.
- Time reporting: full-year comparisons by default; incomplete recent years must be labelled and excluded from like-for-like trend rankings.

## Initial priority framework

The project will keep the component measures visible rather than hiding judgement inside a single opaque score.

1. **Fatal and serious-injury burden:** fatalities plus hospitalisations.
2. **Severity-weighted burden:** a documented scenario weight applied to casualty outcomes for prioritisation only.
3. **Persistence:** number of complete recent years in which an area ranks in the highest burden quintile.
4. **Vulnerable road users:** motorcycle, bicycle and pedestrian involvement.
5. **Recorded factor profile:** alcohol, speed, fatigue and restraint/helmet indicators.

If population or traffic-exposure data can be joined at a compatible geography and period, counts and rates will be shown together. Raw counts will never be presented as risk rates.

## Deliverables

- Reproducible ingestion and curated star schema
- Source-to-target data dictionary and ERD
- Automated data-quality report
- Versioned analytical SQL
- Interactive portfolio dashboard
- Power BI-ready model specification and DAX catalogue
- Executive briefing with prioritised recommendations
- Two-minute portfolio walkthrough script

## Portfolio acceptance criteria

The project is complete only when:

- A new user can reproduce the curated outputs from documented commands.
- Every source file has its URL, resource ID, retrieval time and checksum captured.
- Primary keys and expected relationships are tested.
- All analytical measures have definitions, grain and caveats.
- Counts reconcile between source and curated layers or exceptions are documented.
- Incomplete years are visibly distinguished from complete years.
- The interactive dashboard loads the version-controlled summary dataset successfully.
- The Power BI implementation specification uses explicit measures and a star schema.
- The executive output leads with a decision and recommendations, not tools.
- Every public link works and no confidential or personal data is used.

## Out of scope

- Predicting individual crashes
- Inferring fault or individual behaviour
- Claiming causality from observational associations
- Estimating intervention benefits without treatment and exposure data
- Publishing any record outside the official de-identified open dataset
