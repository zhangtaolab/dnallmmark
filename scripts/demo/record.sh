#!/usr/bin/env bash
# =====================================================================
# record.sh — the one-command TUI demo GIF regeneration wrapper
# (quick-261015-pex).
#
#   scripts/demo/record.sh SCENE LANG [SPEED]
#
#   SCENE  one of the ten scene names (driver --list-scenes)
#   LANG   en | zh
#   SPEED  agg playback speed (default 1.5; use 2-2.5 for the long
#          training scenes launch-monitor-kill / rerun-from-failures)
#
# Chain: asciinema rec (idle gaps capped at 3s) wrapping the pexpect
# driver -> docs/demo/casts/SCENE-LANG.cast; agg --theme monokai renders
# docs/demo/gifs/SCENE-LANG.gif; the driver's --recorded-row mode then
# refreshes the honesty row in docs/demo/RECORDED.md (real targets from
# the recording's meta sidecar + the on-disk artifact sizes).
#
# The cast header is normalized to the console's pinned pty grid
# (100x30): the driver records from any terminal size, but the console
# always renders 100x30 — players and agg must frame exactly that.
#
# Re-recording re-runs the bounded small training (the demo cells the
# scene names); the EHC-3 single-GPU guard keeps a demo re-record from
# colliding with any live production sweep (it refuses at stage 0).
# =====================================================================
set -euo pipefail

SCENE="${1:?usage: record.sh SCENE LANG [SPEED]}"
LANG="${2:?usage: record.sh SCENE LANG [SPEED]}"
SPEED="${3:-1.5}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CASTS="$ROOT/docs/demo/casts"
GIFS="$ROOT/docs/demo/gifs"
CAST="$CASTS/$SCENE-$LANG.cast"
GIF="$GIFS/$SCENE-$LANG.gif"
mkdir -p "$CASTS" "$GIFS"

DRIVER="uv run --group dev --with pexpect==4.9.0 python scripts/demo/record_tui_demo.py"

cd "$ROOT"
asciinema rec --overwrite --idle-time-limit 3 \
    -c "$DRIVER --scene $SCENE --lang $LANG" "$CAST"

# asciinema rec does NOT propagate the wrapped command's exit status —
# the driver's meta sidecar is the authoritative success signal
META="$ROOT/docs/demo/.meta-$SCENE-$LANG.json"
uv run --group dev python - "$META" <<'PYCHECK'
import json, sys
meta = json.load(open(sys.argv[1], encoding="utf-8"))
if meta.get("exit_code") != 0:
    sys.exit(f"driver failed (exit_code={meta.get('exit_code')}) — "
             "the cast is incomplete; fix and re-record")
PYCHECK

# Normalize the cast header to the pinned console grid (100x30).
uv run --group dev python - "$CAST" <<'PYFIX'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    lines = handle.read().splitlines()
header = json.loads(lines[0])
header["width"], header["height"] = 100, 30
lines[0] = json.dumps(header, ensure_ascii=False)
with open(path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
PYFIX

agg --theme monokai --speed "$SPEED" "$CAST" "$GIF"

$DRIVER --recorded-row "$SCENE" --lang "$LANG"
echo "recorded: $GIF"
