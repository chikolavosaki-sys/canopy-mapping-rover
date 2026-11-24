#!/usr/bin/env bash
# Live demo for presentation day: press Enter to run each step.
#   bash presentation/live_demo.sh
# Each step prints what to say. Ctrl+C stops the script at any time;
# the slides have the same pictures as a backup.
cd "$(dirname "$0")/.."
source .venv/bin/activate
export LIBGL_ALWAYS_SOFTWARE=1   # avoids WSL graphics errors in the 3-D windows

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
python scripts/show_demo.py --view 3d

step 2 "Real forest, only the 0.3-4 m layer (Q closes it)" \
  "This is the real TreeScope forest with everything above 4 m removed: columns are trunks, clumps are shrubs - the ladder fuel a drone cannot see."
python - <<'PY'
import numpy as np, open3d as o3d, matplotlib.pyplot as plt
p = np.load("results/real/wsf19/analysis/normalised_cloud.npy")
under = p[(p[:, 2] > 0.3) & (p[:, 2] < 4.0)]
pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(under))
pc.colors = o3d.utility.Vector3dVector(plt.cm.viridis(under[:, 2] / 4.0)[:, :3])
o3d.visualization.draw_geometries([pc], window_name="Real forest: understorey 0.3-4 m")
PY

step 3 "Whole pipeline, live, quick mode (~30-60 s)" \
  "This runs everything end to end: drive, odometry, map, ground, trees, ladder fuel, and 4 navigation runs."
python scripts/run_all.py --seed 0 --fast --out /tmp/live_demo
sed -n '/## Forest analytics/,/## Navigation/p' /tmp/live_demo/report.md

step 4 "Machine learning result (already trained; opens the confusion matrix)" \
  "The Random Forest was trained on 8 simulated forests and got 89.2% accuracy on 4 unseen forests. The diagonal shows correct predictions."
sed -n '/Accuracy/,/rock |/p' results/ml/report.md
explorer.exe "$(wslpath -w results/ml/confusion_matrix.png)" 2>/dev/null || true

step 5 "Proof the code is tested (GitHub CI)" \
  "Every change runs 67 automatic tests on GitHub; these are the latest runs."
gh run list --limit 3 2>/dev/null || echo "(gh not logged in: say 'all 67 tests pass in CI')"

echo
echo "Demo finished - back to the slides."
