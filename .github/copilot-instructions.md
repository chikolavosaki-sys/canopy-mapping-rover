# Copilot instructions

## Project

Canopy Mapping Rover uses recorded datasets and a pure-Python/Open3D
simulator to test a ground rover's 3D LiDAR mapping pipeline from below the
canopy. KISS-ICP is the primary LiDAR-only odometry implementation. FAST-LIO2
is only an optional Docker comparison if time permits. The navigation branch
uses angular sectors and a FORWARD/TURN/STOP state machine; the forest branch
removes ground and estimates height-layer density, stems, and DBH. A small
aerial/satellite context layer remains in scope. The water module is paused.

## Ownership

- Prithvi: forest analytics, final report, aerial context, and repository setup.
- Anwita: LiDAR odometry and navigation.
- Prajwal: simulator world and evaluation scripts.
- Shared file: `src/canopy/aerial_context/indices.py` (NDVI and NDWI).

## Rules

- Use Python 3.10+ with type hints, short docstrings, and small functions.
- Put every tunable number in `configs/default.yaml` and read it via `canopy.config`;
  do not hard-code thresholds inside functions.
- Explain LiDAR and SLAM code in plain language because the team is learning.
- Never commit raw datasets; use `datasets/download_scripts/`.
- Ignore generated `data/` and `results/` files except small summaries.
- Log weekly work in `progress/<name>/`.
- Update `docs/decisions.md` for scope or architecture changes.
- Report measurable outcomes and honest limits in `docs/OUTCOMES.md`.
- Keep `src/water_bodies/` and `datasets/water/` paused and unchanged.

@docs/architecture.md
@datasets/README.md
@datasets/SUFFICIENCY.md
@references/README.md
