# Architecture

The rover records 3D LiDAR and IMU data. LiDAR-inertial odometry (for example FAST-LIO2 or LIO-SAM) estimates the rover motion and registers scans into one point cloud. We then use the same registered cloud in two branches.

```text
3D LiDAR + IMU recordings
             |
             v
 LiDAR-inertial odometry (FAST-LIO2 or LIO-SAM)
             |
      registered point cloud
          /              \
         v                v
 Navigation branch     Forest analytics branch
 angular sectors       remove ground
 FORWARD/TURN/STOP     height-layer density
 obstacle decisions    stems, shrubs, DBH
```

The navigation branch divides nearby points into angular sectors and chooses a simple state: `FORWARD`, `TURN`, or `STOP`. The analytics branch removes or models the ground, counts points by height layer, detects stems, and estimates DBH. An optional aerial/satellite layer adds NDVI, GEDI canopy height, or tree-count context; it is not a replacement for below-canopy measurements. The water-body module is separate.
