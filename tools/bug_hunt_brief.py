"""Build the brief for a subagent whose job is to FIND a defect.

Why this file exists, and why it is not the same as the brief we
already use. The test-writing brief asks an agent to write a guard and
then break the product on purpose to prove the guard works. That is
suite-building, and it is well served: twenty tests arrived that way on
2026-08-13 and all twenty were real. This is the other job -- hunting
for a defect that is in the code RIGHT NOW -- and it needs opposite
incentives, because the two are easy to confuse and the confusion is
expensive.

THE INCENTIVE PROBLEM, stated plainly, because everything below
follows from it. If an agent is rewarded for producing a failing test,
it will produce failing tests, and failing tests are cheap. Three ways
to manufacture one without a defect existing, all of which happened
here in a single day:

  * a dirty fixture. The randomised differential sweep went red by
    twelve percent of its interior pixels. The plugin was entirely
    right -- its table and its map agreed -- and the TEST was leaving
    output layers in the shared project between cases.
  * a misused API. `setCurrentText` on the ramp combo moves the
    display and records nothing, because the choice is recorded from
    `activated`, which is a user picking. A test driving it that way
    "proves" the ramp is not saved.
  * a wrong oracle. A plain weave was handed a passing pattern it
    cannot have, and two of twelve hundred sweep cases duly diverged
    by half their pixels. The comparison was wrong, not the map.

So the unit of reward here is A CONFIRMED DEFECT, and confirmation is
defined below and is not negotiable. An agent that reports nothing is
in good standing. An agent that reports a red test it has not
confirmed has done worse than nothing, because somebody then spends an
afternoon in a worktree bisecting to prove the software was fine.

Calibration, kept honest and updated as claims are judged. Of the
agent claims put through the confirmation below on 2026-08-13: the
asymmetry hunt returned three and all three were real defects; a
boundary agent returned one, and it did not reproduce under either
configuration tried. The difference was not the model. The first was
asked for a structural property that either exists or does not; the
second was asked, in effect, for a failure.

Usage:

    python3 tools/bug_hunt_brief.py --area "the live update path"
    python3 tools/bug_hunt_brief.py --shape asymmetry --area bridge.py

The output is the prompt. Read it before sending it: the areas worth
hunting change, and a brief nobody re-read is how an agent ends up
looking where the last one already looked.
"""
import argparse
import textwrap


# The shapes that have actually produced defects in this project, with
# what each one is and what it costs to check. Ordered by yield: every
# defect found here in the week to 2026-08-13 came from one of the
# first two, and none came from mutation sampling, which measures the
# SUITE rather than the software.
SHAPES = {
  "asymmetry": (
    "A path beside its own twin. This codebase has near-twins written "
    "months apart -- the categorical and graduated styling paths, the "
    "restyle route and the run-landing route, the table and the "
    "layer. Read one beside the other and ask what one does that the "
    "other does not. Each site looks perfectly reasonable alone; only "
    "the PAIR is wrong, which is why reading either one on its own "
    "finds nothing. Three defects came from this in one morning and "
    "none needed a machine to find."),
  "write-only": (
    "A value that is written, stamped, saved or exported, and read "
    "back by nobody. Follow each field from where it is set to where "
    "it is consumed. A stamp with no reader is either dead weight or "
    "a promise the code is not keeping."),
  "two-stores": (
    "One fact held in two places, where only one of them is updated "
    "or persisted. The table and the layer; `_signature` and "
    "`_run_signature`; the catalogue and the spin box. Ask which is "
    "the authority and what happens when they disagree. Both defects "
    "found on 2026-08-13 by this shape were cases where the "
    "disagreement did not stay cosmetic, because the next Generate "
    "pushed the table's belief onto the map."),
  "unreachable": (
    "A branch that cannot run because nothing upstream produces the "
    "state it guards -- the condition is right and the precondition "
    "never arrives. Distinguish carefully from a branch that is "
    "merely rare. The evidence is in the callers, not in the branch."),
  "one-boundary": (
    "State that survives one boundary and not another: a save but not "
    "an export, a session but not a reopen, an idle moment but not a "
    "run in flight. The richest defects here live where something is "
    "written out and read back."),
}


