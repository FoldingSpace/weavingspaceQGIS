# How this plugin was actually tested

These are working records, kept because the reasoning in them is
worth more than the conclusions. They are not tidy, and several of
them are mostly accounts of being wrong.

**The three test campaigns** each set out to find defects in an area
nobody had tested, and each says what it looked for, what it found
and what it did not. The third is the most useful to read first: by
then the method had settled, and the ratio of tests written to
defects found is a fair picture of what this kind of work returns.

**The perceptual colour findings** measure how separable the default
element colours actually are, in a colourspace that models human
vision rather than in RGB. The uncomfortable result — most gallery
maps have element fills closer than a distance a reader can reliably
tell apart — is why the colour editor exists.

**The hunt record** (HUNT-RECORD.md) is the newest of these and the
one to read if you are about to look for defects: which directions
have paid, which came back empty, how to run and watch a hunt, and
how the method compares with the suite, mutation testing and the
sweep. The raw check-in logs from the twelve hunts of 2026-08-13 sit
beside it in `hunt-logs-2026-08-13/`, kept for the ratio of ruled-out
to confirmed rather than for the prose, and including the two hunts
that recorded their own sloppiness about timestamps.

**The upstream note** reports a rendering difference to the
weavingspace project, and opens by retracting an earlier note that
blamed one of their commits. It is kept in full, retraction first,
because a project that publishes only its correct diagnoses is
publishing a fiction. The divergence was eventually found to be in
our own comparison harness, not in the library and not in the plugin.

What is deliberately NOT here: one-shot scripts, scratch files, and
the rolling session handover. Those are working files rather than
records, and publishing them would bury these.

The durable rules these campaigns produced live elsewhere and are
binding rather than historical: `docs/TESTING.md` for the test
shapes and the lessons each cost, `docs/MUTATION-TESTING.md` for what
the mutation score means and what is promised about it, and
`docs/MUTATION-LOOP.md` for running a campaign from scratch.
