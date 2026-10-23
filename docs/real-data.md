# Real data (Tier 1)

Downloaded on 2026-10-23. Files live under `data/raw/` (git-ignored); only
`data/MANIFEST.csv` (name, url, bytes, sha256, date for all 4,328 files) is
committed. Re-check with `python scripts/inspect_data.py`.

## What was downloaded

| Dataset | Files | Size | Outcome metric it serves |
|---|---|---:|---|
| TreeScope VAT-0723 metadata | `metadata/VAT-0723.json`, `VAT-0723M-os-metadata.json` | 15 KB | Sensor/topic context |
| TreeScope VAT-0723 field DBH | `ground_truth/measurements/VAT-0723M-gt.json` + 6 sequence maps | 1.1 MB | DBH RMSE vs field tape (real data) |
| TreeScope VAT-0723 tree clouds | 77 × `ground_truth/pcds/VAT-0723M-0x_treeN.pcd` | 9.5 MB | DBH circle fit vs measured DBH |
| TreeScope VAT-0723 labels | `ground_truth/labels/VAT-0723M.h5` | 103 MB | Ground segmentation and stem detection precision/recall |
| TreeScope WSF-19 recording | `input/cloud3.bag` | 618 MB | Odometry drift; end-to-end map → stems/density |
| TreeScope WSF-19 labels | 91 × `ground_truth/scans/cloud3_N/` + `README.txt` | 70 MB | Tree detection recall and DBH on a real sequence |
| **Total** | 4,328 files | **about 0.80 GB** | |

Not downloaded:
- **DigiForests M1:** `ipb.uni-bonn.de` refused connections on 2026-10-23,
  so the ladder-fuel vs shrub-label check has no real data yet. Retry later.
- **Shivalik:** the Zenodo files are restricted, and access must be requested.
  See `datasets/README.md`.
- **Tier 2** (VAT-0723M-02 processed bag, DigiForests C1): not approved.

## WSF-19 `cloud3.bag`

ROS1 bag, 18.3 s long. Full topic table: `data/raw/treescope/WSF-19/topics.md`.

| Topic | Type | Messages | Rate |
|---|---|---:|---:|
| `/velodyne/cloud` | `sensor_msgs/PointCloud2` | 92 | 5.0 Hz |
| `/imu/imu` | `sensor_msgs/Imu` | 4,573 | 250 Hz |
| `/imu/filter`, `/imu/magnetic_field`, `/imu/pressure` | IMU extras | about 4,572 each | 250 Hz |
| `/camera/...` (colour, aligned depth, info) | `Image`, `CameraInfo` | 543 each | 29.7 Hz |
| `/tf_static` | `TFMessage` | 1 | — |

- **LiDAR frame:** `frame_id = velodyne`, a single row (`height = 1`), dense,
  about 54,000 points per frame within ±96 m.
- **LiDAR fields:** `x, y, z, intensity`, all float32. There is **no per-point
  time field**, so KISS-ICP cannot deskew motion within a sweep. At 5 Hz and
  walking speed this should be a small error. A sample frame is saved to
  `data/samples/WSF-19_frame0.ply`.
- **IMU:** `frame_id = imu`; gravity shows up on +z (about 9.80 m/s²). This
  means a LiDAR-inertial comparison is possible later.

## WSF-19 ground truth (`ground_truth/scans/cloud3_N/`)

There are 91 scan folders (`cloud3_0` … `cloud3_90`, none missing), roughly one
per LiDAR frame (the bag has 92). Each folder contains:

- **`single_dbh_labels.txt`:** one row per tree with columns
  `x y z dbh difficulty`. Difficulty takes the values {1, 2, 3}. **Every scan
  lists the same 63 trees at the same coordinates**, so this is one tree table
  for the whole sequence, in one map frame.
- **`single/cloud3_N_tree_<i>.pcd`:** clouds for the trees visible in that scan.
  `<i>` is the row index in the table.
