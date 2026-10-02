# Canopy Mapping Rover

Canopy Mapping Rover is a BIT Mesra B.Tech CSE minor project. We are building and evaluating a simulated ground rover that uses 3D LiDAR to map forest structure from below the canopy. The map should help us estimate vegetation density at different heights, ladder fuels, tree stems, and trunk diameter at breast height (DBH). A drone or satellite usually cannot see these features through leaves. The project runs on recorded datasets plus a simulator; it does not require real rover hardware.

## Team

| Member | Role | Main areas |
|---|---|---|
| Prithvi (`@chikolavosaki-sys`) | Repository owner | Forest analytics and final report (PROPOSED) |
| Anwita (`@ANWITA_USERNAME`) | LiDAR and navigation | LiDAR-inertial odometry and rover navigation |
| Prajwal (`@PRAJWAL_USERNAME`) | Simulator and evaluation (PROPOSED) | Simulator world and evaluation scripts |

The proposed ownership change is pending team confirmation. The water body module is paused, not deleted, and may return as a weeks 10-12 stretch goal.

## Quick links

- [System architecture](docs/architecture.md)
- [Dataset list](datasets/README.md)
- [Dataset sufficiency](datasets/SUFFICIENCY.md)
- [Outcome metrics](docs/OUTCOMES.md)
- [Simulator options](docs/simulator-options.md)
- [Glossary](docs/glossary.md)
- [Design decisions](docs/decisions.md)
- [References](references/README.md)

## How we work

- Use branches named `<name>/<task>`, such as `prithvi/forest-density`.
- Record weekly work in `progress/<name>/`.
- Do not commit raw datasets. Use scripts in `datasets/download_scripts/` and document dataset links instead.
- Explain LiDAR and SLAM code in plain language because the team is learning these topics.
- Plan around measurable results, not only whether code runs.
