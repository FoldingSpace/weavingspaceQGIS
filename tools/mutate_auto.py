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

That cost is spread very unevenly, and --max-cost turns the unevenness
into an option. Measured on the current record, about a fifth of the
mutants a test can reach are covered by eight tests or fewer while
half are covered by seventy or more, so a uniform random sample spends
nearly all of its wall clock at the expensive end and answers slowly.
`--max-cost N` keeps only mutants whose covering set is N tests or
smaller and runs EVERY one of them: a CENSUS of one cost stratum
rather than a sample of everything. Two things follow, and both are
stated in the output rather than left to the reader. The rate is exact
for that stratum, so no confidence bound belongs on it. And it is not
the plugin's kill rate -- cheaply covered lines are a particular kind
of code, and a stratum rate quoted as if it were the population's
would be the most flattering mistake this tool could make.

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
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# How many mutants are being judged at once. Read by run_tests to size
# the watchdog's stall patience, since a process sharing eight cores
# with three others can legitimately go silent for far longer than one
# with the machine to itself, and a stall counts as CAUGHT. Set once
# from --workers in main(); the default of 1 is what a single-process
# caller (the control run, a --only re-judge) should get.
CONCURRENCY = 1
SRC = os.path.join(ROOT, "weavingspace_qgis")
TARGETS = ["dialog.py", "bridge.py", "catalog.py", "worker.py", "compat.py"]
COVERAGE = os.path.join(ROOT, "reports", "per-test-coverage.json")

# {file: {line numbers that run at import}}, filled in by main()
MODULE_LEVEL = {}

