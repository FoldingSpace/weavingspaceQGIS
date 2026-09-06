#!/usr/bin/env python3
"""The binding documents are split in two, and this keeps the split honest.

WHY THE SPLIT EXISTS. CLAUDE.md, MAINTAINING.md, ROADMAP.md,
docs/TESTING.md and docs/PUBLISHING.md are read at the START of a
session, by somebody who then has to hold them while working. They grow
by appending, because every lesson here is written down the day it is
paid for, and by 2026-09-05 they had reached 19,000 lines between them
-- CLAUDE.md alone was 7,048. A document that cannot be reread is a
document that is not reread, and the rules in it stop binding anything.

WHAT THE SPLIT IS. Each of those documents keeps the RULE and loses the
ACCOUNT. The rule is what changes what you do: the lesson's headline,
the decision, the procedure, the command. The account is what it cost to
learn: the run that produced it, the wrong hypotheses, the measurements,
the superseded form. The account moves to `<NAME>-archived.md` under a
stable id, and the live entry quotes that id. Nothing is deleted, and
one grep gets the rest.

WHAT THIS TOOL DOES. It cannot judge prose, so it checks the things that
rot: that every id a live document quotes exists in its archive, that
every archived account is still pointed at by something, that the two
halves name each other, and that the live half is still inside the
budget that forced the pass in the first place.

    python3 tools/doc_archive.py               # check, exit 1 on trouble
    python3 tools/doc_archive.py --suggest     # what the next pass would cut
    python3 tools/doc_archive.py --stranded    # rules a pass took by mistake
    python3 tools/doc_archive.py --mint C "title"   # next id, stub written

AND IT CHECKS THE SHAPE OF GROWTH, since 2026-09-05 (the maintainer's
ask that the documents be self-fixing at low cost, for whoever edits
them next): every live document carries a "How to add to this file"
section near its top; a document with fixed sections gains none; an
inbox of unthemed lessons holds at most a handful; no entry runs past a
cap or opens with a date. Each failure names the fix, so the standards
gate teaches the practice at the moment somebody departs from it.

`tools/check_standards.py` runs the check, so it runs at every push and
every release. The procedure a person follows is docs/DOC-ARCHIVING.md.
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (live document, its archive, the prefix its ids carry, line budget).
#
# THE BUDGET IS A FORCING FUNCTION, NOT A MEASUREMENT. It is set about a
# fifth above what the document holds after a pass, so ordinary appending
# is free and a document that has grown by a fifth is one somebody should
# read with an archiving pass in mind. Raising a budget is legitimate and
# is done deliberately, in the commit that needs it, with the reason
# written at the number -- exactly like every other hand-kept figure here.
# What it must never become is a number nobody can meet, since a limit a
# healthy document reaches is a limit people learn to route around.
PAIRS = [
  # 1,932 after the third pass of 2026-09-05 (from 3,919 after the
  # first two, and 7,048 before any), made to the maintainer's measure
  # that the file be as context-efficient as it can be while still
  # transmitting each lesson's rule, its logic and some of its evidence.
  # A fifth above where it stands, as the others.
  ("CLAUDE.md", "CLAUDE-archived.md", "C", 2350),
  # 2,414 after a pass that found almost nothing to take: this file is
  # architecture rather than accretion, and the reasoning in it is the
  # thing a maintainer came for. Budgeted for growth, not for a cut.
  ("MAINTAINING.md", "MAINTAINING-archived.md", "M", 2900),
  # 1,052 after the pass of 2026-09-05, from 3,095 -- and RAISED TO
  # 2100 LATER THE SAME DAY, on the maintainer's decision that "the
  # budget shouldn't be that small". The reason, written here because
  # a number without one is a number nobody can argue with later: the
  # 1500 fired THREE TIMES in a single session, and each time the
  # growth was current content rather than accretion -- eight rulings
  # settled by grilling, five field reports, two caching designs and
  # the open work of a version mid-flight. Each firing was answered by
  # moving DONE accounts out (R-73 to R-78), which is the practice
  # working; but a limit that binds three times in a day is sized for
  # a quieter period than a version carrying this much.
  # A LEDGER IS PRUNED BY A RELEASE RATHER THAN BY A PASS, which is
  # what makes this the budget most likely to bind: what a version
  # owes leaves the file when the version ships, and until then it
  # legitimately grows. 2100 is a fifth above where the ledger stands
  # after the day's passes, which is the same rule the other four use.
  ("ROADMAP.md", "ROADMAP-archived.md", "R", 2100),
  # 836 after the third pass of 2026-09-05, which consolidated the
  # dated lessons into one entry per theme (from 2,527 after the first
  # two passes and 5,238 before any). A fifth above where it stands.
  (os.path.join("docs", "TESTING.md"),
   os.path.join("docs", "TESTING-archived.md"), "T", 1000),
  # 893 after the pass, from 1,193.
  (os.path.join("docs", "PUBLISHING.md"),
   os.path.join("docs", "PUBLISHING-archived.md"), "P", 1100),
  # THE PACKAGE'S DOCSTRINGS, since the pass of 2026-09-05 that took
  # the narrative out of them (the maintainer's ask: "not terribly
  # useful for human maintainers"). The live half is the source tree,
  # read as one text; a docstring keeps what a maintainer needs and
  # quotes a D-id for the account. No budget -- the documentation check
  # in tools/check_standards.py governs docstrings.
  ("weavingspace_qgis", os.path.join("docs", "DOCSTRINGS-archived.md"),
   "D", None),
]

# HOW EACH LIVE DOCUMENT IS ALLOWED TO GROW, so that the cheap edit is
# the right one. These documents will be added to by whoever works here
# next, and the failure the split exists to prevent is not a long file
# but a file that grows by APPENDING EPISODES: a new dated section at the
# end, an account where a clause would do, a lesson nobody folds into the
# theme it belongs to. Each shape below turns one of those into a check
# that fails at the standards gate with the fix in the message.
#
#   sections   the headings the document may have, or None where its
#              sections are not fixed (ROADMAP.md's are versions and
#              MAINTAINING.md's are mechanisms). A new lesson is a
#              clause in an existing section, never a section of its own.
#   inbox      the heading of the holding section for a lesson that fits
#              no theme yet, and how many it may hold before somebody
#              folds them in (docs/DOC-ARCHIVING.md, "Folding the inbox").
#   entry      the most lines one entry -- a `- **` bullet, a `**` lead
#              paragraph, or for docs/TESTING.md a `## ` section -- may
#              run to, set a fifth above the longest that stands after
#              the pass of 2026-09-05 (48, 88, 22, 95 and 24). A ruling
#              keeps its whole statement, which is what sets CLAUDE.md's.
#
# Every live document also carries a section headed HOW_TO_ADD near its
# top, which is the instruction a reader meets first, and no entry may
# OPEN with an episode marker (a date, "Same day", "Also 2026-...") --
# that is the diary shape, and the rule belongs in front with the account
# in the archive.
HOW_TO_ADD = "## How to add to this file"
INBOX = "## Inbox: lessons not yet themed"
SHAPES = {
  "CLAUDE.md": dict(
    sections=[
      HOW_TO_ADD, "## Hard rules", "## Required practices",
      "## Working economically in a long session", "## How we decide things",
      "## Lessons learned here (do not relearn these the hard way)",
      "### Qt, QGIS and the libraries: facts about the toolkit",
      "### Records, stores, keys, landings and the file",
      "### Guards, tests, fixtures, probes and the catalogue",
      "### Watchers, long jobs, gates and the shell",
      "### Method: reading, measuring, repairing and releasing",
      INBOX,
      "## Testing (do this after every substantive change)",
      "## Design decisions already settled (don't relitigate silently)",
      "## Cross-version compatibility targets",
      "## The original library: its role and how to upgrade it",
      "## QGIS breaking changes: the playbook",
      "## The test suite: what it is for and how it runs",
    ],
    inbox=6, entry=60, unit="entry"),
  "MAINTAINING.md": dict(sections=None, inbox=None, entry=110, unit="entry"),
  "ROADMAP.md": dict(sections=None, inbox=None, entry=30, unit="entry"),
  os.path.join("docs", "TESTING.md"): dict(
    sections=[
      HOW_TO_ADD,
      "## A PROBE HAS A KIT NOW, AND ITS TRAPS ARE IN IT",
      "## Where a guard's expectation should come from, when the product is the only thing that knows the answer",
      "## The differential sweep: reproducing and sharding",
      "## Instrument the code under test, never replace it",
      "## A seeded sweep's case numbers mean nothing across seeds",
      "## The modal recorder keeps the sentence, not only the title",
      "## What has actually found defects here, and what has not",
      "## The test shapes that earn their keep",
      "## Finding your way around 51,000 lines",
      "## Testing a PROMISE: synthetic shapes crossed with conditions",
      "## CONVERTING A SUITE WHEN ONE ACT SPLITS INTO TWO",
      "## WHAT \"THE FILE DID NOT CHANGE\" MEANS, MEASURED",
      "## REACH FOR THE MATRIX FIRST when writing or improving a test",
      "## A matrix may balloon, because you are SAMPLING anyway",
      "## Bisect by DISABLING, not by reasoning",
      "## THE HARNESS IS PART OF THE MEASUREMENT",
      "## A TEST THAT RESIZES A CHILD WIDGET HAS MEASURED NOTHING",
      "## WAITS, MOMENTS AND CEILINGS",
      "## FIXTURES THAT CANNOT REACH THEIR OWN CASE",
      "## ASSERTIONS, ORACLES AND WHAT A READING IS",
      "## GUARDS, ENTRIES AND THE CATALOGUE",
      "## WHAT THE TESTS TAUGHT ABOUT THE PRODUCT",
      "## TOOLS, SCRIPTS AND RESTORES",
      "## Lessons, each paid for once",
      INBOX,
    ],
    inbox=6, entry=120, unit="section"),
  os.path.join("docs", "PUBLISHING.md"): dict(
    sections=None, inbox=None, entry=30, unit="entry"),
}

# The opening of an entry that is an EPISODE rather than a rule: a date,
# or one of the ways this project writes "and on the same day".
EPISODE = re.compile(
  r"^(?:[-*]\s+)?(?:\*\*)?\s*\(?(?:\d{4}-\d{2}-\d{2}|Same day|Also \d{4}|"
  r"The same (?:evening|day|morning|night)|Later the same day|"
  r"That (?:evening|morning|afternoon))")
# Where an entry begins: a bullet, a bold lead, or a numbered bold item.
ENTRY = re.compile(r"^(?:- \*\*|\*\*|\d+\. \*\*)")
HEADING = re.compile(r"^#{2,3} ")

# An id as the live half quotes it -- "(C-17.)", ": C-17.", "C-17 and".
QUOTED = re.compile(r"\b([A-Z])-(\d+)\b")
# An id as the archive defines it: one heading per account.
DEFINED = re.compile(r"^### ([A-Z])-(\d+) — ", re.M)


def read(relative):
  """The whole text of one document, by its path from the repository root.

  Args:
    relative: e.g. "CLAUDE.md" or os.path.join("docs", "TESTING.md").

  Returns:
    The file's contents as one string. Raises rather than returning ""
    when the file is missing, because a check that silently reads
    nothing reports that everything agrees.
  """
  full = os.path.join(ROOT, relative)
  if os.path.isdir(full):
    # A live half that is a SOURCE TREE: the package's docstrings quote
    # D-ids into docs/DOCSTRINGS-archived.md, so the whole tree is read
    # as one text. It has no budget and no shape; the documentation
    # check in tools/check_standards.py is what governs docstrings.
    parts = []
    for name in sorted(os.listdir(full)):
      if name.endswith(".py"):
        with open(os.path.join(full, name), encoding="utf-8") as handle:
          parts.append(handle.read())
    return "\n".join(parts)
  with open(full, encoding="utf-8") as handle:
    return handle.read()


def check():
  """Every trouble the split can get into, as a list of sentences.

  Returns:
    A list of problems, empty when the documents agree. Each names the
    file and what to do, because this check fires on somebody else's
    edit weeks later and a bare "mismatch" makes them go looking.

  WHAT IS CHECKED, AND WHY EACH ONE ROTS.

  A QUOTED ID THAT IS NOT THERE is the failure this exists to prevent:
  the live document says the account is in the archive, the reader goes
  looking, and the pointer is the thing that is wrong. That happens by
  renumbering, which is why the ids are never renumbered.

  AN ARCHIVED ACCOUNT NOTHING POINTS AT is the opposite and is quieter.
  It means the rule it belonged to was deleted or rewritten without its
  account, so the archive now holds a page nobody can reach except by
  reading the whole file -- and the next pass will archive the same
  ground again, because nothing says it was already done.

  A DOCUMENT THAT DOES NOT NAME ITS ARCHIVE cannot be followed at all:
  the ids are meaningless to a reader who does not know which file they
  are in, and a session that reads only the live half will never learn
  the archive exists.

  A DOCUMENT OVER ITS BUDGET is not broken, it is due a pass. This is
  the only check here that is about size, and it is what makes the
  practice regular rather than remembered.
  """
  problems = []
  for live, archive, prefix, budget in PAIRS:
    if not os.path.exists(os.path.join(ROOT, archive)):
      # A document may legitimately have nothing archived. What it may
      # not do is quote ids into a file that does not exist.
      text = read(live)
      dangling = {f"{one}-{two}" for one, two in QUOTED.findall(text)
                  if one == prefix}
      if dangling:
        problems.append(
          f"{live} quotes {len(dangling)} archived account(s) "
          f"({', '.join(sorted(dangling))}) but {archive} does not "
          f"exist")
      continue

    live_text, archive_text = read(live), read(archive)
    quoted = {f"{one}-{two}" for one, two in QUOTED.findall(live_text)
              if one == prefix}
    defined = [f"{one}-{two}" for one, two in DEFINED.findall(archive_text)
               if one == prefix]

    if os.path.basename(archive) not in live_text:
      problems.append(
        f"{live} does not name {os.path.basename(archive)}, so the ids "
        f"it quotes point nowhere a reader can follow")
    if os.path.basename(live) not in archive_text:
      problems.append(
        f"{archive} does not name {os.path.basename(live)}, so nothing "
        f"says which document these accounts were cut out of")

    repeated = sorted({one for one in defined if defined.count(one) > 1})
    if repeated:
      problems.append(
        f"{archive} defines {', '.join(repeated)} more than once; an id "
        f"names one account or it names nothing")

    missing = sorted(quoted - set(defined))
    if missing:
      problems.append(
        f"{live} quotes {', '.join(missing)}, which {archive} does not "
        f"define. Ids are never renumbered: if an account was removed, "
        f"remove the pointer to it in the same edit")

    orphans = sorted(set(defined) - quoted)
    if orphans:
      problems.append(
        f"{archive} holds {', '.join(orphans)} and nothing in {live} "
        f"points at them. Either the rule they belong to lost its "
        f"pointer, or it was deleted and the account should go with it")

    lines = live_text.count("\n") + 1
    if budget is not None and lines > budget:
      problems.append(
        f"{live} is {lines} lines against a budget of {budget}. Run "
        f"`python3 tools/doc_archive.py --suggest` and make an "
        f"archiving pass (docs/DOC-ARCHIVING.md), or raise the budget "
        f"in tools/doc_archive.py with the reason written beside it")
    problems.extend(shape_problems(live, live_text))
  return problems


def entries(text, unit):
  """Split a live document into the entries the entry cap is about.

  Args:
    text: the document.
    unit: "entry" for `- **` bullets, `**` lead paragraphs and numbered
      bold items, each running to the next entry, heading or blank line
      followed by unindented prose; "section" for `## ` sections.

  Returns:
    A list of (first line number, [non-blank lines]) pairs.
  """
  lines = text.split("\n")
  found = []
  if unit == "section":
    starts = [k for k, line in enumerate(lines) if line.startswith("## ")]
  else:
    starts = [k for k, line in enumerate(lines) if ENTRY.match(line)]
  for n, start in enumerate(starts):
    stop = len(lines)
    for k in range(start + 1, len(lines)):
      line = lines[k]
      if unit == "section":
        if line.startswith("## ") and k != start + 1:
          stop = k
          break
      elif ENTRY.match(line) or HEADING.match(line):
        stop = k
        break
    found.append((start + 1, [line for line in lines[start:stop]
                              if line.strip()]))
  return found


def shape_problems(live, text):
  """The ways a live document can grow that make it worse, each named.

  Args:
    live: the document's path from the repository root, which selects
      its shape in SHAPES; a document with no shape is not checked.
    text: the document.

  Returns:
    A list of problems, each saying what to do instead, because this
    fires on the next person's ordinary edit and the fix is a habit
    they have not been taught yet.

  THE FOUR SHAPES, AND WHY EACH IS CHECKED RATHER THAN ASKED FOR.

  A MISSING "HOW TO ADD" SECTION means the next reader is not told how
  the file grows, and will do what every reader has done here, which
  is append. A NEW SECTION is how a lesson escapes its theme: it reads
  as organisation and it is accretion. AN INBOX PAST ITS CAP is a
  holding section that has become a section. AN ENTRY PAST THE CAP,
  OR ONE THAT OPENS WITH A DATE, is an account standing where a rule
  should, and the archive is where accounts go.
  """
  shape = SHAPES.get(live)
  if shape is None:
    return []
  problems = []
  lines = text.split("\n")
  if HOW_TO_ADD not in lines[:80]:
    problems.append(
      f"{live} has no `{HOW_TO_ADD}` section in its first eighty lines. "
      f"It is the instruction a reader meets first; put it back "
      f"(docs/DOC-ARCHIVING.md, 'Writing for the next reader')")
  headings = [line for line in lines if HEADING.match(line)]
  if shape["sections"] is not None:
    unknown = [one for one in headings if one not in shape["sections"]]
    for one in unknown:
      problems.append(
        f"{live} has a section this tool does not know: `{one}`. New "
        f"sections are not how this file grows: add the lesson as one "
        f"clause to the theme it belongs to, or to `{INBOX}`, and put "
        f"its account in the archive under a minted id "
        f"(`python3 tools/doc_archive.py --mint <PREFIX> \"<title>\"`). "
        f"If a new theme is genuinely needed, add it to SHAPES in "
        f"tools/doc_archive.py in the same commit, with the reason")
  if shape["inbox"] is not None and INBOX in lines:
    start = lines.index(INBOX)
    stop = next((k for k in range(start + 1, len(lines))
                 if HEADING.match(lines[k])), len(lines))
    held = sum(1 for line in lines[start:stop] if line.startswith("- "))
    if held > shape["inbox"]:
      problems.append(
        f"{live}'s inbox holds {held} lessons against a cap of "
        f"{shape['inbox']}. Fold them into their themes -- one clause "
        f"each, its id kept -- rather than raising the cap "
        f"(docs/DOC-ARCHIVING.md, 'Folding the inbox')")
  for first, body in entries(text, shape["unit"]):
    head = body[0]
    if len(body) > shape["entry"]:
      problems.append(
        f"{live}:{first} is an {shape['unit']} of {len(body)} lines "
        f"against a cap of {shape['entry']} (`{head[:50]}`). Keep the "
        f"rule and about one clause of evidence, and move the account "
        f"to the archive under a minted id")
  # and every PARAGRAPH, since an episode written as plain prose under
  # a heading is the commonest form the diary shape took here
  for k, line in enumerate(lines):
    opens = k == 0 or not lines[k - 1].strip() or HEADING.match(lines[k - 1])
    if opens and EPISODE.match(line) and not ENTRY.match(line):
      problems.append(
        f"{live}:{k + 1} opens with a date or 'same day' (`{line[:50]}`), "
        f"which is the diary shape: lead with the rule, put the "
        f"episode in the archive under a minted id, and quote the id")
  for first, body in entries(text, shape["unit"]):
    head = body[0]
    if EPISODE.match(head):
      problems.append(
        f"{live}:{first} opens with a date or 'same day' (`{head[:50]}`), "
        f"which is the diary shape: lead with the rule, put the "
        f"episode in the archive under a minted id, and quote the id")
  return problems


def mint(prefix, title):
  """Take the next id for one archive and write its stub there.

  Args:
    prefix: which archive, by the letter its ids carry -- C, M, R, T
      or P.
    title: the account's title, as it will appear in the archive's
      index and heading.

  Returns:
    The id minted, e.g. "C-319". The stub is appended to the archive
    with an index line, and the caller is told to quote the id in the
    live half and write the account under the heading -- until both
    are done the check reports the account as stranded, which is the
    nudge working rather than a fault.

  Raises:
    SystemExit: when no archive carries that prefix.
  """
  for live, archive, letter, _budget in PAIRS:
    if letter == prefix:
      break
  else:
    raise SystemExit(f"no archive mints {prefix}- ids; the prefixes are "
                     + ", ".join(one[2] for one in PAIRS))
  text = read(archive)
  highest = max((int(number) for letter_, number in DEFINED.findall(text)
                 if letter_ == prefix), default=0)
  ident = f"{prefix}-{highest + 1}"
  lines = text.split("\n")
  index = [k for k, line in enumerate(lines)
           if line.startswith(f"- **{prefix}-")]
  short = title if len(title) <= 90 else title[:87] + "..."
  index_line = f"- **{ident}** — {short}  <sub>minted</sub>"
  if index:
    lines.insert(index[-1] + 1, index_line)
  stub = (f"### {ident} — {title}\n\n"
          f"<sub>Minted with `tools/doc_archive.py --mint`; the account "
          f"goes here, verbatim, and the live half quotes ({ident}).</sub>\n\n"
          f"(The account.)\n")
  new_text = "\n".join(lines).rstrip("\n") + "\n\n" + stub
  with open(os.path.join(ROOT, archive), "w", encoding="utf-8") as handle:
    handle.write(new_text)
  print(f"{ident} minted in {archive}. Now: write the account under its "
        f"heading, and end the rule in {live} with ({ident}.) -- the check "
        f"reports {ident} as stranded until you do.")
  return ident


def suggest():
  """What an archiving pass would look at, longest first.

  Prints, for each live document, the entries and sections whose bodies
  are longest, since those are where an account has grown around a rule.
  It decides nothing: what stays is a judgement about whether the text
  changes what somebody does, and no measure of length can make it.
  """
  for live, _archive, prefix, budget in PAIRS:
    lines = read(live).split("\n")
    blocks, current = [], None
    for number, line in enumerate(lines, 1):
      if line.startswith("- ") or line.startswith("**") or \
         re.match(r"^#{2,3} ", line):
        if current:
          blocks.append((current[0], number - 1, current[1]))
        current = (number, line)
    if current:
      blocks.append((current[0], len(lines), current[1]))
    blocks.sort(key=lambda one: one[0] - one[1])
    print(f"\n{live} — {len(lines)} lines, budget {budget}, ids {prefix}-")
    for first, last, title in blocks[:12]:
      if last - first + 1 < 12:
        break
      print(f"  {last - first + 1:>4} lines  {first:>5}  "
            f"{title.strip()[:70]}")


# A sentence written to be CARRIED FORWARD: an instruction addressed to
# whoever reads it next, rather than a fact about what happened once.
# These are the sentences a live document exists to hold, and they are
# the ones an archiving pass is most likely to take by accident --
# because an entry here usually narrates first and generalises LAST, so
# a cut that keeps the opening keeps the story and archives the rule.
CARRIED = re.compile(
  r"^(ASK OF ANY|ASK WHICH|ASK WHAT|THE RULE:|THE HABIT|SO: |"
  r"THE TEST TO APPLY|TWO THINGS TO CHECK|THE ONE THING TO CARRY|"
  r"WHEN A [A-Z]{2,})")


def stranded():
  """Rules that ended up in an archive with no copy in the live half.

  Prints, for each pair, any archived account whose CLOSING sentences
  are an instruction to a later reader whose words appear nowhere in
  the live document. Each one is a cut that ran backwards: the account
  was supposed to move and the rule was supposed to stay.

  It is a report and not a check. The pattern reads the sentences this
  project happens to write instructions in, so it finds a kind of
  mistake rather than all of them, and a hit is a paragraph to go and
  read rather than a verdict. Run it at the end of an archiving pass,
  against the pass you have just made.

  Returns:
    The number of stranded rules found, so a caller can print a total.
  """
  total = 0
  for live, archive, prefix, _budget in PAIRS:
    if not os.path.exists(os.path.join(ROOT, archive)):
      continue
    flat = " ".join(read(live).split()).lower()
    accounts = re.split(r"^### ([A-Z]-\d+) — .*$", read(archive), flags=re.M)
    hits = []
    for index in range(1, len(accounts), 2):
      ident, body = accounts[index], accounts[index + 1]
      if not ident.startswith(prefix + "-"):
        continue
      body = re.sub(r"<sub>.*?</sub>", "", body, flags=re.S)
      sentences = [" ".join(one.split())
                   for one in re.split(r"(?<=[.!?])\s+", body) if one.strip()]
      for sentence in sentences[-5:]:
        if not 40 <= len(sentence) <= 300 or not CARRIED.match(sentence):
          continue
        if sentence.lower()[:60] not in flat:
          hits.append((ident, sentence))
          break
    total += len(hits)
    print(f"\n{live} — {len(hits)} rule(s) that live only in {archive}")
    for ident, sentence in hits:
      print(f"  {ident:<7} {sentence[:110]}")
  return total


def main():
  """Check the split, or say what the next pass would look at.

  Returns:
    0 when the documents agree and each live half is inside its
    budget, 1 otherwise -- so this can be run on its own as well as
    through tools/check_standards.py, which is what runs it at every
    push and every release.
  """
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--suggest", action="store_true",
                      help="print what the next archiving pass would "
                           "look at, instead of checking")
  parser.add_argument("--stranded", action="store_true",
                      help="print rules that a pass archived by "
                           "mistake, instead of checking")
  parser.add_argument("--mint", nargs=2, metavar=("PREFIX", "TITLE"),
                      help="take the next id for an archive (C, M, R, T "
                           "or P) and write its stub there")
  args = parser.parse_args()
  if args.mint:
    mint(*args.mint)
    return 0
  if args.suggest:
    suggest()
    return 0
  if args.stranded:
    found = stranded()
    print(f"\n{found} rule(s) to read, and each is a paragraph to "
          f"judge rather than a fault to fix.")
    return 0
  problems = check()
  for problem in problems:
    print(f"  {problem}")
  if problems:
    print(f"\n{len(problems)} problem(s) with the archived documents. "
          f"The procedure is docs/DOC-ARCHIVING.md.")
    return 1
  print(f"the {len(PAIRS)} archived documents agree with their live "
        f"halves, and every live half is inside its budget")
  return 0


if __name__ == "__main__":
  sys.exit(main())
