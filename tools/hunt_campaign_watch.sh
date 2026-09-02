#!/bin/bash
# One watcher over a HUNT CAMPAIGN, not over any single hunt.
#
# It reports CHANGE rather than state, names its subject on every
# line, re-derives the whole picture each pass rather than
# accumulating it in shell variables, and EXITS when something is
# owed -- which is what turns a log into a prompt, since the harness
# notifies on a background command ending.
#
# State lives in FILES, deliberately: /bin/bash here is 3.2, which has
# no associative arrays, and `seen[$name]` on an indexed array
# evaluates its subscript as ARITHMETIC -- a log called
# `two-stores.md` is not arithmetic, and the twenty-third watcher
# fault on this project was that script dying on its first pass.
#
# `grep -c` PRINTS 0 and EXITS 1 when nothing matches, so no reading
# here carries a `|| echo 0` fallback: that appends to a good answer
# rather than replacing it, which is the fifteenth fault and has been
# paid for twice.
#
# Usage: campaign_watch.sh <target-bugs> <hunts-wanted> <interval-s>

set -u

# The STATE lives under dev/hunts (gitignored: logs, worktrees, the
# closed list); the INSTRUMENT lives here, committed, because the
# one that names a defect names the next.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUNTS="$ROOT/dev/hunts"
LOGS="$HUNTS/logs"
STATE="$HUNTS/state"
CLOSED="$HUNTS/closed.txt"       # one line per bug repaired AND tested
TARGET="${1:-24}"
WANT="${2:-8}"
EVERY="${3:-300}"
STALE_MIN=20                     # a brief requires an entry every 15
QUIET_LIMIT=$(( 1800 / EVERY ))  # exit after 30 min of no change

mkdir -p "$LOGS" "$STATE"
touch "$CLOSED"

quiet=0
say() { printf '%s\n' "$*"; }

while true; do
  now=$(date +%H:%M:%S)
  changed=0
  owed=""

  # --- what is closed, re-derived every pass -------------------------
  done_n=$(grep -c . "$CLOSED"; true)
  done_n=${done_n:-0}

  # --- which hunts are alive, judged by their own check-in logs ------
  live=0; stale=""; news=""
  for log in "$LOGS"/*.md; do
    [ -e "$log" ] || continue
    slug=$(basename "$log" .md)
    grep -q '^CAMPAIGN-HUNT-ENDED' "$log" && continue
    age=$(( ( $(date +%s) - $(stat -f %m "$log") ) / 60 ))
    if [ "$age" -le "$STALE_MIN" ]; then
      live=$(( live + 1 ))
    else
      stale="$stale $slug(${age}m)"
    fi
    # report only what is NEW in this log, by byte offset
    off_file="$STATE/$slug.offset"
    [ -f "$off_file" ] || echo 0 > "$off_file"
    off=$(cat "$off_file")
    size=$(stat -f %z "$log")
    if [ "$size" -gt "$off" ]; then
      fresh=$(tail -c +$(( off + 1 )) "$log" | grep -E '^(RESULT|CONFIRMED|TRIED):' | tail -3)
      [ -n "$fresh" ] && news="$news
    $slug: $(printf '%s' "$fresh" | tr '\n' ' | ')"
      echo "$size" > "$off_file"
      changed=1
    fi
    # a confirmation is the one thing that always earns an interrupt
    if tail -c +$(( off + 1 )) "$log" 2>/dev/null | grep -q '^CONFIRMED'; then
      owed="$owed a-confirmation($slug)"
    fi
  done

  # --- the two standing obligations ---------------------------------
  [ "$live" -lt "$WANT" ] && [ "$done_n" -lt "$TARGET" ] && \
    owed="$owed replenish(${live}/${WANT})"
  [ -n "$stale" ] && owed="$owed stale:$stale"
  [ "$done_n" -ge "$TARGET" ] && owed="$owed TARGET-REACHED"

  say "[$now] campaign $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null): \
bugs $done_n/$TARGET closed, hunts $live/$WANT live"
  [ -n "$news" ] && { say "  new since last pass:$news"; }
  [ "$live" -eq 0 ] && [ "$done_n" -lt "$TARGET" ] && say "  nothing running"

  if [ -n "$owed" ]; then
    say "ACTION OWED:$owed"
    exit 0
  fi

  if [ "$changed" -eq 1 ]; then quiet=0; else quiet=$(( quiet + 1 )); fi
  if [ "$quiet" -ge "$QUIET_LIMIT" ]; then
    say "ACTION OWED: quiet for $(( quiet * EVERY / 60 ))m -- read the logs yourself"
    exit 0
  fi
  sleep "$EVERY"
done
