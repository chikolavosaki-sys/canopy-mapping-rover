# Slides and script

For each slide: **Show** = what goes on the slide; **Say** = what to tell the
audience (about 30-60 seconds per slide). Generate the current simulator
figures with [the demo commands](03-demo-commands.md). The saved TreeScope
figures are in `presentation/images/`.

---

## 1. Title

**Show:** "Canopy Mapping Rover: mapping wildfire ladder fuels from below the
canopy with 3-D LiDAR". Team names, guide, BIT Mesra, B.Tech CSE minor project.
Background picture: `images/real_top_views.png` (left half) or a forest photo.

**Say:** "Our project is a ground rover that uses a 3-D laser scanner to map the
part of the forest that drones and satellites cannot see: the layer under the
tree crowns, where wildfires find their way up into the trees."

---

## 2. The problem: how wildfires climb

**Show:** A simple drawing: ground fire -> shrubs / low branches -> tree crown, with
the words "ladder fuels". Three bullets: ground fires are controllable; crown fires
are not; ladder fuels connect them.

**Say:** "Most forest fires start on the ground. They become dangerous when they
climb into the crowns. What lets them climb is called ladder fuel: shrubs, young
trees and low branches. If forest departments know where ladder fuel is dense,
they can clear it there first."

---

## 3. Why it is hard to find ladder fuel

**Show:** Two columns. "From above (drone / satellite): crowns hide the
understorey". "On foot (manual survey): slow, small areas, measuring trunks with a
tape".

**Say:** "Drones and satellites see the top of the canopy, not what is under it.
Surveys on foot work, but they are slow and cover small plots. We need something
that sees under the canopy and covers ground automatically."

---

## 4. Our idea

**Show:** Rover + LiDAR icon; "drives under the canopy, scans in 3-D, all around,
5 times a second".

**Say:** "LiDAR sends laser pulses in all directions and measures the distance of
every hit. Mounted on a rover driving under the trees, it records millions of 3-D
points of trunks, shrubs and ground: exactly the hidden layer."

---

## 5. What our system delivers

**Show:** Three boxes: (1) ladder-fuel risk map, (2) tree count + trunk diameter
(DBH), (3) simulated obstacle avoidance. Show the saved TreeScope heatmap and
the current simulator figures from `results/semester-demo/figures/`.

**Say:** "From the scans we produce three things: a risk map of ladder fuel in 1 m
squares, a list of trees with their trunk thickness for forest inventory, and a
simulator where we test whether the rover can navigate around trees and rocks."

---

## 6. How it works: the pipeline

**Show:** The diagram (copy from `docs/architecture.md`, simplified):
`LiDAR scans -> odometry (KISS-ICP) -> 3-D map -> ground (CSF or RANSAC) -> trees & DBH -> ladder-fuel map`,
and a side branch `LiDAR -> obstacle sectors -> FORWARD / TURN / STOP`.

**Say:** "Each scan goes through the same steps: figure out where the rover is,
add the scan to one big map, find the ground, measure the trees, and compute the
ladder-fuel score. In parallel, the rover uses each scan to decide how to drive."

---

## 7. Step 1: knowing where we are and building the map

**Show** the current `lidar_scan.png` and `odometry.png` from
`results/semester-demo/figures/`.

**Say:** "There is no GPS under a forest canopy, so the rover works out its own
movement by lining each new scan up with the previous ones; this is called
odometry, and we use the open-source KISS-ICP. During simulated alignment, we
downweight the effect of the ground by selecting returns above an estimated
ground plane. We keep the complete scans when building the map. Blue shows
the simulator route, and orange shows the estimate."

---

## 8. Step 2: finding the ground and measuring trees

**Show:** `images/real_side_view.png` (ground at 0 m, trunks as columns) and one
line: "DBH = trunk diameter at 1.3 m".

**Say:** "First we separate the ground using the Cloth Simulation Filter or
the RANSAC fallback, then measure every point's height above the soil.
Then we take a thin slice at 1.3 m, chest height, find round clusters, and fit a
circle to each: its diameter is the DBH. We also check the trunk is upright at
0.8 m and 2 m so shrubs are not mistaken for trees."

---

## 9. Step 3: the ladder-fuel score

**Show:** Formula in one line:
`index = 0.5 x fullness(1-4 m) + 0.2 x fullness(1-8 m) + 0.3 x continuity`,
and `images/real_top_views.png` (right half: only 0.3-4 m vegetation).

