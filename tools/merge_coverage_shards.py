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

  merged = {}
  for path in shards:
    with open(path, encoding="utf-8") as handle:
      for test, lines in json.load(handle).items():
        if test in merged:
          sys.exit(f"{test!r} appears in more than one shard; the "
                   f"deal is meant to be disjoint, so this record "
                   f"cannot be trusted")
        merged[test] = lines
  out = os.path.join(ROOT, "reports", "per-test-coverage.json")
  with open(out, "w", encoding="utf-8") as handle:
    json.dump(merged, handle, indent=1, sort_keys=True)
  print(f"merged {len(merged)} tests from {total} shards into "
        f"{os.path.relpath(out, ROOT)}")
  for path in shards:
    os.remove(path)


if __name__ == "__main__":
  main()
