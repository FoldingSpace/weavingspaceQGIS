You are hunting for a defect that is in this code RIGHT NOW, in the
weavingspace QGIS plugin checkout you have been given. You are not
writing tests and you are not improving the suite.

YOUR AREA: everything a person does with the topology tab, saving and loading

THE SHAPE YOU ARE HUNTING: asymmetry.
A path beside its own twin. This codebase has near-twins written
months apart -- the categorical and graduated styling paths, the
restyle route and the run-landing route, the table and the layer. Read
one beside the other and ask what one does that the other does not.
Each site looks perfectly reasonable alone; only the PAIR is wrong,
which is why reading either one on its own finds nothing. Three
defects came from this in one morning and none needed a machine to
find.

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
move on -- that is a useful report.

HOW TO WORK, and none of this is optional.

  * USE THE HARNESS. Do not write your own wrapper to start QGIS's
    Python, and do not copy one from an old hunt's scratchpad:

        python3 tools/hunt_probe.py --prepare        # freeze HEAD
        python3 tools/hunt_probe.py --run probe.py   # in the copy
        python3 tools/hunt_probe.py --status         # has HEAD moved

    Eleven hand-written wrappers in one session all carried the same
    WRONG `QGIS_PREFIX_PATH`, so those hunts probed a QGIS with no
    stock colour ramps and none of them knew. The harness resolves
    that the same way the suite and CI do, freezes HEAD into a copy
    for you, prints the commit on every run, and REFUSES once HEAD
    has moved -- which is not fussiness: two hunts of three in one
    round spent their entire run confirming defects that had been
    fixed while they ran.
  * A PROBE IS A HYPOTHESIS, not a program. The harness supplies the
    interpreter, the environment and the working directory, so a
    probe should be the ten or twenty lines that state the question.
    One session produced 373 probe files at a median of 79 lines,
    most of it the same boilerplate re-typed.
  * WRITE THE LOG IN THE GIVEN FORMAT, exactly. Each entry begins
    `## HH:MM:SS  iteration N` and every result line begins
    `RESULT: confirmed`, `RESULT: ruled out`, or
    `RESULT: inconclusive`. Supervision greps those lines; when the
    wording drifts, the only way to know what a hunt is doing is to
    read the whole log, which costs more than the hunt.
  * RE-READ HEAD BEFORE YOU REPORT and say whether it moved under
    you. Naming the commit makes a claim REPRODUCIBLE; it does not
    make it CURRENT, and a fixed defect reads exactly like a live one.
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
    worker path while investigating.

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
stops the next agent spending its budget the same way.

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
believe.

AND THE RECORD. docs/process/HUNT-RECORD.md holds every direction
this project has hunted in and what each one yielded, because the
yield turns almost entirely on the direction and that is not obvious
in advance. End your report with the row it should gain: your
direction, the question you asked, how many hypotheses you logged,
how many findings you are claiming, and any lesson about HOW to hunt
that your run taught. The maintainer writes it in after judging your
claims -- confirmed means reproduced independently, so it is not
yours to count. Update instructions are at the foot of that file.
Read it before you start, too: a direction already tried and empty is
worth knowing about before you spend a night on it.

A last word on what is being asked. You are NOT being scored on
whether you find something. You are being scored on whether what you
report survives being checked -- and everything you report will be
checked, by somebody who will run it themselves. A clean "nothing
here, and here is what I ruled out" is a good day's work. A finding
that evaporates under checking is worse than silence, because it costs
the time of the person checking it.

