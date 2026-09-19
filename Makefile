# Volta Neobank — task runner
# Targets: make data | test | lint | format | type | board | publish-board | all

.PHONY: data test lint format type board publish-board all setup

setup:
	uv sync --all-groups

# Scripts live in scripts/; utils/ stays at repo root, so both roots go on PYTHONPATH.
PY := PYTHONPATH=.:scripts uv run python

# Regenerate all synthetic datasets (seeded, reproducible)
data:
	$(PY) scripts/generate_ab_data.py
	$(PY) scripts/generate_retention_data.py
	$(PY) scripts/generate_segmentation_data.py
	$(PY) scripts/generate_funnel_data.py
	$(PY) scripts/generate_churn_data.py
	$(PY) scripts/generate_rfm_data.py
	$(PY) scripts/generate_clv_data.py
	$(PY) scripts/generate_attribution_data.py
	$(PY) scripts/generate_anomaly_data.py
	$(PY) scripts/generate_transactions_data.py
	$(PY) scripts/generate_support_tickets_data.py
	$(PY) scripts/generate_nps_data.py
	$(PY) scripts/generate_feature_events_data.py
	$(PY) scripts/generate_campaigns_data.py
	$(PY) scripts/generate_referrals_data.py
	$(PY) scripts/generate_jtbd_data.py
	$(PY) scripts/generate_unit_economics_data.py
	$(PY) scripts/generate_premium_upsell_data.py
	$(PY) scripts/generate_causal_kyc_data.py
	$(PY) scripts/generate_assisted_cac_data.py
	$(PY) scripts/generate_fx_sourcing_data.py
	$(PY) scripts/generate_premium_offers_data.py

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy

notebooks:
	$(PY) scripts/build_notebooks.py

board:
	$(PY) scripts/build_board.py

# Publish the built board into the portfolio site's demos folder (sibling repo).
SITE_BOARD := ../NikitaBoyarkin.github.io/public/demos/volta

publish-board: board
	mkdir -p "$(SITE_BOARD)"
	cp docs/board/volta_board.html "$(SITE_BOARD)/index.html"
	@echo "Published board -> $(SITE_BOARD)/index.html"

all: data test lint type
	@echo "All checks passed."
