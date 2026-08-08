#!/usr/bin/env python3
"""Generate mutants automatically, run only the tests that could
notice them, and report an honest first-run kill rate.

    QT_QPA_PLATFORM=offscreen ... <qgis python> tools/mutate_auto.py \\
        --sample 15 --seed 1

Why not just add more entries to tools/mutation_check.py: those are
hand-picked, aimed at behaviours somebody already believed were
guarded. A kill rate over mutants chosen that way measures the
chooser's judgement, not the suite. These are chosen by a seeded
random walk over the syntax tree, so the rate they produce is a
measurement.

How it stays affordable. Running the whole suite per mutant costs
minutes; most mutants can only be noticed by a handful of tests. So
tools/coverage_per_test.py records which lines each test executes,
and each mutant runs ONLY the tests that touch its line — usually
seconds. Mutants on lines no test reaches are reported separately as
UNCOVERED rather than counted as survivors: nothing failed, because
nothing looked.

Mutation operators, all chosen to change BEHAVIOUR rather than
appearance:

  comparisons   ==  !=  <  <=  >  >=   swapped for a neighbour
  booleans      True <-> False, and <-> or
  numbers       n -> n + 1 (and 0 -> 1), which breaks off-by-one
                guards and thresholds
  calls         a statement that is just a call (setX(...),
                append(...)) removed
  returns       return <expr> -> return None
  conditions    if <test> -> if not <test>

Deliberately NOT mutated, and the exclusions are listed here rather
than buried, because quietly removing awkward operators is how a
mutation score becomes a vanity metric:

  * string literals -- a changed tooltip or window title cannot be
    caught by any test worth writing, and there are hundreds of them;
  * table column widths in pixels -- 55 becoming 56 is invisible, and
    the only test that could catch it would pin exact pixel values and
    break on every legitimate layout tweak. This exclusion is kept
    deliberately narrow. Everything geometric that carries LOGIC stays
    in: the dialog's computed height, the preview canvas minimum, the
    toggle switch's size, control ranges and steps, and of course
    every spatial geometry in the tiling itself. "Geometry" in this
    application usually means the map, not the chrome;
  * docstrings, logging, and anything inside tests/ or vendor/.

Everything else stays in, including mutants that are awkward to kill.
"""

import argparse
import ast
import math
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "weavingspace_qgis")
TARGETS = ["dialog.py", "bridge.py", "catalog.py", "worker.py", "compat.py"]
COVERAGE = os.path.join(ROOT, "reports", "per-test-coverage.json")

# {file: {line numbers that run at import}}, filled in by main()
MODULE_LEVEL = {}

# The one call whose effect is invisible chrome. Kept to a single
# entry on purpose: a broad list would have swallowed resize() (which
# computes the dialog height from its content), setMinimumSize (the
# preview canvas), and setSpacing -- spacing is a distance in METRES
# in this application, not a layout gap.
COSMETIC = ("setColumnWidth",)

# Mutants proven to make no observable difference, so they belong
# outside the denominator rather than inside it as phantom failures.
# Each one needs EVIDENCE: "it looks harmless" is how a mutation score
# becomes a vanity metric. The evidence here comes from applying the
# mutation in a sandbox and comparing everything a test could see.
EQUIVALENT = [
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "self.opt_over_under.blockSignals(True)",
    "mutation": "True -> False",
    "reason":
      "The over-under field's signals are blocked while a family "
      "change resets them. Unblocked, the reset calls _queue_preview "
      "a second time, which RESTARTS the debounce timer the family "
      "change had already started -- the same single rebuild happens, "
      "a fraction of a second later.",
    "evidence":
      "Applied in a sandbox and compared after a family change: unit "
      "n, every tile WKT, the field text, table row count, preview "
      "labels and all element assignments were identical.",
  },
]

COMPARISON_SWAP = {
  ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.LtE, ast.LtE: ast.Lt,
  ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Is: ast.IsNot,
  ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In,
}


class Mutant:
  """One candidate change to one line of one file."""

  def __init__(self, path, line, kind, before, after):
    self.path = path        # repo-relative
    self.line = line        # 1-based
    self.kind = kind        # which operator produced it
    self.before = before    # the original source line
    self.after = after      # the mutated source line

  def __repr__(self):
    return f"{self.path}:{self.line} [{self.kind}]"


