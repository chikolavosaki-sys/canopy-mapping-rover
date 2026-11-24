# Setup and test guide

Copy each block into the terminal **one at a time** and wait for it to finish
before the next. Total time: about 1-1.5 hours, mostly waiting for downloads.

- **Windows:** do Part A first, then everything else in the Ubuntu window.
- **Linux (Ubuntu/Debian):** start at Part B.
- Native Windows without WSL works only partly: see Part G.

## Part A. Windows only: install Ubuntu (WSL), once

Open **PowerShell as Administrator** (Start, type "PowerShell", right-click,
"Run as administrator"):

```powershell
wsl --install -d Ubuntu
```

Restart the PC. Open **Ubuntu** from the Start menu and choose a username and
password (the password does not show while typing; that is normal). Do
everything below **in the Ubuntu window**.

## Part B. One-time setup (about 15 minutes)

**B1. System packages** (asks for your Ubuntu password):

```bash
sudo apt-get update
sudo apt-get install -y git wget python3 python3-venv python3-pip build-essential \
  libusb-1.0-0 libgl1 libegl1 libgomp1 libx11-6
python3 --version
```

The last line must show **Python 3.10, 3.11 or 3.12**. If it shows 3.13 or
newer, run this and use `python3.12` instead of `python3` in B3:

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv
```

**B2. Download the code:**

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/chikolavosaki-sys/canopy-mapping-rover.git
cd canopy-mapping-rover
```

**B3. Python environment and libraries** (5-10 minutes):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[core,csf,odometry,eval,ml,dev]"
```

If the last command fails with a C++/compiler error on
`cloth-simulation-filter`, run this instead (ground detection then uses the
built-in RANSAC fallback; everything else is the same):

```bash
pip install -e ".[core,odometry,eval,ml,dev]"
```

**B4. Quick check:**

```bash
python -c "import canopy, open3d, kiss_icp, sklearn; print('Setup OK')"
```

Expected: `Setup OK`.

## Part C. The real forest data (about 0.8 GB)

Only the real-forest steps need this; the simulator, demo, navigation, ML
training and tests work without it. We use one dataset, **TreeScope**
(https://treescope.org, licence CC BY-NC-SA 4.0: non-commercial use, give
credit). Every file's URL, size and checksum is listed in `data/MANIFEST.csv`.
Never commit `data/` to git.

**Fastest: copy from a teammate.** Ask someone who has it to copy their
`canopy-mapping-rover/data/` folder (pendrive or Google Drive) and put it inside
your repo as `canopy-mapping-rover/data/` (from Ubuntu, `explorer.exe .` opens
the repo folder in Windows). Then skip to C2.

**C1. Or download it** (30-60 minutes; 4 files at a time; complete files are
skipped, so it is safe to run again):

```bash
cd ~/projects/canopy-mapping-rover
tail -n +2 data/MANIFEST.csv | cut -d, -f1,2,3 | tr ',' ' ' | \
  xargs -P 4 -n 3 sh -c '
    f="data/raw/$0"
    [ "$(stat -c %s "$f" 2>/dev/null)" = "$2" ] && exit 0
    mkdir -p "$(dirname "$f")"
    wget -c -q --tries=5 --timeout=60 -O "$f" "$1" || echo "FAILED: $1"'
echo "Download pass finished"
```

If any `FAILED:` lines appear, **run the same block again**: it only fetches
what is missing (the server sometimes drops requests).

**C2. Verify every file:**

```bash
tail -n +2 data/MANIFEST.csv | awk -F, '{print $4"  data/raw/"$1}' | sha256sum -c --quiet \
  && echo "ALL DATA OK"
