# Outcomes

## Problem statement

Can ground-level LiDAR map understorey structure and estimate tree diameters, and how reliably can a simulated rover navigate a forest?

## Questions and measurable results

| Question | Metric | Dataset or test source | Target |
|---|---|---|---|
| How well does the pose estimate follow the true path? | Final displacement error and trajectory error against exact simulator poses | Simulator | Synthetic drift < 2% of distance travelled |
| Can the system count trees and estimate trunk thickness? | Tree recall and DBH error against known tree positions and diameters | Simulator. Real per-tree comparison remains open. | Synthetic DBH RMSE ≤ 3 cm and recall ≥ 90% |
| Does the ladder-fuel proxy agree with labelled low vegetation? | AUC against cells with known shrubs | Simulator. The real shrub-label check remains open. | AUC ≥ 0.75 |
| Can the simulated rover avoid obstacles repeatedly? | Obstacle-avoidance success rate and collision count over repeated runs | Simulator | >= 90% success with 0 collisions over >= 50 runs |

## Evaluation scope

The end-to-end demo maps a simulated forest and benchmarks simulated navigation. The [TreeScope experiment](real-data.md) shows the same forest analytics on recorded scans. The [ML report](../results/ml/report.md) covers the point-classification experiment.

Forest analytics (`canopy.forest_analytics.pipeline`, shared by
`canopy-analyze` and the demo): CSF ground classification with a RANSAC
fallback, a plane-fitted DTM, height normalisation, stem detection (DBSCAN,
RANSAC circle, geometric refinement, 0.8 m / 2.0 m verticality check), stem
removal, height-layer density, and a ladder-fuel index from 1-4 m and 1-8 m
occupancy plus the vertical gap to the crown base. The ladder score is a structural proxy evaluated against known shrub cells in the simulator.

## Reproduce the benchmark

```bash
python scripts/run_all.py --seed 0 --out results/runs/benchmark
```

This saves the survey map, measurements, and 80 navigation trial records locally. The published mapping results below used RANSAC. For the same ground backend, use an environment created with the RANSAC install command in the [setup guide](SETUP.md). Record the actual backend from the run report when comparing results.

### Mapping comparison

On seed 0, ground filtering reduced final drift from 10.77% to 0.85% and
increased tree recall from 0 of 6 to 6 of 6. The scanned map estimated
trunk diameter with 1.81 cm RMSE. On five additional forests (seeds 20–24),
mean final drift fell from 10.43% to 1.58% and mean tree recall rose from 0%
to 83%. Four of the five met the drift target and three met the recall target.
These comparison runs used RANSAC. The [archived all-returns demo](../results/demo/report.md) is an earlier CSF run with a different navigation benchmark.

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

A separate run with CSF also matched all six trees. DBH RMSE was 1.91 cm, and the same 79 of 80 navigation goals were reached. The alignment drift was 0.85% with either ground-classification backend.

## Limitations

- The rover was evaluated in simulation. Physical rover navigation remains untested.
- The ladder-fuel proxy uses height-band occupancy and the vertical gap toward the crown base. It needs validation against real vegetation data.
- Static point clouds go directly to forest analytics. Odometry requires a sequence of scans.
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
- Tree recall depends on scan coverage, alignment, and a 0.5 m matching
  gate. The exact-pose map provides a reference for how well the same
  scans can support the measurements.
- The rover stays level on slopes (no pitch or roll), and its pose for
  obstacle memory is exact; a real rover would use its own odometry.
