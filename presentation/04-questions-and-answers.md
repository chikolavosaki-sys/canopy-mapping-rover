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
Each small movement estimate has a small error; they add up. Over 10.7 m in our
simulated demo the estimate ended about 1.15 m off (10.8 %, from
`results/demo/report.md`).

**Q: How do you find the ground on a slope?**
CSF (Cloth Simulation Filter): flip the point cloud upside down and simulate a
cloth falling onto it; where the cloth rests is the ground. It works on our
15-degree test slopes (99 % precision).

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
It remembers recent obstacles because the LiDAR cannot see low objects right next to it.

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
With accurate positions: all 6 trees found and DBH within about 0.5 cm in the demo;
93 % of trees found with 0.4 cm DBH error on 12 other test forests. Ground: 99 %
precision. Ladder-fuel vs true shrubs: AUC 0.97. Navigation: 94 % success over 80 runs.

**Q: Then why only 5 of 63 trees on the real data?**
Odometry drift. Small position errors blur each trunk across scans (visible as
repeated slanted bands in `images/real_side_view.png`), so most trunks fail the
strict circle checks. When positions are accurate the method works, so better
odometry (for example adding the IMU) is the next step. The 5 trunks found have a
median DBH of 23.5 cm, matching the dataset's 23.4 cm.

**Q: Did you compare tree by tree on the real data?**
Not yet: our map and the dataset's labels use different coordinate frames.
We compared counts and size ranges. Aligning the frames is a planned task.

**Q: What does AUC 0.97 mean?**
If you pick one shrub square and one empty square at random, our score ranks
the shrub square higher 97 % of the time. 0.5 would be random guessing.

**Q: Why did the rover collide 4 times?**
All 4 were rocks, mostly small ones just above the rover's 0.3 m ground
clearance, which are hard to see in the LiDAR. We report it honestly rather
than tuning on the test runs.

**Q: How long does it take to run?**
The whole simulated demo (drive, mapping, analytics, 80 navigation runs) takes
about 2 minutes on a laptop; the real forest analysis about 4 minutes.

## About the work

**Q: What did each of you do?**
Prithvi: forest analytics (ground, trees, ladder fuel), repository and report.
Anwita: LiDAR odometry and navigation. Prajwal: simulator and evaluation.
(Adjust to what each person actually did.)

**Q: What open-source tools did you use, and what did you write yourselves?**
Used: Open3D, KISS-ICP, CSF, rosbags, NumPy/SciPy. Wrote: the simulator, the
pipeline that connects everything, stem detection, the ladder-fuel index,
navigation, and the evaluation; 63 automated tests run on every change.

**Q: What would you do with more time?**
Better odometry (LiDAR + IMU), tree-by-tree validation on real data, the
DigiForests shrub labels and the Indian Shivalik dataset, and a physical rover.

**Q: What datasets did you use, and are you allowed to?**
TreeScope (CC BY-NC-SA 4.0: non-commercial use with attribution), credited in
`references/README.md`. Raw data is not stored in the repository.
