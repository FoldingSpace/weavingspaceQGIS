#!/usr/bin/env python3
"""Show whether a mutation changes anything a test could see.

    <qgis python> tools/prove_equivalent.py \\
        --file weavingspace_qgis/dialog.py --line 1710 \\
        --old '      combo.blockSignals(True)' \\
        --new '      combo.blockSignals(False)' \\
        --scenario column_appears

A mutation survives when no test fails. That says the SUITE did not
notice; it does not say whether there was anything to notice. This
answers the second question directly: apply the mutation in a copy of
the tree, drive the same scenario against both copies, and compare
everything a test could see. Identical output is the demonstration an
EQUIVALENT entry in tools/mutate_auto.py requires; a difference NAMES
the dimension that moved, which is what a test should then assert.

Why it earns its place beside the mutation tools. Triage by reading
the code and imagining a harm was measured on this project across one
campaign: six of eight harms so imagined were false, and each cost a
test written, run, disproved and withdrawn. The two that held were
found here instead. It is also far cheaper on the expensive end -- a
mutant covered by 220 tests takes some 1,700 seconds to confirm, where
this takes under a minute -- which matters because most of the pool
sits at that end and has never been measured at all.

THE EXECUTION GUARD IS THE POINT. "Identical" means nothing unless the
mutated line actually RAN during the scenario: comparing unmutated
behaviour with itself proves equivalence for anything at all. So the
line is monitored, and a scenario that never reaches it is reported as
VACUOUS rather than as equivalence. The same reasoning is why an
anchor matching more than once is refused: it would mutate one site
while its identical siblings kept the behaviour alive.
"""
import argparse
import difflib
import json
import os
import subprocess
import sys

# Derived, never written down: a hard-coded path meant an earlier tool
# run from inside a git WORKTREE quietly exercised the other checkout,
# giving green results about code nobody was editing. It also keeps
# this file free of a machine path, which check_no_secrets refuses.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def apply_mutation(path, old, new):
  """Replace `old` with `new`, refusing an ambiguous anchor.

  Args:
    path: absolute path to the file inside the SANDBOX.
    old: the exact text to replace. Must appear exactly once.
    new: what to put there.

  Returns:
    None.

  Raises:
    SystemExit: when the anchor matches zero or several times. Several
      is the dangerous case and the reason this is fatal rather than a
      warning: mutating one of two identical sites leaves the other
      doing the work, so the comparison would find no difference and
      report equivalence for a site that may be hiding a real defect.
      That is not hypothetical here -- two blockSignals sites were
      textually identical for two lines, one equivalent and one a
      genuine fault.
  """
  with open(path, encoding="utf-8") as handle:
    source = handle.read()
  found = source.count(old)
  if found != 1:
    sys.exit(f"anchor matches {found} time(s), not once: widen it with "
             f"surrounding lines until it names one site")
  with open(path, "w", encoding="utf-8") as handle:
    handle.write(source.replace(old, new))


def run_probe(tree, scenario, target, line):
  """Run one scenario in one tree and bring back what it saw.

  Args:
    tree: the checkout to run in (the real one, or a sandbox).
    scenario: a key of SCENARIOS in tools/equivalence_scenarios.py.
    target: the mutated file, relative to the tree root.
    line: the mutated line number, watched so a scenario that never
      reaches it can be reported rather than believed.

  Returns:
    (snapshot dict, reached bool). `reached` is False when the line
    never executed, which makes any comparison meaningless.
  """
  runner = os.path.join(tree, "tools", "equivalence_scenarios.py")
  result = subprocess.run(
    [sys.executable, runner, tree, scenario, target, str(line)],
    capture_output=True, text=True, cwd=tree)
  marker = "---PROBE---"
  if marker not in result.stdout:
    sys.exit(f"the probe produced no result in {tree}:\n"
             f"{result.stdout[-800:]}\n{result.stderr[-800:]}")
  payload = json.loads(result.stdout.split(marker, 1)[1])
  return payload["snapshot"], payload["reached"]


def main():
  """Compare a mutated tree against a clean one and report.

  Returns:
    0 when the two are identical (the mutation is unobservable in this
    scenario), 1 when they differ, and 2 when the verdict is VACUOUS
    because the mutated line never ran. Two is deliberately not 0: a
    scenario that misses its line is a broken measurement, not a
    passing one.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--file", required=True,
                      help="the file to mutate, relative to the repo")
  parser.add_argument("--line", required=True, type=int,
                      help="the line the mutation sits on, watched so a "
                           "scenario that never reaches it is reported "
                           "as vacuous rather than as equivalence")
  parser.add_argument("--old", required=True,
                      help="exact text to replace; must match once")
  parser.add_argument("--new", required=True, help="what to put there")
  parser.add_argument("--scenario", required=True,
                      help="which scenario to drive (see "
                           "tools/equivalence_scenarios.py)")
  args = parser.parse_args()

  sys.path.insert(0, HERE)
  from sandbox import discard, make_sandbox

  sandbox = make_sandbox("equivalence")
  try:
    apply_mutation(os.path.join(sandbox, args.file), args.old, args.new)
    plain, plain_ran = run_probe(ROOT, args.scenario, args.file, args.line)
    mutant, _ = run_probe(sandbox, args.scenario, args.file, args.line)
  finally:
    discard(sandbox)

  if not plain_ran:
    print(f"VACUOUS: {args.file}:{args.line} never ran under "
          f"{args.scenario!r}, so the two trees were never given the "
          f"chance to differ. Choose a scenario that reaches the line, "
          f"or write one. Do NOT read this as equivalence.")
    return 2

  left = json.dumps(plain, indent=1, sort_keys=True).splitlines()
  right = json.dumps(mutant, indent=1, sort_keys=True).splitlines()
  if left == right:
    print(f"IDENTICAL over {len(left)} lines, and "
          f"{args.file}:{args.line} DID run: nothing this snapshot can "
          f"see changed. Quote the scenario and the line count as the "
          f"evidence, and remember the claim is only as wide as the "
          f"snapshot.")
    return 0

  print(f"DIFFERS, and here is the dimension that moved -- assert THIS "
        f"rather than a harm you imagined:")
  for row in difflib.unified_diff(left, right, "plain", "mutant",
                                  lineterm="", n=1):
    print("  " + row)
  return 1


if __name__ == "__main__":
  sys.exit(main())
