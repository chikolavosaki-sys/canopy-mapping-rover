"""Tests for the shared configuration loader."""

import numpy as np
import pytest

from canopy.config import load_config, section
from canopy.forest_analytics.ladder_fuel import ladder_fuel_index


def test_load_config_returns_an_independent_copy() -> None:
    """Editing a loaded config must not change what the next caller sees."""
    first = load_config()
    first["navigation"]["safety_distance_m"] = -1.0

    assert load_config()["navigation"]["safety_distance_m"] > 0


def test_section_reads_custom_file_and_rejects_unknown_names(tmp_path) -> None:
    """A different YAML file can be used, and missing sections fail clearly."""
    custom = tmp_path / "custom.yaml"
    custom.write_text("navigation:\n  safety_distance_m: 2.5\n")

    assert section("navigation", custom)["safety_distance_m"] == 2.5
    with pytest.raises(KeyError, match="not_a_section"):
        section("not_a_section", custom)


def test_ladder_weights_must_match_bands_and_sum_to_one() -> None:
    """Bad weights are rejected instead of silently leaving [0, 1]."""
    points = np.array([[0.2, 0.2, 2.0]])

    with pytest.raises(ValueError, match="weight"):
        ladder_fuel_index(points, bands=((1.0, 4.0), (1.0, 8.0)), weights=(0.7, 0.7))