# set to 1 when a --require threshold is missed. release.py no longer
# gates on it -- the guard runs remotely and reports -- but the exit
# code stays for anyone who does want a gate, and for the workflow
_exit_code = [0]

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
    "snippet": "      combo.blockSignals(True)\n      combo.clear()\n"
               "      for text, data in wanted:",
    "mutation": "bool True -> False (and the call removed)",
    "reason":
      "Silencing the CLASS-SOURCE chooser while its items are rebuilt. "
      "Its handler applies a class source, and importing a scheme "
      "deliberately clears that element's hand-picked colours -- so a "
      "handler firing during the refill is the one thing here that "
      "could destroy a user's work without their choosing anything. "
      "It does not: the refill happens inside a table rebuild, and "
      "the choice is restored from `current` before anything reads "
      "it.",
    "evidence":
      "Measured 2026-08-13, mutation applied in a copy of the tree "
      "beside the unmutated one, same scenario against both: a "
      "categorized element with a hand-picked colour "
      "(landcover/forest = #ff0000), then the element count changed "
      "to 5 to force a whole-table rebuild. 189 lines of snapshot "
      "IDENTICAL, including every assignment's class_source, the "
      "category colours for that element specifically, and every cell "
      "widget's full item list. UNIT REBUILDS identical at 3 and "
      "preview refreshes at 2. The anchor is three lines because two "
      "lines match a second site -- the variable refill in "
      "_adapt_to_the_layer, which is NOT equivalent; mutating that one "
      "by mistake would have compared unmutated behaviour with itself "
      "and 'proved' equivalence for both.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "      combo.blockSignals(True)\n"
               "      combo.setCurrentIndex(idx)",
    "mutation": "bool True -> False (and the call removed)",
    "reason":
      "The same chooser, a few lines on: silencing it while the "
      "remembered choice is put back after the items were rebuilt. "
      "Unblocked, restoring a selection reads as the user picking it, "
      "which would apply a class source nobody asked for.",
    "evidence":
      "Measured 2026-08-13 in the same run as the entry above and by "
      "the same method: 189 lines IDENTICAL, rebuilds 3, preview "
      "refreshes 2, class_source unchanged on every element and the "
      "hand-picked colour still #ff0000.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "      self.opt_over_under.blockSignals(True)",
    "mutation": "bool True -> False (and the call removed, which leaves "
                "the signals live across the same statement)",
    "reason":
      "Silencing the over-under entry while _on_family_changed fills "
      "it from the family's own spec, on a twill or basket weave. "
      "Unblocked, the edit reads as though the user had typed it and "
      "restarts the preview debounce -- which was already running, "
      "because choosing a family started it.",
    "evidence":
      "Measured 2026-08-13, mutation applied in a copy of the tree "
      "beside the unmutated one, the same scenario against both: two "
      "elements, kind weave, family 'twill weave a|b'. 91 lines of "
      "snapshot IDENTICAL -- every assignment, the category colours, "
      "ramp ranges, preview colours, note line, row/column counts, "
      "hidden columns, every cell widget's type, text, item list, "
      "checked state, value and enabled state, the n/kind/family/"
      "spacing/shells/live controls, the unit's element count, and "
      "the over-under field's own text, visibility and enabled state "
      "(it reads '2' either way). The count of UNIT REBUILDS was also "
      "identical at 3, which is the measure that matters here and the "
      "one an end-state comparison cannot see.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "        sp.blockSignals(True)",
    "mutation": "bool True -> False (and the call removed)",
    "reason":
      "Silencing the grid's row and column spin boxes while "
      "_on_family_changed resets them to the tightest fit for the "
      "element count. The comment there says a signal would schedule "
      "a second rebuild of the same unit -- and that turns out to "
      "OVERSTATE the block's necessity: the rebuild is debounced, so "
      "the extra signal falls inside the window already open and "
      "coalesces. The block is still worth keeping, because it makes "
      "the intent explicit and costs nothing, but it is not load "
      "bearing.",
    "evidence":
      "Measured 2026-08-13 exactly as the entry above, with family "
      "'grid 2' at two elements. 94 lines of snapshot IDENTICAL, "
      "including both spin boxes' values, visibility and enabled "
      "state. UNIT REBUILDS identical at 4 -- which is the claim in "
      "the code's own comment, tested rather than taken on trust, and "
      "found not to hold. Rebuilds were counted by patching the "
      "method on the CLASS before the dialog existed: wrapping the "
      "instance attribute counts direct calls and misses every "
      "signal-driven one, since a connection holds the original bound "
      "method, and that is the instrumentation fault this project has "
      "already paid for twice.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "      self.kind_combo.blockSignals(True)",
    "mutation": "bool True -> False (and, identically, the call removed: "
                "with the block gone the matching unblock is a no-op, so "
                "both spellings leave the signals live across exactly the "
                "same statement)",
    "reason":
      "Silencing the KIND chooser while _on_n_changed switches it on "
      "the user's behalf. The branch runs only for an element count "
      "that carries one kind alone -- thirteen and above are all "
      "tilings -- so asking for one while the chooser reads 'weave' "
      "makes the handler set it to 'tiling' itself. Unblocked, that "
      "flip re-enters _on_n_changed, which the handler's own docstring "
      "says the block exists to prevent. The re-entrant pass computes "
      "the same family list from the same count and kind and settles "
      "on the same family, so the second pass overwrites the first "
      "with its own result.",
    "evidence":
      "Measured 2026-08-13 by applying the mutation in a copy of the "
      "tree beside the unmutated one and running the identical "
      "scenario against both: a dialog with a layer, the kind set to "
      "weave, then the count set to 13. Compared EVERYTHING a test "
      "could see rather than the dimension that had been imagined -- "
      "every element's assignment, the category colours, the ramp "
      "ranges, the preview colours, the note line, the row and column "
      "counts, which columns are hidden, every cell widget's type, "
      "current text, full item list, checked state, value and enabled "
      "state, the n/kind/family/spacing/shells/live controls, the "
      "unit's element count, and the kind and family the switch "
      "settled on with the whole family list offered. 436 lines of "
      "snapshot, IDENTICAL. That width matters: the sibling mutant in "
      "_adapt_to_the_layer looked equivalent under a narrower "
      "comparison and was not -- it seeds every element's single "
      "colour, which sits in the signature, so a column added in QGIS "
      "would have discarded the user's own styling. Harness in the "
      "session's scratchpad as eq_probe.py and eq_run.sh; the latter "
      "refuses an anchor matching more than once, since mutating one "
      "of several identical sites would compare unmutated behaviour "
      "with itself and 'prove' equivalence.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "    self.family_combo.blockSignals(True)",
    "mutation": "call removed (True -> False)",
    "reason":
      "Blocking the family list's signals while it is refilled. "
      "Unblocked, _on_family_changed runs once per family added "
      "instead of once at the end -- but the handler is idempotent: "
      "it sets six option rows' visibility and the offset and angle "
      "RANGES from the current spec, and the last call settles them "
      "from the same spec the single call would have used. The unit "
      "is not rebuilt any more often, because the rebuild is "
      "debounced and the extra calls fall inside the same window. "
      "This is the same shape as the over-under entry above and was "
      "held open until it had the same class of evidence.",
    "evidence":
      "Measured 2026-08-12 by running the mutation in a copy of the "
      "tree beside the unmutated one and comparing everything a test "
      "could see across six element counts and both kinds: the family "
      "list, the selected family, the offset range and value, the "
      "offset-angle range, the over-under text, all six option-row "
      "visibilities, every element assignment, and the unit's element "
      "count. EVERY one identical. The only field that moved was the "
      "count of handler calls (8 against 23), and the count of unit "
      "REBUILDS was identical -- which also disproves the catalogue "
      "entry this replaces, whose reason was 'the unit being rebuilt "
      "once per family added to the list'. Two instrumentation faults "
      "were corrected before believing it: rewiring the signal to "
      "count it changed what was under study, and a *args wrapper "
      "made PyQt pass a combo index the real slot never receives, "
      "raising a TypeError that read as a finding.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "            if self._source_layer_alive(layer) else -1",
    "mutation": "1 -> 2",
    "reason":
      "A sentinel standing for 'this layer is gone, so it has no such "
      "field'. The next line is `if index < 0: continue`, and -2 is "
      "as negative as -1, so both values take the same branch. The "
      "sentinel is never compared with anything else, never printed "
      "and never returned, so no test can distinguish the two.",
    "evidence":
      "By construction, checked mechanically rather than argued: "
      "walking the syntax tree of the enclosing `done` closure finds "
      "exactly two references to `index` -- one Store, at the line "
      "above, and one Load, which is the `< 0` test on the line "
      "below. A value read once, by a comparison both candidates "
      "satisfy, cannot reach anything observable. Re-check by "
      "parsing dialog.py and listing ast.Name nodes for `index` "
      "inside that closure; deliberately stated without line "
      "numbers, because the first version of this evidence cited "
      "four of them and every one was wrong within the day, an "
      "unrelated refactor above having moved the function twenty-one "
      "lines down.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": 'k_spin.setValue(min(int(k_spin.property("user_k") or 5), 20))',
    "mutation": "20 -> 21",
    "reason":
      "The line above sets the spin box's range to (2, 20), and Qt "
      "clamps setValue to the range. A ceiling of 21 therefore "
      "produces 20, exactly as before. The 2-20 class range itself is "
      "a settled decision and is enforced by setRange, which a "
      "different mutant would have to reach.",
    "evidence":
      "Same clamp as the opacity entry, demonstrated under QGIS's own "
      "Qt: setValue above the maximum returns the maximum.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "      and not self.table.isColumnHidden(7)",
    "mutation": "7 -> 8",
    "reason":
      "Column 7 is the class source and column 8 is Edit colours, and "
      "_update_dynamic_columns shows and hides BOTH on the same "
      "condition -- any element categorized with a variable. Asking "
      "about 8 therefore gets the same answer as asking about 7 in "
      "every state the dialog can be in.",
    "evidence":
      "By construction rather than by sampling: the two setColumnHidden "
      "calls in _update_dynamic_columns take the identical "
      "has_categorical flag, so no sequence of user actions can "
      "separate them.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": """    if not mode_combo.property("touched"):
      mode_combo.blockSignals(True)""",
    "mutation": "call removed",
    "reason":
      "WITHDRAWN 2026-08-12. This claimed that blocking the style "
      "combo's signals while it is set to follow the variable "
      "changes nothing, because the only slot on currentIndexChanged "
      "was _refresh_preview_colours and the surrounding code calls "
      "that on the next line anyway. A SECOND slot was connected to "
      "the same signal afterwards -- _on_style_changed -- and this "
      "entry was never revisited. That slot destroys an element's "
      "positional class picks when the scheme crosses into or out of "
      "the graduated family, and the comment above the connection "
      "says in as many words that the dialog's programmatic style "
      "writes block signals so nothing reacts to the dialog talking "
      "to itself. Blocking is therefore what makes that slot safe, "
      "which is the opposite of harmless. It is NOT claimed here "
      "that the mutant is observable, only that the exclusion is no "
      "longer earned: an equivalence is a demonstration, and this "
      "one's demonstration was falsified by a later change. The "
      "mutant goes back into the denominator until somebody shows "
      "otherwise, because a wrongly excluded mutant flatters the "
      "score, which docs/MUTATION-TESTING.md lists as this "
      "measurement's characteristic failure.",
    "evidence":
      "None that still holds. The original read 'the combo has two "
      "connections, at dialog.py:1912-1915' -- there are three now, "
      "and those line numbers point at unrelated code. Found by "
      "auditing the citations rather than by any test, which is the "
      "third time on this project that reading a claim with fresh "
      "attention has found a number quietly favouring the suite.",
    "withdrawn": True,
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": """    if source_layer is None:
      return False""",
    "mutation": "return None",
    "reason":
      "_source_layer_alive is only ever read as a TRUTH VALUE. False "
      "and None are both falsy, so every caller behaves identically. "
      "The annotation says bool, which None violates, but nothing at "
      "runtime consults it. (This said 'exactly one caller' until "
      "2026-08-12; there are two now, and the argument holds for "
      "both because it never depended on the count -- only on how "
      "the result is consumed. An argument phrased over a count "
      "expires when the count changes, even when the reasoning does "
      "not.)",
    "evidence":
      "Demonstrated by exhausting the call sites rather than by "
      "sampling, and RE-CHECKED 2026-08-12: `grep _source_layer_alive` "
      "now finds TWO callers, not the one this said. Both consume it "
      "as a truth value -- `if not self._source_layer_alive(...)` in "
      "the run guard, and the condition of a ternary choosing between "
      "a field index and -1 -- and None is falsy exactly where False "
      "is, so the argument survives the second caller arriving. "
      "Stated without line numbers deliberately: the version that "
      "cited one had rotted.",
  },
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "self._opacity_choices.get(row_id, 100)",
    "mutation": "100 -> 101",
    "reason":
      "The default opacity is handed straight to a QSpinBox whose "
      "range is 0-100, and Qt clamps a value above the maximum. 101 "
      "therefore becomes 100 before anything can read it. The value "
      "is clamped a second time downstream, in both _restyle_only and "
      "_add_output_layers, where max(0, min(100, ...)) guards the "
      "conversion to a layer opacity -- so even a spin box that "
      "accepted 101 could not carry it to a layer.",
    "evidence":
      "Run under QGIS's own Qt: a QSpinBox with setRange(0, 100) "
      "returns 100 from value() after setValue(100) and after "
      "setValue(101) alike. No caller can distinguish the two.",
  },
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
  {
    "file": "weavingspace_qgis/dialog.py",
    "snippet": "self.opt_offset.setDecimals(2)",
    "mutation": "call removed",
    "reason":
      "QDoubleSpinBox already defaults to two decimals, so this call "
      "restates Qt's own behaviour. It is kept in the source on "
      "purpose -- pinning the precision explicitly means a future Qt "
      "changing its default cannot quietly coarsen the control -- but "
      "removing it changes nothing observable TODAY, which is what a "
      "mutation score can measure.",
    "evidence":
      "A bare QDoubleSpinBox under this QGIS build reports "
      "decimals() == 2, and 0.05 assigned to one with no setDecimals "
      "call reads back as exactly 0.05.",
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
  """The lower limit of the TWO-SIDED 95%% interval on the kill rate.

  Named exactly, because this line said "one-sided" while the Args
  below explain at length that the default is deliberately the
  two-sided lower limit and that the one-sided bound would read
  several points higher. A summary contradicting its own argument is
  the half a reader quotes.

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


