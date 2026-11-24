# Canopy Mapping Rover

Canopy Mapping Rover is a BIT Mesra B.Tech CSE minor project. We are building and evaluating a simulated ground rover that uses 3D LiDAR to map forest structure from below the canopy. The map should help us estimate vegetation density at different heights, ladder fuels, tree stems, and trunk diameter at breast height (DBH). A drone or satellite usually cannot see these features through leaves. The project runs on recorded datasets plus a simulator; it does not require real rover hardware.

## Team

| Member | Role | Main areas |
|---|---|---|
| Prithvi (`@chikolavosaki-sys`) | Repository owner | Forest analytics and final report (PROPOSED) |
| Anwita (GitHub handle TODO) | LiDAR and navigation | LiDAR odometry (KISS-ICP) and simulated rover navigation |
| Prajjwal (`@praj1221`) | Simulator and evaluation | Simulator world and evaluation scripts |

The proposed ownership change is pending team confirmation. The water body module is paused, not deleted, and may return as a weeks 10-12 stretch goal.

## Quick links

- **[Setup and test guide](docs/SETUP.md)**: copy-paste install, data download and tests (Windows and Linux)
- [Presentation kit](presentation/README.md)
- [System architecture](docs/architecture.md)
- [Dataset list](datasets/README.md)
- [Dataset sufficiency](datasets/SUFFICIENCY.md)
- [Outcome metrics](docs/OUTCOMES.md)
- [Simulator options](docs/simulator-options.md)
- [Real data downloaded so far](docs/real-data.md)
- [Running on real data](docs/running-on-real-data.md)
- [Glossary](docs/glossary.md)
- [Design decisions](docs/decisions.md)
- [References](references/README.md)

## Quick start

New here? Follow **[docs/SETUP.md](docs/SETUP.md)** step by step.

The demo uses a simulated forest, so you can run it without downloading a dataset.
On Windows, run these commands from PowerShell in the project folder.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[core,odometry,eval,ml,dev]"
.\.venv\Scripts\python.exe scripts/run_all.py --seed 0 --fast --out results/semester-demo
.\.venv\Scripts\python.exe -m pytest -q
```

Open `results/semester-demo/survey_map.png` to see the rover path, detected
trees and ladder-fuel proxy on one map. The same folder has `trees.csv` for
trunk measurements, `summary.json` for metrics and `report.md` for the
run summary. You can pass the registered point cloud in `map.npy` to
`canopy-analyze` to rerun forest analytics on it. Use a different `--out`
folder for each run you want to keep.

On macOS or Linux, use the following commands.

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[core,odometry,eval,ml,dev]"
pytest -q && ruff check .
python scripts/run_all.py --seed 0 --fast --out results/semester-demo
python scripts/show_demo.py                 # figures in results/demo/figures/
python scripts/show_demo.py --view 3d       # rotate the scanned forest in a 3-D window
python scripts/train_point_classifier.py    # train and evaluate the point classifier
```

The demo estimates motion with ground-filtered LiDAR returns by default.
Use `--odometry all-returns` and a separate output folder to reproduce the
original alignment method. The report records which method ran. Omit
`--fast` to run the full 80-trial navigation benchmark.

`canopy-odometry --synthetic 0 --out results/odom-synthetic` runs just
odometry on the same demo forest. Its summary includes final drift and the
alignment mode. Recorded bags and NPY scans use all valid returns.

For the live demo, follow the [presentation walkthrough](presentation/03-demo-commands.md).
It uses the generated PNGs and the saved TreeScope figures.

All tunable numbers live in `configs/default.yaml`. The project uses RANSAC
for ground classification when the optional `csf` extra is absent. On WSL,
Open3D also needs `sudo apt-get install -y libusb-1.0-0`.

## How we work

- Use branches named `<name>/<task>`, such as `prithvi/forest-density`.
- Record weekly work in `progress/<name>/`.
- Do not commit raw datasets. Use scripts in `datasets/download_scripts/` and document dataset links instead.
- Explain LiDAR and SLAM code in plain language because the team is learning these topics.
- Plan around measurable results, not only whether code runs.
