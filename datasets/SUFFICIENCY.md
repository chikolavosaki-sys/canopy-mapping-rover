# Dataset sufficiency

| Project need | Status | Reason |
|---|---|---|
| LiDAR odometry needs LiDAR plus IMU sequences | Gap | TreeScope explicitly documents raw LiDAR and IMU in ROS bags, but fixed sequence durations are not stated. The other six sources do not confirm a released raw IMU stream; WildScenes has continuous LiDAR traversal and poses, but not confirmed raw IMU. |
| Canopy density by height layer | Covered | DigiForests, WildScenes, TreeScope, Shivalik, Weiser, and LiDAR-Forest provide 3D point data or simulated point data that can support a prototype after ground handling. |
| Stem detection and DBH with ground truth | Covered | TreeScope has annotated tree stems and field-measured diameters; Shivalik and Weiser have measured DBH, although their point-label structure differs. |
| Ladder-fuel ground truth | Gap | None of the seven reviewed sources documents a direct ladder-fuel label. |
| Obstacle and terrain labels | Partly | WildScenes labels natural scene and terrain classes; LiDAR-Forest includes semantic ground/tree/stone labels. Rover-specific traversability labels are not documented. |
| Live navigation testing | Gap | Public recordings can test algorithms, but they do not replace our rover, sensor, and field trials. |
| Data from an Indian forest | Covered | Shivalik is from forest regions in the Shivalik Range of northern Haryana, India, and includes 12 plots and 674 trees. |
| Satellite canopy context | Covered | GEDI, WorldCover, and Dynamic World provide possible context layers; exact access and licence details remain to be checked. |
| Water body masks | Partly | The Kaggle and S1S2-Water sources are candidates, but mask format and licensing need verification before use. |

## Verdict

These sources are enough to prototype forest analytics and test parts of the pipeline. TreeScope is the only reviewed source that clearly documents both LiDAR and raw IMU in the released contents, while WildScenes is the strongest continuous-traversal source but does not confirm raw IMU delivery. That is not enough to claim a broadly validated LiDAR-inertial odometry dataset, and none of the reviewed sources has direct ladder-fuel labels. Live driving still requires our own hardware and field recordings; ladder-fuel results must be treated as a proxy or a separately labelled experiment.
