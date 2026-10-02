# Dataset opening priority

These are reading priorities only. Do not download files until the team agrees on an access plan.

## Prajwal

1. **LiDAR-Forest (Purdue):** Start here because it is simulated and has semantic/instance records that can seed the simulator test.
2. **TreeScope:** Read next because its raw LiDAR and IMU ROS bags support the primary odometry test and its DBH/stem ground truth supports evaluation.

## Anwita

1. **TreeScope:** Use first for LiDAR-inertial odometry because raw LiDAR and IMU are confirmed in the released contents.
2. **WildScenes:** Use next for long continuous traversals and pose/semantic evaluation, while noting that raw IMU delivery is not confirmed.

## Prithvi

1. **DigiForests:** Read first for tree, shrub, ground, and stem/crown labels and for validating the ladder-fuel proxy against shrub labels.
2. **Shivalik Range Tree LiDAR:** Use for Indian-forest context and field DBH measurements; it is a static scan dataset.
3. **Weiser et al.:** Use for multi-platform forest point clouds and field DBH measurements; it is not an odometry dataset.
