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
import traceback

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
  """Every decision in a file, as (line, code, offset) triples.

  Args:
    path: a source file.

  Returns:
    A set of (source line, code-object first line, instruction offset)
    for each conditional jump the interpreter will execute —
    ``if``/``while`` tests, boolean short-circuits, comprehension
    filters, and loop exits (``FOR_ITER``, whose "branch" is
    loop-again versus loop-done).

  The code object's first line is part of the key because INSTRUCTION
  OFFSETS RESTART AT ZERO IN EVERY CODE OBJECT. Keyed by offset alone,
  a decision in one function collides with a decision at the same
  offset in another: measured on bridge.py, 130 branch instructions
  occupy only 95 distinct offsets, so a quarter of them shared a key.
  Merged destinations then made decisions look taken both ways when
  one of the two had only ever gone one way, and the "taken both ways"
  figure this tool publishes was inflated accordingly.

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
        out.add((line, code.co_firstlineno, instruction.offset))
    stack += [c for c in code.co_consts if hasattr(c, "co_lines")]
  return out


def gaps(missing, minimum=3):
  """Consecutive runs of unexecuted lines, longest first: the useful
  form for "where should the next test go", since scattered single
  lines are usually error branches while a run of twenty is a feature
  nothing exercises.

  Args:
    missing: the line numbers of one file that the suite never
      executed, in any order (they are sorted here). Line numbers
      only: the caller has already narrowed this to a single module.
    minimum: the shortest run worth reporting. Three is the default
      because one or two adjacent unexecuted lines are almost always
      a guard's body, and listing every one of those would bury the
      runs that mean a whole feature is untested.

  Returns:
    A list of (first line, last line) pairs, longest run first, each
    spanning at least minimum consecutive lines. Runs shorter than
    minimum are dropped rather than merged, so the pairs do not
    account for every line in missing. The argument is not modified.
  """
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


def run_suite_with_monitoring(seen, branches=None, on_suite_exit=None):
  """Execute tests/run_tests.py with LINE monitoring active.

  The suite ends in os._exit rather than returning or raising, so
  anything the caller means to do with the recording has to happen on
  the way through that exit: pass it as on_suite_exit.

  Args:
    seen: the set this call FILLS with (absolute filename, line) for
      every plugin line that executed. Passed in rather than returned
      so that a run which dies part-way still leaves the caller
      holding whatever was recorded before the crash.
    branches: when given, the dict this call fills with
      {(filename, instruction offset): set of destination offsets},
      recording which way each decision went. Leave it None to skip
      BRANCH monitoring entirely, which is the cheaper of the two
      measurements.
    on_suite_exit: called with the suite's exit status once monitoring
      is torn down and before the process ends, which is the ONLY
      moment a report can be written. Omit it and this function
      records coverage that nothing will ever read. Any exception it
      raises is reported and swallowed, since a fault in the report
      must not change the status the suite earned.

  Returns:
    The suite's exit status: 0 when every test passed, non-zero
    otherwise, so a caller can propagate a real test failure instead
    of reporting coverage of a broken run as though it were news.
    Both seen and branches are mutated in place. Monitoring is torn
    down in a finally block, because the tool id is a global resource
    of the interpreter and leaving it claimed would break any later
    profiler in the same process.

  The suite runs in THIS process (runpy, not a subprocess) because
  sys.monitoring only sees the interpreter it is registered in, and
  sys.argv is set to the suite's own path first so anything the suite
  reads from argv sees what it would see when run directly.
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

    Args:
      code: the code object the branch is in.
      offset: the instruction offset of the decision, which is what
        distinguishes two branches in one function.
      destination: the offset it jumped to this time.

    Keyed by (file, code-object first line, instruction offset) with
    the set of destinations seen, because a decision is only properly
    tested once it has gone both ways — one destination means the
    suite has only ever seen that ``if`` succeed (or only ever fail).
    Unlike lines, these are never DISABLEd: the second way through the
    same decision is exactly what we are waiting for.

    The code object is part of the key because offsets restart at zero
    in each one; see branch_points, which must key identically or the
    two inventories do not line up at all."""
    filename = code.co_filename
    if not filename.startswith(SRC) or filename.startswith(EXCLUDED):
      return mon.DISABLE
    branches.setdefault(
      (filename, code.co_firstlineno, offset), set()).add(destination)
    return None

  mon.register_callback(tool, mon.events.LINE, on_line)
  events = mon.events.LINE
  if branches is not None:
    mon.register_callback(tool, mon.events.BRANCH, on_branch)
    events |= mon.events.BRANCH
  mon.set_events(tool, events)
  status = 0

  # The suite does not RETURN, and it does not raise SystemExit
  # either: it ends in os._exit, added 2026-08-11 so that a segfault
  # in Qt/QGIS teardown could not turn a finished, fully reported run
  # into exit 139. os._exit takes the process down immediately --
  # past finally blocks, past atexit, past the `except SystemExit`
  # below, past every line of main() after this call. So this tool
  # ran the whole suite, wrote no report, printed no summary, and
  # exited with the suite's status: you ran the documented command,
  # waited out the suite, and got nothing, with nothing to say why.
  # Four documents recommend that command. Measured 2026-08-13.
  #
  # The fix is the one tools/coverage_per_test.py already uses and
  # explains: stand in for os._exit and do the work on the way
  # through. It is done HERE rather than by editing the suite because
  # this tool observes a suite it does not own -- a suite that grows
  # another exit path later costs nothing on this side.
  #
  # Unlike the per-test recorder, a NON-ZERO status still writes the
  # report. That record feeds mutate_auto, where a partial file
  # silently understates survivors; this one is a description for a
  # person, and a coverage map of a run whose suite had one failure
  # is still worth reading, as long as the status travels with it.
  real_exit = os._exit
  finished = []

  def exit_after_writing_the_report(code):
    """Stand in for os._exit so the report survives the suite's exit.

    Args:
      code: the exit status the suite chose, which becomes this
        process's status once the report is written.

    Returns:
      Never returns; the process ends here.
    """
    finished.append(code)
    mon.set_events(tool, 0)
    mon.free_tool_id(tool)
    if on_suite_exit is not None:
      try:
        on_suite_exit(code)
      except Exception:                       # pragma: no cover
        traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    real_exit(code)

  os._exit = exit_after_writing_the_report
  try:
    sys.argv = [os.path.join(ROOT, "tests", "run_tests.py")]
    import runpy
    runpy.run_path(sys.argv[0], run_name="__main__")
  except SystemExit as e:
    status = e.code or 0
  finally:
    os._exit = real_exit
    if not finished:
      # only reached if the suite ever stops exiting for itself
      mon.set_events(tool, 0)
      mon.free_tool_id(tool)
  return status


def write_report(seen, path, branches=None):
  """Write coverage.md and return (lines hit, lines total, decisions
  both ways, decisions total).

  Args:
    seen: the (filename, line) pairs recorded during the run. It is
      intersected with each module's executable lines, so lines
      recorded for code that has since changed cannot inflate the
      total.
    path: absolute destination for the Markdown report, overwritten
      if it exists. A release no longer runs this -- the stage left
      the release path on 2026-08-12 -- so point it by hand at
      reports/v<version>/coverage.md.
    branches: the decision record from the run, keyed by (filename,
      instruction offset). None means branch monitoring was not
      enabled; the report is still written, with every decision
      shown as never reached.

  Returns:
    (lines executed, lines executable, decisions taken both ways,
    decisions total) summed over every module, for the caller to
    print. Nothing in memory is mutated; the one side effect is the
    file at path.

  Modules are listed worst-covered first, since the table exists to
  be read from the top and stopped at.
  """
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
    for line, first, offset in decisions:
      seen_dests = branches.get((filename, first, offset), set())
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
  """Run the suite under monitoring and write coverage.md beside it.

  The optional command-line argument is the output DIRECTORY (default
  the repository root); it is read before the suite starts, because
  running the suite rewrites sys.argv. The repository root goes on
  sys.path so that ``import weavingspace_qgis`` resolves to the
  working tree rather than to any copy installed in a QGIS profile.

  Returns:
    Nothing; exits with the SUITE's status, not with its own. A
    coverage report is a description, never a gate: it must not turn
    a passing release into a failing one, and equally must not hide a
    test failure behind a successfully written report.

  The report is written from INSIDE the run, through the callback
  below, because the suite ends the process itself and nothing after
  the call ever runs. See run_suite_with_monitoring.
  """
  sys.path.insert(0, ROOT)
  out_dir = sys.argv[1] if len(sys.argv) > 1 else ROOT
  os.makedirs(out_dir, exist_ok=True)
  seen, branches = set(), {}
  path = os.path.join(out_dir, "coverage.md")

  def report(status):
    """Write coverage.md and say where it went.

    Args:
      status: the suite's exit status, quoted in the summary so a
        report of a run with failures cannot be mistaken for a report
        of a clean one.

    Returns:
      None; writes the file at `path` and prints one summary line.
    """
    hit, ex, both, dec = write_report(seen, path, branches)
    note = "" if status == 0 else f"  [suite exited {status}]"
    print(f"\ncoverage: {hit}/{ex} lines "
          f"({100 * hit / max(ex, 1):.0f}%), "
          f"{both}/{dec} decisions taken both ways "
          f"({100 * both / max(dec, 1):.0f}%) -> {path}{note}")

  status = run_suite_with_monitoring(seen, branches, on_suite_exit=report)
  # only reached if the suite ever stops exiting for itself
  report(status)
  sys.exit(status)


if __name__ == "__main__":
  main()
