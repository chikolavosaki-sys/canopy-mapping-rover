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

## Honest limits

- The rover is simulated; there is no real rover hardware in this project.
- Ladder fuel is a proxy based on height-band point density, not a direct label.
- Static scans are used for forest analytics, not for odometry.
