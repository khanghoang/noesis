# Assets

| File | What it is |
|---|---|
| [`noesis-mock-demo.mp4`](noesis-mock-demo.mp4) | ~40 s H.264 recording of the mock below (shown in the top-level README) |
| [`mock_noesis.py`](mock_noesis.py) | Scripted mock of the tree view and main view. Made-up data, no herdr-core, no real agents |
| [`make-demo.sh`](make-demo.sh) | Rebuilds the MP4 from the mock: asciinema → agg → ffmpeg |

## The mock

`mock_noesis.py` plays a fixed script; the key being "pressed" is shown in the bottom-right corner:

1. Tree view with `@machine` roots and status rolled up from agents (spec §3).
2. `j` / `l` / `h` to move, unfold and fold; `]a` jumps to the agent that needs input.
3. `Enter` opens the main view (the conversation); you answer and the agent goes back to work.
4. `f` forks a thread for a side investigation (§6.2); open it to watch.
5. `u` rolls the finding up into central memory and sends the parent a summary (§6.4).

Run it in any 120×34 terminal to watch it live: `python3 assets/mock_noesis.py`.

## Rebuild the video

```sh
bash assets/make-demo.sh
```

Needs `nix`, `tmux` and `python3`; asciinema, agg, ffmpeg and the fonts come from nixpkgs. The script records
in a fixed 120×34 tmux session, drops the final "leave alternate screen" event (otherwise the video ends on a
blank frame), renders with agg and encodes H.264 MP4 (plays in browsers, QuickTime and GitHub). The
intermediate `.cast` lives in a temp dir and isn't kept.

Fonts: JetBrains Mono plus DejaVu Sans Mono for symbols. Neither has `⑂` or `⎿`, so the mock shows forks with a
`└` connector instead of the draft `⑂` glyph in spec §3.3.

For PRs, attach the MP4 with `gh pr edit <n> --attach assets/noesis-mock-demo.mp4`; that upload is what
GitHub renders as an inline player.
