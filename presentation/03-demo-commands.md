# Commands: preparing, the live demo, and fallbacks

All commands run in the Ubuntu (WSL) terminal from the repository folder.
Start every session with:

```bash
cd ~/projects/Minor_project/canopy-mapping-rover
source .venv/bin/activate
```

## A. One-time setup on a new laptop

```bash
git clone https://github.com/chikolavosaki-sys/canopy-mapping-rover.git
cd canopy-mapping-rover
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[core,odometry,eval,dev]"
sudo apt-get install -y libusb-1.0-0          # Open3D needs this on WSL
pytest -q                                     # expect: all tests pass (about 2 min)
```

The real-forest data is **not** in git. Copy the `data/` folder from Prithvi's
laptop, or download it again using the URLs in `data/MANIFEST.csv`
(see `docs/real-data.md`). Without it, everything except the real-forest part works.

## B. Real forest run (once, about 4 minutes; needs `data/`)

```bash
# 1. track the rover through the real recording and build the map
canopy-odometry --bag data/raw/treescope/WSF-19/input/cloud3.bag \
  --topic /velodyne/cloud --out results/real/wsf19

# 2. keep the dense part of the map (the drive +- 20 m)
python -c "import numpy as np; from canopy.io import crop_box; \
m=np.load('results/real/wsf19/map.npy'); p=np.load('results/real/wsf19/poses.npy')[:,:3,3]; \
np.save('results/real/wsf19/map_crop.npy', crop_box(m, p.min(0)-[20,20,5], p.max(0)+[20,20,25]))"

# 3. ground, trees, ladder fuel
canopy-analyze results/real/wsf19/map_crop.npy --out results/real/wsf19/analysis
```

Expected: step 1 prints `"frames": 92`, path about 8.6 m; step 3 prints
`"n_stems": 5` and `"ladder_cells_above_0_5": 333`.

## C. Prepare all slide images (one day before, about 5 minutes)

```bash
bash presentation/prepare.sh
explorer.exe "$(wslpath -w presentation/images)"    # opens the folder in Windows
```

It re-runs the synthetic demo, redraws all figures, draws the real-forest
pictures (if section B was done), and copies everything into
`presentation/images/`:

| Image | Slide |
|---|---|
| `sim_lidar_scan.png` | 5, 7 |
| `sim_odometry.png` | 7 |
| `real_side_view.png` | 8 |
| `real_top_views.png` | 1, 9, 13 |
| `sim_forest_map.png` | 5, 10 |
| `sim_ladder_fuel.png` | 12 |
| `real_ladder_fuel.png` | 5, 13 |

The numbers for slide 12 are in `results/demo/report.md`; for slide 13 in
`docs/real-data.md`. If you re-ran anything, re-check them against the slides.

## D. Live demo (during the presentation, 1-2 minutes)

Open the terminal **before** you start presenting, activate the environment,
and run each command once beforehand so files are cached.

**1. The simulated forest in 3-D** (window opens in about 15 s):
```bash
python scripts/show_demo.py --view 3d
```
Say: "Each dot is one laser hit: blue trunks, orange shrubs, green rocks, grey
ground. The blue line is the rover's true path, the orange one what odometry
estimated." Drag to rotate, scroll to zoom, press `Q` to close.

**2. The real forest, only the understorey layer (0.3-4 m)**:
```bash
LIBGL_ALWAYS_SOFTWARE=1 python - <<'PY'
import numpy as np, open3d as o3d, matplotlib.pyplot as plt
p = np.load("results/real/wsf19/analysis/normalised_cloud.npy")
under = p[(p[:, 2] > 0.3) & (p[:, 2] < 4.0)]
pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(under))
pc.colors = o3d.utility.Vector3dVector(plt.cm.viridis(under[:, 2] / 4.0)[:, :3])
o3d.visualization.draw_geometries([pc], window_name="Real forest: understorey 0.3-4 m")
PY
```
Say: "This is the real forest with everything above 4 m removed: the columns are
trunks and the clumps are shrubs and low branches, the ladder fuel."

**3. (Only if there is time) run the analytics live on the real map** (about 1 min):
```bash
canopy-analyze results/real/wsf19/map_crop.npy --out /tmp/live_demo
```
Say: "This is the same command used for the results slide; it finds the ground,
the trees and the ladder-fuel map from 2.7 million points."

## E. If something fails

| Problem | What to do |
|---|---|
| 3-D window does not open, or `libEGL` / `MESA` warnings and nothing appears | Add `LIBGL_ALWAYS_SOFTWARE=1 ` in front of the command. If it still fails, show the pictures in the slides instead (they are the same data). |
| `ModuleNotFoundError: canopy` | You forgot `source .venv/bin/activate`, or you are not in the repo folder. |
| `ImportError: libusb-1.0.so.0` | `sudo apt-get install -y libusb-1.0-0` |
| `No such file ... cloud3.bag` or `normalised_cloud.npy` | The `data/` folder or section B is missing on this laptop: use the pictures. |
| A command takes too long | Press `Ctrl+C` and continue with the slides. Never wait on stage. |

## F. Checks you can show if asked "does the code really work?"

```bash
pytest -q          # 63 automatic tests (about 2 min); also run on GitHub on every push
ruff check .       # code style check
gh run list --limit 3   # green CI runs on GitHub (needs the gh CLI logged in)
```
