# Setup and verification

Use Git and Python 3.10 or 3.11, the versions tested by GitHub Actions. Run the commands from the folder containing `pyproject.toml`. The simulated demo, navigation benchmark, and automated tests use local fixtures or generated data. The TreeScope downloads are needed for real-data reruns.

## Install on Windows

Open PowerShell in the clone. Check `python --version` before creating the environment, or use `py -3.11 -m venv .venv` if multiple Python versions are installed.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[core,odometry,ml,dev]"
.\.venv\Scripts\python.exe -c "import canopy.config, open3d, kiss_icp, sklearn; print('Setup OK')"
```

These commands use the interpreter directly, so changing PowerShell's execution policy is unnecessary. To enable the optional cloth simulation filter (CSF) on Windows, install Visual Studio Build Tools with the **Desktop development with C++** workload and a Windows SDK, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[core,csf,odometry,ml,dev]"
.\.venv\Scripts\python.exe -c "import CSF; print('CSF available')"
```

If the CSF build fails, the first install command provides the built-in RANSAC ground classifier. Each demo report records the backend used.

## Install on Linux, WSL, or macOS

On Ubuntu or Debian, install the build and Open3D runtime libraries. On Windows with WSL, run these commands inside the Linux distribution.

```bash
sudo apt-get update
sudo apt-get install -y git python3-venv build-essential libusb-1.0-0 libgl1 libegl1 libgomp1 libx11-6
```

On macOS, start with a Git installation and Python 3.10 or 3.11, then use the virtual-environment commands below. Install the Xcode Command Line Tools if a dependency needs a local compiler.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[core,csf,odometry,ml,dev]"
python -c "import canopy.config, open3d, kiss_icp, sklearn; print('Setup OK')"
```

If CSF fails to build, repeat the install with `.[core,odometry,ml,dev]` to use RANSAC.

## Run the checks and demo

**PowerShell**

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/run_all.py --seed 0 --fast --out results/runs/demo
.\.venv\Scripts\python.exe scripts/show_demo.py --out results/runs/demo/figures
```

**Bash or Zsh with the environment activated**

```bash
python -m ruff check .
python -m pytest -q
python scripts/run_all.py --seed 0 --fast --out results/runs/demo
python scripts/show_demo.py --out results/runs/demo/figures
```

The fast run writes `survey_map.png`, `trees.csv`, `summary.json`, and `report.md` and runs four navigation scenarios. Use `python scripts/run_all.py --seed 0 --out results/runs/benchmark` for the 80-trial benchmark and see [outcomes](OUTCOMES.md) for the reference results. Use the direct virtual-environment interpreter on Windows.

The [CI workflow](../.github/workflows/ci.yml) runs lint and tests on Linux with CSF and on Windows with the RANSAC fallback. Linux jobs also install the wheel and run the installed odometry command from outside the checkout.

For the optional 3D view, add `--view 3d` to `scripts/show_demo.py`. A display and working OpenGL are needed for interactive rendering. If that view fails to launch, the script can fall back to saved PNGs.

## Optional data and ML workflows

- **Recorded LiDAR and static clouds.** Follow the [real-data guide](running-on-real-data.md) for the download manifest, local layout, and processing commands.
- **Classification.** Run `python scripts/train_point_classifier.py --out results/runs/ml`. The [saved ML report](../results/ml/report.md) includes accuracy on unseen synthetic forests and the VAT-0723 recall check. The local run can include that check if the labelled TreeScope frames are available.
- **Presentation.** Follow the [demo walkthrough](../presentation/03-demo-commands.md). It uses the synthetic survey and the saved TreeScope figures.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `ModuleNotFoundError` for `canopy`, `open3d`, or `kiss_icp` | Run from the repository folder and use the interpreter you installed the extras into. |
| `cloth-simulation-filter` cannot build | Install the platform build tools or use the RANSAC install command above. |
| `libusb-1.0.so.0` or `libEGL.so.1` is missing | Install the Ubuntu/Debian runtime libraries above. |
| OpenGL warnings on WSL or a headless machine | Run the PNG example, or try `LIBGL_ALWAYS_SOFTWARE=1` in WSL before opening the viewer. |
| Missing ROS bag or labels | Check the paths and checksums in the [real-data guide](running-on-real-data.md). |
