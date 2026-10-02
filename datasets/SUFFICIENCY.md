# Dataset sufficiency

| Project need | Status | Reason |
|---|---|---|
| LiDAR odometry needs LiDAR plus IMU sequences | Partly | WildScenes has traversal and 6-DoF ground truth, and DigiForests has backpack LiDAR, but IMU availability and exact synchronized streams still need checking. |
| Canopy density by height layer | Covered | Point clouds from forest scenes can support a prototype height-bin calculation after ground removal. |
| Stem detection and DBH with ground truth | Partly | TreeScope explicitly provides stem labels and measured diameters; coverage may not match a natural Indian forest. |
| Ladder-fuel ground truth | Gap | No listed source directly labels ladder fuels as a target class. |
| Obstacle and terrain labels | Partly | WildScenes has natural-scene semantic labels; rover-specific obstacle and traversability labels are not guaranteed. |
| Live navigation testing | Gap | Public recordings can test algorithms, but they do not replace our rover, sensor, and field trials. |
| Data from an Indian forest | Partly | The Shivalik source is intended for an Indian forest context, but its exact fields and access details are UNVERIFIED here. |
| Satellite canopy context | Covered | GEDI, WorldCover, and Dynamic World provide possible context layers; exact access and licence details remain to be checked. |
| Water body masks | Partly | The Kaggle and S1S2-Water sources are candidates, but mask format and licensing need verification before use. |

## Verdict

Yes, these sources are enough to build and test the software pipeline on recorded data. They are not enough to prove reliable live driving: that requires our own hardware and field recordings. There are also no direct ladder-fuel labels in the planned list, so ladder-fuel results should be described as a proxy or an experiment unless we create and validate labels ourselves.
