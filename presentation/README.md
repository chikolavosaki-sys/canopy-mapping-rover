# Presentation kit

Everything needed to present the Canopy Mapping Rover, even if you did not
write the code. Read the files in this order:

| File | What it is for |
|---|---|
| [`01-project-explained.md`](01-project-explained.md) | The whole project in plain words: the problem, the idea, how each part works, key terms |
| [`02-slides-and-script.md`](02-slides-and-script.md) | Slide by slide: what to **show** and what to **say** |
| [`03-demo-commands.md`](03-demo-commands.md) | Exact commands: preparing results, the live demo, and what to do if something fails |
| [`04-questions-and-answers.md`](04-questions-and-answers.md) | Questions examiners are likely to ask, with honest answers |
| `prepare.sh` | One command that regenerates all results and copies slide images into `images/` |
| `make_slide_images.py` | Draws the real-forest pictures (used by `prepare.sh`) |
| `images/` | All pictures for the slides (after running `prepare.sh`) |

## Quick plan

1. **One day before:** run `bash presentation/prepare.sh` (about 5 minutes). Put the
   pictures from `images/` into your slides. Use the numbers in
   `02-slides-and-script.md` (they come from `results/demo/report.md` and
   `docs/real-data.md`; re-check them if you re-ran anything).
2. **Practise** the script once each, and try the live demo from
   `03-demo-commands.md` on the laptop you will present with.
3. **On the day:** keep the pictures in the slides as the backup; the live demo is a
   bonus, not a dependency.

## Suggested split (about 12-15 minutes in total)

| Presenter | Slides | Topic |
|---|---|---|
| Prithvi | 1-5, 9, 15-17 | Problem, idea, outputs, ladder fuel, limits, impact, close |
| Anwita | 6-8, 10 | How it works, mapping/odometry, trees, navigation |
| Prajwal | 11-14 | Testing (simulator + real data), results, live demo |

Change it as you like; each slide's script stands on its own.

## The one-sentence summary

> Wildfires climb into treetops through low vegetation ("ladder fuels") that
> drones and satellites cannot see under the canopy; our ground rover's 3-D
> LiDAR maps that hidden layer, measures the trees, and drives itself through
> the forest.
