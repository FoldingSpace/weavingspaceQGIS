# Keeping the binding documents readable: the archiving pass

The documents an assistant reads at the start of a session are the ones
that decide what it does. They are also the ones this project appends
to, every time something is learned, which is the right habit and has a
cost that compounds: by 2026-09-05 CLAUDE.md, MAINTAINING.md,
ROADMAP.md, docs/TESTING.md and docs/PUBLISHING.md held **18,997 lines**
between them, and CLAUDE.md alone held 7,048.

A document that cannot be reread is not reread. The rules in it go on
being true and stop being followed, which is worse than not having
written them down, because everybody believes they are in force.

So each of those documents is split in two. The five now hold 10,832 lines between them, and every line that left is still in the repository.

## What stays and what goes

**The live half keeps the rule. The archive keeps the account.**

**THE MEASURE IS THE RULE PLUS ABOUT ONE CLAUSE OF EVIDENCE.**
(Maintainer's ruling, 2026-09-05, with room to break it where the
situation demands.) A rule stripped to a bare imperative degrades into
a platitude nobody applies -- "assert the premise" means nothing to
somebody who has never watched a premise fail green -- so the live
entry keeps the sentence that makes it believable, and one clause of
what it cost. Not the run, not the measurements, not the hypotheses
tried first, not the superseded wording. If you find yourself keeping
a second sentence of evidence, ask whether it is evidence for the same
claim or a second claim wearing the first one's headline; if it is the
second, that is a separate entry, and if it is the first, it belongs
in the archive.

WHAT BREAKING IT LOOKS LIKE, since the room to break it is part of the
ruling. A RULING keeps its whole statement, because the section exists
so nobody relitigates silently and a reader has to see what was decided
without opening another file. A PROCEDURE keeps every step: an
instruction with a step missing is worse than no instruction. A DEBT
keeps whatever names what is owed. What none of those licenses is
keeping the narrative -- the day, the wrong first hypothesis, the
measurement -- and that is what the archive is for.

The RULE is whatever changes what you do: the lesson's headline, the
decision, the procedure, the command, the constraint. It stays where it
was, in the order it was in, so the document still reads as a document.

The ACCOUNT is what it cost to learn: the run that produced it, the
measurements, the wrong hypotheses, the fix that was tried first, the
superseded form of the rule, the date and the person who ruled. It moves
to `<NAME>-archived.md` under an id — `C-17`, `T-4`, `R-22` — and the
live entry ends by quoting that id.

Nothing is deleted. That is the whole basis on which this is safe: an
archived account is one `grep` away, and the live half tells you it is
there. Deleting is a different decision and needs a different argument.

Two tests, in order:

1. **Would somebody act differently for having read it?** If yes it
   stays, however old it is. A rule from the first week is a rule.
2. **Would somebody who is NOT working on this ground today have to read
   it?** If no it goes, however good it is. The best-written account of
   a defect in the save path is not something the next twelve sessions
   need in front of them.

**AND THE RULE IS OFTEN THE LAST SENTENCE, NOT THE FIRST.** This is
the mistake the first pass made thirty-eight times, and it is the one
to guard against, because it inverts the whole practice. An entry here
usually narrates first and generalises last: it opens with the day and
the defect and closes with `ASK OF ANY WATCHER WHETHER ITS OUTPUT CAN
EXPRESS THE FAILURE`, or `THE HABIT: when a gate's behaviour surprises
you, open the gate, not the document that describes it`. A cut that
keeps the opening keeps the STORY and archives the RULE -- which is
exactly backwards, and leaves a live document that reads as a bug diary
while the transferable sentences sit in a file nobody opens. Read to
the END of an entry before deciding what it is. `python3
tools/doc_archive.py --stranded` finds this shape after the fact.

The headline is what does the work here, and it survives because these
documents are written rule-first: the bold lead states the finding and
the body proves it. Where a headline is a noun phrase or a slogan that
means nothing on its own — "The Categorical colour editor" — the live
half keeps enough sentences to stand alone. A pointer is not a summary,
and an entry cut to something that no longer says anything has been
deleted with extra steps.

## What is exempt, and why

**Anything a version still OWES.** ROADMAP.md's outstanding entries stay
in full: the release gate reads that file, deferring is the maintainer's
decision and nobody else's, and a debt somebody has to go and look up is
a debt that gets forgotten. Only entries whose work is DONE were moved,
and even they keep their headline in the ledger.

**Architecture.** MAINTAINING.md was passed over almost entirely. It is
not accretion — its measurements and its history are the answer to "how
does this work and why is it like that", which is what somebody opened
it for. The pass took two shard-fault episodes and left everything else.
A document that is dense is not a document that is bloated.

