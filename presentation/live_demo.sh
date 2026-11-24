#!/usr/bin/env bash
# Live demo for presentation day: press Enter to run each step.
#   bash presentation/live_demo.sh
# Each step prints what to say. Ctrl+C stops the script at any time;
# the slides have the same pictures as a backup.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
elif [[ -f .venv/Scripts/activate ]]; then
  source .venv/Scripts/activate
fi
if ! python -c 'import open3d; import kiss_icp; import canopy.config'; then
  printf '%s\n' "Activate an environment with the project and its odometry dependencies." >&2
  exit 1
fi
export LIBGL_ALWAYS_SOFTWARE=1   # avoids WSL graphics errors in the 3-D windows
demo_out="$(mktemp -d "${TMPDIR:-/tmp}/canopy-live.XXXXXXXX")"
real_cloud="results/real/wsf19/analysis/normalised_cloud.npy"

step() {  # step <number> <title> <what to say>
  echo
  echo "=================================================================="
  echo " STEP $1: $2"
  echo " SAY: $3"
  echo "=================================================================="
  read -r -p " Press Enter to run (or Ctrl+C to stop) " _
}

step 1 "Simulated forest in 3-D (window opens in ~15 s; Q closes it)" \
  "Each dot is one laser hit: blue trunks, orange shrubs, green rocks, grey ground. Blue line = true path, orange = what odometry estimated."
python scripts/show_demo.py --view 3d --out "$demo_out/figures"

step 2 "TreeScope forest" \
  "The low layer shows trunks, shrubs, and branches under the canopy."
if [[ -f "$real_cloud" ]]; then
  python - "$real_cloud" <<'PY'
import sys

import numpy as np, open3d as o3d, matplotlib.pyplot as plt
p = np.load(sys.argv[1])
under = p[(p[:, 2] > 0.3) & (p[:, 2] < 4.0)]
pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(under))
pc.colors = o3d.utility.Vector3dVector(plt.cm.viridis(under[:, 2] / 4.0)[:, :3])
o3d.visualization.draw_geometries([pc], window_name="Real forest: understorey 0.3-4 m")
PY
else
  printf '%s\n' "Use the saved TreeScope figure at presentation/images/real_side_view.png."
fi

step 3 "Whole pipeline, live, quick mode (~30-60 s)" \
  "This runs everything end to end: drive, odometry, map, ground, trees, ladder fuel, and 4 navigation runs."
python scripts/run_all.py --seed 0 --fast --out "$demo_out"
sed -n '/## Forest analytics/,/## Navigation/p' "$demo_out/report.md"

step 4 "Saved machine learning result and confusion matrix" \
  "The Random Forest was trained on 8 simulated forests and got 89.2% accuracy on 4 unseen forests. The diagonal shows correct predictions."
sed -n '/Accuracy/,/rock |/p' results/ml/report.md
printf '%s\n' "Confusion matrix: results/ml/confusion_matrix.png"
if command -v explorer.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
  explorer.exe "$(wslpath -w results/ml/confusion_matrix.png)" 2>/dev/null || true
fi

step 5 "GitHub CI status" \
  "If GitHub is available, these are the latest CI runs."
if ! command -v gh >/dev/null 2>&1 || ! gh run list --limit 3; then
  printf '%s\n' "Live CI status is unavailable. Check the repository's Actions tab."
fi

echo
printf 'Demo completed. Results are in %s\n' "$demo_out"