**Say:** "For every 1 m square we look at how full the 1 to 4 m and 1 to 8 m height
layers are, and whether there is a gap between the shrubs and the crown. No gap
means a continuous ladder, so a high score. We remove trunks first, because a
trunk is continuous but is not fuel. The picture shows only the 0.3 to 4 m layer:
the fuel the rover sees and a drone would not."

---

## 10. Step 4: driving safely

**Show** the current `results/semester-demo/figures/forest_map.png` and the
four states FORWARD, TURN LEFT, TURN RIGHT, and STOP.

**Say:** "The rover splits the space ahead into 9 directions and checks a corridor
as wide as itself. If something is in the way it turns immediately, keeps turning
the same way until clear, and steers back towards the goal only when that
direction is free. It also remembers obstacles it saw a moment ago, because the
LiDAR cannot see low rocks right next to it."

---

## 11. How we tested it

**Show:** Two boxes: "Simulator: virtual forests with known true answers (trees,
DBH, shrubs, slopes up to 15 degrees)" and "Real data: TreeScope WSF-19 forest
recording (LiDAR + IMU, tree labels)".

**Say:** "We tested in two ways. In our simulator we build the forest ourselves, so
we know every tree's true size and can measure our accuracy exactly. Then we ran
the same pipeline on a real public forest recording from the TreeScope project."

---

## 12. Results in simulation

**Show** these results from [the seed 0 benchmark](../docs/OUTCOMES.md).

| Task | Result |
|---|---|
| Final odometry drift | 0.85% over a 10.67 m route |
| Trees matched on the LiDAR-estimated map | 6 of 6, DBH RMSE 1.81 cm |
| Ladder-fuel score vs simulated shrub locations | AUC about 0.97 |
| Navigation regression benchmark | 80 of 80 reached the goal, zero collisions and timeouts |

Use `results/semester-demo/survey_map.png` alongside the table.

**Say** "On the demo forest, the LiDAR-estimated route ended about nine
centimetres from the simulator's endpoint. The map matched all six trees,
with a trunk-diameter error of about 1.8 centimetres. The rover reached its
goal in all 80 scenarios we reran for the navigation benchmark."

---

## 13. Results on a real forest

**Show:** `images/real_ladder_fuel.png` (big) and `images/real_top_views.png`.
Numbers: 92 scans, 8.6 m drive, 2.7 million-point map, 40 x 46 m, 17 % of cells
above a score of 0.5, DBH median 23.5 cm (ours) vs 23.4 cm (labels).

**Say:** "On the real TreeScope recording, the full pipeline ran end to end: it
built a 2.7-million-point map of a 40 by 46 m stand and produced this ladder-fuel
map, where about 17% of the cells scored above 0.5. Our five detected stems
had a median diameter of 23.5 cm. The median across the dataset labels was
23.4 cm. These are separate groups of trees."

---

## 14. Live demo (optional, 1-2 minutes)

**Show** the saved survey map and, if there is time, rerun the quick
simulation from [the live walkthrough](03-demo-commands.md).

**Say** "The solid line shows the simulator's route. The dashed line shows
where the LiDAR estimate places the rover, and the blue crosses mark the
detected trees. The heatmap shows the ladder-fuel score."

---

## 15. Limitations and future work

**Show:** Bullets:
- Ground-filtered odometry was tested in simulation. Tree matching averaged
  83% across five additional simulated forests
- The earlier TreeScope run detected five stems. The dataset lists 63
  labelled trees and tree-by-tree matching is pending
- Simulated rover only; no physical hardware
- Ladder fuel is a proxy, validated against shrub positions
- One real dataset so far (DigiForests and Indian Shivalik data need access)
- Future: better odometry (LiDAR + IMU), more datasets, a real rover

**Say** "The ground filter helped on simulated scans. In a real forest, low
logs and other near-ground features might be important for aligning a scan.
Our earlier TreeScope run detected five stems in the processed map. We
still need to align that map with the labelled tree survey to measure
real-world tree recall."

---

## 16. Real-world impact

**Show:** Who benefits: forest departments (where to clear fuel first, fire-risk
zones), forest inventory (tree counts and sizes without tape surveys), research
(repeatable measurements). India context: large forest areas, e.g. the Shivalik
range.

**Say:** "A tool like this lets a forest department send a rover instead of a survey
team, get a map of where fire could climb into the canopy, and decide where to clear
first. The same scan also gives a tree inventory."

---

## 17. Thank you / questions

**Show:** Team, guide, repository link
(`github.com/chikolavosaki-sys/canopy-mapping-rover`), dataset credit: "TreeScope
dataset, CC BY-NC-SA 4.0".

**Say:** "Thank you. We are happy to take questions." (See `04-questions-and-answers.md`.)
