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

echo "[$(date +%H:%M:%S)] coverage record"
"$PY" -u tools/coverage_per_test.py > "$LOGS/coverage-$SEED.log" 2>&1

echo "[$(date +%H:%M:%S)] batch (seed $SEED, sample $SAMPLE, $WORKERS workers)"
"$PY" -u tools/mutate_auto.py --sample "$SAMPLE" --seed "$SEED" \
    --workers "$WORKERS" > "$LOGS/batch-$SEED.log" 2>&1

previous=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$previous" ]; then
  echo "[$(date +%H:%M:%S)] incremental guard since $previous"
  "$PY" -u tools/mutate_auto.py --since "$previous" --workers "$WORKERS" \
      --require 70 > "$LOGS/incremental-$SEED.log" 2>&1
fi
echo "[$(date +%H:%M:%S)] CYCLE-DONE seed $SEED"
