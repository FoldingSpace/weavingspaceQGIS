#!/bin/bash
# One cycle of the mutation-score improvement loop, unattended.
#
#     tools/loop/cycle.sh <seed> [sample] [workers]
#
# Records per-test coverage (mandatory: tests missing from the record
# cannot kill anything), samples a batch of mutants, then holds the
# code changed since the last release to the incremental guard. Writes
# every log under $LOOP_LOGS and prints a stage line with a timestamp
# so a watcher can report progress without guessing.
#
# The full procedure this belongs to, including triage and the
# stopping rule, is docs/MUTATION-LOOP.md. Read that first.
set -u
SEED="${1:?usage: cycle.sh <seed> [sample] [workers]}"
SAMPLE="${2:-30}"
WORKERS="${3:-2}"
LOGS="${LOOP_LOGS:-/tmp/weavingspace-loop}"
mkdir -p "$LOGS"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1

# The QGIS whose Python runs everything. Override QGIS_APP elsewhere.
QP="${QGIS_APP:-/Applications/QGIS-final-4_0_3.app}/Contents"
export QT_QPA_PLATFORM=offscreen PYTHONHOME="$QP/Frameworks"
export PROJ_LIB="$QP/Resources/qgis/proj" QGIS_PREFIX_PATH="$QP/MacOS"
PY="$QP/MacOS/python3.12"

# Every stage is checked. A driver that announces CYCLE-DONE whether
# or not its stages ran is worse than no driver: cycle seven's batch
# refused to start against a stale coverage record and the cycle
# reported completion in zero seconds, which read as success.
stage() {
  local label="$1"; shift
  local log="$1"; shift
  echo "[$(date +%H:%M:%S)] $label"
  if ! "$@" > "$log" 2>&1; then
    echo "[$(date +%H:%M:%S)] STAGE FAILED: $label"
    echo "    last line: $(tail -1 "$log")"
    echo "[$(date +%H:%M:%S)] CYCLE ABANDONED at $label"
    exit 1
  fi
}

stage "coverage record" "$LOGS/coverage-$SEED.log" \
  "$PY" -u tools/coverage_per_test.py

stage "batch (seed $SEED, sample $SAMPLE, $WORKERS workers)" \
  "$LOGS/batch-$SEED.log" \
  "$PY" -u tools/mutate_auto.py --sample "$SAMPLE" --seed "$SEED" \
    --workers "$WORKERS"

previous=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$previous" ]; then
  stage "incremental guard since $previous" \
    "$LOGS/incremental-$SEED.log" \
    "$PY" -u tools/mutate_auto.py --since "$previous" \
      --workers "$WORKERS" --require 70
fi
echo "[$(date +%H:%M:%S)] CYCLE-DONE seed $SEED"
