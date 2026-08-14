# Two-minute portfolio walkthrough

## 0:00–0:20 — Business question

I built this project to help a Queensland road-safety planning team decide where limited investigation resources should go. I deliberately framed the output as a decision product, not just a dashboard.

## 0:20–0:45 — Data and engineering

The pipeline discovers and downloads six official Queensland Government datasets, records checksums and retrieval metadata, and integrates ABS population. I modelled 415,407 crash records in SQLite and kept the supplementary aggregate datasets at their published grains to prevent invalid joins and double counting.

## 0:45–1:10 — Analysis

I used SQL window functions, ranking and segmentation to compare fatal-and-serious-injury burden, persistence and resident-normalised rates. I also built automated checks for keys, relationships, completeness, ranges and casualty reconciliation. The 2025 data is preliminary, so comparable analysis stops at 2024.

## 1:10–1:40 — Finding and recommendation

The key insight is that absolute burden and resident-normalised burden answer different questions. Brisbane has the largest five-year volume, while normalisation produces a regional shortlist including Cook, Somerset and Isaac. I recommend separate high-volume program and regional diagnostic tracks instead of one composite risk score.

## 1:40–2:00 — Judgement and next step

I do not interpret population as traffic exposure or recorded factors as causes. Before selecting treatments, I would add traffic counts, vehicle-kilometres travelled, road geometry and treatment history, then move from LGA screening to corridor-level diagnosis.
