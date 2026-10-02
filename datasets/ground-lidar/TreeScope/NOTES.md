# TreeScope notes

- **LiDAR sensor model:** The source exposes a sensor-model metadata file for each dataset, but the accessed overview does not state the model name; **NOT STATED IN SOURCES**. [Data overview](https://treescope.org/data_overview/)
- **IMU included:** Yes. Raw ROS bags contain raw data from all onboard sensors, including LiDAR and IMU. [Data overview](https://treescope.org/data_overview/)
- **Continuous walking or driving sequences:** Raw mobile-platform ROS bags are provided, including datasets collected with a cart and human-carried backpack, but sequence duration is **NOT STATED IN SOURCES**. [Paper](https://arxiv.org/html/2310.02162) [Data overview](https://treescope.org/data_overview/)
- **Point-cloud format:** Raw and processed ROS bags; ground-truth individual-tree PCD files; HDF5 semantic labels; JSON field measurements. [Data overview](https://treescope.org/data_overview/) [GitHub README](https://github.com/KumarRobotics/treescope/blob/main/README.md)
- **Labels:** Manually annotated tree-stem semantic labels; field-measured tree diameters for all measured trees; total height and full diameter profiles for some trees. Ground and shrub labels are **NOT STATED IN SOURCES**. [Data overview](https://treescope.org/data_overview/)
- **Region and forest type:** Forestry datasets include VAT-0723, VAT-1022, and WSF-19; the source describes forests and orchards, but a more specific region/forest type is **NOT STATED IN SOURCES**. [Data overview](https://treescope.org/data_overview/) [Official site](https://treescope.org)
- **Licence:** CC BY-NC-SA 4.0. [Official site](https://treescope.org)
- **Download size:** **NOT STATED IN SOURCES** for the full dataset. A separate 41.6 GB VAT-0723 multimodal subset is reported in its dataset card. [Data overview](https://treescope.org/data_overview/) [Subset card](https://huggingface.co/datasets/Voxel51/treescope-vat0723-multimodal)

Paper: [TreeScope arXiv paper](https://arxiv.org/abs/2310.02162). GitHub: [KumarRobotics/treescope](https://github.com/KumarRobotics/treescope).
