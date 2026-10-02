# Copilot instructions

## Project

Canopy Mapping Rover uses a ground rover's 3D LiDAR and IMU to map forest structure from below the canopy. LiDAR-inertial odometry (FAST-LIO2 or LIO-SAM) registers scans; the navigation branch uses angular sectors and a FORWARD/TURN/STOP state machine; the forest branch removes ground and estimates height-layer density, stems, and DBH. A small aerial/satellite context layer and separate water module are also maintained.

## Ownership

- Prithvi: forest analytics, aerial context, and repository setup.
- Anwita: LiDAR odometry and navigation.
- Prajwal: water body module.
- Shared file: `src/aerial_context/indices.py` (NDVI and NDWI).

## Rules

- Use Python 3.10+.
- Add type hints, short docstrings, and small functions.
- Explain code in plain language.
- Never commit raw datasets; use `datasets/download_scripts/`.
- Log weekly work in `progress/<name>/`.
- Update `docs/decisions.md` for any scope change.

@docs/architecture.md
@datasets/README.md
@datasets/SUFFICIENCY.md
@references/README.md
