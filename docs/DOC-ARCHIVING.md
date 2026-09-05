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

    python3 tools/doc_archive.py --suggest    # where the length is
    python3 tools/doc_archive.py              # what is inconsistent

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
| CLAUDE.md | 7,048 | 3,945 | 244 |
| docs/TESTING.md | 5,238 | 2,528 | 118 |
| ROADMAP.md | 3,095 | 1,053 | 71 |
| MAINTAINING.md | 2,422 | 2,414 | 1 |
| docs/PUBLISHING.md | 1,193 | 892 | 5 |

The two documents with almost nothing taken are the finding, not the
omission: MAINTAINING.md is architecture, and docs/PUBLISHING.md is a
runbook whose sections are mostly the procedure itself. What was taken
from PUBLISHING was five accounts of what things cost — the first three
CI rounds, what a release stopped doing, a candidate number spent on a
test repair.

Still owed from that pass, and named here so the next one does not have
to rediscover it.

**MAINTAINING.md has not been read end to end against these two tests**,
only sampled. Its long sections were checked and kept because they name
live mechanisms; the scattered ten- and twenty-line episodes inside them
have not been looked at one by one.

**docs/TOPOLOGY.md (725 lines) and docs/PERFORMANCE.md (604) were left
whole on their outlines** -- section titles and sizes -- rather than on
their prose. Both are topic documents of a size somebody can hold, read
only when working on their ground, so they were last in the queue and
the queue ran out. Neither has an archive, and neither should get one
until somebody has read it.
