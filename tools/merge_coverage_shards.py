#!/usr/bin/env python3
"""Combine the per-test coverage written by several sharded runs.

    python3 tools/merge_coverage_shards.py

Reads every ``reports/per-test-coverage.<i>of<n>.json`` and writes the
single ``reports/per-test-coverage.json`` the mutation tools expect.

Sharding the recording is safe in a way that sharding a MEASUREMENT
usually is not: which lines a test touches is a property of that test
alone, and this suite's tests are order-independent by construction --
every one runs with an empty project, which is the rule that makes a
failure name the test that is actually broken. So three processes
recording a third each produce the same map as one process recording
all of it, only sooner.

What sharding does cost is time per test, since concurrent QGIS
processes inflate per-unit times by 15-50%, and that is why the
suite's stall ceilings widen whenever a shard is in force.

Exit status: 0 when the shards were complete and merged, 1 when a
shard is missing or two shards disagree about a test -- both of which
would produce a record that looks healthy and is not.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
  """Merge the shard files, refusing anything that looks incomplete.

  Returns:
    None. Writes reports/per-test-coverage.json and prints how many
    tests came from how many shards, so a reader can see the whole
    suite is accounted for rather than trusting that it is.
  """
  pattern = os.path.join(ROOT, "reports", "per-test-coverage.*of*.json")
  shards = sorted(glob.glob(pattern))
  if not shards:
    sys.exit(f"no shard files matching {pattern}; nothing to merge")

  # Every shard names the total it was part of, so a missing one is
  # arithmetic rather than a guess: three files that each say "of 3"
  # is complete, two of them is not.
  expected = {os.path.basename(f).split("of")[1].split(".")[0]
              for f in shards}
  if len(expected) != 1:
    sys.exit(f"the shard files disagree about how many there are: "
             f"{sorted(os.path.basename(f) for f in shards)}")
  total = int(expected.pop())
  if len(shards) != total:
    sys.exit(f"{len(shards)} shard file(s) present, {total} expected. "
             f"A partial record OVERSTATES survivors, because a test "
             f"missing from it is never offered the chance to notice "
             f"a mutant. Re-run the missing shard rather than merging.")

  # An overlap is two different claims about one test, and the two
  # cases are not equally serious.
  #
  # A test named by several shards where only ONE of them recorded any
  # lines is RECOVERABLE, and the recovery is exact rather than a
  # guess: an empty entry is a shard saying "I did not run this", so
  # the single non-empty entry is the whole truth about that test.
  # This is what a recorder that logged every registration rather than
  # every RUN produced (fixed in tools/coverage_per_test.py on
  # 2026-08-11), and it cost a candidate 56 minutes in -- the data to
  # finish the release was sitting on disk, correct, and this refused
  # it. Salvaging costs nothing and is said out loud.
  #
  # A test with lines from TWO shards is not recoverable and never
  # will be: the deal was not disjoint, so the run measured something
  # other than the suite, and merging would produce a record that
  # looks healthy. That still stops the release.
  merged = {}
  salvaged = []
  for path in shards:
    with open(path, encoding="utf-8") as handle:
      for test, lines in json.load(handle).items():
        if test not in merged:
          merged[test] = lines
          continue
        if merged[test] and lines:
          sys.exit(f"{test!r} was RUN by more than one shard: two "
                   f"shards recorded lines for it, so the deal was "
                   f"not disjoint and this run measured something "
                   f"other than the suite. Re-record; do not merge.")
        # exactly one side ran it, so take that side
        if lines:
          merged[test] = lines
        salvaged.append(test)
  if salvaged:
    print(f"{len(salvaged)} test(s) were named by more than one shard "
          f"with lines from only one, so the empty claims were "
          f"discarded and the recorded one kept. That is exact, not a "
          f"guess -- an empty entry is a shard saying it did not run "
          f"the test -- but it means a recorder logged registrations "
          f"rather than runs, which is worth fixing: e.g. "
          f"{sorted(salvaged)[:3]}")
  out = os.path.join(ROOT, "reports", "per-test-coverage.json")
  with open(out, "w", encoding="utf-8") as handle:
    json.dump(merged, handle, indent=1, sort_keys=True)
  print(f"merged {len(merged)} tests from {total} shards into "
        f"{os.path.relpath(out, ROOT)}")
  for path in shards:
    os.remove(path)


if __name__ == "__main__":
  main()
