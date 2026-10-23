"""Read project settings from ``configs/default.yaml``.

Modules take their default numbers from here, so every tunable value lives in
one YAML file. Pass a different path to ``load_config`` to try other settings,
or set the ``CANOPY_CONFIG`` environment variable before importing ``canopy``
modules to change the defaults everywhere (command-line ``--config`` does this).
"""

import copy
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_REPO_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
DEFAULT_CONFIG = Path(os.environ.get("CANOPY_CONFIG", _REPO_CONFIG))


@lru_cache(maxsize=8)
def _read(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Return the whole configuration as a fresh dictionary (safe to modify)."""
    return copy.deepcopy(_read(Path(path).resolve()))


def section(name: str, path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Return one top-level section, e.g. ``section("navigation")``."""
    config = load_config(path)
    if name not in config:
        raise KeyError(f"config section {name!r} not found in {path}")
    return config[name]
