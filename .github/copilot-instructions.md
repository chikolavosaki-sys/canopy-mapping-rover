# Copilot instructions

Canopy Mapping Rover uses a Python/Open3D simulator and recorded LiDAR to map forest structure below the canopy. KISS-ICP estimates sensor motion. Forest analytics measure ground-normalised height, stems, trunk diameter, and a ladder-fuel proxy. Obstacle avoidance is evaluated in simulation.

- Use Python 3.10-compatible syntax. Run `python -m ruff check .` and `python -m pytest -q`.
- Use `canopy.config` and `configs/default.yaml` for tunable defaults.
- Describe outcomes with their inputs and limits. Use synthetic ground truth, held-out navigation seeds, and the recorded TreeScope checks as documented.
- Keep raw inputs under `data/raw/` and new experiment outputs under `results/runs/`. Preserve the published snapshots.
- Record changes to the pipeline or evaluation protocol in [design decisions](../docs/decisions.md). Use [architecture](../docs/architecture.md) and [outcomes](../docs/OUTCOMES.md) for the current system and published measurements.