def changed_lines(ref):
  """Which lines of the target files this branch has added or changed.

  Args:
    ref: any git revision to compare against -- a tag like v0.22.0,
      "HEAD~1", or a branch name.

  Returns:
    {path: {line numbers}} for lines that are NEW or MODIFIED relative
    to ref, taken from git's own diff rather than guessed. An empty
    dict means the tree really is unchanged, never that the baseline
    could not be found -- see Raises.

  Raises:
    SystemExit: when ``ref`` does not resolve to a commit in this
      working directory. Returning an empty dict there would be
      indistinguishable from an unchanged tree, and the caller would
      print a reassuring "0 line(s) changed".

  This is what makes mutation testing affordable as a routine guard
  rather than a campaign. A full run samples a pool of a thousand
  mutations across the whole plugin and answers "how good is the
  suite"; that question does not need asking on every change. The
  question that does is "is the code I just wrote defended", and its
  pool is only the lines that changed. On a normal day that is a
  handful of mutants and a few minutes.
  """
  # Resolve the baseline ONCE, before any per-file diff, and refuse
  # if it is not there. The per-path loop below swallows a failed
  # `git diff` and moves on, which is right when one target file does
  # not exist yet and catastrophic when the REF is the thing missing:
  # every target then yields nothing and the caller prints "0 line(s)
  # changed", which reads exactly like a tree nobody touched. That is
  # what the remote incremental leg reported on 2026-08-12 while
  # deps.py carried 89 changed lines. The cause there was not a
  # missing tag, which was the first guess: the qgis container runs
  # as root against a checkout owned by the runner user, so git
  # refused the whole repository with "detected dubious ownership"
  # and every command failed identically. Either way an instrument
  # that cannot look must say so rather than report a clean zero, and
  # the probe below catches both because it asks git to do one thing
  # and requires an answer.
  try:
    probe = subprocess.run(
      ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
      cwd=ROOT, capture_output=True, text=True)
  except FileNotFoundError:
    # Not every machine that runs this HAS git. qgis/qgis:stable ships
    # none, which is worth stating plainly rather than letting a
    # FileNotFoundError escape from a function whose contract is a
    # dict of changed lines.
    raise SystemExit(
      "git is not installed here, so there is no way to tell what "
      "changed since {}. This is NOT the same as 'nothing changed'. "
      "Install git, or run this where git exists -- the qgis/qgis "
      "stable image, for one, does not carry it.".format(ref))
  if probe.returncode != 0 or not probe.stdout.strip():
    raise SystemExit(
      f"cannot resolve '{ref}', so there is nothing to diff against "
      f"and no honest answer to give. This is NOT the same as "
      f"'nothing changed'. Two causes have been seen: git shut out "
      f"of the directory entirely (a container running as root over "
      f"somebody else's checkout -- 'detected dubious ownership', "
      f"fixed with `git config --global --add safe.directory`), and "
      f"a checkout without the tag (actions/checkout needs "
      f"fetch-depth: 0 and the tag actually fetched). git said: "
      f"{(probe.stderr or '').strip() or '(nothing)'}")

  changed = {}
  for name in TARGETS:
    path = os.path.join("weavingspace_qgis", name) \
        if not name.startswith("weavingspace_qgis") else name
    try:
      diff = subprocess.run(
        ["git", "diff", "-U0", ref, "--", path],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
      continue
    lines = set()
    for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff,
                            re.M):
      start = int(hunk.group(1))
      count = int(hunk.group(2) or 1)
      lines.update(range(start, start + count))
    if lines:
      changed[path] = lines
  return changed


