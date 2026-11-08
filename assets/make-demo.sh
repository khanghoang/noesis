#!/usr/bin/env bash
# Rebuild assets/noesis-mock-demo.mp4 from assets/mock_noesis.py.
#
#   bash assets/make-demo.sh            # run from anywhere; needs nix, tmux, python3
#
# Steps: record the scripted mock with asciinema in a fixed 120x34 tmux session,
# drop the final "leave alternate screen" event (otherwise the video ends blank),
# render with agg, then encode H.264 MP4 with ffmpeg.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cast="$work/noesis-mock.cast"
out="$here/noesis-mock-demo.mp4"

# 1. record
sock="noesis-demo-$$"
tmux -L "$sock" new-session -d -x 120 -y 34 -s rec \
  "TERM=xterm-256color nix-shell -p asciinema --run \"asciinema rec -q --overwrite -f asciicast-v2 -t 'noesis mock demo' -c 'python3 -I $here/mock_noesis.py' $cast\"; tmux -L $sock wait-for -S done"
tmux -L "$sock" wait-for done
tmux -L "$sock" kill-server 2>/dev/null || true

# 2. trim the exit event and tidy the header
python3 -I - "$cast" <<'PY'
import json, sys
path = sys.argv[1]
lines = open(path).read().splitlines()
head = json.loads(lines[0])
head["command"] = "python3 assets/mock_noesis.py"
head.pop("env", None)
events = [json.loads(l) for l in lines[1:]]
while events and (events[-1][1] != "o" or "?1049l" in events[-1][2]):
    events.pop()
open(path, "w").write("\n".join([json.dumps(head)] + [json.dumps(e, ensure_ascii=False) for e in events]) + "\n")
PY

# 3. fonts: JetBrains Mono for text, DejaVu Sans Mono for the symbols it lacks (⚠ ✓ ✕ …)
fonts="$work/fonts"
mkdir -p "$fonts"
jb="$(nix-build '<nixpkgs>' -A jetbrains-mono --no-out-link)"
dv="$(nix-build '<nixpkgs>' -A dejavu_fonts --no-out-link)"
cp "$jb"/share/fonts/truetype/JetBrainsMono-{Regular,Bold}.ttf "$fonts/"
cp "$dv"/share/fonts/truetype/DejaVuSansMono{,-Bold}.ttf "$fonts/"

# 4. render
nix-shell -p asciinema-agg ffmpeg --run "
  agg --font-dir '$fonts' --font-family 'JetBrains Mono,DejaVu Sans Mono' --font-size 18 \
      --theme monokai --fps-cap 15 --last-frame-duration 2 '$cast' '$work/demo.gif' &&
  ffmpeg -y -v error -i '$work/demo.gif' \
      -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos,format=yuv420p' \
      -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 20 -preset slow -r 15 \
      -movflags +faststart -an '$out' &&
  ffmpeg -v error -i '$out' -f null -
"
echo "wrote $out ($(du -h "$out" | cut -f1))"
