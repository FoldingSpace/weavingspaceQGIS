#!/usr/bin/env python3
"""Line coverage of the plugin's own code, measured by running the
functional suite.

Run under QGIS's own Python, from the repository root:

    QT_QPA_PLATFORM=offscreen ... <qgis python> tools/coverage_report.py
    <qgis python> tools/coverage_report.py reports/v0.19.0   # write there

Why a hand-rolled collector rather than `coverage.py`: macOS
code-signing refuses PyPI packages inside the signed QGIS process (the
same wall the reference renderer hit), and the plugin must never
acquire a test-only dependency it might ship. Everything here is
stdlib.

How it works. Python 3.12's ``sys.monitoring`` lets a tool subscribe
to LINE events with far less overhead than ``sys.settrace``; the
callback records (filename, line) into a set and returns DISABLE for
lines already seen, so each line costs once rather than once per
execution. Executable lines come from walking the compiled code
objects of each source file (``co_lines()``), which is what "could
have run" means precisely — comments, blank lines, and docstrings are
not counted against the total.

What it covers: ``weavingspace_qgis/*.py`` excluding ``vendor/`` (the
upstream library is not ours to test) and ``libs/`` (downloaded
wheels).

TWO numbers, and neither is a grade:

* LINE coverage — this line executed at least once. The weakest
  useful measure: a line is "covered" by a test that runs it and
  asserts nothing at all, and `if a and b:` counts as covered when
  only the true/true case ever ran.
* BRANCH coverage — this decision was taken BOTH ways. Stricter, and
  the one that finds happy-path-only testing: an error branch, a
  guard's refusal, a fallback that no test ever reaches shows up here
  while line coverage stays quiet about it.

Neither measures whether anything was CHECKED. For that, see
``tools/mutation_check.py``, which breaks behaviours on purpose and
requires the tests to notice; its mutation score is the measure that
speaks to detection rather than execution. Read these two as a map of
untested ground — the report lists the largest unexecuted line runs
and the un-taken branches per module, so the next test has somewhere
obvious to go.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "weavingspace_qgis")
EXCLUDED = (os.path.join(SRC, "vendor"), os.path.join(SRC, "libs"))


def source_files():
  """Plugin modules whose coverage we care about."""
  out = []
  for dirpath, dirnames, filenames in os.walk(SRC):
    if dirpath.startswith(EXCLUDED):
      continue
    dirnames[:] = [d for d in dirnames
                   if not os.path.join(dirpath, d).startswith(EXCLUDED)]
    out += [os.path.join(dirpath, f) for f in filenames
            if f.endswith(".py")]
  return sorted(out)


def executable_lines(path):
  """Line numbers that could execute in this file.

  Compiling the module yields a code object whose ``co_lines()``
  reports the source line of every bytecode range; recursing through
  nested code objects (functions, comprehensions, classes) reaches
  bodies that the top-level object only references.
  """
  with open(path, encoding="utf-8") as f:
    source = f.read()
  try:
    top = compile(source, path, "exec")
  except SyntaxError:
    return set()
  lines, stack = set(), [top]
  while stack:
    code = stack.pop()
    for _start, _end, lineno in code.co_lines():
      if lineno:
        lines.add(lineno)
    stack += [c for c in code.co_consts if hasattr(c, "co_lines")]
  return lines


def branch_points(path):
  """Every decision in a file, as (line, bytecode offset) pairs.

  Args:
    path: a source file.

  Returns:
    A set of (source line, instruction offset) for each conditional
    jump the interpreter will execute — ``if``/``while`` tests,
    boolean short-circuits, comprehension filters, and loop exits
    (``FOR_ITER``, whose "branch" is loop-again versus loop-done).

  Why bytecode and not the syntax tree: what matters is what the
  interpreter actually decides. One ``if a and b:`` is two decisions,
  a ``while`` is one decision reached from two places, and an
  ``assert`` is a decision the source barely looks like. Compiling
  and reading the instructions counts them the way the runtime will
  report them, so the static inventory and the runtime record line up
  offset for offset. (``co_branches()`` would do this directly, but
  it arrives in Python 3.14 and QGIS ships 3.12.)
  """
  import dis
  with open(path, encoding="utf-8") as f:
    source = f.read()
  try:
    top = compile(source, path, "exec")
  except SyntaxError:
    return set()
  out, stack = set(), [top]
  while stack:
    code = stack.pop()
    # dis.Instruction spells the source line differently across
    # versions (starts_line here in 3.12, line_number from 3.13), and
    # it is only set on the FIRST instruction of each line, so carry
    # the last seen value forward
    line = None
    for instruction in dis.get_instructions(code):
      at = getattr(instruction, "line_number", None)
      if at is None:
        at = instruction.starts_line
      if isinstance(at, int):
        line = at
      name = instruction.opname
      if line and (name.startswith(("POP_JUMP_IF", "JUMP_IF"))
                   or name == "FOR_ITER"):
        out.add((line, instruction.offset))
    stack += [c for c in code.co_consts if hasattr(c, "co_lines")]
  return out


def gaps(missing, minimum=3):
  """Consecutive runs of unexecuted lines, longest first: the useful
  form for "where should the next test go", since scattered single
  lines are usually error branches while a run of twenty is a feature
  nothing exercises."""
  runs, current = [], []
  for line in sorted(missing):
    if current and line == current[-1] + 1:
      current.append(line)
    else:
      if len(current) >= minimum:
        runs.append((current[0], current[-1]))
      current = [line]
  if len(current) >= minimum:
    runs.append((current[0], current[-1]))
  return sorted(runs, key=lambda r: r[1] - r[0], reverse=True)


def run_suite_with_monitoring(seen, branches=None):
  """Execute tests/run_tests.py with LINE monitoring active.

  The suite calls sys.exit() when it finishes, which is caught here so
  the report can still be written; its exit status is returned so a
  caller can tell whether the tests themselves passed.
  """
  mon = sys.monitoring
  tool = mon.COVERAGE_ID
  mon.use_tool_id(tool, "weavingspace-coverage")

  def on_line(code, lineno):
    filename = code.co_filename
    if filename.startswith(SRC) and not filename.startswith(EXCLUDED):
      seen.add((filename, lineno))
      return mon.DISABLE  # this line is recorded; stop paying for it
    return mon.DISABLE     # not our code at all: never ask again

  def on_branch(code, offset, destination):
    """A decision was resolved: record WHERE it jumped to.

    Keyed by (file, instruction offset) with the set of destinations
    seen, because a decision is only properly tested once it has gone
    both ways — one destination means the suite has only ever seen
    that ``if`` succeed (or only ever fail). Unlike lines, these are
    never DISABLEd: the second way through the same decision is
    exactly what we are waiting for."""
    filename = code.co_filename
    if not filename.startswith(SRC) or filename.startswith(EXCLUDED):
      return mon.DISABLE
    branches.setdefault((filename, offset), set()).add(destination)
    return None

  mon.register_callback(tool, mon.events.LINE, on_line)
  events = mon.events.LINE
  if branches is not None:
    mon.register_callback(tool, mon.events.BRANCH, on_branch)
    events |= mon.events.BRANCH
  mon.set_events(tool, events)
  status = 0
  try:
    sys.argv = [os.path.join(ROOT, "tests", "run_tests.py")]
    import runpy
    runpy.run_path(sys.argv[0], run_name="__main__")
  except SystemExit as e:
    status = e.code or 0
  finally:
    mon.set_events(tool, 0)
    mon.free_tool_id(tool)
  return status


def write_report(seen, path, branches=None):
  """Write coverage.md and return (lines hit, lines total, decisions
  both ways, decisions total)."""
  branches = branches if branches is not None else {}
  rows, total_ex, total_hit = [], 0, 0
  total_dec = total_both = 0
  for filename in source_files():
    ex = executable_lines(filename)
    hit = {ln for fn, ln in seen if fn == filename} & ex
    if not ex:
      continue
    total_ex += len(ex)
    total_hit += len(hit)
    # decisions: both ways taken, one way only, or never reached. The
    # middle case is the interesting one — the code ran, so line
    # coverage is content, but the suite has only ever seen it go one
    # way, which is where untested guards and fallbacks hide
    decisions = branch_points(filename)
    both = one_way = 0
    half_lines = []
    for line, offset in decisions:
      seen_dests = branches.get((filename, offset), set())
      if len(seen_dests) >= 2:
        both += 1
      elif len(seen_dests) == 1:
        one_way += 1
        half_lines.append(line)
    total_dec += len(decisions)
    total_both += both
    rows.append((os.path.relpath(filename, ROOT), len(ex), len(hit),
                 gaps(ex - hit), len(decisions), both, one_way,
                 sorted(set(half_lines))[:6]))
  rows.sort(key=lambda r: (r[2] / r[1]) if r[1] else 1.0)

  lines = [
    "# Coverage of plugin code (functional suite)", "",
    f"**Lines**: {total_hit}/{total_ex} executed "
    f"({100 * total_hit / max(total_ex, 1):.0f}%). ",
    f"**Decisions taken both ways**: {total_both}/{total_dec} "
    f"({100 * total_both / max(total_dec, 1):.0f}%).", "",
    "Vendored library and downloaded wheels excluded. Neither number "
    "says anything was CHECKED — a line can be executed by a test "
    "that asserts nothing. For detection, see the mutation score "
    "from `tools/mutation_check.py`.", "",
    "| module | lines | covered | % | decisions | both ways | % | "
    "one way only (lines) | largest untested line runs |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
  for name, ex, hit, runs, dec, both, one_way, half in rows:
    where = ", ".join(f"{a}-{b}" for a, b in runs[:3]) or "—"
    halves = ", ".join(str(x) for x in half) or "—"
    pct_b = f"{100 * both / dec:.0f}%" if dec else "—"
    lines.append(f"| {name} | {ex} | {hit} | "
                 f"{100 * hit / ex:.0f}% | {dec} | {both} | {pct_b} | "
                 f"{halves} | {where} |")
  lines += [
    "", "How to read this:", "",
    "- *largest untested line runs* — nothing in the suite reaches "
    "these lines at all; usually a whole feature or error path with "
    "no test.",
    "- *one way only* — the decision on that line ran, but always "
    "went the same way. The other side is untested: a guard that "
    "never refused, a fallback never taken, an error never raised. "
    "These are the cheapest gaps to close and the ones line coverage "
    "hides."]
  with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
  return total_hit, total_ex, total_both, total_dec


def main():
  sys.path.insert(0, ROOT)
  out_dir = sys.argv[1] if len(sys.argv) > 1 else ROOT
  os.makedirs(out_dir, exist_ok=True)
  seen, branches = set(), {}
  status = run_suite_with_monitoring(seen, branches)
  path = os.path.join(out_dir, "coverage.md")
  hit, ex, both, dec = write_report(seen, path, branches)
  print(f"\ncoverage: {hit}/{ex} lines "
        f"({100 * hit / max(ex, 1):.0f}%), "
        f"{both}/{dec} decisions taken both ways "
        f"({100 * both / max(dec, 1):.0f}%) -> {path}")
  sys.exit(status)


if __name__ == "__main__":
  main()
