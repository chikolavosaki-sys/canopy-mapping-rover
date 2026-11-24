# References and data credits

## Methods and software

- **KISS-ICP.** Vizzo et al. (2023), *KISS-ICP: In Defense of Point-to-Point ICP*. The project uses KISS-ICP for frame-to-frame LiDAR odometry. [Paper](https://doi.org/10.1109/LRA.2023.3236571) · [Code](https://github.com/PRBonn/kiss-icp)
- **Open3D.** Zhou, Park, and Koltun (2018), *Open3D: A Modern Library for 3D Data Processing*. The simulator uses its ray-casting library. [Paper](https://arxiv.org/abs/1801.09847) · [Code](https://github.com/isl-org/Open3D)

## Dataset used in the saved experiments

- **TreeScope.** Cheng et al. (2023), *TreeScope: An Agricultural Robotics Dataset for LiDAR-Based Mapping of Trees in Forests and Orchards*. WSF-19 supplies the recorded mapping example and VAT-0723 supplies labelled ground and stem points for the classifier check. TreeScope is distributed under CC BY-NC-SA 4.0. [Paper](https://arxiv.org/abs/2310.02162) · [Dataset and terms](https://treescope.org/)

The [data manifest](../data/MANIFEST.csv) records the source files and checksums. The [dataset catalogue](../datasets/README.md) covers additional sources the team considered, including DigiForests and Shivalik Range Tree LiDAR. The [learning links](youtube-links.md) collect introductory material on sensing, navigation, and forestry.
