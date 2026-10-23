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
  --bag data/treescope/VAT-0723/recording.bag \
  --topic /points \
  --out results/treescope-vat0723
```

Replace `/points` with the actual PointCloud2 topic after inspecting the bag.
The adapter uses `rosbags` and does not require a ROS installation.

List available topics before choosing one:

```bash
python - <<'PY'
from canopy.io.bag_reader import list_topics
for topic in list_topics("data/treescope/VAT-0723/recording.bag"):
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
