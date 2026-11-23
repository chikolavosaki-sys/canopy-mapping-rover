"""Train and test the Random Forest point classifier (the project's ML part).

    pip install -e ".[ml]"                  # once: scikit-learn
    python scripts/train_point_classifier.py   # about 1-2 min

1. Build a labelled dataset from 8 simulated forests and train the model.
2. Test it on 4 *different* forests it has never seen (honest accuracy).
3. If the real TreeScope files exist: check it on real labelled frames
   (VAT-0723 .h5: ground and trunk labels only) and draw the real WSF-19 forest
   coloured by predicted class.

Writes ``results/ml/``: report.md, metrics.json, confusion_matrix.png,
feature_importance.png, real_classified_side_view.png, and the model file.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from canopy.config import section
from canopy.forest_analytics.ground import normalize_heights
from canopy.ml import point_classifier as classifier
from canopy.ml.dataset import balanced_sample, build_dataset
from canopy.ml.features import FEATURE_NAMES, point_features

ROOT = Path(__file__).resolve().parents[1]
VAT_H5 = ROOT / "data/raw/treescope/VAT-0723/ground_truth/labels/VAT-0723M.h5"
WSF_CLOUD = ROOT / "results/real/wsf19/analysis/normalised_cloud.npy"
COLOURS = {"stem": "#2a78d6", "shrub": "#eb6834", "rock": "#1baf7a",
           "ground": "#c9c8c3", "crown": "#8f8e89"}
_ML = section("ml")


def main() -> None:
    """Train, test on unseen forests, check on real data, write the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=Path("results/ml"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print("Building training set from simulated forests", _ML["train_seeds"])
    train_x, train_y = build_dataset(_ML["train_seeds"])
    print("Building test set from unseen forests", _ML["test_seeds"])
    test_x, test_y = build_dataset(_ML["test_seeds"])
    model = classifier.train(train_x, train_y)
    result = classifier.evaluate(model, test_x, test_y)
    importance = classifier.feature_importance(model)
    classifier.save(model, args.out / "point_classifier.joblib")
    classifier.plot_confusion(result, "Unseen simulated forests: true vs predicted",
                              args.out / "confusion_matrix.png")
    _plot_importance(importance, args.out / "feature_importance.png")
    real = real_check(model) if VAT_H5.exists() else None
    if WSF_CLOUD.exists():
        _plot_real_side_view(model, args.out / "real_classified_side_view.png")
    metrics = {"test": result, "real_vat0723": real, "feature_importance": importance,
               "train_points": len(train_y), "test_points": len(test_y)}
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    _write_report(metrics, args.out / "report.md")
    print((args.out / "report.md").read_text())


def real_check(model: object) -> dict:
    """Recall on real labelled frames. They contain only ground and trunk points."""
    import h5py

    rng = np.random.default_rng(0)
    features, labels = [], []
    with h5py.File(VAT_H5, "r") as handle:
        keys = sorted(handle)
        spread = np.linspace(0, len(keys) - 1, _ML["real_eval_frames"]).astype(int)
        for key in [keys[i] for i in spread]:
            ground, trunk = handle[key][f"ground_{key}"][:], handle[key][f"tree_trunks_{key}"][:]
            points = np.vstack((ground, trunk))
            truth = np.array(["ground"] * len(ground) + ["stem"] * len(trunk))
            _, normalized, _ = normalize_heights(points)
            picked = balanced_sample(truth, _ML["samples_per_class"] // 4, rng)
            features.append(point_features(normalized, normalized[picked]))
            labels.append(truth[picked])
    predicted = model.predict(np.vstack(features))
    truth = np.concatenate(labels)
    return {name: {"recall": float(np.mean(predicted[truth == name] == name)),
                   "predicted_as": {c: int(np.sum(predicted[truth == name] == c))
                                    for c in _ML["classes"]}}
            for name in ("ground", "stem")}


def _plot_importance(importance: dict[str, float], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = sorted(importance, key=importance.get)
    figure, axis = plt.subplots(figsize=(6.5, 3.8), facecolor="#fcfcfb")
    axis.barh(names, [importance[n] for n in names], color="#2a78d6", height=0.6)
    for row, name in enumerate(names):
        axis.text(importance[name], row, f" {importance[name]:.2f}", va="center", fontsize=8)
    axis.set_title("Which features the model relied on", loc="left", fontsize=11)
    axis.set_xlabel("importance (sums to 1)", color="#52514e")
    for spine in axis.spines.values():
        spine.set_visible(False)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _plot_real_side_view(model: object, path: Path) -> None:
    """A 4 m strip of the real WSF-19 forest, each point coloured by predicted class."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cloud = np.load(WSF_CLOUD)
    centre = float(np.median(cloud[:, 1]))
    nearby = cloud[np.abs(cloud[:, 1] - centre) < 3.0]  # strip + margin for neighbours
    strip = nearby[np.abs(nearby[:, 1] - centre) < 2.0]
    strip = strip[np.random.default_rng(0).choice(len(strip), min(len(strip), 150_000),
                                                 replace=False)]
    predicted = model.predict(point_features(nearby, strip))
    figure, axis = plt.subplots(figsize=(13, 4.5), facecolor="#fcfcfb")
    for name in ("ground", "crown", "shrub", "rock", "stem"):
        chosen = strip[predicted == name]
        axis.scatter(chosen[:, 0], chosen[:, 2], s=0.6, color=COLOURS[name],
                     label=f"{name} ({len(chosen)})", linewidths=0)
    axis.set_title("Real forest (TreeScope WSF-19), each point coloured by the ML model's "
                   "prediction", loc="left", fontsize=11)
    axis.set_xlabel("x (m)", color="#52514e")
    axis.set_ylabel("height above ground (m)", color="#52514e")
    axis.legend(loc="upper left", fontsize=8, markerscale=8, frameon=False)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _write_report(metrics: dict, path: Path) -> None:
    test = metrics["test"]
    lines = ["# ML point classifier (Random Forest)", "",
             f"Trained on {metrics['train_points']} labelled points from simulated forests "
             f"{_ML['train_seeds']}; tested on {metrics['test_points']} points from unseen "
             f"forests {_ML['test_seeds']}.", "",
             f"**Accuracy on unseen forests: {100 * test['accuracy']:.1f} %**", "",
             "| Class | Precision | Recall | F1 | Test points |", "|---|---:|---:|---:|---:|"]
    for i, name in enumerate(test["classes"]):
        lines.append(f"| {name} | {test['precision'][i]:.2f} | {test['recall'][i]:.2f} | "
                     f"{test['f1'][i]:.2f} | {test['support'][i]} |")
    lines += ["", "![Confusion matrix](confusion_matrix.png)", "",
              "![Feature importance](feature_importance.png)", ""]
    real = metrics["real_vat0723"]
    if real:
        lines += ["## Real data check (TreeScope VAT-0723 labelled frames)", "",
                  "These frames contain only ground and trunk points, so only recall can "
                  "be measured (precision needs the other classes).", "",
                  "| True class | Recall | Predicted as |", "|---|---:|---|"]
        for name, row in real.items():
            spread = ", ".join(f"{c} {n}" for c, n in row["predicted_as"].items() if n)
            lines.append(f"| {name} | {row['recall']:.2f} | {spread} |")
        lines.append("")
    lines += ["Features: " + ", ".join(FEATURE_NAMES) + ".", "",
              "Limits: trained only on simulated forests (perfect cylinders, flat leaf "
              "patches); real forests look messier, and real shrub/crown labels are not "
              "available yet to measure those classes on real data."]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
