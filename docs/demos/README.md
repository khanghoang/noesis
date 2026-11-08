# Demos

## `mock_noesis.py` — scripted mock of the tree view and main view

A **mock**: no herdr-core, no real agents. It plays a fixed ~40 s script that shows the tree
(spec §3), `]a` attention jump, the main view, a fork (§6.2) and a roll-up into memory (§6.4). The key being
"pressed" is shown in the bottom-right corner.

Record and render (asciinema → agg → H.264 MP4), from the repo root:

```sh
# 1. record in a fixed 120x34 terminal (tmux keeps the size reproducible)
tmux new-session -d -x 120 -y 34 -s rec \
  "nix-shell -p asciinema --run \"asciinema rec -q --overwrite -f asciicast-v2 \
     -c 'python3 docs/demos/mock_noesis.py' docs/demos/noesis-mock.cast\""

# 2. render: agg needs fonts with the box-drawing and status glyphs
nix-shell -p asciinema-agg ffmpeg --run '
  agg --font-dir <dir with JetBrains Mono + DejaVu Sans Mono .ttf> \
      --font-family "JetBrains Mono,DejaVu Sans Mono" --font-size 18 --theme monokai \
      --fps-cap 15 docs/demos/noesis-mock.cast demo.gif &&
  ffmpeg -i demo.gif -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p" \
      -c:v libx264 -crf 20 -preset slow -movflags +faststart -an noesis-mock-demo.mp4'
```

Before rendering, drop the cast's last event (it leaves the alternate screen, which would end the video on a
blank frame). Attach the MP4 to the PR with `gh pr edit <n> --attach noesis-mock-demo.mp4`; don't commit media.
`.cast` files are git-ignored because they're reproducible from the script.

Fonts: JetBrains Mono and DejaVu Sans Mono don't have `⑂` or `⎿`, so the mock shows forks with a `└` connector
instead of the draft `⑂` glyph in spec §3.3.
