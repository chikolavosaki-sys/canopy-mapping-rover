"""Random Forest point classifier: ground / stem / shrub / crown / rock.

A Random Forest is many decision trees, each trained on a random part of the
data; every tree votes and the majority wins. It works well on small tables of
hand-made features like ours, needs no GPU, trains in seconds, and shows which
features it relied on (feature importance). Uses scikit-learn (``ml`` extra).
"""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from canopy.config import section

from .features import FEATURE_NAMES

_ML = section("ml")


def train(features: NDArray[np.float64], labels: NDArray[np.str_]) -> object:
    """Fit a Random Forest on a feature table and its labels."""
    from sklearn.ensemble import RandomForestClassifier

    cfg = _ML["random_forest"]
    model = RandomForestClassifier(
        n_estimators=cfg["n_estimators"],
        max_depth=cfg["max_depth"],
        min_samples_leaf=cfg["min_samples_leaf"],
        class_weight="balanced",  # do not ignore rare classes such as rocks
        random_state=cfg["seed"],
        n_jobs=-1,
    )
    return model.fit(features, labels)


def evaluate(
    model: object, features: NDArray[np.float64], labels: NDArray[np.str_]
) -> dict:
    """Accuracy, per-class precision/recall/F1 and the confusion matrix."""
    from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

    classes = list(_ML["classes"])
    predicted = model.predict(features)
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predicted, labels=classes, zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(labels, predicted)),
        "classes": classes,
        "precision": precision.tolist(),
        "recall": recall.tolist(),
        "f1": f1.tolist(),
        "support": support.tolist(),
        "confusion": confusion_matrix(labels, predicted, labels=classes).tolist(),
    }


def feature_importance(model: object) -> dict[str, float]:
    """How much each feature helped the forest's decisions (sums to 1)."""
    return dict(zip(FEATURE_NAMES, map(float, model.feature_importances_)))


def save(model: object, path: str | Path) -> None:
    """Store a trained model on disk."""
    import joblib

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load(path: str | Path) -> object:
    """Load a model saved with :func:`save`. Only load files you created yourself."""
    import joblib

    return joblib.load(path)


def plot_confusion(result: dict, title: str, path: str | Path) -> None:
    """Confusion matrix as row percentages (each true class sums to 100 %)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    counts = np.asarray(result["confusion"], dtype=float)
    shares = 100 * counts / np.maximum(counts.sum(axis=1, keepdims=True), 1)
    names = result["classes"]
    figure, axis = plt.subplots(figsize=(6.2, 5.2), facecolor="#fcfcfb")
    axis.imshow(shares, cmap="Blues", vmin=0, vmax=100)
    for (row, col), share in np.ndenumerate(shares):
        if counts[row].sum():
            colour = "white" if share > 60 else "#0b0b0b"
            axis.text(col, row, f"{share:.0f}%", ha="center", va="center", color=colour)
    axis.set_xticks(range(len(names)), names)
    axis.set_yticks(range(len(names)), names)
    axis.set_xlabel("predicted class", color="#52514e")
    axis.set_ylabel("true class", color="#52514e")
    axis.set_title(title, loc="left", color="#0b0b0b", fontsize=11)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
