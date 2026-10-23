#!/usr/bin/env bash
# Regenerate every result and slide image, then collect the images here.
# Run from anywhere:  bash presentation/prepare.sh      (about 4-6 minutes)
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
IMAGES=presentation/images
mkdir -p "$IMAGES"

echo "1/4 Synthetic demo: drive, KISS-ICP, map, analytics, 80 navigation runs (~2 min)"
python scripts/run_all.py --seed 0 --update-outcomes

echo "2/4 Simulator figures: forest map, LiDAR scan, odometry (~15 s)"
python scripts/show_demo.py

echo "3/4 Real forest (TreeScope WSF-19)"
if [ -f results/real/wsf19/analysis/normalised_cloud.npy ]; then
  python presentation/make_slide_images.py
else
  echo "   skipped: run the 'Real forest run' commands in presentation/03-demo-commands.md first"
fi

echo "4/4 Copying slide images into $IMAGES/"
cp results/demo/figures/forest_map.png "$IMAGES/sim_forest_map.png"
cp results/demo/figures/lidar_scan.png "$IMAGES/sim_lidar_scan.png"
cp results/demo/figures/odometry.png "$IMAGES/sim_odometry.png"
cp results/demo/ladder_fuel.png "$IMAGES/sim_ladder_fuel.png"
if [ -f results/real/wsf19/analysis/ladder_fuel.png ]; then
  cp results/real/wsf19/analysis/ladder_fuel.png "$IMAGES/real_ladder_fuel.png"
fi
ls -1 "$IMAGES"
echo "Done. Numbers for the slides: results/demo/report.md and docs/real-data.md"
