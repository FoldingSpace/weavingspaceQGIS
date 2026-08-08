#!/bin/bash
# Health check for work that outlasts a turn.
#
#     LOOP_LOGS=/path/to/logs JOB_PATTERN='pytest|make' ./health.sh
#
# Answers the three questions that matter when things go quiet: what
# is running and is it actually working, has a watcher got stuck, and
# is there a finished result nobody has picked up.
LOGS="${LOOP_LOGS:-/tmp/jobs}"
JOBS="${JOB_PATTERN:-python|node|pytest|cargo|make}"

echo "=== $(date '+%H:%M:%S') ==="

# Elapsed AND cpu: a process burning little CPU across a long elapsed
# time is blocked, not busy, and neither number says that alone.
echo "-- running (elapsed | cpu | command)"
ps -A -o etime=,time=,command= | grep -E "$JOBS" | grep -v grep \
  | awk '{printf "   %-10s %-9s %s\n", $1, $2, substr($0, index($0,$3), 62)}'
ps -A -o command= | grep -Eq "$JOBS" || echo "   (nothing running)"

# A watcher with a long elapsed time is either patient or looping on a
# condition that can never come true. It is worth looking at which.
echo "-- watcher loops"
ps -A -o etime=,command= | grep -E "until |while true" | grep -v grep \
  | awk '{printf "   %-10s %s\n", $1, substr($0, index($0,$2), 70)}'

# The LAST LINE, whatever it says. Grepping only for expected progress
# patterns makes an informative log ("refusing to start because...")
# look empty, and a job that declined to run look like one that never
# launched.
echo "-- recent logs (age | lines | last line)"
for f in "$LOGS"/*.log; do
  [ -e "$f" ] || continue
  age=$(( $(date +%s) - $(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f") ))
  [ "$age" -lt 3600 ] || continue
  printf "   %-20s %5ds %4s | %s\n" "$(basename "$f")" "$age" \
    "$(wc -l < "$f" | tr -d ' ')" "$(tail -1 "$f" | cut -c1-56)"
done

# The most common failure: work finished, nobody claimed it, machine
# idle ever since.
echo "-- finished, possibly unclaimed"
grep -l -iE "done|complete|finished|passed|failed" "$LOGS"/*.log 2>/dev/null \
  | while read -r f; do
      printf "   %-20s %s\n" "$(basename "$f")" "$(tail -1 "$f" | cut -c1-56)"
    done