BACKGROUND = """\
THE SOFTWARE. A QGIS 4 plugin (PyQt6) that draws tiled and woven
multivariate maps. It is a shell around a vendored library that does
all the mathematics; the plugin's job is parameters in, GeoDataFrame
to layer, symbology, threading and guards. Its characteristic failure
is A WRONG MAP THAT LOOKS EXACTLY LIKE A RIGHT ONE, which is why "a
map appeared" assertions have walked past real bugs here repeatedly.

WHAT COUNTS AS A DEFECT. A user is worse off in a way they would not
have noticed. Preferably: their map is wrong, or their work is
destroyed, or a control says something the map contradicts. If you
cannot finish the sentence "a user loses ___", you have found a
curiosity, not a defect, and the honest report is that you found
nothing.

WHAT IS DELIBERATE AND IS NOT A DEFECT. Read CLAUDE.md's settled
decisions before claiming anything -- roughly half of what looks wrong
in this dialog is a decision somebody made on purpose, and reporting
one of those costs the maintainer the time to re-explain it. Known
examples: a reopened dialog does NOT restore which variable each
element carried (the design tool starts fresh; the output layers and
their styling persist); choosing a ramp DESTROYS that element's
hand-picked colours for the current field, and says so; a constant
column collapses to one class deliberately; an element left on "---"
draws as flat fill; live update is gated and declines rather than
chasing a remote source. If your finding is one of these, say so and
move on -- that is a useful report."""


RULES = """\
HOW TO WORK, and none of this is optional.

  * READ FIRST: CLAUDE.md, docs/TESTING.md, and docs/TEST-MAP.md.
    The first two are binding, not background. The third tells you
    what is already covered, and re-finding a covered thing wastes
    the review it costs.
  * The tree is SHARED. Do not edit tests/run_tests.py or the plugin
    source in place -- other agents and the maintainer are working in
    it, and a break you leave behind is charged to somebody else's
    afternoon. Work in a copy, and say in your report which copy.
  * Everything shares one QgsProject singleton. If you leave layers
    behind, the next thing you run is measuring your rubbish. This is
    the exact mechanism behind the false alarm described above.
  * An exception raised inside a Qt slot does NOT reach the calling
    code: Qt sits between them and the traceback goes to
    `sys.excepthook`, so your assertions go on passing over the top
    of it. The suite has `_QtNoiseWatch` for this. A real IndexError
    of exactly this kind sat in a signal handler unnoticed.
  * Drive controls the way a USER does. The ramp combo records from
    `activated`, not `setCurrentText`. A categorical ramp is refused
    on a graduated row. Class counts run 2..20. If a control appears
    not to work, suspect your driving of it first -- that suspicion
    has been right more often than not.
  * pyproj is main-thread-only in this process; QGIS links the same
    PROJ and concurrent use segfaults. Do not add CRS work to the
    worker path while investigating."""


CONFIRMATION = """\
CONFIRMING A FINDING. A failing test is not a defect. It is a
disagreement between the software and your expectation, and your
expectation is the newer of the two. Before you report anything:

  1. Reach the same fact by a SECOND, INDEPENDENT ROUTE. Not the same
     test with another assertion -- a different mechanism. If a value
     is wrong in the table, read it off the layer. If a colour is
     wrong on the map, read the renderer. If a file is wrong, open it
     with GDAL rather than through QGIS.
  2. State the harm in the user's terms, in one sentence, before you
     write any code. If you cannot, stop.
  3. Check it against the settled decisions above and in CLAUDE.md.
  4. Rule out your own fixture: run your reproduction on a CLEAN
     project, and confirm the same result when nothing else has run
     first.
  5. Say when it started, if you can. `git log -S` on the line, or a
     run against an earlier commit, turns "this is broken" into
     "this broke here", which is the difference between a report and
     a diagnosis.

If a step fails, that is a RESULT and you should report it. "I thought
X was wrong, it was my fixture" is worth more than silence, because it
stops the next agent spending its budget the same way."""


