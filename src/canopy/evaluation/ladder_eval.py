"""Ladder-fuel proxy metrics."""

import numpy as np
from scipy.stats import spearmanr


def evaluate_ladder(scores: np.ndarray, shrub_labels: np.ndarray) -> dict[str, float]:
    """Return rank correlation and binary AUC for shrub presence."""
    values = np.asarray(scores, dtype=float).ravel()
    labels = np.asarray(shrub_labels, dtype=bool).ravel()
    if values.shape != labels.shape or len(values) < 2:
        raise ValueError("scores and shrub_labels must be equal, non-empty arrays")
    correlation = spearmanr(values, labels).statistic
    auc = _auc(values, labels)
    return {"spearman": float(correlation) if np.isfinite(correlation) else 0.0, "auc": auc}


def _auc(scores: np.ndarray, labels: np.ndarray) -> float:
    positives = scores[labels]
    negatives = scores[~labels]
    if not len(positives) or not len(negatives):
        return 0.5
    comparisons = (positives[:, None] > negatives[None, :]).mean()
    ties = (positives[:, None] == negatives[None, :]).mean()
    return float(comparisons + 0.5 * ties)
