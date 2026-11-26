# Likely questions and honest answers

Short answers first; add detail only if asked. If you do not know, say what the
project does measure and point to the limitation. Never claim more than the
numbers show.

## About the problem

**Q: Why ladder fuel? Why not just map trees?**
A ground fire becomes a crown fire by climbing ladder fuel (shrubs, young trees,
low branches). Knowing where it is dense tells fire managers where to clear first.
We also map trees (count and DBH) because that comes from the same scan.

**Q: Why not use a drone or satellite?**
They see the canopy from above; the crowns hide the understorey. Our LiDAR is
under the canopy, so it sees exactly the layer they miss. (Airborne LiDAR can
partly see through gaps, but a ground scanner sees the understorey much more densely.)

**Q: Who would use this?**
Forest departments planning fuel clearing and fire-risk zones, and forest
inventory teams who currently measure trees by hand.

## About the method

**Q: What is LiDAR?**
A laser scanner that sends pulses in all directions and measures how long each
takes to return, giving distance. Thousands of pulses per scan give a 3-D point cloud.

**Q: How does the rover know where it is without GPS?**
Odometry: it lines up each new scan with the previous ones (KISS-ICP, an
open-source ICP method) to estimate how it moved. Under a canopy, GPS is weak.

**Q: What is drift?**
Small movement errors add up. On the 10.67 m seed 0 route, the ground-filtered
estimate ended about 9 cm away from the simulator endpoint (0.85% drift).
The all-returns baseline ended about 1.15 m away (10.77%).

**Q: Why filter the ground for odometry? Can you use this on real data?**
Smooth ground looks similar from one scan to the next. In the simulated
demo, keeping returns more than 10 cm above each scan's estimated ground
surface helped KISS-ICP align the scans. The run falls back to all returns
if any filtered scan has fewer than 100 points. We keep every valid scan
return for building the map. Recorded inputs use all returns for alignment.
Low logs and uneven ground can provide useful features in a real forest,
so using this filter there would require its own tests.

**Q: How do you find the ground on a slope?**
The Cloth Simulation Filter identifies ground by simulating cloth over an
inverted point cloud. RANSAC is the fallback and fits terrain planes from
the scan. The current Windows benchmark used RANSAC and measured about 99%
ground precision and recall on the labelled simulated scans.

**Q: What is DBH and why 1.3 m?**
Diameter at Breast Height: the standard forestry measure of tree size, taken 1.3 m
above the ground. We take a slice of points at 1.2-1.4 m and fit a circle.

**Q: How do you avoid counting shrubs as trees?**
Several checks: the points must form a good circle (RANSAC fit, small error), at
least 90 degrees of the circle must be visible, the radius must be plausible, and
the trunk must also appear, upright, at 0.8 m or 2.0 m.

**Q: How is the ladder-fuel index computed? Where do the weights come from?**
`0.5 x fullness(1-4 m) + 0.2 x fullness(1-8 m) + 0.3 x continuity to the crown`.
The weights are a reasoned design choice, not fitted to data yet; calibrating them
on labelled shrub data (DigiForests) is planned future work.

**Q: How does the rover avoid obstacles?**
A FORWARD / TURN LEFT / TURN RIGHT / STOP state machine. It turns as soon as a
rover-wide corridor ahead is blocked, keeps the same turn direction until clear
(so it does not wobble), and only steers back to the goal when that way is free.
It remembers recent obstacles because LiDAR can lose sight of low objects
near the rover. The stored height is measured above the ground under each
obstacle. When the simulated rover moves uphill, the obstacle's XY changes
relative to the rover and its ground clearance stays the same. A physical
rover would need to account for pitch, roll, and terrain estimation errors.

## About machine learning

**Q: Where is the machine learning in this project?**
A supervised Random Forest classifier (scikit-learn) labels every LiDAR point as
ground, trunk, shrub, crown or rock (`src/canopy/ml/`). Tree detection also uses
DBSCAN, an unsupervised clustering algorithm.

**Q: What are the features?**
Eight numbers per point, from its 20 nearest neighbours: height above ground,
linearity (on a line, like a trunk edge), planarity (flat, like ground),
scattering (spread out, like leaves), verticality, the direction of the main
spread, the height spread, and how far the neighbours are (density).