**Settled decisions keep their statement.** CLAUDE.md's settled
decisions were cut to the decision plus enough of the reasoning to act
on, never to a title. The section exists so nobody relitigates silently,
and that only works if the reader can see what was decided without
opening another file.

**Generated documents.** docs/TEST-MAP.md and docs/BUG-REGISTER.md are
produced from the suite and are never edited by hand, so there is
nothing to archive: they are already exactly as long as the thing they
describe.

**User-facing documents.** README.md, docs/USER-GUIDE.md and
docs/index.html are written short already and are read by people who are
not us.

## Doing a pass

    python3 tools/doc_archive.py --suggest     # where the length is
    python3 tools/doc_archive.py --stranded    # rules a pass took by mistake
    python3 tools/doc_archive.py               # what is inconsistent

`--suggest` lists the longest entries and sections in each live
document. It is a starting point and not a verdict: length is a symptom,
and only reading decides.

Then, for each entry you take:

1. Copy the whole entry, verbatim, into `<NAME>-archived.md` under a
   new `### <PREFIX>-<n> — <title>` heading, with a line saying which
   document and which lines it came from. Add it to the index at the
   top of that file.
2. Leave the rule in place, ending with the id in brackets: `(C-17.)`
3. **Ids are never reused and never renumbered.** They are quoted in the
   live document, in commits, and in conversations. The next id is one
   past the highest that has ever existed, whatever has since been
   removed.
4. Run `python3 tools/doc_archive.py`. It will tell you about a pointer
   with no account, an account with no pointer, and a document still
   over its budget.
5. Run `python3 tools/doc_archive.py --stranded` against the pass you
   have just made, and read every paragraph it names. It reports an
   archived account whose closing sentences instruct a later reader in
   words that appear nowhere in the live half. It is a report and not a
   check: it finds the shape this project has actually got wrong, not
   every way of getting it wrong, and a hit is a paragraph to judge.

## When a pass happens

**Whenever a live document goes over its budget.**
`tools/check_standards.py` runs this check, so it fires at every push and
at every release, and the budgets in `tools/doc_archive.py` are set about
a fifth above what each document held after the pass of 2026-09-05.
Ordinary appending is free; a fifth of growth is the signal.

**And whenever you have just appended a long account.** The moment to
split an entry is the moment you write it, when you still know which
half is the rule. Write the rule into the live document and the account
straight into the archive — that is cheaper than any later pass, and it
is the habit this practice is really asking for.

**Raising a budget is legitimate**, and is done in the commit that needs
it with the reason written at the number, like every other hand-kept
figure here. What it must not be is a reflex: a budget raised to make a
check pass is a check that has been switched off.

## What the pass of 2026-09-05 did

| Document | Before | After | Accounts archived |
|---|---|---|---|
| CLAUDE.md | 7,048 | 3,883 | 262 |
| docs/TESTING.md | 5,238 | 2,481 | 131 |
| ROADMAP.md | 3,095 | 1,051 | 72 |
| MAINTAINING.md | 2,422 | 2,415 | 1 |
| docs/PUBLISHING.md | 1,193 | 902 | 5 |

("After" is after the audit below, which put the archived rules back
and then made a second pass against the measure.)

The two documents with almost nothing taken are the finding, not the
omission: MAINTAINING.md is architecture, and docs/PUBLISHING.md is a
runbook whose sections are mostly the procedure itself. What was taken
from PUBLISHING was five accounts of what things cost — the first three
CI rounds, what a release stopped doing, a candidate number spent on a
test repair.

## What the audit of 2026-09-05 found, and put back

The pass above was made from OUTLINES for three of the five documents
-- section titles and sizes and a sample, not the prose -- which is a
thing to say plainly rather than to let a results table imply. Read
properly afterwards, it had three faults, all the same fault wearing
three coats: **the cut kept each entry's head, and these entries state
their rule last.**

| What was wrong | How many | Where |
|---|---|---|
| A generalised instruction archived, its incident left live | 38 | CLAUDE 33, TESTING 3, ROADMAP 1, PUBLISHING 1 |
| An entry promising an enumeration and delivering one item | 3 | R-54, T-15, R-33 |
| A live cross-reference pointing at a fact that had moved | 1 | P-3, from "Coverage is NOT among them any more" |

All of them are repaired: the rules are back in the live halves, T-15
(which is procedure end to end and should never have been cut at all)
is restored whole, and R-54's unclosed parenthesis -- made by the cut
itself -- is closed. The archives were left exactly as they were, so
they remain a verbatim record of what the pass took; a restored rule
therefore appears in both halves, which is the honest cost of mending
a cut rather than pretending it was never made.

