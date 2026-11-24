# Outcomes

## Problem statement

> Wildfire risk depends on ladder fuels, which drones cannot see. We show that a ground LiDAR rover can find them, count trees and measure their thickness, and drive through a forest without hitting things.

## Questions and measurable results

| Question | Metric | Dataset or test source | Target |
|---|---|---|---|
| How well does the pose estimate follow the true path? | Position drift against exact synthetic poses; ATE/RPE against the TreeScope reference trajectory | Simulator, TreeScope | Synthetic drift < 2% of distance travelled |
| Can the system count trees and estimate trunk thickness? | Tree recall and DBH error against field measurements | TreeScope, Shivalik, Weiser | Synthetic DBH RMSE <= 3 cm and recall >= 90%; real-data DBH RMSE <= 5 cm |
| Does the ladder-fuel proxy agree with labelled low vegetation? | Point-density in the 1-4 m and 1-8 m bands compared with shrub labels | DigiForests | Positive correlation and AUC >= 0.75 |
| Can the simulated rover avoid obstacles repeatedly? | Obstacle-avoidance success rate and collision count over repeated runs | Simulator | >= 90% success with 0 collisions over >= 50 runs |

## Final demo

The system processes a forest recording and outputs a map highlighting zones with the most ladder fuel.

Phase 4 adds repeatable simulator navigation metrics: goal success, collision,
timeout, and path length. These metrics describe the synthetic controller only,
not deployment safety on a physical rover.

Forest analytics (`canopy.forest_analytics.pipeline`, shared by
`canopy-analyze` and the demo): CSF ground classification with a RANSAC
fallback, a plane-fitted DTM, height normalisation, stem detection (DBSCAN,
RANSAC circle, geometric refinement, 0.8 m / 2.0 m verticality check), stem
removal, height-layer density, and a ladder-fuel index from 1-4 m and 1-8 m
occupancy plus the vertical gap to the crown base. The ladder score is a
proxy checked against shrub labels, not a fire-behaviour label.

## Demo results

`python scripts/run_all.py --seed 0 --out results/semester-benchmark --update-outcomes`
regenerates the table and saves the survey map, measurements, and navigation
results. The run uses synthetic scans and requires no datasets.

### Mapping comparison

On seed 0, ground filtering reduced final drift from 10.77% to 0.85% and
increased tree recall from 0 of 6 to 6 of 6. The scanned map estimated
trunk diameter with 1.81 cm RMSE. On five additional forests (seeds 20–24),
mean final drift fell from 10.43% to 1.58% and mean tree recall rose from 0%
to 83%. Four of the five met the drift target and three met the recall target.
These runs used the RANSAC ground classifier. The original all-returns run
is available in [the original demo results](../results/demo/report.md).

### Seed 0 mapping and held-out navigation benchmark

The updated navigation configuration reached the goal in 80 of 80 runs when
we replayed seeds 2000–2019 across four densities. Those scenarios helped
diagnose failures. The table below reports the independent run on seeds
3000–3019 with the configuration fixed before testing.

The held-out run reached 79 of 80 goals (98.75%). The collision occurred on
seed 3014 with 40 trees, so the zero-collision target is still open. All
other runs reached the goal and there were no timeouts.

<!-- demo-results:start -->
Seed 0. Ground classification used RANSAC.
Navigation seeds 3000-3019.

| Metric | Value | Target |
|---|---:|---:|
| Odometry final drift (% of path) | 0.8473 | < 2 % |
| Odometry ATE RMSE (m) | 0.0502 | - |
| Tree recall, scanned map | 1.0000 | >= 0.90 |
| Tree recall, exact-pose map (no odometry error) | 1.0000 | - |
| Tree recall, perfect cloud (upper bound) | 1.0000 | - |
| DBH RMSE (m), scanned map | 0.0181 | <= 0.03 |
| DBH RMSE (m), exact-pose map | 0.0047 | <= 0.03 |
| Ground precision (rocks excluded) / recall | 0.994 / 0.995 | - |
| Ladder AUC vs shrub cells, scanned map | 0.9658 | >= 0.75 |
| Navigation runs | 80 | >= 50 |
| Navigation success rate | 0.9875 | >= 0.90 |
| Navigation collisions | 1 | 0 |
| Navigation timeouts | 0 | - |
<!-- demo-results:end -->

## Honest limits

- The rover is simulated; there is no real rover hardware in this project.
- Ladder fuel is a proxy based on height-band point density, not a direct label.
- Static scans are used for forest analytics, not for odometry.
- The simulated LiDAR ray-casts against simple meshes (cylinder trunks,
  sphere rocks, crowns and shrubs as clusters of small spheres). Real bark,
  foliage, and returns from partly hit objects are messier.
- Smooth ground supplies many similar returns, which can obscure motion
  during scan alignment. The ground filter helps in the simulator, and
  sparse or weakly structured scans can still yield unreliable alignment.
  The ground-filtered method needs separate testing on recorded data.
- Small boulders may be hidden by terrain or fall below useful LiDAR
  coverage in some poses. The navigation results apply to the
  [wider simulated navigation sensor](decisions.md) and the sampled forests.
- CSF's cloth drapes over low boulders, so rock points are often classed as
  ground (ground precision is reported with rocks excluded).
- Simulated foliage is flat triangles and trunks are perfect cylinders; real
  bark, branches and leaves will make stem fitting harder than here.
- Tree recall depends on scan coverage, alignment, and a 0.5 m matching
  gate. The exact-pose map provides a reference for how well the same
  scans can support the measurements.
- The rover stays level on slopes (no pitch or roll), and its pose for
  obstacle memory is exact; a real rover would use its own odometry.
