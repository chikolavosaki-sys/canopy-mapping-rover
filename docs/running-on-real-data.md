# Running on real data

Real datasets are not downloaded by this repository. Obtain access manually,
accept each dataset's terms, and keep the files under ignored paths such as
`data/treescope/`.

## Check local layouts

These commands only print official links and check folders that already exist:

```bash
python datasets/download_scripts/treescope.py
python datasets/download_scripts/digiforests.py
python datasets/download_scripts/shivalik.py
```

Use the validator functions from Python when checking a specific local root:

```bash
python - <<'PY'
from datasets.download_scripts.treescope import validate
print(validate("data/treescope"))
PY
```

## Run KISS-ICP on a ROS bag

Install the optional odometry dependencies in a virtual environment:

```bash
python -m pip install -e ".[core,odometry,dev]"
canopy-odometry \
  --bag data/raw/treescope/WSF-19/input/cloud3.bag \
  --topic /velodyne/cloud \
  --out results/odom-wsf19
```

`/velodyne/cloud` is the confirmed LiDAR topic for WSF-19 (see
`data/raw/treescope/WSF-19/topics.md`). For another bag, list its topics first.
The adapter uses `rosbags` and does not require a ROS installation. Outputs:
`trajectory.tum` (open with evo), `poses.npy`, `map.npy`, `summary.json`.
This run takes about 2 minutes on a laptop.

List available topics before choosing one:

```bash
python - <<'PY'
from canopy.io.bag_reader import list_topics
for topic in list_topics("data/raw/treescope/WSF-19/input/cloud3.bag"):
    print(topic)
PY
```

## Run analytics on a static cloud

```bash
canopy-analyze data/shivalik/plot.las \
  --config configs/default.yaml \
  --out results/shivalik-plot
```

## Common output formats

- Point clouds: `(N, 3)` float64 arrays.
- Trajectories: TUM rows containing timestamp, translation, and quaternion.
- Tree tables: CSV or JSON records with explicitly mapped `x`, `y`, and `dbh`
  fields.

The Shivalik and Weiser field-table schemas are not guessed here. Add a small
dataset-specific mapping after confirming the released column names.
