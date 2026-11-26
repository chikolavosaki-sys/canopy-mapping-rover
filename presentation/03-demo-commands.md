# Rehearse the demo

Run these commands from the project folder after [setup](../docs/SETUP.md). The rehearsal uses the simulated forest and generates its own outputs. A fresh clone already includes the saved TreeScope and classifier figures.

## Generate the survey and figures

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --seed 0 --fast --out results/runs/demo
.\.venv\Scripts\python.exe scripts/show_demo.py --out results/runs/demo/figures
```

**Bash**

```bash
bash presentation/prepare.sh
```

| File | What to show | Slides |
| --- | --- | --- |
| `results/runs/demo/survey_map.png` | Estimated and reference routes, tree detections, and ladder-fuel proxy | 13, 15 |
| `results/runs/demo/trees.csv` | Tree positions and estimated diameters in metres | 13 |
| `results/runs/demo/figures/lidar_scan.png` | A simulated LiDAR scan | 5, 7 |
| `results/runs/demo/figures/odometry.png` | Estimated path and position error | 7 |
| `results/runs/demo/figures/forest_map.png` | One navigation run in a simulated forest | 5, 10 |
| [`real_side_view.png`](images/real_side_view.png) and [`real_top_views.png`](images/real_top_views.png) | Saved TreeScope views of the forest and understorey | 1, 8, 9, 14 |
| [`real_ladder_fuel.png`](images/real_ladder_fuel.png) | The saved TreeScope ladder-fuel heatmap | 5, 14 |
| [`ml_confusion_matrix.png`](images/ml_confusion_matrix.png) | Random Forest predictions on unseen simulated forests | 11 |
| [`ml_feature_importance.png`](images/ml_feature_importance.png) | Feature rankings from the Random Forest | 11 |

The quick demo runs four navigation trials. For the full 80-trial benchmark on seeds 3000–3019, use the command in [outcomes](../docs/OUTCOMES.md#reproduce-the-benchmark).

## Walk through the results

1. Show the prepared survey map. The solid line is the simulated reference route, the dashed line is the LiDAR estimate, and the blue crosses mark detected trees.
2. If time allows, rerun the quick survey. Open `trees.csv` or `summary.json` and point out the matched trees and the four navigation trials.
3. Use the TreeScope figures to illustrate the offline mapping workflow and the [real-data limitations](../docs/real-data.md).
4. Use the confusion matrix to discuss the synthetic classifier result and the [real-data recall check](../results/ml/report.md#real-data-check-treescope-vat-0723-labelled-frames).

With Bash you can run `bash presentation/live_demo.sh` for an interactive walkthrough. For a 3D view on its own, add `--view 3d` to the `show_demo.py` command. The interactive walkthrough points to the saved figures if a viewer fails and continues to the next step.

## Optional real-data rehearsal

Follow the [TreeScope guide](../docs/running-on-real-data.md) to generate a local WSF-19 analysis. To regenerate the side and top views from that analysis, use the Python interpreter from your environment:

```bash
python presentation/make_slide_images.py --analysis results/runs/wsf19/analysis --out results/runs/wsf19/figures
```

The interactive demo can open the fresh height-normalised cloud when available. It points you to the saved TreeScope side view if the data is absent.

## Standalone odometry

With the environment activated:

```bash
canopy-odometry --synthetic 0 --out results/runs/odom-synthetic
canopy-odometry --synthetic 0 --odometry all-returns --out results/runs/odom-synthetic-baseline
```

Compare `odometry_drift_percent` in the two `summary.json` files. The default synthetic command uses ground-filtered alignment. Recorded bags and NPY frame inputs use all valid returns.
