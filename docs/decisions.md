# Design decisions

| Date | Decision | Reason |
|---|---|---|
| 2026-10-02 | Water module is owned solely by Prajwal; aerial layer kept small to protect scope. | The project has about three months and a three-person team, so ownership and scope need to stay clear. |
| 2026-10-02 | TreeScope is the primary dataset for LiDAR-inertial odometry testing. | It is the only reviewed dataset with confirmed raw LiDAR and IMU data in its released contents. |
| 2026-10-02 | Shivalik, EuroSDR/FGI, and Weiser are static-scan datasets for canopy density, stem detection, and DBH only, not odometry. | Their documented acquisitions are plot or tripod scans rather than continuous rover sequences, so they cannot test motion estimation fairly. |
| 2026-10-02 | Ladder fuel is defined as a proxy: point density in the 1-4 m and 1-8 m height bands, validated against shrub labels in DigiForests. | None of the reviewed datasets has direct ladder-fuel labels, so height-band density is a measurable substitute that can be checked against available shrub labels. |
| 2026-10-02 | If IMU data is unavailable, fall back to LiDAR-only odometry and research KISS-ICP. | This keeps a usable motion-estimation baseline, although it loses inertial information and requires extra setup and evaluation work. |
| 2026-10-02 | Open question for mam: choose a simulator or real rover hardware for live-driving tests. | The choice affects budget, integration effort, safety, and whether the project can validate navigation in the field within three months. |
| 2026-10-02 | The project runs fully on recorded datasets plus a simulator; no real rover hardware. | This keeps the work achievable in three months and makes repeated evaluation safer and more reproducible. |
| 2026-10-02 | The water body module is paused, not deleted, and may return as a weeks 10-12 stretch goal. | Keeping its folders preserves prior work without taking time away from the core canopy-mapping outcome. |
| 2026-10-02 | The project is planned around measurable results and actual problem-solving outcomes. | Metrics make it possible to judge whether the system works rather than only whether the code executes. |
| 2026-10-02 | PROPOSED ownership: Prithvi handles forest analytics and the final report; Anwita handles LiDAR odometry and navigation; Prajwal handles the simulator world and evaluation scripts. | The split gives each teammate a clear deliverable and matches the simulator-only scope; team confirmation is still pending. |
