# Volta Neobank — task runner
# Targets: make data | test | lint | format | type | all

.PHONY: data test lint format type all setup

setup:
	uv sync --all-groups

# Regenerate all synthetic datasets (seeded, reproducible)
data:
	uv run python generate_ab_data.py
	uv run python generate_retention_data.py
	uv run python generate_segmentation_data.py
	uv run python generate_funnel_data.py
	uv run python generate_churn_data.py
	uv run python generate_rfm_data.py
	uv run python generate_clv_data.py
	uv run python generate_attribution_data.py
	uv run python generate_anomaly_data.py
	uv run python generate_transactions_data.py
	uv run python generate_support_tickets_data.py
	uv run python generate_nps_data.py
	uv run python generate_feature_events_data.py
	uv run python generate_campaigns_data.py
	uv run python generate_referrals_data.py

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy

notebooks:
	uv run python build_notebooks.py

all: data test lint type
	@echo "All checks passed."
