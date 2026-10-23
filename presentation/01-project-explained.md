# The project in plain words

Read this first. No code knowledge needed.

## 1. The real-world problem

- **Wildfires** often start as a fire on the ground (dry leaves, grass). A ground
  fire is easier to control. It becomes dangerous when it **climbs into the tree
  crowns**, where it spreads fast and is very hard to stop.
- Fire climbs using **ladder fuels**: shrubs, young trees and low branches that
  connect the ground to the crowns, like the steps of a ladder.
- Forest departments reduce fire risk by **clearing ladder fuels** in the most
  dangerous places. To do that, they first need to know **where** those places are.

## 2. Why this is hard today

- **Drones and satellites look from above.** The tree crowns block their view, so
  they cannot see the shrubs and low branches *underneath*.
- **Manual surveys** (people walking through plots, measuring trunks with a tape)
  are slow, tiring and cover only small areas.
- Forest inventories also need **how many trees** there are and **how thick** each
  trunk is (DBH), which is the same kind of slow manual work.

## 3. Our idea

A **ground rover** carrying a **3-D LiDAR** drives *under* the canopy. LiDAR is a
laser scanner: it sends out laser pulses all around and measures how long each
takes to bounce back, giving millions of 3-D points (a "point cloud") that show
the shape of everything around it, including the hidden understorey.

## 4. What the system produces

1. A **ladder-fuel risk map**: a heatmap of the forest in 1 m squares, from 0 (no
   ladder) to 1 (continuous vegetation from the ground up to the crowns).
2. A **tree list**: where each trunk is and its **DBH** (diameter at breast height,
   1.3 m above the ground: the standard way foresters measure tree size).
3. **Safe driving**: the rover avoids trunks and rocks on its own, on slopes.

## 5. How it works, step by step

Think of the rover as doing what a person would do with a tape and a notebook,
but automatically:

| Step | What it does | Plain-words analogy | Tool / method |
|---|---|---|---|
| 1. Scan | LiDAR takes about 5 scans per second, each with tens of thousands of points | Taking 3-D photos all around | Velodyne-type LiDAR (simulated, and a real recording) |
| 2. Odometry ("where am I?") | Works out how the rover moved between scans by lining each scan up with the previous ones | Recognising you moved by watching the trees shift | **KISS-ICP** (open-source) |
| 3. Map | Puts all scans together into one big 3-D map | Gluing photos into a panorama | our `register` step |
| 4. Find the ground | Separates ground points from everything else, even on 15-degree slopes | Laying a cloth over an upside-down forest: where it rests is the ground | **CSF** (Cloth Simulation Filter) |
| 5. Height above ground | Every point gets its height above the local ground | Measuring from the soil, not from sea level | terrain model (DTM) |
| 6. Trees and DBH | Takes a thin slice at 1.2-1.4 m, finds round clusters, fits circles to get trunk diameter; checks the trunk is upright | Wrapping a tape round each trunk at chest height | **DBSCAN** clustering + **RANSAC** circle fit (like 3DFIN/FSCT) |
| 7. Ladder fuel | For each 1 m square: how full the 1-4 m and 1-8 m height layers are, and how big the empty gap is between shrubs and the crown base | Looking up from the ground: is there a "ladder" of leaves to the crown? | our ladder-fuel index |
| 8. Navigation | Splits the space ahead into 9 directions, checks a rover-wide corridor, and chooses FORWARD / TURN LEFT / TURN RIGHT / STOP | A careful walker who turns before bumping into a tree | our state machine |

**Ladder-fuel index** = 0.5 x (how full 1-4 m is) + 0.2 x (how full 1-8 m is) +
0.3 x (continuity: 1 when there is no gap to the crown, 0 when the gap is 4 m or more).
Trunks are removed first, because a trunk is continuous but is not fuel.

## 6. How we tested it

- **Simulator** (`canopy.simulation`): we generate a virtual forest (trees, shrubs,
  rocks, slopes up to 15 degrees) and a virtual LiDAR. Because we built the forest,
  we know the *true* answer (every tree's position and DBH, every shrub), so we can
  measure accuracy exactly. The navigation tests run here (no real rover).
- **Real data**: a public forest recording, **TreeScope WSF-19** (a real LiDAR + IMU
  drive through a forest, with tree diameter labels). We ran the whole pipeline on it.

## 7. Key results (from `results/demo/report.md` and `docs/real-data.md`)

| What | Result | Meaning |
|---|---|---|
| Ground detection (simulated scans) | 99.3 % precision, 97.9 % recall | Almost every ground point found, almost no mistakes |
| Trees, with accurate rover positions | 6 of 6 found, DBH error 0.5 cm | Trunk thickness measured to about half a centimetre |
| Trees on 12 new test forests (accurate positions) | 93 % found, 96 % correct, DBH error 0.4 cm | Works beyond the one demo forest |
| Ladder-fuel map vs true shrubs | AUC 0.88-0.97 (1.0 = perfect, 0.5 = guessing) | The map highlights the right places |
| Navigation | 75 of 80 runs reached the goal (94 %), 4 collisions | Drives through forests of 10-80 trees on slopes |
| **Real forest (WSF-19)** | 2.7 million-point map, ladder map of 2,016 cells (17 % high-risk), 5 trunks with median DBH 23.5 cm vs 23.4 cm in the labels | The full pipeline runs on real data |

## 8. Honest limitations (say these; examiners respect them)

- **Odometry drift**: the position estimate slowly drifts (about 11 % in the
  simulated demo). That blurs trunks in the map, so on real data only 5 of 63
  labelled trees were found. With exact positions, accuracy is excellent; better
  odometry is the next step.
- The rover is **simulated**; there is no physical rover in this project.
- Ladder fuel is a **proxy** (a measurable stand-in), checked against shrub
  positions, not a full fire-behaviour model.
- Only one real dataset was used so far; others (DigiForests, the Indian Shivalik
  dataset) need download access.

## 9. Key terms

| Term | Meaning |
|---|---|
| LiDAR | Laser scanner that measures distances to make a 3-D point cloud |
| Point cloud | Millions of 3-D dots, one per laser hit |
| Canopy / understorey | Tree crowns at the top / the layer of shrubs and young trees under them |
| Ladder fuel | Vegetation that lets fire climb from the ground into the crowns |
| DBH | Diameter at Breast Height: trunk thickness 1.3 m above the ground |
| Odometry | Estimating the rover's movement from its own sensors |
| Drift | Small errors in odometry that add up over distance |
| ICP / KISS-ICP | Iterative Closest Point: lines up two scans; KISS-ICP is a simple open-source version |
| CSF | Cloth Simulation Filter: finds ground by "dropping a cloth" on the inverted cloud |
| DTM | Digital Terrain Model: a map of ground height |
| DBSCAN | Groups nearby points into clusters (each trunk slice becomes one cluster) |
| RANSAC | Robust fitting: tries many random guesses and keeps the one most points agree with |
| Precision / recall | Of what we found, how much is right / of what exists, how much we found |
| RMSE | Typical size of the error (root mean square error) |
| AUC | How well a score separates two groups: 1.0 perfect, 0.5 random guessing |

## 10. Tools used

Python 3.10+, NumPy/SciPy, **Open3D** (3-D processing and the simulated LiDAR),
**KISS-ICP** (odometry), **CSF** (ground), **rosbags** (reading robot recordings),
matplotlib (figures), pytest + GitHub Actions (63 automatic tests on every change).
