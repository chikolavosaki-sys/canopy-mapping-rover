"""Make the real-forest slide images from the WSF-19 analysis (no 3-D window needed).

    python presentation/make_slide_images.py

Needs ``results/real/wsf19/analysis/`` from the commands in
``presentation/03-demo-commands.md`` (section "Real forest run"). Writes:

- images/real_top_views.png - the same forest from above: all heights vs only
  0.3-4 m (the understorey / ladder-fuel layer the rover maps)
- images/real_side_view.png - a 4 m wide strip from the side: ground, trunks,
  shrubs, and the drift "ladders" on some trunks
"""

import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results" / "real" / "wsf19" / "analysis"
OUT = Path(__file__).resolve().parent / "images"
INK, MUTED, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
TRUNK = "#2a78d6"
MAX_POINTS = 300_000  # enough for a picture, fast to draw


def main() -> None:
    """Load the real-forest cloud and write both slide images."""
    import matplotlib

    matplotlib.use("Agg")
    cloud_path = ANALYSIS / "normalised_cloud.npy"
    if not cloud_path.exists():
        raise SystemExit(f"{cloud_path} not found: run the real-forest commands first")
    points = np.load(cloud_path)
    rng = np.random.default_rng(0)
    if len(points) > MAX_POINTS:
        points = points[rng.choice(len(points), MAX_POINTS, replace=False)]
    stems = _stems(ANALYSIS / "trees.csv")
    OUT.mkdir(exist_ok=True)
    _top_views(points, stems, OUT / "real_top_views.png")
    _side_view(points, OUT / "real_side_view.png")
    print(f"Wrote real_top_views.png and real_side_view.png to {OUT}")


def _stems(path: Path) -> np.ndarray:
    if not path.exists():
        return np.empty((0, 3))
    rows = list(csv.DictReader(path.open()))
    return np.array([[float(r["x"]), float(r["y"]), float(r["dbh"])] for r in rows]).reshape(-1, 3)


def _greens():
    """Single-hue green ramp, light to dark, without the near-white start."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("heights", plt.cm.Greens(np.linspace(0.35, 1, 256)))


def _style(axis, title: str) -> None:
    axis.set_title(title, loc="left", color=INK, fontsize=11)
    axis.set_facecolor(SURFACE)
    axis.tick_params(colors=MUTED, labelsize=8)
    axis.set_xlabel("x (m)", color=MUTED)
    for spine in axis.spines.values():
        spine.set_visible(False)


def _top_views(points: np.ndarray, stems: np.ndarray, path: Path) -> None:
    import matplotlib.pyplot as plt

    figure, (top, under) = plt.subplots(1, 2, figsize=(14, 6.2), facecolor=SURFACE)
    above = points[np.argsort(points[:, 2])]  # draw highest last, as seen from above
    everything = top.scatter(above[:, 0], above[:, 1], c=np.clip(above[:, 2], 0, 15), s=0.3,
                             cmap=_greens(), vmin=0, vmax=15, linewidths=0)
    _style(top, "All heights, seen from above (white centre = LiDAR blind zone)")
    figure.colorbar(everything, ax=top, shrink=0.8).set_label("height (m)", color=MUTED)
    low = points[(points[:, 2] > 0.3) & (points[:, 2] < 4.0)]
    image = under.scatter(low[:, 0], low[:, 1], c=low[:, 2], s=0.5, cmap=_greens(),
                          vmin=0.3, vmax=4.0, linewidths=0)
    for x, y, dbh in stems:
        under.add_patch(plt.Circle((x, y), max(dbh, 0.6), fill=False, color=TRUNK, lw=1.5))
    _style(under, f"Only 0.3-4 m: shrubs and trunks (ladder-fuel layer); "
                  f"blue rings = {len(stems)} detected stems")
    for axis in (top, under):
        axis.set_aspect("equal")
    top.set_ylabel("y (m)", color=MUTED)
    figure.colorbar(image, ax=under, shrink=0.8).set_label("height (m)", color=MUTED)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _side_view(points: np.ndarray, path: Path) -> None:
    import matplotlib.pyplot as plt

    centre_y = float(np.median(points[:, 1]))
    strip = points[np.abs(points[:, 1] - centre_y) < 2.0]
    figure, axis = plt.subplots(figsize=(13, 4.5), facecolor=SURFACE)
    axis.scatter(strip[:, 0], strip[:, 2], c=np.clip(strip[:, 2], 0, 15), s=0.4,
                 cmap=_greens(), vmin=0, vmax=15, linewidths=0)
    for height in (1.0, 4.0):  # the ladder-fuel band
        axis.axhline(height, color=MUTED, lw=0.8, ls="--")
    axis.text(axis.get_xlim()[0], 2.3, "  ladder-fuel band 1-4 m", color=INK, fontsize=9)
    _style(axis, "Side view of a 4 m wide strip: ground at 0 m, trunks as columns; "
                 "repeated slanted bands on a trunk = odometry drift")
    axis.set_ylabel("height above ground (m)", color=MUTED)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


if __name__ == "__main__":
    main()
