PYTHON ?= python3

.PHONY: all ingest population profile warehouse validate outputs test

all: ingest population profile warehouse validate outputs test

ingest:
	$(PYTHON) -m src.ingest

population:
	$(PYTHON) -m src.ingest_population

profile:
	$(PYTHON) -m src.profile_sources

warehouse:
	$(PYTHON) -m src.build_warehouse

validate:
	$(PYTHON) -m src.validate_warehouse

outputs:
	$(PYTHON) -m src.generate_outputs

test:
	$(PYTHON) -m unittest discover -s tests -v