DELIVERABLE = """\
WHAT TO HAND BACK. A reproduction, not a test file. The maintainer
writes the test, because a test is a promise about behaviour and
deciding what to promise is their call, not yours.

  * the harm, one sentence, in a user's terms;
  * the smallest script that shows it, and the exact command to run;
  * what the second independent route said;
  * the file and line where you believe it goes wrong, and why;
  * when it started, if you found out;
  * your CONFIDENCE, and what would change your mind.

Under 250 words. If you found nothing, say what you looked at, what
you ruled out and where you would look next -- that is a good report
and is credited as one. Do not pad it with a finding you do not
believe."""


def build_brief(area: str, shape: str = "asymmetry",
                budget: str = "") -> str:
  """Assemble the full prompt for one bug-hunting subagent.

  Args:
    area: what the agent should hunt over, in this project's own
      terms -- a file ("bridge.py"), a path through the dialog ("the
      live update path"), or a boundary ("what a saved project
      restores"). Narrow beats broad: an agent told to search
      everything reports the first thing it sees.
    shape: which key of SHAPES to hunt for. The shape is the point.
      An agent asked for a structural property that either holds or
      does not will report honestly; an agent asked for "a bug" is
      being asked to come back with something.
    budget: optional free text bounding the work ("read only, no
      QGIS runs", "at most an hour"). Empty means no bound is
      stated, which is right when the area is already narrow.

  Returns:
    The prompt, as one string ready to pass to the Agent tool. It
    carries the background, the rules, the confirmation protocol and
    the deliverable format, because a brief that assumes the agent
    has read this project before is a brief that gets a confident
    stranger's answer.

  Raises:
    KeyError: the shape is not one of SHAPES. Deliberately not
      defaulted: silently hunting the wrong shape would produce a
      plausible report about the wrong thing.
  """
  # wrapped to the same width as the constants below, because a brief
  # arriving as one very long line reads as machine output and gets
  # skimmed, which is the one thing this text cannot afford
  description = textwrap.fill(SHAPES[shape], width=70)
  closing = textwrap.fill(
    "A last word on what is being asked. You are NOT being scored on "
    "whether you find something. You are being scored on whether what "
    "you report survives being checked -- and everything you report "
    "will be checked, by somebody who will run it themselves. A clean "
    "\"nothing here, and here is what I ruled out\" is a good day's "
    "work. A finding that evaporates under checking is worse than "
    "silence, because it costs the time of the person checking it.",
    width=70)
  parts = [
    textwrap.fill(
      "You are hunting for a defect that is in this code RIGHT NOW, "
      "in the weavingspace QGIS plugin checkout you have been given. "
      "You are not writing tests and you are not improving the "
      "suite.", width=70),
    f"YOUR AREA: {area}",
    f"THE SHAPE YOU ARE HUNTING: {shape}.\n{description}",
    BACKGROUND, RULES, CONFIRMATION, DELIVERABLE, closing,
  ]
  if budget:
    parts.append(textwrap.fill(f"BUDGET. {budget}", width=70))
  return "\n\n".join(parts) + "\n"


def main() -> int:
  """Print a brief for the area and shape given on the command line.

  Returns:
    0 always. This writes a prompt to stdout and touches nothing; it
    is a document generator, not a gate, and nothing should key a
    decision on its exit code.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--area", required=True,
                      help="what to hunt over, e.g. 'the live update path'")
  parser.add_argument("--shape", default="asymmetry", choices=sorted(SHAPES),
                      help="which defect shape to hunt (default: asymmetry)")
  parser.add_argument("--budget", default="",
                      help="optional bound on the work, in plain words")
  args = parser.parse_args()
  print(build_brief(args.area, args.shape, args.budget))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
