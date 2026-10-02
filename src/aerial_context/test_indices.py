"""Tests for spectral indices."""

import numpy as np

from src.aerial_context.indices import ndvi, ndwi


def test_ndvi_and_ndwi_values() -> None:
    """Both formulas should return the expected values."""
    np.testing.assert_allclose(ndvi(np.array([3.0]), np.array([1.0])), [0.5])
    np.testing.assert_allclose(ndwi(np.array([3.0]), np.array([1.0])), [0.5])


def test_zero_denominators_are_zero() -> None:
    """Zero denominators should not produce NaN or infinity."""
    np.testing.assert_array_equal(ndvi(np.array([0.0]), np.array([0.0])), [0.0])
    np.testing.assert_array_equal(ndwi(np.array([0.0]), np.array([0.0])), [0.0])
