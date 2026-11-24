# Presentation kit

Everything needed to present the Canopy Mapping Rover, even if you did not
write the code. Read the files in this order:

| File | What it is for |
|---|---|
| [`01-project-explained.md`](01-project-explained.md) | The whole project in plain words: the problem, the idea, how each part works, key terms |
| [`02-slides-and-script.md`](02-slides-and-script.md) | Slide by slide: what to **show** and what to **say** |
| [`03-demo-commands.md`](03-demo-commands.md) | Exact commands: preparing results, the live demo, and what to do if something fails |
| [`04-questions-and-answers.md`](04-questions-and-answers.md) | Questions examiners are likely to ask, with honest answers |
| [`05-presentation-day.md`](05-presentation-day.md) | **Presentation day checklist:** what to run, when, and what to say |
| `live_demo.sh` | The live demo: press Enter for each step; it shows what to say |
| `prepare.sh` | Regenerates mapping figures and copies the saved ML benchmark figures into `images/` |
| `make_slide_images.py` | Draws the real-forest pictures (used by `prepare.sh`) |
| `images/` | All pictures for the slides (after running `prepare.sh`) |

## Quick plan

1. **Before the presentation**, run the [rehearsal commands](03-demo-commands.md).
   Use the current simulator figures from `results/semester-demo/` and the
   saved TreeScope figures from `images/`. The simulated benchmark and
   earlier TreeScope run are documented in
   [OUTCOMES.md](../docs/OUTCOMES.md) and [real-data.md](../docs/real-data.md).
2. **Practise** the script once each, and try the live demo from
   `03-demo-commands.md` on the laptop you will present with.
3. **On the day**, start with the saved survey map. Run the quick simulated
   demo live if there is time.

## Suggested split (about 12-15 minutes in total)

| Presenter | Slides | Topic |
|---|---|---|
| Prithvi | 1-5, 9, 11, 16-18 | Problem, idea, outputs, ladder fuel, ML, limits, impact, close |
| Anwita | 6-8, 10 | How it works, mapping/odometry, trees, navigation |
| Prajwal | 12-15 | Testing (simulator + real data), results, live demo |

Change it as you like; each slide's script stands on its own.

## The one-sentence summary

> Wildfires climb into treetops through low vegetation ("ladder fuels") that
> drones and satellites cannot see under the canopy; our ground rover's 3-D
> LiDAR maps that hidden layer, measures the trees, and drives itself through
> the forest.
