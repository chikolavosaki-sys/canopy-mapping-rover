# Presentation kit

Use the [plain-language walkthrough](01-project-explained.md) to learn the system, then rehearse how the simulator turns LiDAR scans into a map and forest measurements.

| File | Purpose |
| --- | --- |
| [Project explained](01-project-explained.md) | The problem, pipeline, results, and key terms |
| [Slides and script](02-slides-and-script.md) | What to show and say for each slide |
| [Demo commands](03-demo-commands.md) | How to generate results and run the live demonstration |
| [Questions and answers](04-questions-and-answers.md) | Answers about design choices, evidence, and limitations |
| [Presentation-day checklist](05-presentation-day.md) | What to prepare and what to open during the demo |
| [Saved figures](images) | Simulator, TreeScope, and classifier figures ready to use |

The [rehearsal script](prepare.sh) generates a fresh survey and figures in `results/runs/demo/`. The [interactive demo](live_demo.sh) walks through the simulator, TreeScope example, and classifier results. Both scripts use Bash. PowerShell commands are included in the [demo guide](03-demo-commands.md).

## Suggested presenter split

| Presenter | Slides | Topic |
| --- | --- | --- |
| Prithvi | 1–5, 9, 11, 16–18 | Problem, outputs, ladder fuel, ML, limitations, and close |
| Anwita | 6–8, 10 | Mapping, tree measurement, and navigation |
| Prajjwal | 12–15 | Evaluation, results, and live demo |

Use the full held-out benchmark for the results slide and the four-trial quick run for the live demonstration. For the real-data example, use the saved figures or rerun the dataset workflow in advance. [Published outcomes](../docs/OUTCOMES.md) · [TreeScope experiment](../docs/real-data.md)
