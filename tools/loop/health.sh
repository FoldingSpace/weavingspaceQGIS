#!/bin/bash
# Session health check: what is running, what is stuck, what is done.
#
# The three failure modes worth catching, each of which has already
# happened in this session:
#   - a watcher looping forever on a condition that can never be true
#     (12 hours, polling for a string the tool never prints);
#   - a job alive but making no progress (blocked, not busy: the tell
#     is CPU time far below elapsed time);
#   - a job FINISHED whose result nobody has picked up, leaving the
#     machine idle when it could be working.
# Where the loop writes its logs. Override with LOOP_LOGS.
SP="${LOOP_LOGS:-/tmp/weavingspace-loop}"

echo "=== $(date '+%H:%M:%S') ==="

echo "-- running work (elapsed | cpu | command)"
ps -A -o etime=,time=,command= \
  | grep -E "python3.12 -u (tools|tests)|mutate_auto|coverage_per_test|run_tests|release.py" \
  | grep -v grep \
  | awk '{printf "   %-10s %-9s %s\n", $1, $2, substr($0, index($0,$3), 62)}'
[ -z "$(pgrep -f 'python3.12 -u (tools|tests)')" ] && echo "   (nothing running)"

echo "-- watcher loops (long elapsed here means a stuck poll)"
ps -A -o etime=,command= | grep -E "until grep|while true" | grep -v grep \
  | awk '{printf "   %-10s %s\n", $1, substr($0, index($0,$2), 70)}'

echo "-- logs (age of last write; stale + process alive = stuck)"
for f in "$SP"/*.log; do
  [ -e "$f" ] || continue
  age=$(( $(date +%s) - $(stat -f %m "$f") ))
  if [ "$age" -lt 3600 ]; then
    # the LAST LINE, whatever it says. Grepping only for expected
    # progress patterns once made an informative 350-byte log ("STALE
    # COVERAGE: ... re-record first") look empty, and a job that had
    # refused to start look like a job that had never been launched.
    printf "   %-20s %4ds ago  %3s lines | %s\n" "$(basename "$f")" "$age" \
      "$(wc -l < "$f" | tr -d ' ')" "$(tail -1 "$f" | cut -c1-58)"
  fi
done

echo "-- finished but unclaimed (a result waiting for the next step)"
for f in "$SP"/batch*.log "$SP"/incremental.log; do
  [ -e "$f" ] || continue
  grep -l "kill rate" "$f" 2>/dev/null | while read -r done_log; do
    printf "   %-22s %s\n" "$(basename "$done_log")" \
      "$(grep -h 'kill rate' "$done_log" | tail -1)"
  done
done

echo "-- leftovers"
n=$(ls -d /var/folders/*/*/T/weavingspace-* 2>/dev/null | wc -l | tr -d ' ')
echo "   sandboxes: $n"
echo "   swap: $(sysctl -n vm.swapusage | sed 's/total = //;s/  used/, used/')"
