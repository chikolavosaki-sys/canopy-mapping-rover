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

`python scripts/run_all.py --seed 0 --update-outcomes` regenerates the table
between the markers below (full report: `results/demo/report.md`). It needs no
downloads and takes about 2 minutes. Values are synthetic results, not claims
about real forests.

<!-- demo-results:start -->
Seed 0.

| Metric | Value | Target |
|---|---:|---:|
| Odometry final drift (% of path) | 10.7746 | < 2 % |
| Odometry ATE RMSE (m) | 0.7880 | - |
| Tree recall, scanned map | 0.0000 | >= 0.90 |
| Tree recall, exact-pose map (no odometry error) | 1.0000 | - |
| Tree recall, perfect cloud (upper bound) | 1.0000 | - |
| DBH RMSE (m), scanned map | n/a | <= 0.03 |
| DBH RMSE (m), exact-pose map | 0.0051 | <= 0.03 |
| Ground precision (rocks excluded) / recall | 0.993 / 0.979 | - |
| Ladder AUC vs shrub cells, scanned map | 0.8767 | >= 0.75 |
| Navigation runs | 80 | >= 50 |
| Navigation success rate | 0.9375 | >= 0.90 |
| Navigation collisions | 4 | 0 |
<!-- demo-results:end -->

## Honest limits

- The rover is simulated; there is no real rover hardware in this project.
- Ladder fuel is a proxy based on height-band point density, not a direct label.
- Static scans are used for forest analytics, not for odometry.
- The simulated LiDAR ray-casts against simple meshes (cylinder trunks,
  sphere rocks, crowns and shrubs as clusters of small spheres). Real bark,
  foliage, and returns from partly hit objects are messier.
- Odometry suffers from ground degeneracy: smooth-ish ground looks the same
  wherever the rover is, so KISS-ICP under-estimates motion. In the sparse demo
  forest (6 trees in 20 x 20 m) drift is about 12 %; removing ground points
  would cut ATE from 0.74 m to 0.04 m on a 6 m test drive, but KISS-ICP is
  used unmodified. Real data may behave differently.
- Tree recall on the KISS-ICP map is limited by that drift: with exact poses
  the same scans reach the perfect-cloud recall (see the exact-pose column).
- Navigation seeds 0-19 were used for tuning and 1000-1019 for diagnosing the
  blind zone; reported runs use fresh seeds (2000+). Remaining collisions are
  mostly small rocks only a few cm taller than the rover's 0.3 m ground
  clearance, which the per-scan ground plane and sensor noise can hide.
- CSF's cloth drapes over low boulders, so rock points are often classed as
  ground (ground precision is reported with rocks excluded).
- Simulated foliage is flat triangles and trunks are perfect cylinders; real
  bark, branches and leaves will make stem fitting harder than here.
- With KISS-ICP's drift in the demo forest, no detected tree lands within the
  0.5 m matching gate; with exact poses recall is 1.0 and DBH RMSE 0.5 cm.
  Better odometry, not better analytics, is the next bottleneck.
- The rover stays level on slopes (no pitch or roll), and its pose for
  obstacle memory is exact; a real rover would use its own odometry.
