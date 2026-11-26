# Running on real data

The project accepts a recorded LiDAR sequence for odometry and a point cloud for forest analytics. Start with the [installation guide](SETUP.md). Use the activated environment in Bash, or the corresponding `.venv\Scripts\python.exe`, `.venv\Scripts\canopy-odometry.exe`, and `.venv\Scripts\canopy-analyze.exe` commands in PowerShell.

## Get the TreeScope inputs

Obtain the files from TreeScope under its dataset terms. The [manifest](../data/MANIFEST.csv) lists the URL, byte count, and SHA-256 checksum of each file used in the team's earlier experiments. Save each file at `data/raw/<name>`, using its `name` from the manifest. For the WSF-19 mapping and analytics commands below, the only required download is `treescope/WSF-19/input/cloud3.bag`. The saved VAT-0723 classifier check uses different labelled files. [TreeScope data](https://treescope.org/data_overview/) · [Dataset attribution](../references/README.md)

On Windows, compare the output of this command with the manifest's `sha256` value:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'data/raw/treescope/WSF-19/input/cloud3.bag'
```

On Linux or WSL, use `sha256sum` on the same path. On macOS, use `shasum -a 256`. Raw data is ignored by Git. The [dataset catalogue](../datasets/README.md) lists other sources and their formats.

## Estimate the rover path and register the scans

```bash
canopy-odometry --bag data/raw/treescope/WSF-19/input/cloud3.bag --topic /velodyne/cloud --out results/runs/wsf19
```

`/velodyne/cloud` is the WSF-19 LiDAR topic. To inspect a different recording, call `canopy.io.bag_reader.list_topics` with its path. ROS installation is unnecessary because the package reads bags through `rosbags`. The output includes `trajectory.tum`, `poses.npy`, `map.npy`, and `summary.json`.

## Analyse the mapped forest

The WSF-19 experiment kept a crop around the trajectory. These commands reproduce that crop and analyse it using the installed ground classifier.

```bash
python -c "import numpy as np; from canopy.io import crop_box; root='results/runs/wsf19'; m=np.load(root+'/map.npy'); p=np.load(root+'/poses.npy')[:,:3,3]; np.save(root+'/map_crop.npy', crop_box(m, p.min(0)-[20,20,5], p.max(0)+[20,20,25]))"
canopy-analyze results/runs/wsf19/map_crop.npy --out results/runs/wsf19/analysis
```

The analytics folder contains tree measurements, vegetation density, the ladder-fuel CSV and heatmap, and the height-normalised cloud. [Earlier TreeScope run and limitations](real-data.md#first-full-pipeline-run-on-real-data-2026-10-23)

## Reproduce the classifier's real-data check

Download `treescope/VAT-0723/ground_truth/labels/VAT-0723M.h5` from the [manifest](../data/MANIFEST.csv) and place it at that path under `data/raw/`. Train the classifier in an environment with the `ml` extra:

```bash
python scripts/train_point_classifier.py --out results/runs/ml
```

The script reads the labelled VAT frames when the HDF5 file is present and reports recall separately for ground and stems. The [saved classifier benchmark](../results/ml/report.md) includes that check.

## Analyse a standalone point cloud

A registered or static cloud can go directly into the analytics. Replace the input path with a file you have.

```bash
canopy-analyze data/raw/shivalik/plot.las --config configs/default.yaml --out results/runs/static-plot
```

Point-cloud arrays use `(N, 3)` XYZ coordinates. TUM trajectories store timestamps, translations, and quaternions. Reference tree tables must identify their `x`, `y`, and `dbh` fields explicitly. Confirm dataset-specific field names and coordinate frames before comparing measurements.