def candidates(path):
  """Every mutation this file admits.

  Args:
    path: absolute path to a plugin module.

  Returns:
    A list of Mutant objects. Mutations are expressed as whole-line
    rewrites, which keeps applying and reverting them trivial and
    means a mutant can never leave a file half-edited.
  """
  with open(path, encoding="utf-8") as f:
    source = f.read()
  lines = source.splitlines()
  rel = os.path.relpath(path, ROOT)
  try:
    tree = ast.parse(source, path)
  except SyntaxError:
    return []
  out = []

  def line_of(node):
    return getattr(node, "lineno", None)

  for node in ast.walk(tree):
    line = line_of(node)
    if not line or line > len(lines):
      continue
    text = lines[line - 1]
    stripped = text.strip()
    if stripped.startswith("#") or '"""' in text:
      continue

    if isinstance(node, ast.Compare) and node.ops:
      op = type(node.ops[0])
      if op in COMPARISON_SWAP:
        pairs = {ast.Eq: ("==", "!="), ast.NotEq: ("!=", "=="),
                 ast.Lt: ("<", "<="), ast.LtE: ("<=", "<"),
                 ast.Gt: (">", ">="), ast.GtE: (">=", ">"),
                 ast.Is: (" is ", " is not "),
                 ast.IsNot: (" is not ", " is "),
                 ast.In: (" in ", " not in "),
                 ast.NotIn: (" not in ", " in ")}
        old, new = pairs[op]
        if old in text and text.count(old) == 1:
          out.append(Mutant(rel, line, f"compare {old.strip()}->"
                            f"{new.strip()}", text,
                            text.replace(old, new, 1)))

    elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
      word, other = ("True", "False") if node.value else ("False", "True")
      if text.count(word) == 1:
        out.append(Mutant(rel, line, f"bool {word}->{other}", text,
                          text.replace(word, other, 1)))

    elif isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
      literal = str(node.value)
      if text.count(literal) == 1 and abs(node.value) < 10_000 \
              and not any(c in text for c in COSMETIC):
        out.append(Mutant(rel, line, f"number {literal}->"
                          f"{node.value + 1}", text,
                          text.replace(literal, str(node.value + 1), 1)))

    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
      indent = text[:len(text) - len(text.lstrip())]
      if stripped and not stripped.startswith(("print", "raise")) \
              and not any(c in text for c in COSMETIC) \
              and text.rstrip().endswith(")"):
        out.append(Mutant(rel, line, "call removed", text,
                          f"{indent}pass  # mutant: call removed"))

    elif isinstance(node, ast.Return) and node.value is not None:
      indent = text[:len(text) - len(text.lstrip())]
      if stripped.startswith("return ") and text.rstrip().count("(") == \
              text.rstrip().count(")"):
        out.append(Mutant(rel, line, "return None", text,
                          f"{indent}return None  # mutant"))

  seen, unique = set(), []
  for m in out:
    key = (m.path, m.line, m.kind)
    if key not in seen and m.after != m.before:
      seen.add(key)
      unique.append(m)
  return unique


def display_to_function():
  """Map each test's display name to its function name.

  The coverage map keys tests the way the suite reports them ("UI vs
  library: clipped edges"), because that is what check() is given.
  Running one needs the function name instead. Getting this wrong is
  not a subtle failure -- getattr raises, the runner dies, and every
  mutant looks killed by a harness that never ran a test, which is
  precisely what the control run caught.

  Returns:
    {display name: function name} read from the check() calls in
    tests/run_tests.py.
  """
  import re
  with open(os.path.join(ROOT, "tests", "run_tests.py"),
            encoding="utf-8") as f:
    source = f.read()
  pairs = re.findall(r'check\(\s*"([^"]+)",\s*\n?\s*(test_\w+)\)',
                     source)
  return dict(pairs)