- **`all/`:** `*_all_points.pcd` / `.labels` and `*_trees_only.pcd` / `.labels`.
  The labels are plain text with one integer per point (0 = background,
  otherwise a tree index). The folder also has `*_bad_trees.pcd`.

## VAT-0723 ground truth

- **`VAT-0723M-gt.json`:** 76 trees keyed exactly by the `.pcd` filename stem,
  e.g. `VAT-0723M-03_tree8`. Every tree has `DBH` in metres (0.20–0.45,
  mean 0.31). Most also have `THT` (74 trees, probably total height) and `CH`
  (73, probably crown height); 11 have crown widths `CW1`/`CW2`. Trees per
  sequence: M-01 11, M-02 7, M-03 15, M-04 7, M-05 25, M-06 11.
- **Tree `.pcd` files:** binary PCD v0.7 with `x y z` float32, about
  11,000–24,000 points per tree. 76 of 77 match a JSON key; only
  `VAT-0723M-05_tree39` has no measurement.
- **`VAT-0723M.h5`:** 145 groups, each named by a nanosecond timestamp and
  spanning 78 s at about 0.5 s apart. Each group holds two float64 `(N, 3)`
  arrays: `ground_<t>` (about 17,000 points) and `tree_trunks_<t>` (about
  13,500 points). There are no attributes. The timestamps fall inside one
  processed sequence, and we did not download the bag they come from.

## Surprises and open questions

1. **WSF-19 DBH is almost certainly in inches, not metres or cm.** The table
   gives 2.8–17.7. Circles fitted to tree clouds in scans 0, 45 and 90 come out
   2.45–2.53 times larger in cm, and 1 inch is 2.54 cm. The README does not
   state the unit. Adapters must convert with `× 0.0254` and say so.
2. **WSF-19 scan clouds are already in a shared map frame.** Tree centres
   fitted from scans 0, 45 and 90 land within about 0.2 m of the table
   positions. Each scan is a ±20 m crop that moves with the rover (its y-range
   shifts by about 7 m over the run). The crop centre therefore gives a rough
   **reference trajectory**, though it is not true ground truth.
3. **The sequence is short.** 18.3 s and 92 frames give a few metres of motion,
   which is enough for start-to-end drift and a small map but not for
   loop-closure drift.
4. **Tree clouds are not height-normalised.** VAT-0723 tree clouds run from
   about −3.5 to +6.4 m in z, and WSF-19 is similar. The DBH slice at
   1.2–1.4 m needs the local ground found first (the VAT `.h5` ground points
   and WSF `all_points` can provide it).
5. **The VAT-0723 field DBH is from a different place than the WSF-19 bag.**
   The VAT field DBH (metres) belongs to the VAT-0723 sequences, whose raw bags
   we did not download. WSF-19 is our only real sequence that has its own DBH
   table (in inches).
6. **Environment:** Open3D needs the system library `libusb-1.0-0` on WSL
   (`sudo apt-get install -y libusb-1.0-0`). Without it, `.pcd` and `.ply`
   I/O fails.
7. **Server behaviour:** `tnl.treescope.org` returns 403 to Python's default
   user agent and drops some requests when 8 run in parallel. Twelve files
   failed and succeeded on a retry with 3 parallel jobs. No checksums are
   published, so the sha256 values in the manifest are our own.

## Metric coverage after Tier 1

| Outcome metric | Real data now |
|---|---|
| Odometry drift / ATE | WSF-19 `cloud3` (start-to-end drift; rough reference from scan crops) |
| Tree recall + DBH RMSE | WSF-19 (63 trees, inches) and VAT-0723 (76 trees, metres, per-tree clouds) |
| Ground / stem segmentation | VAT-0723 `.h5` (145 labelled frames) |
| Ladder fuel vs shrub labels | **None yet:** blocked on DigiForests |
| Navigation | Simulator only (by design) |
