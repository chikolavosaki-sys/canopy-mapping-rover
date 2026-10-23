"""Small, safe spectral-index helpers for the shared aerial context layer."""

import numpy as np


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Compute a ratio and return zero where its denominator is zero."""
    numerator_array = np.asarray(numerator, dtype=float)
    denominator_array = np.asarray(denominator, dtype=float)
    return np.divide(
        numerator_array,
        denominator_array,
        out=np.zeros_like(numerator_array, dtype=float),
        where=denominator_array != 0,
    )


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Return NDVI, `(nir - red) / (nir + red)`, safely."""
    return _safe_ratio(np.asarray(nir) - np.asarray(red), np.asarray(nir) + np.asarray(red))


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Return green-NIR NDWI, `(green - nir) / (green + nir)`, safely."""
    return _safe_ratio(
        np.asarray(green) - np.asarray(nir),
        np.asarray(green) + np.asarray(nir),
    )