def clopper_pearson_lower(killed, total, alpha=0.025):
  """The one-sided 95%% lower bound on the true kill rate.

  Args:
    killed: mutants the suite caught.
    total: mutants tried (equivalents already removed).
    alpha: tail mass left below the bound. The default 0.025 is the
      LOWER LIMIT OF THE TWO-SIDED 95%% INTERVAL, deliberately the
      conservative convention: a one-sided 95%% bound (alpha=0.05)
      would read several points higher for the same data, and
      choosing the flattering convention is precisely the kind of
      quiet thumb on the scale this campaign is meant to avoid.

  Returns:
    The largest rate p for which seeing this many kills would still
    be unsurprising -- i.e. we are 95%% confident the true rate is at
    least this. Exact (Clopper-Pearson), computed by bisecting the
    binomial tail, so it needs no scipy and stays honest at the small
    sample sizes a mutation campaign can afford.

  Why a bound rather than the raw fraction: 19 kills out of 20 looks
  like 95%%, but a suite whose true rate is 75%% produces that result
  often enough that the raw number cannot support a claim of 70%%.
  The bound is what the sample can actually defend.
  """
  if total == 0 or killed == 0:
    return 0.0
  low, high = 0.0, 1.0
  for _ in range(200):
    mid = (low + high) / 2
    tail = sum(math.comb(total, i) * mid ** i * (1 - mid) ** (total - i)
               for i in range(killed, total + 1))
    if tail > alpha:
      high = mid
    else:
      low = mid
  return (low + high) / 2


def suite_stamp():
  """Which version of the test suite this measurement was taken against.

  Returns:
    A human-readable string: how many tests ran and when the suite was
    last edited.

  A mutation score is a property of a SUITE, not of a project, and it
  expires the moment the suite changes -- so the number is worth
  little without saying which suite earned it. A checksum would also
  detect edits, but nobody here is forging test results; the useful
  question is "is this still current?", and a date and a test count
  answer it at a glance where a hex digest does not.
  """
  path = os.path.join(ROOT, "tests", "run_tests.py")
  with open(path, encoding="utf-8") as f:
    tests = f.read().count("\n  check(")
  edited = time.strftime("%Y-%m-%d %H:%M",
                         time.localtime(os.path.getmtime(path)))
  return f"{tests} tests, last edited {edited}"


def is_equivalent(mutant):
  """Is this a mutation already PROVEN to change nothing observable?

  Args:
    mutant: a candidate mutation.

  Returns:
    True if it matches an entry in EQUIVALENT, in which case it is
    dropped before sampling rather than counted as a survivor. Every
    entry carries its evidence; nothing is excluded on a hunch.
  """
  for known in EQUIVALENT:
    if mutant.path.endswith(known["file"]) and known["snippet"] in mutant.before:
      return True
  return False


def module_level_lines(path):
  """Lines that run at IMPORT time rather than inside a function.

  Args:
    path: absolute path to a module.

  Returns:
    A set of line numbers belonging to module-level statements --
    catalogue literals, constants, class bodies.

  Why it matters for mutation testing: an import happens once per
  process, so per-test coverage attributes every module-level line to
  whichever test imported first. Choosing "the tests that touch this
  line" then picks an arbitrary single test, and a mutant on a
  catalogue entry gets judged by a test that never looks at it. For
  these lines the honest selection is every test that touches the
  FILE at all.
  """
  with open(path, encoding="utf-8") as f:
    source = f.read()
  try:
    tree = ast.parse(source, path)
  except SyntaxError:
    return set()
  inside = set()
  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
      for child in ast.walk(node):
        if hasattr(child, "lineno"):
          inside.add(child.lineno)
  everything = {getattr(n, "lineno", None) for n in ast.walk(tree)}
  return {line for line in everything if line and line not in inside}


def tests_touching_file(coverage, path):
  """Every test that executes any line of this file."""
  prefix = f"{path}:"
  return [name for name, lines in coverage.items()
          if any(line.startswith(prefix) for line in lines)]


def tests_touching(coverage, path, line):
  """Which tests execute this line.

  Args:
    coverage: the per-test map from coverage_per_test.py.
    path: repo-relative file.
    line: 1-based line number.

  Returns:
    A list of test names, empty when the line is never reached.
  """
  key = f"{path}:{line}"
  return [name for name, lines in coverage.items() if key in lines]


RUNNER = """
import importlib.util, os, sys
ROOT = {root!r}   # the SANDBOX root, not the project
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
from qgis.core import QgsApplication
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._enable_stack_dumps()
rt._no_modal_dialogs()
for name in {tests!r}:
    rt.check(name, getattr(rt, name))
app.exitQgis()
sys.exit(1 if rt.FAILED else 0)
"""


