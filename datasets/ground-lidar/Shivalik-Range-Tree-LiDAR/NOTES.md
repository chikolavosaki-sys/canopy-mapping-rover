# Shivalik Range Tree LiDAR notes

- **LiDAR sensor model:** TLS used a RIEGL VZ-2000i; ALS used a Riegl LMS-Q780. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/)
- **IMU included:** **NOT STATED IN SOURCES** as a separately released IMU stream. The TLS scanner has a built-in IMU used for onboard registration, which is not the same as confirming exported IMU data. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/)
- **Continuous walking or driving sequences:** No continuous walking/driving sequence is described. TLS was collected from 22–29 static scan positions per plot; ALS used 118 flight strips. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/)
- **Point-cloud format:** Individual-tree TLS files are LAS; processing scripts emit TXT classifications. [GitHub tools README](https://github.com/moonis-ali/Dataset)
- **Labels:** 674 individual trees from 12 plots and 24 species; wood/leaf classification is supported. Field measurements include DBH; ground and shrub labels are **NOT STATED IN SOURCES**. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/) [GitHub tools README](https://github.com/moonis-ali/Dataset)
- **Region and forest type:** Shivalik Range, northern Haryana, India, in forest regions managed by the Haryana Forest Department; plots include varied topography and mixed species. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/)
- **Licence:** **NOT STATED IN SOURCES**. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/) [GitHub tools README](https://github.com/moonis-ali/Dataset)
- **Download size:** **NOT STATED IN SOURCES**. [Data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC13004935/) [GitHub tools README](https://github.com/moonis-ali/Dataset)

Paper/data descriptor: [Nature Scientific Data article](https://www.nature.com/articles/s41597-026-06674-w).
