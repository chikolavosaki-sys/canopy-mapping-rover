# Dataset sufficiency

| Project need | Status | Reason |
|---|---|---|
| LiDAR odometry needs LiDAR plus IMU sequences | Covered (confirmed 2026-10-23) | TreeScope WSF-19 `cloud3.bag` (ROS1, 18.3 s) has `/velodyne/cloud` PointCloud2 at 5 Hz (x, y, z, intensity; no per-point time) and `/imu/imu` at 250 Hz. KISS-ICP stays primary; the IMU allows a later LiDAR-inertial comparison. See `docs/real-data.md`. |
| Canopy density by height layer | Covered | DigiForests, WildScenes, TreeScope, Shivalik, Weiser, and LiDAR-Forest provide 3D point data or simulated point data that can support a prototype after ground handling. |
| Stem detection and DBH with ground truth | Covered (TreeScope confirmed 2026-10-23) | TreeScope has annotated tree stems and field-measured diameters (VAT-0723: 76 trees, DBH in metres; WSF-19: 63 trees, DBH apparently in inches; VAT-0723 `.h5` has 145 frames of ground/trunk points); Shivalik and Weiser have measured DBH, although their point-label structure differs. Those static datasets are reserved for this analytics work, not odometry. |
| Ladder-fuel ground truth | Gap | No reviewed dataset has direct ladder-fuel labels. We will use a proxy based on point density in 1-4 m and 1-8 m height bands, validated against DigiForests shrub labels. DigiForests was unreachable on 2026-10-23, so this check has no real data yet. |
| Obstacle and terrain labels | Partly | WildScenes labels natural scene and terrain classes; LiDAR-Forest includes semantic ground/tree/stone labels. Rover-specific traversability labels are not documented. |
| Live navigation testing | Partly | The project will use repeated simulator runs for obstacle-avoidance success and collisions. There will be no real-rover field validation. |
| Data from an Indian forest | Covered | Shivalik is from forest regions in the Shivalik Range of northern Haryana, India, and includes 12 plots and 674 trees. |
| Satellite canopy context | Covered | GEDI, WorldCover, and Dynamic World provide possible context layers; exact access and licence details remain to be checked. |
| Water body masks | Partly | The Kaggle and S1S2-Water sources are candidates, but mask format and licensing need verification before use. |

## Verdict

These sources are enough to prototype forest analytics and test the recorded-data pipeline. TreeScope is the only reviewed source that clearly documents both LiDAR and raw IMU in the released contents, while WildScenes is the strongest continuous-traversal source but does not confirm raw IMU delivery. Simulator runs can measure navigation outcomes, but this project will not claim real-rover field validation. None of the reviewed sources has direct ladder-fuel labels, so that result must remain a proxy.

For implementation, use TreeScope first for LiDAR-inertial odometry. Use Shivalik, EuroSDR/FGI, and Weiser only for static forest analytics. Define ladder fuel as the 1-4 m and 1-8 m point-density proxy and compare it with DigiForests shrub labels. If the required IMU stream is unavailable, evaluate KISS-ICP as a LiDAR-only fallback; it avoids IMU integration but may be less robust during rapid motion or in geometrically sparse areas, and it adds setup and tuning effort. Navigation outcome testing will be simulator-only.
