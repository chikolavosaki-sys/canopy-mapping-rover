# Copilot instructions

## Project

Canopy Mapping Rover uses recorded datasets and a simulator to test a ground rover's 3D LiDAR and IMU pipeline for mapping forest structure from below the canopy. LiDAR-inertial odometry (FAST-LIO2 or LIO-SAM) registers scans; the navigation branch uses angular sectors and a FORWARD/TURN/STOP state machine; the forest branch removes ground and estimates height-layer density, stems, and DBH. A small aerial/satellite context layer remains in scope. The water module is paused.

## Ownership

- Prithvi: forest analytics, final report, aerial context, and repository setup (PROPOSED).
- Anwita: LiDAR odometry and navigation.
- Prajwal: simulator world and evaluation scripts (PROPOSED).
- Shared file: `src/aerial_context/indices.py` (NDVI and NDWI).

## Rules

- Use Python 3.10+.
- Add type hints, short docstrings, and small functions.
- Explain code in plain language.
- Never commit raw datasets; use `datasets/download_scripts/`.
- Log weekly work in `progress/<name>/`.
- Update `docs/decisions.md` for any scope change.
- Report measurable outcomes and honest limits in `docs/OUTCOMES.md`.

@docs/architecture.md
@datasets/README.md
@datasets/SUFFICIENCY.md
@references/README.md
