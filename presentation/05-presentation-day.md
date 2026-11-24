# Presentation-day checklist

## Before the presentation

1. Set up the environment on the laptop you will use. Generate and open the survey map and PNG figures using the [rehearsal commands](03-demo-commands.md).
2. Match the slides to the [published simulator benchmark](../docs/OUTCOMES.md), [recorded TreeScope run](../docs/real-data.md), and [ML evaluation](../results/ml/report.md). The four quick navigation runs are for the live demonstration.
3. If you plan to show the 3D view, rehearse opening and closing it on that laptop. Keep the saved plots ready.

## During the presentation

| Step | What to show |
| --- | --- |
| 1. Synthetic survey | Open the survey map. Point out the reference and estimated routes, tree detections, and ladder-fuel proxy. |
| 2. TreeScope | Show the saved understorey view and heatmap. Explain what the offline recording shows and why real per-tree accuracy remains open. |
| 3. Quick run | Run the four-trial demo if time allows. Open the generated report. |
| 4. Classification | Show the confusion matrix and compare the synthetic and real-data results. |
| 5. Verification | Show the [GitHub Actions runs](https://github.com/chikolavosaki-sys/canopy-mapping-rover/actions/workflows/ci.yml) or describe the automated tests and installation check. |

For the guided Bash walkthrough, run `bash presentation/live_demo.sh` and press **Enter** for each step. For PowerShell, follow the manual walkthrough in the [demo guide](03-demo-commands.md).

## If the live run stalls

Use the prepared map and saved figures. If a 3D viewer fails to open, use the PNG plots. If TreeScope was never downloaded, use the checked-in side view. The [viva questions](04-questions-and-answers.md) cover the most likely follow-ups.