def run_tests(names, base):
  """Run some tests in a fresh process, under the watchdog.

  Args:
    names: test function names.

  Returns:
    "killed" when any failed, "survived" when all passed, "stalled"
    when the watchdog had to intervene.
  """
  code = RUNNER.format(root=base, tests=list(names))
  watchdog = os.path.join(base, "tools", "watchdog.py")
  result = subprocess.run(
    [sys.executable, watchdog, "--stall", "40", "--timeout", "300",
     "--quiet", "--", sys.executable, "-c", code],
    cwd=base, capture_output=True, text=True)
  if result.returncode in (124, 125):
    return "stalled"
  return "survived" if result.returncode == 0 else "killed"


def apply_mutant(mutant, base):
  """Write the mutated line INSIDE THE SANDBOX.

  Args:
    mutant: the change to make.
    base: the sandbox root; the real project is never written to, so
      a kill or a crash mid-campaign cannot leave broken source in
      the tree (which is exactly what happened before sandboxing).

  Returns:
    (path, original text) for restoring within the sandbox, which is
    still worth doing so one mutant does not contaminate the next.
  """
  path = os.path.join(base, mutant.path)
  with open(path, encoding="utf-8") as f:
    original = f.read()
  lines = original.splitlines(keepends=True)
  ending = "\n" if lines[mutant.line - 1].endswith("\n") else ""
  lines[mutant.line - 1] = mutant.after + ending
  with open(path, "w", encoding="utf-8") as f:
    f.write("".join(lines))
  return path, original


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--sample", type=int, default=15)
  parser.add_argument("--seed", type=int, default=1)
  parser.add_argument("--control", action="store_true",
                      help="apply NO mutation and check the tests pass "
                           "in the sandbox; a 100%% kill rate means "
                           "nothing if the harness fails everything")
  parser.add_argument("--max-tests", type=int, default=4,
                      help="most tests to run per mutant (the cheapest "
                           "covering tests are preferred)")
  args = parser.parse_args()

  if not os.path.exists(COVERAGE):
    sys.exit("run tools/coverage_per_test.py first (it builds the map "
             "of which tests touch which lines)")
  with open(COVERAGE, encoding="utf-8") as f:
    coverage = json.load(f)

  names = display_to_function()
  missing = [d for d in coverage if d not in names]
  if missing:
    print(f"note: {len(missing)} recorded test(s) no longer match a "
          f"check() call, e.g. {missing[:2]}")

  pool = []
  for name in TARGETS:
    full = os.path.join(SRC, name)
    pool += candidates(full)
    MODULE_LEVEL[os.path.relpath(full, ROOT)] = module_level_lines(full)
  known_equivalent = [m for m in pool if is_equivalent(m)]
  pool = [m for m in pool if not is_equivalent(m)]
  if known_equivalent:
    print(f"excluded {len(known_equivalent)} mutation(s) proven "
          f"equivalent; see EQUIVALENT in this file for the evidence")
  rng = random.Random(args.seed)
  rng.shuffle(pool)

  chosen, uncovered = [], []
  for mutant in pool:
    if len(chosen) >= args.sample:
      break
    if mutant.line in MODULE_LEVEL.get(mutant.path, set()):
      touching = tests_touching_file(coverage, mutant.path)
    else:
      touching = tests_touching(coverage, mutant.path, mutant.line)
    if not touching:
      uncovered.append(mutant)
      continue
    functions = [names[t] for t in touching if t in names]
    if not functions:
      uncovered.append(mutant)
      continue
    # keep the full covering set as well: a mutant that survives the
    # cheap sample is re-run against all of them before we believe it
    chosen.append((mutant, functions[:args.max_tests], functions))

  print(f"{len(pool)} possible mutations; sampling {len(chosen)} "
        f"(seed {args.seed}); {len(uncovered)} skipped as unreached "
        f"by any test\n")

  killed = survived = stalled = 0
  survivors = []

  # Everything below happens in a throwaway copy. The project itself
  # is never opened for writing, so an interrupted campaign cannot
  # leave a deliberately broken line behind -- which is not
  # hypothetical: a killed audit did exactly that before this.
  sys.path.insert(0, HERE)
  from sandbox import discard, make_sandbox
  base = make_sandbox("auto")
  print(f"mutating a copy at {base}\n")
  import signal

  def cleanup(*_a):
    discard(base)
    raise SystemExit(130)

  for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(sig, cleanup)

  chosen = [(m, t, a) for m, t, a in chosen]
  if args.control:
    # the null mutant: change nothing, run the same tests the same
    # way. They must PASS. If they fail, every "killed" verdict above
    # would be an artefact of a broken sandbox rather than a test
    # noticing anything.
    print("control run: no mutation applied\n")
    for i, (mutant, tests, _all) in enumerate(chosen, 1):
      verdict = run_tests(tests, base)
      ok = verdict == "survived"
      print(f"{i:>3}/{len(chosen)} {'ok' if ok else 'BROKEN':>8}  "
            f"{', '.join(tests)}")
      if not ok:
        survivors.append((mutant, tests))
    discard(base)
    if survivors:
      print(f"\nHARNESS BROKEN: {len(survivors)} test set(s) fail with "
            "no mutation applied; kill rates are meaningless until "
            "this is fixed")
      sys.exit(1)
    print("\ncontrol passed: the sandbox runs these tests green, so a "
          "'killed' verdict really is a test noticing a change")
    return

  for i, (mutant, tests, all_tests) in enumerate(chosen, 1):
    path, original = apply_mutant(mutant, base)
    started = time.perf_counter()
    try:
      verdict = run_tests(tests, base)
      if verdict == "survived" and len(all_tests) > len(tests):
        # Survival is a claim about the WHOLE suite, and the sample
        # above is a shortcut. Three survivors in the first batch had
        # a test that would have caught them sitting just outside the
        # four chosen, so confirm against every covering test before
        # reporting a gap that is really a truncation.
        verdict = run_tests(all_tests, base)
        tests = all_tests
    finally:
      with open(path, "w", encoding="utf-8") as f:
        f.write(original)
    seconds = time.perf_counter() - started
    if verdict == "killed":
      killed += 1
    elif verdict == "stalled":
      stalled += 1
    else:
      survived += 1
      survivors.append((mutant, tests))
    print(f"{i:>3}/{len(chosen)} {verdict:>8}  {mutant}  "
          f"({len(tests)} test(s), {seconds:.0f}s)")
    print(f"        {mutant.before.strip()[:88]}")
    if verdict == "survived":
      print(f"     -> {mutant.after.strip()[:88]}")

  discard(base)
  total = killed + survived + stalled
  caught = killed + stalled
  rate = 100 * caught / max(total, 1)
  bound = clopper_pearson_lower(caught, total)
  print(f"\nfirst-run kill rate: {caught}/{total} = {rate:.0f}%"
        f"  (killed {killed}, stalled {stalled}, survived {survived})")
  print(f"true rate is at least {bound * 100:.0f}% with 95% "
        f"confidence  (exact Clopper-Pearson, two-sided lower limit, "
        f"n={total})")
  print(f"measured against {suite_stamp()}; the number expires when "
        f"the suite changes")

  # Stratified, because a single blended figure lets deterministic
  # logic hide behind Qt plumbing. bridge.py and catalog.py are pure
  # computation and should sit far higher than the dialog's wiring;
  # averaging them into one number would conceal exactly the weakness
  # worth knowing about.
  per_file = {}
  for mutant, _, _ in chosen:
    entry = per_file.setdefault(mutant.path, [0, 0])
    entry[1] += 1
  for mutant, _ in survivors:
    per_file[mutant.path][0] += 1
  if len(per_file) > 1:
    print("\nby module (caught / tried):")
    for path in sorted(per_file, key=lambda k: -per_file[k][1]):
      lost, tried = per_file[path]
      got = tried - lost
      print(f"  {path:<44} {got:>3}/{tried:<3} = "
            f"{100 * got / max(tried, 1):>3.0f}%")
  if survivors:
    print("\nsurvivors, for triage (weak assertion / unreached in "
          "practice / equivalent):")
    for mutant, tests in survivors:
      print(f"  {mutant}\n      was: {mutant.before.strip()[:80]}"
            f"\n      now: {mutant.after.strip()[:80]}"
            f"\n      tests run: {', '.join(tests)}")


if __name__ == "__main__":
  main()
