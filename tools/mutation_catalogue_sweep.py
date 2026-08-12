#!/usr/bin/env python3
"""Run the WHOLE hand-picked mutation catalogue, sharded for speed.

Run under any Python 3 from the repository root:

    python3 tools/mutation_catalogue_sweep.py              # 4 shards
    python3 tools/mutation_catalogue_sweep.py --shards 2

Why this exists. `tools/mutation_check.py --only <name>` proves one
catalogue entry: it breaks the named behaviour in a throwaway clone
and requires the named test to fail. Before a SUBSTANTIAL release the
whole catalogue is run -- a refactor elsewhere can quietly stop an old
test from reaching the behaviour it names, and only re-breaking
everything finds that -- but at well over a hundred entries a serial
sweep takes hours. Mutation JUDGING parallelises safely (measured on
this project: three workers, identical verdicts, unlike full test
suites which degrade each other into false hangs), so the entries are
dealt round-robin across a few shards, each walking its slice one
entry at a time in its own clone.

The caveat that keeps the number honest: under contention a mutant
runs 15-50% slower, and one slowed past a timeout can be recorded as
caught when it merely stalled. Anything reported ATTENTION below, and
any entry whose runtime looks like a stall, is re-run ALONE before
being believed. The sweep is a screen; a surprising verdict gets a
solo confirmation.

Exit status: 0 when every entry was caught, 1 when any needs
attention, with the offending names listed last.
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import threading
import time

# The floor below which a listing is assumed broken rather than
# shrunken. Well under the catalogue's real size, so ordinary pruning
# never trips it.
MINIMUM_CATALOGUE = 100

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def catalogue_names() -> list:
  """Every entry name in tools/mutation_check.py, in catalogue order.

  Returns:
    The names, read by importing the checker itself so this tool can
    never drift from the catalogue it sweeps: an entry added there is
    swept here with no second list to forget to update.
  """
  spec = importlib.util.spec_from_file_location(
    "mutation_check", os.path.join(HERE, "mutation_check.py"))
  module = importlib.util.module_from_spec(spec)
  sys.modules["mutation_check"] = module
  spec.loader.exec_module(module)
  return [entry["name"] for entry in module.MUTATIONS]


def run_shard(names, results, index):
  """Walk one shard's entries serially, recording each verdict.

  Args:
    names: this shard's entry names, in catalogue order.
    results: shared dict of {name: (ok, seconds)}; each shard writes
      only its own names, so no lock is needed beyond the GIL.
    index: the shard number, used only in progress lines.

  Returns:
    None. A non-zero exit from mutation_check is recorded as not-ok
    rather than stopping the shard: the sweep's job is the complete
    list of entries needing attention, not the first one.
  """
  # QGIS's own interpreter, never the system one: this project's
  # environment exports PYTHONHOME for QGIS, under which a system
  # python3 dies instantly. A shell version of this sweep listed the
  # catalogue with the wrong interpreter, got nothing back, and
  # announced a clean sweep of one entry (2026-08-10).
  python = sys.executable
  for name in names:
    started = time.time()
    proc = subprocess.run(
      [python, os.path.join(HERE, "mutation_check.py"), "--only", name],
      cwd=ROOT, capture_output=True, text=True)
    spent = time.time() - started
    results[name] = (proc.returncode == 0, spent)
    verdict = "caught" if proc.returncode == 0 else "ATTENTION"
    print(f"  shard {index}: {verdict:9s} {name} ({spent:.0f}s)",
          flush=True)


def main():
  """Deal the catalogue across shards, run them, and report."""
  parser = argparse.ArgumentParser()
  parser.add_argument("--shards", type=int, default=4,
                      help="concurrent clones (default 4; judging "
                           "parallelises safely, suites do not)")
  parser.add_argument("--slice", default="",
                      help="i/n: take only this share of the "
                           "catalogue, for splitting across MACHINES "
                           "rather than across processes on one")
  args = parser.parse_args()
  names = catalogue_names()
  whole = len(names)
  if args.slice:
    # Splitting across machines as well as across processes. Four
    # shards on one machine turn ninety minutes into twenty-five;
    # four MACHINES each running four shards turn it into seven, and
    # a CI matrix hands out machines for nothing. The slice is taken
    # round-robin, like the shards, so each machine gets a mixture of
    # cheap and expensive entries rather than one machine drawing the
    # whole slow tail.
    index, _, count = args.slice.partition("/")
    index, count = int(index), int(count)
    if not 0 <= index < count:
      sys.exit(f"--slice {args.slice} is not i/n with 0 <= i < n")
    names = names[index::count]
    print(f"slice {index} of {count}: {len(names)} of {whole} entries")
  # A listing this small means the LISTING failed, not that the
  # catalogue shrank. A shell version of this sweep listed the
  # catalogue with the wrong interpreter, got one name back, judged
  # that single entry and announced a clean sweep (2026-08-10). Refuse
  # rather than report success nothing earned; a real shrinkage is a
  # deliberate act and whoever performs it can lower this floor.
  # the floor is about the LISTING, so it is applied to the whole
  # catalogue rather than to a slice: a quarter of the catalogue is
  # legitimately
  # under a hundred, and refusing that would make sharding impossible
  if whole < MINIMUM_CATALOGUE:
    sys.exit(
      f"LISTING FAILED: {whole} entries found, fewer than the "
      f"{MINIMUM_CATALOGUE} this catalogue is known to hold. Not "
      f"sweeping: a sweep of a broken listing reports success it "
      f"never earned. Check that the catalogue imports under THIS "
      f"interpreter.")
  print(f"sweeping {len(names)} catalogue entries "
        f"across {args.shards} shard(s)")
  shards = [names[i::args.shards] for i in range(args.shards)]
  results = {}
  threads = [threading.Thread(target=run_shard,
                              args=(shard, results, i), daemon=True)
             for i, shard in enumerate(shards)]
  started = time.time()
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join()
  spent = time.time() - started

  trouble = [name for name in names if not results.get(name, (False,))[0]]
  # the slowest entries are named so a stall can be told from a slow
  # test: a surprising verdict on one of these is re-run alone
  slowest = sorted(results, key=lambda n: -results[n][1])[:5]
  print(f"\n{len(names) - len(trouble)} of {len(names)} caught "
        f"in {spent / 60:.0f} min")
  print("slowest: " + ", ".join(
    f"{n} ({results[n][1]:.0f}s)" for n in slowest))
  if trouble:
    print("NEEDS ATTENTION (re-run each alone before believing it): "
          + ", ".join(trouble))
    sys.exit(1)
  print("full catalogue clean")


if __name__ == "__main__":
  main()