def is_equivalent(mutant):
  """Is this a mutation already PROVEN to change nothing observable?

  Args:
    mutant: a candidate mutation.

  Returns:
    True if it matches an entry in EQUIVALENT, in which case it is
    dropped before sampling rather than counted as a survivor. Every
    entry carries its evidence; nothing is excluded on a hunch.

    An entry marked ``withdrawn`` does NOT exclude anything. A
    withdrawn entry is one whose demonstration a later change
    falsified, and it is kept in the list rather than deleted so that
    the argument and its collapse stay readable -- but the mutant
    goes straight back into the denominator, because an exclusion is
    only as good as the demonstration behind it and a wrongly
    excluded mutant flatters the score. Kept honest by
    ``test_a_withdrawn_equivalence_stops_excluding_its_mutant``.
    (2026-08-12, after an audit found one whose evidence cited three
    line numbers that had all moved and a slot count that had grown.)
  """
  for known in EQUIVALENT:
    if known.get("withdrawn"):
      continue
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


def rank_covering_tests(coverage, touching, mutant):
  """Order a mutant's covering tests, likeliest killer first.

  Args:
    coverage: the per-test record, display name -> executed lines.
    touching: the display names of the tests that reach this mutant's
      line, in whatever order the record held them.
    mutant: the Mutant, read for its file and its original source
      line.

  Returns:
    The same names, reordered. Nothing is added or dropped: a mutant
    is still judged by exactly the tests that reach it, so the VERDICT
    cannot change. Only the order does, and with it how much of the
    covering set has to run before a kill is found.

  Two signals, both free:

  WORD OVERLAP between the mutated line and the test's name. A test
  called "element opacity (layer opacity, authority, gpkg)" is far
  more likely to notice a change to a line mentioning `opacity` than
  a test called "race: two Generate presses". Test names in this
  suite are sentences about behaviour, which makes this unusually
  effective here.

  FOCUS, as the number of lines the test executes. A test covering
  two hundred lines is aimed at something; one covering four thousand
  is an integration session that touches this line in passing and is
  both likelier to be slow and less likely to assert about it.

  Overlap decides first because it is the stronger signal, focus
  breaks ties. Both are heuristics, and being wrong costs only time:
  a mutant that survives the first pass is re-run against everything
  before it is believed.
  """
  import re as _re
  words = set(_re.findall(r"[a-z]{4,}", mutant.before.lower()))
  words |= set(_re.findall(
    r"[a-z]{4,}", os.path.basename(mutant.path).lower()))
  # words too common in this codebase to discriminate between tests
  words -= {"self", "none", "true", "false", "return", "value",
            "weavingspace", "qgis", "test", "with", "that", "from",
            "this", "have", "when", "then", "name", "text"}

  def score(display):
    theirs = set(_re.findall(r"[a-z]{4,}", display.lower()))
    return (-len(words & theirs), len(coverage.get(display, ())))

  return sorted(touching, key=score)


def tests_touching_file(coverage, path):
  """Every test that executes any line of this file.

  Args:
    coverage: the per-test map from coverage_per_test.py -- each test's
      DISPLAY name (the string the suite reports it under) against the
      list of "repo/relative/file.py:line" entries that test executed.
    path: repo-relative file, e.g. weavingspace_qgis/dialog.py, spelled
      the way the coverage entries are.

  Returns:
    A list of display names, in whatever order the record holds them,
    empty when no recorded test so much as imports the file.

  Used INSTEAD of tests_touching for module-level lines. An import runs
  once per process, so the record credits every module-level line to
  whichever test imported first; asking which tests touch such a line
  would pick that one arbitrary test, and the mutant would be judged by
  a test that never looks at it. Every test reaching the FILE is the
  honest covering set there. It is also an expensive one, which is why
  module-level mutants rarely fall inside a small --max-cost stratum.
  """
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


