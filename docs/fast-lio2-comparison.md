# Optional: FAST-LIO2 comparison (Docker)

> **Status: untested plan.** FAST-LIO2 is not a project dependency. KISS-ICP
> is the primary odometry. Do this only if time permits, and report results
> as a comparison between two estimates. Neither one is ground truth.

FAST-LIO2 (https://github.com/hku-mars/FAST_LIO) is C++/ROS1 and fuses LiDAR
with the IMU. It runs in a ROS Noetic container so nothing touches the host.

## 1. Build an image

```dockerfile
# docker/fast-lio2.Dockerfile
FROM ros:noetic
RUN apt-get update && apt-get install -y git libpcl-dev libeigen3-dev \
    ros-noetic-pcl-ros ros-noetic-eigen-conversions && rm -rf /var/lib/apt/lists/*
WORKDIR /catkin_ws/src
RUN git clone https://github.com/Livox-SDK/livox_ros_driver.git && \
    git clone --recursive https://github.com/hku-mars/FAST_LIO.git
WORKDIR /catkin_ws
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && catkin_make"
```

```bash
docker build -f docker/fast-lio2.Dockerfile -t fast-lio2 .
```

## 2. Configure it for WSF-19

Edit `FAST_LIO/config/velodyne.yaml` in the container:

| Setting | Value | Source |
|---|---|---|
| `lid_topic` | `/velodyne/cloud` | `data/raw/treescope/WSF-19/topics.md` |
| `imu_topic` | `/imu/imu` | same |
| `scan_line` | number of LiDAR rings | TODO: check `VAT-0723M-os-metadata.json` / the TreeScope sensor page |
| `extrinsic_T`, `extrinsic_R` | LiDAR to IMU transform | TODO: read the bag's `/tf_static` |

**Known risk:** WSF-19 frames contain only `x, y, z, intensity`, without the
`ring` and `time` fields FAST-LIO's Velodyne reader expects. Without them its
per-point time estimate (and therefore deskewing) may be wrong. Check this
before trusting any result.

## 3. Run and export

```bash
docker run --rm -it -v "$PWD/data:/data" -v "$PWD/results:/results" fast-lio2 bash
# inside the container:
source /catkin_ws/devel/setup.bash
roslaunch fast_lio mapping_velodyne.launch rviz:=false &
rosbag record -O /results/fastlio_odom.bag /Odometry &
rosbag play /data/raw/treescope/WSF-19/input/cloud3.bag
```

Convert `/Odometry` to TUM with `canopy.io.bag_reader.iter_odometry` and
`canopy.io.tum.write_tum`, then compare it with KISS-ICP using evo, e.g.
`evo_ape tum kiss.tum fastlio.tum -a`.
