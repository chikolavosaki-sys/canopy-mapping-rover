# Outcomes

## Problem statement

> Wildfire risk depends on ladder fuels, which drones cannot see. We show that a ground LiDAR rover can find them, count trees and measure their thickness, and drive through a forest without hitting things.

## Questions and measurable results

| Question | Metric | Dataset or test source | Target |
|---|---|---|---|
| How well does the pose estimate follow the true path? | Position drift against the true path | TreeScope | |
| Can the system count trees and estimate trunk thickness? | Tree-count error and DBH error against field measurements | TreeScope, Shivalik, Weiser | |
| Does the ladder-fuel proxy agree with labelled low vegetation? | Point-density in the 1-4 m and 1-8 m bands compared with shrub labels | DigiForests | |
| Can the simulated rover avoid obstacles repeatedly? | Obstacle-avoidance success rate and collision count over repeated runs | Simulator | |

## Final demo

The system processes a forest recording and outputs a map highlighting zones with the most ladder fuel.

## Honest limits

- The rover is simulated; there is no real rover hardware in this project.
- Ladder fuel is a proxy based on height-band point density, not a direct label.
- Static scans are used for forest analytics, not for odometry.
