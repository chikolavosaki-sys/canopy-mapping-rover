# Demo commands

Run these from the project folder after setting up the Python environment in the
[README](../README.md). The live walkthrough uses only the synthetic forest.
The saved TreeScope figures are ready to show on a fresh clone.

## A. Prepare and rehearse

On Windows, run these commands in PowerShell.

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --seed 0 --fast --out results/semester-demo
.\.venv\Scripts\python.exe scripts/show_demo.py --out results/semester-demo/figures
```

On Linux, macOS, or WSL, activate your environment and run:

```bash
source .venv/bin/activate
python scripts/run_all.py --seed 0 --fast --out results/semester-demo
python scripts/show_demo.py --out results/semester-demo/figures
```

Rehearse on the presentation laptop. Keep these files open or ready to open:

| File | What to show |
|---|---|
| `results/semester-demo/survey_map.png` | The estimated and reference routes, tree detections, and the ladder-fuel heatmap |
| `results/semester-demo/trees.csv` | Tree locations and estimated diameters in metres |
| `results/semester-demo/figures/lidar_scan.png` | One simulated LiDAR scan |
| `results/semester-demo/figures/odometry.png` | Estimated path and position error along the drive |
| `results/semester-demo/figures/forest_map.png` | An example simulated navigation run |
| `presentation/images/real_side_view.png` and `real_top_views.png` | Saved figures from the earlier TreeScope run |
| `presentation/images/real_ladder_fuel.png` | Saved real-data heatmap |

The quick demo runs four navigation trials. To reproduce the 80-trial benchmark
in [the outcomes document](../docs/OUTCOMES.md), omit `--fast` and choose a
separate output folder, such as `results/semester-benchmark`.

## B. Optional real-forest rerun before the presentation

Check for the WSF-19 bag in PowerShell before attempting a rerun.

```powershell
Test-Path -LiteralPath 'data/raw/treescope/WSF-19/input/cloud3.bag' -PathType Leaf
```

When it prints `False`, show the checked-in TreeScope figures during the
presentation. The raw recording is available separately through the
[real-data instructions](../docs/real-data.md).

When it prints `True`, you can rerun the processing ahead of time in PowerShell.

```powershell
.\.venv\Scripts\canopy-odometry.exe --bag data/raw/treescope/WSF-19/input/cloud3.bag --topic /velodyne/cloud --out results/real/wsf19-rehearsal
```

After that command succeeds, crop the map and run analytics.

```powershell
.\.venv\Scripts\python.exe -c "import numpy as np; from canopy.io import crop_box; root='results/real/wsf19-rehearsal'; m=np.load(root+'/map.npy'); p=np.load(root+'/poses.npy')[:,:3,3]; np.save(root+'/map_crop.npy', crop_box(m, p.min(0)-[20,20,5], p.max(0)+[20,20,25]))"
.\.venv\Scripts\canopy-analyze.exe results/real/wsf19-rehearsal/map_crop.npy --out results/real/wsf19-rehearsal/analysis
```

The published TreeScope figures and numbers are from an earlier run.
Use that run's [documented settings and results](../docs/real-data.md) when
comparing a fresh run.

## C. Live walkthrough

1. Open the rehearsed survey map. The solid line shows the simulator's route,
   the dashed line shows the LiDAR estimate, and the blue crosses mark
   detected tree centres.
2. If there is time, rerun the first command in section A. Open `trees.csv`
   or `summary.json` and point out the six matched trees and the four quick
   navigation trials.
3. Show the saved TreeScope figures when discussing the real recording.
   Use the [outcomes document](../docs/OUTCOMES.md) for the full simulated
   benchmark and the [real-data notes](../docs/real-data.md) for TreeScope.

Keep the PNGs ready for the live walkthrough. The optional `--view 3d` window
uses OpenGL. If it fails to launch or exits with an error, the command creates
PNG figures. Rehearse the window on the exact laptop before using it live.

## D. Standalone odometry

With the environment activated, run:

```bash
canopy-odometry --synthetic 0 --out results/odom-synthetic
canopy-odometry --synthetic 0 --odometry all-returns --out results/odom-synthetic-baseline
```

The default synthetic command uses the same forest and ground-filtered
alignment as the full demo. Compare `odometry_drift_percent` in the two
`summary.json` files. The TreeScope and NPY input commands use all valid
returns for alignment.
