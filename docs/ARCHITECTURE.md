# Architecture

```text
Queensland Open Data CKAN API
        |
        |  source discovery + six versioned CSV downloads
        v
data/raw/<retrieval-id>/
        |
        |  Python profiling, column normalisation and validation
        v
data/staging/
        |
        |  typed transformations + conformed dimensions
        v
SQLite analytical warehouse (portable, locally verified)
        |
        +--> SQL views and prioritisation analysis
        |
        +--> interactive web dashboard

        +--> Power BI-ready exports and implementation specification
        |
        +--> data-quality and reconciliation report
```

The transformation layer generates a compact, version-controlled dashboard dataset and deterministic CSV tables for downstream BI use. SQLite is deliberate here: a reviewer can reproduce the complete analytical build without credentials, containers or a hosted service. A production migration to PostgreSQL would preserve the fact grains and SQL logic but is outside the current evidence claim.

## Design principles

- Raw files are immutable and identified by retrieval timestamp and SHA-256.
- Business labels are retained while SQL-facing names are normalised to snake case.
- Transformations are deterministic and rerunnable.
- Fact grains are documented before joins to prevent many-to-many double counting.
- Aggregated outputs preserve numerator and denominator fields.
- Configurable prioritisation weights are scenario inputs, not scientific valuations.