**AND A SECOND PASS FOLLOWED, ON THE MEASURE.** Once "the rule plus
about one clause of evidence" was the standard rather than an
instinct, the five documents were read against it and the entries that
broke it were cut: the big grilling blocks, whose numbered rulings are
the rule and whose surrounding narrative was not; the CI-parity
practices, which carried their whole account beside a pointer to it;
and the closed field report in ROADMAP.md, which kept a full
measurement of finished work in the live ledger. Eighteen accounts
moved, C-245 to C-262, T-119 to T-131 and R-72.

WHAT THE SECOND PASS DID NOT TOUCH, and the reason is the ruling's own
room to break the measure. MAINTAINING.md is architecture and stayed
whole. The numbered rulings of the grillings kept every statement.
Procedures kept every step -- the `check_before_push` block lost its
account and not one line of its command. And the outstanding entries
in ROADMAP.md were left exactly as they are, because a debt is not
evidence.

**What this says about the practice, and not just about one pass.** A
mechanical cutter cannot do this, and the first pass half-believed it
could. Length is a symptom and the tool may point at it, but every
entry has to be READ TO ITS END by somebody deciding what is rule and
what is account. That is the whole of the judgement, and it is why the
budget is a trigger for a person rather than a job.

Still owed from that pass, and named here so the next one does not have
to rediscover it.

**MAINTAINING.md HAS NOW BEEN READ END TO END** (2026-09-05, later the
same day). It found one fault and it was not length: the dataset-switch
contract of 2026-08-21 and 24 was set out in full, and the block
beneath it opened by saying that contract had been REPLACED on
2026-08-25 -- so a maintainer met the superseded rules first and the
governing ones second, with nothing but reading order to tell them
apart. The governing contract leads now and the earlier machinery is
named in one clause, because it does survive in the source; the full
earlier contract is M-2. Nothing else was taken. The file is
architecture, and a document that is dense is not a document that is
bloated.

A SUPERSEDED CONTRACT STATED BEFORE THE ONE THAT GOVERNS is worth
adding to the two tests as a thing to look for, since length does not
reveal it and neither does `--suggest`: both blocks are healthy prose,
and only reading them in order shows that the first is no longer true.

**docs/TOPOLOGY.md (724) AND docs/PERFORMANCE.md (603) HAVE NOW BEEN
READ, AND NEITHER GETS AN ARCHIVE.** They are topic documents: nobody
reads them at the start of a session, only when working on their
ground, so the measure that governs the five binding documents does not
bind them in the same way -- what looks like an over-long account in
CLAUDE.md is the entire point of a document somebody opened BECAUSE
they wanted the evidence. Both were also checked for the fault
MAINTAINING.md had, a superseded statement standing before the one that
governs, and neither has it.

WHAT WOULD CHANGE THAT is somebody being asked to read either at
session start. If that happens they are binding documents and they get
the same treatment as the other five.

## The third pass, and the measure it was made to

**CONTEXT-EFFICIENT, AND STILL EFFECTIVE.** (Maintainer's instruction,
2026-09-05, later the same day: the documents are to be "as context
efficient as possible while being effective -- we want their lessons
and logics and some reasons/evidence to be transmitted".) That is the
measure above stated from the reader's side, and it licenses one thing
the first two passes did not do: CONSOLIDATION. Where a section held
forty lessons each stated as its own dated episode, the lessons of one
theme are now one entry each, a family of related rules with the ids
of every original quoted beside the clause it became, and the forty
originals archived verbatim under one id per theme (C-264 to C-268).
Nothing was deleted and no id was renumbered; a rule that had lived
only in its account was put back live in the consolidated form.

What the pass took from CLAUDE.md, 3,919 to 1,932 lines: the five
lesson themes; the Hard rules' and Required practices' accounts
(C-269 to C-293); the narrative round the settled rulings, whose
numbered statements stay whole (C-294 to C-314); the two-relationships
framing and the decision-check (C-315, C-316); and the suite
environment's and the reference column's accounts (C-317, C-318).

docs/TESTING.md took the same pass the same day, 2,527 to 836 lines:
the procedures, the test shapes, the matrix method and the probe kit
stay whole, and the hundred and fifty dated lessons became seven themed
entries (T-134 to T-140) with the two long sections compressed in place
(T-141, T-142). Its budget follows it to 1000.

TWO THINGS THE CONSOLIDATION TAUGHT. First, `--stranded` reports every
rule whose exact wording now lives only in the archive, and after a
consolidation that list is mostly paraphrase rather than loss -- so
read each hit against the consolidated entry before restoring it, and
restore only what is genuinely missing (two of twenty-seven were).
Second, a pass over a document is written as a script of anchored
moves (`dev/doc_pass.py`) rather than by hand, so every cut is a
verbatim copy and the id placeholder is filled by the tool; the end
anchor of the last entry in a file needs a sentinel line, since the
tool anchors on the NEXT block.
