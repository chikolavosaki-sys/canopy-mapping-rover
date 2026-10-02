# Canopy Mapping Rover

Canopy Mapping Rover is a BIT Mesra B.Tech CSE minor project. We are building a ground rover that uses a 3D LiDAR sensor to map forest structure from below the canopy. The map should help us estimate vegetation density at different heights, ladder fuels, tree stems, and trunk diameter at breast height (DBH). A drone or satellite usually cannot see these features through leaves.

## Team

| Member | Role | Main areas |
|---|---|---|
| Prithvi (`@chikolavosaki-sys`) | Repository owner | Forest analytics and aerial context |
| Anwita (`@ANWITA_USERNAME`) | LiDAR and navigation | LiDAR-inertial odometry and rover navigation |
| Prajwal (`@PRAJWAL_USERNAME`) | Water module | NDWI, U-Net, and water change detection |

## Quick links

- [System architecture](docs/architecture.md)
- [Dataset list](datasets/README.md)
- [Dataset sufficiency](datasets/SUFFICIENCY.md)
- [Glossary](docs/glossary.md)
- [Design decisions](docs/decisions.md)
- [References](references/README.md)

## How we work

- Use branches named `<name>/<task>`, such as `prithvi/forest-density`.
- Record weekly work in `progress/<name>/`.
- Do not commit raw datasets. Use scripts in `datasets/download_scripts/` and document dataset links instead.
- Explain LiDAR and SLAM code in plain language because the team is learning these topics.