def run_tests(names, base, alone=False):
  """Run some tests in a fresh process, under the watchdog.

  Args:
    names: test function names.
    base: the sandbox to run in — a throwaway copy of the tree, so
      the project itself is never opened for writing.
    alone: nothing else is competing for the machine. Raises the
      wall-clock ceiling, because the ceiling exists to catch hangs
      and a run sharing eight cores with three other workers needs
      far longer for the same work than one that has them to itself.
      Set only by the retry pass.

  Returns:
    "killed" when any test failed, "survived" when all passed,
    "stalled" when the watchdog found no CPU and no output (the
    program really stopped, which is a test noticing something), and
    "timeout" when the ceiling was reached — which is NOT a verdict
    and must not be counted as either.
  """
  code = RUNNER.format(root=base, tests=list(names))
  watchdog = os.path.join(base, "tools", "watchdog.py")
  # The wall-clock ceiling has to scale with the work. A mutant on a
  # heavily covered line is confirmed against every test that touches
  # it -- sixty or more -- and a fixed 300 seconds cannot fit that,
  # least of all with three workers competing. Batch five produced
  # four "stalls" at 313-314 seconds, all running the same 66 tests:
  # not four hangs, one ceiling.
  limit = max(300, 15 * len(names))
  # The STALL patience has to scale with contention too, and for a
  # sharper reason than the ceiling does: a stall is scored as CAUGHT,
  # so a false one FLATTERS the rate, which is the direction this
  # tool's defects keep failing in. Measured 2026-08-12: three mutants
  # that "stalled" at 141-175s with three workers each ran to a real
  # `killed` verdict in 1683-1855s when re-judged alone. Forty seconds
  # of silence is a hang on an idle machine and unremarkable on a
  # crowded one -- which is exactly why the suite's own ceilings widen
  # whenever a shard is in force (MAINTAINING.md).
  #
  # Widening cannot hide a defect. What it converts a false stall into
  # is either a real verdict or a timeout, and a timeout is explicitly
  # NOT a verdict, so the honest failure mode replaces the flattering
  # one.
  stall = 40 if alone else 40 * max(1, CONCURRENCY)
  if alone:
    # a retry with the machine to itself: give it room, since the
    # point is to convert a non-verdict into a verdict rather than to
    # confirm that a crowded machine is slow
    limit *= 3
  result = subprocess.run(
    [sys.executable, watchdog, "--stall", str(stall),
     "--timeout", str(limit), "--quiet", "--", sys.executable,
     "-c", code],
    cwd=base, capture_output=True, text=True)
  if result.returncode == 125:
    # no CPU and no output for the whole stall window: the program
    # really did stop, which is a test noticing something via the
    # watchdog
    return "stalled"
  if result.returncode == 124:
    # we ran out of patience, which says nothing about the mutant
    return "timeout"
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
  """Choose mutants, judge each in a sandbox, and report the rate.

  Args:
    None taken directly; every input arrives on the command line and
    each option is described where it is declared below. Three of them
    change the SHAPE of the measurement rather than its size, and are
    the ones worth knowing before reading any number this prints.
    ``--since`` narrows the pool to the lines a given revision changed,
    which asks whether new code is defended rather than how good the
    suite is. ``--max-cost`` narrows it to mutants covered by few
    enough tests to be affordable and then runs all of them, so the
    result describes that stratum exactly and no other. ``--only``
    abandons sampling altogether and re-judges named mutations.

  Returns:
    None. Everything goes to standard output: the selection, one line
    per verdict, the rate with its confidence bound or its census
    note, the per-module breakdown, and the survivors for triage.
    Nothing in the project is written to -- mutants are applied inside
    throwaway sandboxes, which are discarded before this returns.
    Two side effects reach beyond the printing. ``_exit_code[0]`` is
    set to 1 when a ``--require`` threshold is missed, which is how
    release.py gates on it. And a stale coverage record exits 2
    outright, before any test runs, because a rate measured against a
    record that has not heard of the suite's newest tests understates
    the suite in a direction nobody would notice.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "--sample", type=int, default=None,
    help="how many mutants to judge, default 15. With --max-cost the "
         "sample is drawn from WITHIN that cost stratum, and passing "
         "it turns the census back into a sample; without --max-cost "
         "it is drawn from the whole reachable pool")
  parser.add_argument("--seed", type=int, default=1)
  parser.add_argument("--control", action="store_true",
                      help="apply NO mutation and check the tests pass "
                           "in the sandbox; a 100%% kill rate means "
                           "nothing if the harness fails everything")
  parser.add_argument(
    "--require", type=float, default=None,
    help="exit non-zero if the kill rate falls below this percentage. "
         "Only enforced on samples of five or more, because a rate "
         "over three mutants is not a rate")
  parser.add_argument(
    "--since", default=None,
    help="mutate only lines added or changed since this git revision "
         "(a tag, HEAD~1, a branch). This is the routine guard: it "
         "asks whether the code just written is defended, which is a "
         "different and much cheaper question than how good the whole "
         "suite is")
  parser.add_argument(
    "--only", default=None,
    help="comma-separated file:line specs to re-judge instead of "
         "sampling, e.g. weavingspace_qgis/dialog.py:508")
  parser.add_argument(
    "--no-retry", action="store_true",
    help="do not re-run timed-out mutants alone; leave them as "
         "non-verdicts, which is what happened before retrying "
         "existed")
  parser.add_argument(
    "--allow-stale-coverage", action="store_true",
    help="run even though tests exist that the coverage record does "
         "not know about. They cannot kill anything, so the rate will "
         "understate the suite")
  parser.add_argument(
    "--workers", type=int, default=2,
    help="mutants to judge at once, each in its OWN sandbox and its "
         "own QGIS process. Two by default: measured 1.9x at three "
         "workers with identical verdicts, which is the level the "
         "verdicts were actually shown to survive. Raise it on more "
         "cores, and watch the STALL and TIMEOUT counts -- a mutant "
         "slowed past the watchdog's patience is recorded as caught, "
         "so contention can quietly flatter the score, which makes "
         "this a limit on the MEASUREMENT rather than on the machine")
  parser.add_argument("--max-tests", type=int, default=4,
                      help="most tests to run per mutant (the cheapest "
                           "covering tests are preferred)")
  parser.add_argument(
    "--max-cost", type=int, default=None,
    help="consider only mutants whose covering-test count is this or "
         "smaller, and run ALL of them instead of sampling. A mutant "
         "is judged solely by the tests that cover its line, so that "
         "count IS its price, and it ranges from one to over a "
         "hundred: a uniform sample therefore buys most of its wall "
         "clock at the expensive end. This measures the cheap end "
         "exhaustively instead. The rate it produces belongs to THAT "
         "STRATUM and is not the plugin's kill rate; every line that "
         "reports it says which stratum it measured")
  args = parser.parse_args()

  # Whether a sample size was actually ASKED for, recorded before the
  # --since and --only branches below rewrite args.sample for their own
  # purposes. --max-cost with no --sample is a census of the stratum,
  # and a census must not be mistaken for a sample of one afterwards:
  # its fraction is exact rather than estimated, so the confidence
  # bound a sample earns would be answering a question nobody asked.
  sample_asked = args.sample is not None
  census = args.max_cost is not None and not sample_asked
  if args.sample is None and args.max_cost is None:
    args.sample = 15

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

  # The record decides which tests are even OFFERED the chance to
  # notice a mutant, so a test missing from it can never kill
  # anything. That is not noise, it is a one-directional error that
  # flatters nobody: survivors are overstated and the suite's newest
  # work is exactly what gets ignored. Batch three lost two verdicts
  # this way before the check existed.
  unrecorded = [d for d in names if d not in coverage]
  if unrecorded:
    print(f"\nSTALE COVERAGE: {len(unrecorded)} test(s) in the suite "
          f"are absent from the record, so they cannot kill any "
          f"mutant:")
    for display in unrecorded[:8]:
      print(f"  {display}")
    if len(unrecorded) > 8:
      print(f"  ... and {len(unrecorded) - 8} more")
    # A SAMPLE must not run against a stale record: the rate would be
    # understated and the newest tests ignored, which is the whole
    # reason for this check. A targeted re-judge (--only) is a
    # different act -- it asks whether specific known mutants are
    # caught, usually to settle a timing question -- so it proceeds
    # with the warning above rather than being blocked by it. The
    # verdicts are still read in that light: a test absent from the
    # record cannot kill, so a survivor here may simply be untested
    # by the record rather than by the suite.
    if args.only:
      print("proceeding anyway: --only re-judges named mutations "
            "rather than estimating a rate, so a stale record cannot "
            "understate anything except these verdicts\n")
    elif not args.allow_stale_coverage:
      print("\nRe-record first:\n  QT_QPA_PLATFORM=offscreen ... "
            "<qgis python> tools/coverage_per_test.py\n"
            "or pass --allow-stale-coverage if you genuinely mean to "
            "measure against the older suite.")
      sys.exit(2)
    print("continuing anyway, as asked; the rate will understate the "
          "suite\n")

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
  if args.since:
    changed = changed_lines(args.since)
    total_changed = sum(len(v) for v in changed.values())
    pool = [m for m in pool
            if m.line in changed.get(m.path, ())]
    print(f"{total_changed} line(s) changed since {args.since}, "
          f"carrying {len(pool)} mutation(s)")
    if not pool:
      print("nothing mutable has changed; the suite is unaffected")
      return
    args.sample = min(args.sample, len(pool)) if args.sample else len(pool)

  if args.only:
    # Re-judge named mutations rather than sampling. This is how a
    # previous batch's survivors get a second, honest hearing after
    # the suite has been strengthened -- and after a stale coverage
    # record has been replaced, which is its own reason for a verdict
    # to have been wrong the first time.
    wanted = set()
    for spec in args.only.split(","):
      path, _, line = spec.strip().rpartition(":")
      wanted.add((path, int(line)))
    pool = [m for m in pool if (m.path, m.line) in wanted]
    found = {(m.path, m.line) for m in pool}
    for spec in sorted(wanted - found):
      print(f"note: no mutation available at {spec[0]}:{spec[1]} "
            f"(the line may have changed since it was reported)")
    print(f"re-judging {len(pool)} mutation(s) at {len(found)} "
          f"named line(s)\n")
    # `or 0` because --max-cost leaves the sample size unset; every
    # named mutation is wanted either way, and the pool is already
    # exactly the named ones
    args.sample = max(args.sample or 0, len(pool))

  rng = random.Random(args.seed)
  rng.shuffle(pool)

  # Price every mutant before deciding what to run. A mutant's price is
  # the size of its covering set, because that set is the entire bill:
  # a cheap first pass of --max-tests of them, and, if it survives, a
  # confirming run against all of them.
  #
  # Without --max-cost this stops as soon as the sample is full, which
  # is what it has always done -- the pool is shuffled, so the first N
  # reachable mutants ARE the sample and pricing the rest would be
  # work for nothing. With --max-cost everything has to be priced to
  # know what qualifies, which costs about a second of scanning.
  reachable, uncovered = [], []
  for mutant in pool:
    if mutant.line in MODULE_LEVEL.get(mutant.path, set()):
      touching = tests_touching_file(coverage, mutant.path)
    else:
      touching = tests_touching(coverage, mutant.path, mutant.line)
    # Likeliest killer first, so the cheap first pass has the best
    # chance of finding the kill before the expensive confirming run
    # is needed. Reordering cannot change a verdict; see
    # rank_covering_tests.
    touching = rank_covering_tests(coverage, touching, mutant)
    # Either nothing reaches the line, or the only tests that do have
    # been renamed out of the suite since the record was made. Both are
    # UNCOVERED rather than survivors: nothing looked, so nothing
    # failed to see.
    functions = [names[t] for t in touching if t in names]
    if not functions:
      uncovered.append(mutant)
      continue
    reachable.append((mutant, functions))
    if args.max_cost is None and len(reachable) >= args.sample:
      break

  if args.max_cost is None:
    stratum, qualifying = None, reachable
  else:
    stratum = f"covered by {args.max_cost} test(s) or fewer"
    qualifying = [(m, f) for m, f in reachable
                  if len(f) <= args.max_cost]
  dearer = len(reachable) - len(qualifying)

  # args.sample is None only under a census, where the whole stratum
  # runs; otherwise it caps the draw, and the pool was shuffled before
  # pricing, so a capped draw is a random sample of whatever set it is
  # drawn from.
  limit = len(qualifying) if args.sample is None \
      else min(args.sample, len(qualifying))
  # keep the full covering set as well: a mutant that survives the
  # cheap sample is re-run against all of them before we believe it
  chosen = [(m, f[:args.max_tests], f) for m, f in qualifying[:limit]]

  if args.max_cost is None:
    print(f"{len(pool)} possible mutations; sampling {len(chosen)} "
          f"(seed {args.seed}); {len(uncovered)} skipped as unreached "
          f"by any test\n")
  else:
    share = 100 * len(qualifying) / max(len(reachable), 1)
    print(f"{len(pool)} possible mutations; {len(uncovered)} are "
          f"unreached by any test, leaving {len(reachable)} that a "
          f"test could notice.")
    print(f"COST STRATUM: {len(qualifying)} of those {len(reachable)} "
          f"({share:.0f}%) are {stratum}. The other {dearer} cost "
          f"more and are NOT measured by this run.")
    if not chosen:
      print(f"\nno mutant is {stratum}, so there is nothing to "
            f"measure; raise --max-cost, or re-record coverage if "
            f"that many lines being unreached looks wrong")
      return
    if census:
      print(f"CENSUS of the stratum: running all {len(chosen)}, so "
            f"the rate below is that stratum's exact rate rather than "
            f"an estimate of it.")
    else:
      print(f"sampling {len(chosen)} of the {len(qualifying)} "
            f"(seed {args.seed}); the rate below estimates THIS "
            f"STRATUM and nothing wider.")
    budget = sum(len(t) for _m, t, _a in chosen)
    print(f"first pass is {budget} test run(s); survivors are then "
          f"re-run against their full covering set\n")

  killed = survived = stalled = 0
  survivors = []
  # Runs that hit the wall-clock ceiling. NOT a verdict: counting them
  # as caught would let the machine's load flatter the suite, and
  # counting them as survivors would blame the tests for a scheduling
  # decision. They are reported and excluded, and their existence is
  # a sign the ceiling needs raising rather than the tests improving.
  timeouts = []

  # Everything below happens in a throwaway copy. The project itself
  # is never opened for writing, so an interrupted campaign cannot
  # leave a deliberately broken line behind -- which is not
  # hypothetical: a killed audit did exactly that before this.
  sys.path.insert(0, HERE)
  # Tell run_tests how crowded the machine is about to be, so the
  # watchdog's stall patience is sized for it rather than for an idle
  # one. Set before any judging starts, because a stall counts as
  # caught and a rate is not something to correct afterwards.
  global CONCURRENCY
  CONCURRENCY = max(1, args.workers)
  from sandbox import discard, make_sandbox
  # One sandbox per worker. Each is a separate copy of the tree and
  # each mutant runs in its own QGIS process, so two workers can never
  # see each other's mutation, each other's QgsProject, or each
  # other's temporary files.
  bases = [make_sandbox(f"auto{i}") for i in range(args.workers)]
  base = bases[0]
  if args.workers == 1:
    print(f"mutating a copy at {base}\n")
  else:
    print(f"mutating {args.workers} copies, one per worker, at "
          f"{os.path.dirname(base)}\n")
  import signal

  def cleanup(*_a):
    for sandbox in bases:
      discard(sandbox)
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

  def judge(job):
    """Decide one mutant's fate inside one sandbox.

    Args:
      job: (index, mutant, cheap tests, every covering test, sandbox).

    Returns:
      (index, mutant, tests actually run, verdict, seconds).

    The sandbox is restored afterwards whatever happens, so one
    mutant cannot contaminate the next to use that copy.
    """
    index, mutant, tests, all_tests, sandbox = job
    path, original = apply_mutant(mutant, sandbox)
    began = time.perf_counter()
    try:
      verdict = run_tests(tests, sandbox)
      if verdict == "survived" and len(all_tests) > len(tests):
        # Survival is a claim about the WHOLE suite, and the sample
        # above is a shortcut. Three survivors in the first batch had
        # a test that would have caught them sitting just outside the
        # four chosen, so confirm against every covering test before
        # reporting a gap that is really a truncation.
        verdict = run_tests(all_tests, sandbox)
        tests = all_tests
    finally:
      with open(path, "w", encoding="utf-8") as f:
        f.write(original)
    return index, mutant, tests, verdict, time.perf_counter() - began

  def report(result):
    """Print one verdict and count it."""
    index, mutant, tests, verdict, seconds = result
    print(f"{index:>3}/{len(chosen)} {verdict:>8}  {mutant}  "
          f"({len(tests)} test(s), {seconds:.0f}s)")
    print(f"        {mutant.before.strip()[:88]}")
    if verdict == "survived":
      print(f"     -> {mutant.after.strip()[:88]}")

  jobs = [(i, mutant, tests, all_tests, bases[(i - 1) % len(bases)])
          for i, (mutant, tests, all_tests) in enumerate(chosen, 1)]
  wall = time.perf_counter()
  if args.workers == 1:
    results = (judge(job) for job in jobs)
    for result in results:
      report(result)
      _index, mutant, tests, verdict, _seconds = result
      if verdict == "killed":
        killed += 1
      elif verdict == "stalled":
        stalled += 1
      elif verdict == "timeout":
        timeouts.append((mutant, tests))
      else:
        survived += 1
        survivors.append((mutant, tests))
  else:
    # Each worker owns one sandbox for the whole run, so jobs are
    # handed out round-robin and a thread only ever touches its own
    # copy. Threads are the right tool despite the GIL: every worker
    # spends its life blocked in subprocess.run waiting for a QGIS
    # process to finish.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
      for result in pool.map(judge, jobs):
        report(result)
        _index, mutant, tests, verdict, _seconds = result
        if verdict == "killed":
          killed += 1
        elif verdict == "stalled":
          stalled += 1
        elif verdict == "timeout":
          timeouts.append((mutant, tests))
        else:
          survived += 1
          survivors.append((mutant, tests))
  wall = time.perf_counter() - wall

  # Second chance for the runs that never finished. A timeout usually
  # means contention rather than a hang: four workers on eight cores,
  # and a mutant whose covering set is ninety tests. Re-run alone, one
  # at a time, nothing else competing. Whatever finishes becomes a
  # real verdict; whatever times out again is reported as before.
  #
  # This cannot flatter the score. A retry can only convert a
  # non-verdict into a verdict, and it is as free to return "survived"
  # as "killed" -- the mutant is judged by the same tests either way.
  # Leaving them out was the safe choice when a timeout might mean a
  # hang; measuring them is the accurate one.
  if timeouts and not args.no_retry:
    print(f"\n{len(timeouts)} run(s) hit the ceiling. Re-running them "
          f"alone, where nothing competes for the machine:")
    retried, still_out = [], []
    for mutant, tests in timeouts:
      verdict = run_tests(tests, bases[0], alone=True)
      if verdict == "timeout":
        still_out.append((mutant, tests))
        print(f"  timeout again  {mutant} ({len(tests)} tests)")
        continue
      retried.append((mutant, tests, verdict))
      print(f"  {verdict:>8}  {mutant} ({len(tests)} tests)")
      if verdict == "killed":
        killed += 1
      elif verdict == "stalled":
        stalled += 1
      else:
        survived += 1
        survivors.append((mutant, tests))
    if retried:
      print(f"  {len(retried)} of {len(timeouts)} became real verdicts "
            f"on a second run")
    timeouts = still_out

  for sandbox in bases:
    discard(sandbox)
  total = killed + survived + stalled
  caught = killed + stalled
  rate = 100 * caught / max(total, 1)
  bound = clopper_pearson_lower(caught, total)
  if timeouts:
    print(f"\n{len(timeouts)} run(s) hit the time limit and are "
          f"EXCLUDED from the rate below; they are not verdicts:")
    for mutant, tests in timeouts:
      print(f"  {mutant} ({len(tests)} tests)")

  # The rate line names its own scope. A number that silently
  # describes a subset is the failure this whole tool exists to avoid,
  # and "kill rate: 90%" on a cheap stratum would be exactly that.
  scope = "" if args.max_cost is None else \
      f"  [ONLY MUTANTS {stratum.upper()}]"
  print(f"\nfirst-run kill rate{scope}: {caught}/{total} = {rate:.0f}%"
        f"  (killed {killed}, stalled {stalled}, survived {survived})")
  if args.max_cost is None:
    print(f"true rate is at least {bound * 100:.0f}% with 95% "
          f"confidence  (exact Clopper-Pearson, two-sided lower limit, "
          f"n={total})")
  elif census:
    # A census has no sampling error, so there is nothing to bound:
    # every mutant in the stratum was run and the fraction IS the
    # stratum's rate. What remains uncertain is the other strata, and
    # no interval computed from these mutants can speak for those.
    print("every qualifying mutant was run, so that fraction is the "
          "stratum's exact rate, not an estimate of it")
    print(f"it is NOT the plugin's kill rate: {dearer} of "
          f"{len(reachable)} reachable mutants are covered by more "
          f"than {args.max_cost} test(s) and were never run here")
  else:
    print(f"within this stratum the true rate is at least "
          f"{bound * 100:.0f}% with 95% confidence  (exact "
          f"Clopper-Pearson, two-sided lower limit, n={total})")
    print(f"neither figure is the plugin's kill rate: {dearer} of "
          f"{len(reachable)} reachable mutants are covered by more "
          f"than {args.max_cost} test(s) and were never run here")
  print(f"measured against {suite_stamp()}; the number expires when "
        f"the suite changes")
  print(f"{wall / 60:.0f} min of wall clock with {args.workers} "
        f"worker(s)")

  # Stratified, because a single blended figure lets deterministic
  # logic hide behind Qt plumbing. bridge.py and catalog.py are pure
  # computation and should sit far higher than the dialog's wiring;
  # averaging them into one number would conceal exactly the weakness
  # worth knowing about.
  # Timeouts are excluded here exactly as they are from the headline
  # rate. They were not: every timed-out run counted towards `tried`
  # while never counting as a survivor, so `tried - lost` credited it
  # as a KILL. Batch 10's modules summed to 77/100 against a headline
  # of 73/96 -- the four discarded runs reappearing as successes, in
  # the one place a reader looks to find which module is weakest.
  # This is the same mistake the headline was fixed for once already:
  # machine load flattering the suite.
  timed_out = {id(mutant) for mutant, _ in timeouts}
  per_file = {}
  for mutant, _, _ in chosen:
    if id(mutant) in timed_out:
      continue
    entry = per_file.setdefault(mutant.path, [0, 0])
    entry[1] += 1
  for mutant, _ in survivors:
    if mutant.path in per_file:
      per_file[mutant.path][0] += 1
  if len(per_file) > 1:
    print("\nby module (caught / tried):")
    for path in sorted(per_file, key=lambda k: -per_file[k][1]):
      lost, tried = per_file[path]
      got = tried - lost
      print(f"  {path:<44} {got:>3}/{tried:<3} = "
            f"{100 * got / max(tried, 1):>3.0f}%")
  if args.require is not None:
    if args.max_cost is not None:
      # Worth saying out loud: --require was written to gate a release
      # on the whole population's rate, and here it is being held
      # against one stratum of it. Cheaply covered lines are a
      # particular kind of code, so passing or failing says something
      # narrower than the threshold's usual meaning.
      print(f"\nnote: this threshold is being applied to a STRATUM "
            f"rate (mutants {stratum}), not to the population")
    if total < 5:
      print(f"\n{total} mutation(s) is too few to hold to a "
            f"threshold; reporting only")
    elif rate < args.require:
      print(f"\nBELOW THRESHOLD: {rate:.0f}% caught, {args.require:.0f}% "
            f"required. The code that changed is not defended by the "
            f"tests that changed with it. Close the gaps below, or "
            f"say plainly why each survivor is acceptable.")
      _exit_code[0] = 1
    else:
      print(f"\nnew code holds: {rate:.0f}% caught against a "
            f"{args.require:.0f}% requirement")

  if survivors:
    print("\nsurvivors, for triage (weak assertion / unreached in "
          "practice / equivalent):")
    for mutant, tests in survivors:
      print(f"  {mutant}\n      was: {mutant.before.strip()[:80]}"
            f"\n      now: {mutant.after.strip()[:80]}"
            f"\n      tests run: {', '.join(tests)}")


if __name__ == "__main__":
  main()
  sys.exit(_exit_code[0])
