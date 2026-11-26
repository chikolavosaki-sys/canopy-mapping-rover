#!/usr/bin/env bash
# Generate a rehearsal survey and figures from the checked-out code.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
elif [[ -f .venv/Scripts/activate ]]; then
  source .venv/Scripts/activate
fi

out=results/runs/demo
python scripts/run_all.py --seed 0 --fast --out "$out"
python scripts/show_demo.py --out "$out/figures"
printf 'Rehearsal outputs: %s\n' "$out"
printf '%s\n' "Saved TreeScope and ML figures: presentation/images/"
