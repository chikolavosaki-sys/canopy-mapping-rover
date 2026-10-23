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

Phase 2 adds the first forest-analytics path: a grid-lowest-point terrain
model, height normalization, voxel occupancy density, a ladder-fuel proxy
report, and breast-height stem circle fitting. These outputs are intended for
synthetic testing first; the ladder score is not a direct fire-behaviour label.

## Demo results

`python scripts/run_all.py --seed 0 --update-outcomes` regenerates the table
between the markers below (full report: `results/demo/report.md`). It needs no
downloads and takes about 2 minutes. Values are synthetic results, not claims
about real forests.

<!-- demo-results:start -->
Seed 0.

| Metric | Value | Target |
|---|---:|---:|
| Odometry final drift (% of path) | 0.0414 | < 2 % |
| Odometry ATE RMSE (m) | 0.0052 | - |
| Tree recall, scanned map | 0.1667 | >= 0.90 |
| Tree recall, perfect cloud (upper bound) | 0.8333 | - |
| DBH RMSE (m), scanned map | 0.0128 | <= 0.03 |
| Ladder AUC vs shrub cells, scanned map | 0.9343 | >= 0.75 |
| Navigation success rate | 0.4000 | >= 0.90 |
| Navigation collisions | 3 | 0 |
<!-- demo-results:end -->

## Honest limits

- The rover is simulated; there is no real rover hardware in this project.
- Ladder fuel is a proxy based on height-band point density, not a direct label.
- Static scans are used for forest analytics, not for odometry.
- Synthetic odometry is unrealistically easy: the simulated scanner returns the
  same fixed sample points every frame, so ICP matching is nearly perfect.
- The scanned map is sparse (the scanner fires only 16 x 180 rays), so tree
  recall on it is far below the perfect-cloud upper bound until the scanner is
  replaced with ray casting.