```

Expected: `ALL DATA OK`. If it lists files instead, run C1 again, then C2.

## Part D. Test everything (about 10 minutes)

Start **every** new terminal with:

```bash
cd ~/projects/canopy-mapping-rover && source .venv/bin/activate
```

| Step | Command | Expected result |
|---|---|---|
| D1. Automatic tests (~2 min) | `pytest -q` | Ends with `passed` (67 tests; a few "skipped" are fine) |
| D2. Synthetic demo (~2 min) | `python scripts/run_all.py --seed 0 && cat results/demo/report.md` | Exact-pose map: Trees detected **6**, recall **1.0000** |
| D3. Figures (~15 s) | `python scripts/show_demo.py` | `Wrote forest_map.png, lidar_scan.png, odometry.png` |
| D4. ML model (~2 min) | `python scripts/train_point_classifier.py --out results/ml-rehearsal` | Writes a new report and figures without replacing the saved benchmark |
| D5. Real forest: odometry (~3 min, needs Part C) | block below | `"frames": 92`, `path_length_m` about 8.6 |
| D6. Real forest: analytics (~1 min) | block below | `"n_stems": 5`, `"ladder_cells_above_0_5": 333` |
| D7. All slide images (~5 min) | `bash presentation/prepare.sh` | Lists the images in `presentation/images/` |
| D8. 3-D view | `python scripts/show_demo.py --view 3d` | A window opens; drag to rotate, `Q` closes |

The [saved ML benchmark](../results/ml/report.md) reports 89.2% accuracy on
unseen simulated forests and includes the TreeScope check. A local rerun skips
the TreeScope check when the labelled frames are absent.

**D5 and D6, real forest:**

```bash
canopy-odometry --bag data/raw/treescope/WSF-19/input/cloud3.bag \
  --topic /velodyne/cloud --out results/real/wsf19

python -c "import numpy as np; from canopy.io import crop_box; \
m=np.load('results/real/wsf19/map.npy'); p=np.load('results/real/wsf19/poses.npy')[:,:3,3]; \
np.save('results/real/wsf19/map_crop.npy', crop_box(m, p.min(0)-[20,20,5], p.max(0)+[20,20,25]))"

canopy-analyze results/real/wsf19/map_crop.npy --out results/real/wsf19/analysis
```

To see results in Windows: `explorer.exe results` opens the folder.

## Part E. Presentation day

```bash
cd ~/projects/canopy-mapping-rover && source .venv/bin/activate
git pull                              # latest code
bash presentation/live_demo.sh        # press Enter for each step
```

Full checklist: [`presentation/05-presentation-day.md`](../presentation/05-presentation-day.md).

## Part F. If something goes wrong

| Error | Fix |
|---|---|
| `ModuleNotFoundError: canopy` (or `open3d`, `sklearn`) | `cd ~/projects/canopy-mapping-rover && source .venv/bin/activate` |
| `libusb-1.0.so.0` / `libEGL.so.1` not found | Run B1 again |
| `pip` fails on `cloth-simulation-filter` | Use the install command without `csf` (B3) |
| 3-D window does not open, or `MESA` / `libEGL` warnings | Put `LIBGL_ALWAYS_SOFTWARE=1 ` in front of the command. On old Windows 10 without WSLg, 3-D windows do not work: use the PNG figures |
| `bag file ... not found` | Part C is missing or the files are in the wrong place: run C1 and C2 |
| Download shows `FAILED` or 403 | Run C1 again later; it resumes |
| A command seems stuck | It is working: the demos print nothing for 1-2 minutes. Do not press `Ctrl+C` |

## Part G. Native Windows without WSL (not recommended)

In PowerShell, with Python 3.12 from python.org ("Add python.exe to PATH"
ticked) and Git for Windows installed:

```powershell
cd $HOME\Documents
git clone https://github.com/chikolavosaki-sys/canopy-mapping-rover.git
cd canopy-mapping-rover
python -m venv .venv
.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -e ".[core,odometry,eval,ml,dev]"
pytest -q
python scripts/run_all.py --seed 0
```

These work on native Windows: tests, the synthetic demo, figures, ML and the 3-D
view. These do not: the data download (Part C), the real-forest crop step,
`prepare.sh` and `live_demo.sh`. Use WSL for those.
