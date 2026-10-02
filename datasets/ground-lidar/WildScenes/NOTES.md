# WildScenes notes

- **LiDAR sensor model:** Velodyne Puck, 16 beams, mounted on a rotating motor; the Puck is inclined at 45 degrees and the motor rotates at 0.5 Hz. [Official website](https://csiro-robotics.github.io/WildScenes)
- **IMU included:** **NOT STATED IN SOURCES** as a released raw stream. The dataset provides SLAM-derived 6-DoF poses, but that does not prove raw IMU delivery. [Official website](https://csiro-robotics.github.io/WildScenes) [GitHub README](https://github.com/csiro-robotics/WildScenes/blob/main/README.md)
- **Continuous walking or driving sequences:** Yes: five traversals contain over 21 km and 300 minutes of continuous LiDAR traversal. Whether the operator walked or drove is **NOT STATED IN SOURCES**. [Official website](https://csiro-robotics.github.io/WildScenes)
- **Point-cloud format:** PLY files are used for full 360-degree point clouds; the repository also describes 3D labelled point clouds. [GitHub README](https://github.com/csiro-robotics/WildScenes/blob/main/README.md)
- **Labels:** Dense 2D and 3D natural-scene labels, including tree foliage, tree trunk, and terrain classes such as dirt and mud. Shrub, stem-as-a-separate-label, and DBH labels are **NOT STATED IN SOURCES**. [Official website](https://csiro-robotics.github.io/WildScenes)
- **Region and forest type:** Venman National Park and Karawatha Forest Park near Brisbane, Australia; Australian natural forests. [Official website](https://csiro-robotics.github.io/WildScenes)
- **Licence:** Non-commercial access terms are listed on the CSIRO data record; a more specific licence name is **NOT STATED IN SOURCES**. [CSIRO data record](https://data.csiro.au/collection/csiro:61541)
- **Download size:** **NOT STATED IN SOURCES**. [CSIRO data record](https://data.csiro.au/collection/csiro:61541) [GitHub README](https://github.com/csiro-robotics/WildScenes/blob/main/README.md)

Paper: [IJRR paper](https://doi.org/10.1177/02783649241278369).
