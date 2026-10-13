#!/usr/bin/env bash
# Volta EDA (wave 2, flagship) — exact profiling commands.
# Run from the project root: bash reports/eda/scripts/profile.sh
set -euo pipefail

EDA="/Users/nikitaboarkin/Desktop/00 ide/00 portfolio/.eda-tools/.venv/bin/python"
PROF="/Users/nikitaboarkin/Desktop/00 obsidian/obsidian/.claude/skills/eda/scripts/eda_profile.py"

"$EDA" "$PROF" --input data/charts/funnel.csv --metric first_tx \
    --segments channel,device,age_group --time-col install_date \
    --out reports/eda/raw2/funnel.md

"$EDA" "$PROF" --input data/volta_ab_experiment.csv --metric kyc_completed \
    --segments group,age_group,device,channel \
    --out reports/eda/raw2/ab_experiment.md

# Exact recomputation of every number in the report + 6 figures.
"$EDA" reports/eda/scripts/explore_volta.py
"$EDA" reports/eda/scripts/plot_volta.py
