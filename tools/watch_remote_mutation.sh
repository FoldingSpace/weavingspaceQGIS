#!/bin/bash
# Dispatch a mutation run on GitHub and report it until it finishes.
#
#   bash tools/watch_remote_mutation.sh <branch> catalogue|incremental|both [since-tag]
#
# WHY REMOTE. Both instruments want a machine to themselves for a long
# time: the catalogue sweep is hours, and the incremental guard has to
# record per-test coverage before it can mutate anything. Run either
# here and the development machine is unusable for the rest of the
# afternoon, which in practice means they are run rarely -- and an
# instrument used rarely is one whose findings arrive too late to act
# on. GitHub hands out four machines for the sweep's slices at no cost
# to this one.
#
# WHY A WATCHER RATHER THAN `gh run watch`. Three properties this
# project has paid for (docs/MUTATION-LOOP.md, and the
# long-job-supervision skill):
#
#   it reports CHANGE, not state, so a job that has been running for
#   an hour does not re-announce itself every poll;
#   it reports every TERMINAL state, not just success, because a
#   watcher that matches only good news is indistinguishable from one
#   that has died;
#   its SILENCE is a signal -- if no run appears within two minutes
#   of dispatch, the run was never created, and that is worth knowing
#   in a minute rather than in an hour.
#
# It prints the artifact names at the end: the findings are in those,
# not in the exit status, because these runs REPORT rather than gate.
set -u
BRANCH="${1:?usage: watch_remote_mutation.sh <branch> <what> [since-tag]}"
WHAT="${2:?catalogue, incremental or both}"
SINCE="${3:-v0.24.0}"
cd "$(dirname "$0")/.."

echo "dispatching mutation/${WHAT} on ${BRANCH} (since ${SINCE})"
gh workflow run mutation.yml --ref "$BRANCH" \
  -f what="$WHAT" -f since="$SINCE" || exit 1

# The dispatch API returns nothing useful, so the run has to be found.
# Match on the workflow AND the branch: another workflow starting at
# the same moment must not be mistaken for this one.
RUN=""
for _ in $(seq 1 20); do
  sleep 6
  RUN=$(gh run list --workflow mutation.yml --branch "$BRANCH" \
        --limit 1 --json databaseId,status \
        --jq '.[0] | select(.status != "completed") | .databaseId' 2>/dev/null)
  [ -n "$RUN" ] && break
done
if [ -z "$RUN" ]; then
  echo "NO RUN APPEARED within two minutes of dispatching."
  echo "It was not created. Check that mutation.yml is on ${BRANCH}:"
  echo "workflow_dispatch only offers workflows present on the ref."
  exit 1
fi
echo "RUN APPEARED: $(gh run view "$RUN" --json url --jq .url)"

# Report only what has CHANGED since the last poll.
PREVIOUS=""
while true; do
  NOW=$(gh run view "$RUN" --json jobs \
        --jq '.jobs[] | "\(.conclusion // .status)\t\(.name)"' 2>/dev/null)
  if [ "$NOW" != "$PREVIOUS" ] && [ -n "$NOW" ]; then
    echo "--- $(date '+%H:%M') ---"
    echo "$NOW" | sed 's/^/  /'
    PREVIOUS="$NOW"
  fi
  STATUS=$(gh run view "$RUN" --json status --jq .status 2>/dev/null)
  [ "$STATUS" = "completed" ] && break
  sleep 120
done

echo "FINISHED: $(gh run view "$RUN" --json conclusion --jq .conclusion)"
echo "The findings are in the artifacts, not the exit status:"
gh run view "$RUN" --json jobs \
  --jq '.jobs[] | "  \(.conclusion)\t\(.name)"'
gh api "repos/{owner}/{repo}/actions/runs/${RUN}/artifacts" \
  --jq '.artifacts[] | "  artifact: \(.name)"' 2>/dev/null
echo "Download with: gh run download ${RUN}"
