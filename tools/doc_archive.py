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
  # 3,919 lines after the pass of 2026-09-05, from 7,048.
  ("CLAUDE.md", "CLAUDE-archived.md", "C", 4700),
  # 2,414 after a pass that found almost nothing to take: this file is
  # architecture rather than accretion, and the reasoning in it is the
  # thing a maintainer came for. Budgeted for growth, not for a cut.
  ("MAINTAINING.md", "MAINTAINING-archived.md", "M", 2900),
  # 1,052 after the pass, from 3,095. A ledger grows between releases
  # and is pruned by them, so this is the budget most likely to bind.
  ("ROADMAP.md", "ROADMAP-archived.md", "R", 1500),
  # 2,527 after the pass, from 5,238.
  (os.path.join("docs", "TESTING.md"),
   os.path.join("docs", "TESTING-archived.md"), "T", 3000),
  # 893 after the pass, from 1,193.
  (os.path.join("docs", "PUBLISHING.md"),
   os.path.join("docs", "PUBLISHING-archived.md"), "P", 1100),
]

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
  with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
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
    if lines > budget:
      problems.append(
        f"{live} is {lines} lines against a budget of {budget}. Run "
        f"`python3 tools/doc_archive.py --suggest` and make an "
        f"archiving pass (docs/DOC-ARCHIVING.md), or raise the budget "
        f"in tools/doc_archive.py with the reason written beside it")
  return problems


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
  args = parser.parse_args()
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
