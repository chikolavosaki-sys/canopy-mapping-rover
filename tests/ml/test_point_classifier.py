"""Tests for the ML point classifier: features, sampling, and learning."""

import numpy as np
import pytest

from canopy.ml.dataset import balanced_sample
from canopy.ml.features import FEATURE_NAMES, point_features


def _feature(table: np.ndarray, name: str) -> np.ndarray:
    return table[:, FEATURE_NAMES.index(name)]


def test_features_tell_a_trunk_line_from_flat_ground_and_leaves() -> None:
    """A vertical line is linear and vertical; ground is planar; a blob is scattered."""
    rng = np.random.default_rng(0)
    line = np.column_stack((np.zeros(50), np.zeros(50), np.linspace(0.5, 3.0, 50)))
    x, y = np.meshgrid(np.linspace(0, 2, 10), np.linspace(0, 2, 10))
    ground = np.column_stack((x.ravel(), y.ravel(), np.zeros(100)))
    blob = rng.normal(0, 0.3, size=(80, 3)) + [10.0, 10.0, 6.0]

    trunk_f, ground_f, blob_f = (point_features(cloud) for cloud in (line, ground, blob))

    assert _feature(trunk_f, "linearity").mean() > 0.9
    assert _feature(trunk_f, "vertical_direction").mean() > 0.9
    assert _feature(ground_f, "planarity").mean() > 0.6
    assert _feature(ground_f, "verticality").mean() < 0.1
    assert _feature(blob_f, "scattering").mean() > _feature(trunk_f, "scattering").mean()
    assert trunk_f.shape == (50, len(FEATURE_NAMES))


def test_balanced_sample_caps_every_class() -> None:
    """No class gets more than the cap; small classes are kept whole."""
    labels = np.array(["ground"] * 500 + ["stem"] * 40 + ["rock"] * 5)

    picked = balanced_sample(labels, per_class=50, rng=np.random.default_rng(0))

    counts = {name: int((labels[picked] == name).sum()) for name in ("ground", "stem", "rock")}
    assert counts == {"ground": 50, "stem": 40, "rock": 5}


def test_model_learns_on_one_forest_and_works_on_another(tmp_path) -> None:
    """Trained on forest 0, the classifier beats guessing clearly on unseen forest 1."""
    pytest.importorskip("sklearn")
    from canopy.ml import point_classifier as classifier
    from canopy.ml.dataset import build_dataset

    train_x, train_y = build_dataset([0], per_class=300)
    test_x, test_y = build_dataset([1], per_class=300)

    model = classifier.train(train_x, train_y)
    result = classifier.evaluate(model, test_x, test_y)
    classifier.save(model, tmp_path / "model.joblib")
    reloaded = classifier.load(tmp_path / "model.joblib")

    assert result["accuracy"] > 0.7, result
    assert abs(sum(classifier.feature_importance(model).values()) - 1.0) < 1e-6
    np.testing.assert_array_equal(reloaded.predict(test_x[:20]), model.predict(test_x[:20]))
    classifier.plot_confusion(result, "test", tmp_path / "confusion.png")
    assert (tmp_path / "confusion.png").exists()