**Q: Where did the training labels come from?**
From our simulator: we build the forest, so we know what every laser ray hit.
That gave about 93,000 labelled training points from 8 forests without any manual
labelling.

**Q: How did you make sure the accuracy is honest?**
We tested on 4 different forests the model never saw during training (41,429
points): 89.2 % accuracy. We also tested on real labelled frames from TreeScope.

**Q: Why Random Forest and not deep learning?**
Our features are a small table of numbers, where Random Forests work very well.
It trains in seconds on a laptop without a GPU and shows which features it used.
Deep learning (for example PointNet++) needs much more labelled real data and a GPU.

**Q: Why is it worse on real data (ground 60 %, trunk 35 %)?**
The model learned only from our simulated forest. Real ground is rougher (often
called "rock"), and real trunks are 20+ m tall while in simulation the LiDAR mostly
saw the lower part, so upper trunk points look like "crown" to the model. This is
the sim-to-real gap; training or fine-tuning on real labelled data is the next step.

**Q: Which classes are confused most?**
Shrub and trunk (23 % of shrub points predicted as trunk), because both occur at
1-4 m height and both can look upright locally.

## About testing and results

**Q: Is there a real rover?**
No. The project uses a simulator for driving and a real public recording
(TreeScope) for mapping. This was decided at the start to fit a three-month,
two-credit project.

**Q: Why trust a simulator?**
Because we build the forest, we know the true answer for every tree and shrub,
so we can measure accuracy exactly, which is impossible in a real forest without
a survey. Then we checked on real data.

**Q: How accurate is it?**
On the seed 0 LiDAR-estimated map, we matched all six trees and measured
trunk diameter with 1.81 cm RMSE. Mean tree recall was 83% over five other
simulated forests. Ladder-fuel score versus shrub locations had an AUC of
about 0.97 on the demo forest. On held-out navigation seeds 3000–3019, the
rover reached 79 of 80 goals (98.75%), with one collision and zero timeouts.

**Q: What do the five detected stems and 63 labels mean on real data?**
The earlier TreeScope run detected five stems in the processed point cloud.
The field table contains 63 labelled trees. Blur from scan alignment, coverage,
and the stem fit checks can affect the detection count. We still need common
map coordinates to match detections to individual labels. The detected stems
had a median DBH of 23.5 cm. The median across all labels was 23.4 cm.

**Q: Did you compare tree by tree on the real data?**
Not yet: our map and the dataset's labels use different coordinate frames.
We compared counts and size ranges. Aligning the frames is a planned task.

**Q: What does AUC 0.97 mean?**
If you pick one shrub square and one empty square at random, our score ranks
the shrub square higher 97 % of the time. 0.5 would be random guessing.

**Q: What changed after the original four collisions?**
The original simulator benchmark had four collisions, mostly with rocks as
the rover approached them. We widened the simulated navigation scan, added a
detection margin, and improved how the rover approaches a nearby goal.
Replaying seeds 2000–2019 gave zero collisions and zero timeouts. On the
fresh seeds 3000–3019, the rover collided once, on seed 3014 with 40 trees.
The held-out run measures how the fixed setup performed on new forests.

**Q: How long does it take to run?**
The quick demo runs four navigation trials. The full benchmark runs 80 and
takes several minutes depending on the laptop. The saved figures are ready
to show during the presentation.

## About the work

**Q: What did each of you do?**
Each person should explain their own contributions using a concrete example from the project. Mention the problem, the change or review you handled, and the evidence that shows what improved.

**Q: What open-source tools did you use, and what did you write yourselves?**
Used: Open3D, KISS-ICP, CSF, rosbags, NumPy/SciPy. Wrote: the simulator, the
pipeline that connects everything, stem detection, the ladder-fuel index,
navigation, and the evaluation. Run `pytest -q` to see the test result for
the installed configuration.

**Q: What would you do with more time?**
Better odometry (LiDAR + IMU), tree-by-tree validation on real data, the
DigiForests shrub labels and the Indian Shivalik dataset, and a physical rover.

**Q: What datasets did you use, and are you allowed to?**
TreeScope (CC BY-NC-SA 4.0: non-commercial use with attribution), credited in
`references/README.md`. Raw data is not stored in the repository.
