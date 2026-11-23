# Presentation day: what to run, when, and in what order

The live demo is a **bonus**, not a dependency. If anything gets stuck, press
`Ctrl+C` and show the pictures in the slides (they are the same data). Never wait
on stage.

## 1. One day before (once)

```bash
cd ~/projects/Minor_project/canopy-mapping-rover
source .venv/bin/activate
git switch main && git pull                 # latest code
bash presentation/prepare.sh                 # ~5 min: fresh results and images
explorer.exe "$(wslpath -w presentation/images)"
```

- Put the pictures from `presentation/images/` into the slides (which picture goes
  on which slide: `03-demo-commands.md`, section C).
- Check the numbers on slides 11 (ML), 13 and 14 against `results/ml/report.md`,
  `results/demo/report.md` and `docs/real-data.md`.
- **Rehearse the full live demo once:** `bash presentation/live_demo.sh`, on the
  laptop you will present with.

## 2. Ten minutes before presenting

1. Laptop on charge, notifications off, screen brightness up.
2. Open the Ubuntu terminal, make the font bigger (`Ctrl` + `+`), then:
   ```bash
   cd ~/projects/Minor_project/canopy-mapping-rover
   source .venv/bin/activate
   ```
3. Open the slides. Keep the terminal minimised (do not close it).
4. If the laptop was restarted, run `python scripts/show_demo.py --view 3d` once
   and close it, so the first-time slowness does not happen on stage.

## 3. During the presentation (slide 15: live demo, about 3 minutes)

One command in the terminal:

```bash
bash presentation/live_demo.sh
```

Before each step the script prints **"SAY: ..."** (what to tell the audience),
then runs the step when you press **Enter**:

| Step | What appears | Time | What to say (short) |
|---|---|---|---|
| 1 | Simulated forest in a 3-D window (drag to rotate, scroll to zoom, `Q` to close) | ~15 s | "Each dot is one laser hit: blue trunks, orange shrubs, green rocks. The blue line is the true path, the orange line what odometry estimated." |
| 2 | Real forest, only the 0.3-4 m layer, in 3-D | ~10 s | "This is the real forest with everything above 4 m removed: columns are trunks, clumps are shrubs. That is the ladder fuel a drone cannot see." |
| 3 | The whole pipeline runs live (quick mode), then the results table | ~30-60 s | "Drive, odometry, map, ground, trees, ladder fuel and navigation: all from one command." |
| 4 | ML report and the confusion matrix picture | ~5 s | "The Random Forest was trained on 8 forests and tested on 4 new ones: 89 % accuracy. The diagonal shows correct predictions." |
| 5 | Green test runs on GitHub | ~3 s | "Every change runs 67 automatic tests." |

During step 3 the screen stays quiet while it works, so keep talking.
If a 3-D window does not open, press `Ctrl+C` and show the slide picture.

## 4. If something goes wrong

| Problem | What to do |
|---|---|
| 3-D window does not open / `libEGL` warnings | The script already uses software rendering; if it still fails, `Ctrl+C` and show the slide picture |
| `ModuleNotFoundError: canopy` | You forgot `source .venv/bin/activate`, or you are in the wrong folder |
| `normalised_cloud.npy` not found (step 2) | The real forest run was not done on this laptop: show the picture instead |
| Step 3 takes too long | `Ctrl+C`, and show the results table on slide 13 |
| Any other error | Stay calm: say "this is the same result you see on the slide" and show the slide |

## 5. Questions

Read `04-questions-and-answers.md` beforehand. The most likely questions:
"Where is the ML?", "Why only 5 trees on the real data?", "Is the rover real?",
"Why not a drone?". If you do not know an answer, say what the project does
measure, call the rest a limitation or future work, and never claim more than the
numbers show.
