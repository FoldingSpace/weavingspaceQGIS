# Archive: CLAUDE.md

The full accounts cut out of `CLAUDE.md` by the archiving pass
(docs/DOC-ARCHIVING.md). Nothing here is a rule you must read
before working: `CLAUDE.md` carries every rule and the headline
of every lesson. This file carries the episode each one came
out of -- what was measured, what was tried first, what the
superseded form of a rule was.

READ IT WHEN `CLAUDE.md` points you here by id (C-1,
C-2, ...), when a rule surprises you and you want to
know what it cost, or when you are about to change a rule and
need to know what it was built to prevent. Ids are stable:
quote them, do not renumber them.

## Index

- **C-1** — The unversioned zip the push gate itself wrote into dist/  <sub>Hard rules: the accounts behind them</sub>
- **C-2** — What a round of hunts costs, and the three invariants a sweep uses instead  <sub>Required practices: the accounts behind them</sub>
- **C-3** — Why publish_candidate refuses, and what ten hand-published candidates risked  <sub>Required practices: the accounts behind them</sub>
- **C-4** — What the platform probe cost before it existed: Windows, 75 minutes in  <sub>Required practices: the accounts behind them</sub>
- **C-5** — The three faults the macOS leg found on its first complete run  <sub>Required practices: the accounts behind them</sub>
- **C-6** — Two widenings of the CI-parity check, and the sixteen days its promise was false  <sub>Required practices: the accounts behind them</sub>
- **C-7** — The three stages that left the release path in a day, and the two that stayed  <sub>Required practices: the accounts behind them</sub>
- **C-8** — The third renderer: the changelog entry that ran on through the previous version  <sub>Required practices: the accounts behind them</sub>
- **C-9** — The four faults heartbeats found on 2026-08-10  <sub>Required practices: the accounts behind them</sub>
- **C-10** — Why the new-code mutation guard stopped gating a candidate  <sub>Required practices: the accounts behind them</sub>
- **C-11** — The historical form of the new-code guard, when it still gated a release  <sub>Required practices: the accounts behind them</sub>
- **C-12** — The window-height question nobody had asked  <sub>How we decide things: the accounts behind them</sub>
- **C-13** — Label anchors: centroid for the visual centre; representative_point only as the...  <sub>Lessons learned here, in full</sub>
- **C-14** — A test that PASSES is not a test that WORKS  <sub>Lessons learned here, in full</sub>
- **C-15** — A PAIRED ARTEFACT INHERITS THE IDENTITY OF WHAT IT IS PAIRED WITH, so every reader...  <sub>Lessons learned here, in full</sub>
- **C-16** — A NAME THE USER CAN EDIT IS NOT AN IDENTITY, AND MUST NEVER BE A KEY  <sub>Lessons learned here, in full</sub>
- **C-17** — TARGETED RUNS CANNOT FIND WHAT THEY DO NOT NAME, and three candidate builds aborted...  <sub>Lessons learned here, in full</sub>
- **C-18** — Check upstream's actual semantics before reimplementing behaviour: "unclassed"...  <sub>Lessons learned here, in full</sub>
- **C-19** — When batch-editing via heredoc Python scripts: assert every anchor BEFORE any write,...  <sub>Lessons learned here, in full</sub>
- **C-20** — When waiting on a long background run, key the wait on the PROCESS ENDING, not on...  <sub>Lessons learned here, in full</sub>
- **C-21** — SEED a watcher with what is already true before it reports anything  <sub>Lessons learned here, in full</sub>
- **C-22** — Two watchers must never share a log file  <sub>Lessons learned here, in full</sub>
- **C-23** — A WHOLESALE SPAN REWRITE TAKES ITS NEIGHBOURS  <sub>Lessons learned here, in full</sub>
- **C-24** — AND THE OPPOSITE EDIT IS QUIETER: A SECOND DEFINITION REPLACES THE FIRST AND NOTHING...  <sub>Lessons learned here, in full</sub>
- **C-25** — A SIGNAL CONNECTED TO THE PROJECT OUTLIVES THE WINDOW THAT MADE IT, AND SO DOES A COMBO  <sub>Lessons learned here, in full</sub>
- **C-26** — A GATE WHOSE EXIT NOBODY BRANCHES ON IS NOT A GATE EITHER, and the second visit pushed  <sub>Lessons learned here, in full</sub>
- **C-27** — A GATE PIPED INTO ANYTHING IS NOT A GATE  <sub>Lessons learned here, in full</sub>
- **C-28** — A WATCHER IS A PROGRAM, AND A PROGRAM CAN DIE  <sub>Lessons learned here, in full</sub>
- **C-29** — A FALLBACK THAT APPENDS INSTEAD OF REPLACING, AND THE FIFTEENTH WATCHER FAULT  <sub>Lessons learned here, in full</sub>
- **C-30** — AND THE MIRROR IMAGE: A LAUNCHER THAT FAILS MAY HAVE STARTED THE JOB FIRST  <sub>Lessons learned here, in full</sub>
- **C-31** — READ THE LINE THAT ASSIGNS A TOOL'S VERDICT BEFORE TRUSTING THE WORD  <sub>Lessons learned here, in full</sub>
- **C-32** — AND A SUMMARY THAT NAMES WHAT IT SUMMARISES IS CAUGHT BY ANY FILTER LOOKING FOR IT  <sub>Lessons learned here, in full</sub>
- **C-33** — `gh run list --commit` MATCHES THE FULL FORTY-CHARACTER SHA, AND A SHORT ONE RETURNS...  <sub>Lessons learned here, in full</sub>
- **C-34** — A `PASS` LINE IS LOST TO A PIPE, SO SILENCE PLUS EXIT 0 IS NOT A PASS  <sub>Lessons learned here, in full</sub>
- **C-35** — AND THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE  <sub>Lessons learned here, in full</sub>
- **C-36** — `exists` THEN `remove` IS A RACE, AND EVERYTHING HERE SHARDS  <sub>Lessons learned here, in full</sub>
- **C-37** — A WATCHER THAT SUBSTITUTES "NOTHING" FOR A FAILED CALL REPORTS ITSELF TWICE  <sub>Lessons learned here, in full</sub>
- **C-38** — COLOUR BELONGS TO QGIS  <sub>Design decisions already settled, in full</sub>
- **C-39** — AT MOST THREE SIGNIFICANT FIGURES IN ANY NUMBER BOX  <sub>Design decisions already settled, in full</sub>
- **C-40** — The Categorical colour editor (`category_editor.py`, the "Edit colours" column) lets...  <sub>Design decisions already settled, in full</sub>
- **C-41** — A CATEGORICAL SCHEME COPIES LIKE A GRADUATED ONE, AND IT OVERWRITES  <sub>Design decisions already settled, in full</sub>
- **C-42** — A NEW REGION DATASET: THE RULE IS THE COLUMN NAME  <sub>Design decisions already settled, in full</sub>
- **C-43** — THE GROUP CHOOSER IS THE ONLY DOOR TO A NEW GROUP  <sub>Design decisions already settled, in full</sub>
- **C-44** — THREE TABS ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A BOX THAT STARTS...  <sub>Design decisions already settled, in full</sub>
- **C-45** — A SAVE PRESSED WHILE A RE-TILE IS COMING IS KEPT, NOT REFUSED  <sub>Design decisions already settled, in full</sub>
- **C-46** — AND THE SECOND ONE FOUND A COLLISION BETWEEN TWO SETTLED RULES  <sub>Design decisions already settled, in full</sub>
- **C-47** — A FULL SUITE FINDS WHAT A TARGETED RUN CANNOT REACH, AND THE FIRST ONE HERE FOUND A...  <sub>Design decisions already settled, in full</sub>
- **C-48** — WHEN YOU CHANGE A NAME OR A FORMAT, FIND EVERY READER -- BY SYMBOL AS WELL AS BY LITERAL  <sub>Design decisions already settled, in full</sub>
- **C-49** — A STAMP TAKEN AWAY FROM A LANDING MAY CARRY ONLY WHAT A LANDING DECIDED  <sub>Design decisions already settled, in full</sub>
- **C-50** — A STRING THAT CARRIES A PATH INSIDE IT IS A PATH  <sub>Design decisions already settled, in full</sub>
- **C-51** — ATTRIBUTION BEATS DELTA, AND THREE NARROW GUARDS ARE THE SIGNAL TO STOP PATCHING ROUTES  <sub>Design decisions already settled, in full</sub>
- **C-52** — A GUARD ADDED TO ONE DOOR BELONGS AT EVERY DOOR INTO THE SAME ROOM  <sub>Design decisions already settled, in full</sub>
- **C-53** — A HARM NAMED BY READING IS A HYPOTHESIS, EXACTLY LIKE A SITE  <sub>Design decisions already settled, in full</sub>
- **C-54** — A GATE CAN BE SATISFIED BY A SENTENCE DENYING IT  <sub>Design decisions already settled, in full</sub>
- **C-55** — PRESENCE IS NOT ORDER, AND A CALL PUT BACK IN THE WRONG PLACE IS WORSE THAN ONE...  <sub>Design decisions already settled, in full</sub>
- **C-56** — BEFORE CLEARING ON AN ABSENCE, ASK WHAT MAKES THE RECORD ABSENT  <sub>Design decisions already settled, in full</sub>
- **C-57** — WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE THAT ALREADY HELD...  <sub>Design decisions already settled, in full</sub>
- **C-58** — A RECORD ASSEMBLED FROM TWO MOMENTS MUST SAY WHICH MOMENT EACH FIELD CAME FROM  <sub>Design decisions already settled, in full</sub>
- **C-59** — THE SIZE GUARD ASKS; ONLY WHAT IS NOT A SIZE IS REFUSED  <sub>Design decisions already settled, in full</sub>
- **C-60** — A BLANK THE PLUGIN IMPOSED IS NOT A CHOICE THE USER MADE  <sub>Design decisions already settled, in full</sub>
- **C-61** — A constant numeric column gets ONE class, and a notice  <sub>Design decisions already settled, in full</sub>
- **C-62** — ONE COLOUR MEANS ONE THING, wherever it appears — and the rule is about MEANING, not...  <sub>Design decisions already settled, in full</sub>
- **C-63** — CLASS BOUNDS A PERSON SET, and the record that holds them  <sub>Design decisions already settled, in full</sub>
- **C-64** — What ELEVEN defects taught about that feature pair, 2026-08-15  <sub>Design decisions already settled, in full</sub>
- **C-65** — A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE  <sub>Design decisions already settled, in full</sub>
- **C-66** — WHEN A FIX IS WRITTEN INTO TWO PATHS IN ONE COMMIT, DIFF THE TWO HUNKS AGAINST EACH...  <sub>Design decisions already settled, in full</sub>
- **C-67** — A GUARD THAT ASKS ABOUT ONE THING MUST NOT STAND IN FRONT OF AN EXIT THAT IS ABOUT...  <sub>Design decisions already settled, in full</sub>
- **C-68** — A REPRODUCTION CAN STOP REPRODUCING BECAUSE A NEIGHBOURING RULE CHANGED, AND THE...  <sub>Design decisions already settled, in full</sub>
- **C-69** — CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO, AND WRONG WHEN THE PLUGIN MERELY...  <sub>Design decisions already settled, in full</sub>
- **C-70** — A GATE THAT CHECKS HALF OF WHAT IT NAMES IS WORSE THAN NO GATE, because the other...  <sub>Design decisions already settled, in full</sub>
- **C-71** — WHEN A FIX WIDENS A CALL SO IT STOPS IGNORING X AND Y, ENUMERATE EVERY KEY OF THE...  <sub>Design decisions already settled, in full</sub>
- **C-72** — THE PLUGIN'S TABLE FOLLOWS THE LAYER'S RENDERER, AND THE SCOPE OF THAT IS THE WHOLE...  <sub>Design decisions already settled, in full</sub>
- **C-73** — WHEN A FIX THREADS A "WHO FIRED THIS" ARGUMENT THROUGH A FAMILY OF HANDLERS, GREP...  <sub>Design decisions already settled, in full</sub>
- **C-74** — AN UNCLASSED END IS NAMED BY TWO CONTROLS, AND THEY MUST AGREE  <sub>Design decisions already settled, in full</sub>
- **C-75** — ONE HATCHING NOW, AND THE OTHER WAS WITHDRAWN  <sub>Design decisions already settled, in full</sub>
- **C-76** — A tiles inset that swallows elements is refused in terms of the inset  <sub>Design decisions already settled, in full</sub>
- **C-77** — The plugin follows the layer, and adapts where the answer is unambiguous  <sub>Design decisions already settled, in full</sub>
- **C-78** — NULLs are kept out of class breaks, and that is a WORKAROUND with an expiry test  <sub>Design decisions already settled, in full</sub>
- **C-79** — The dependency consent dialogue states what can be checked  <sub>Design decisions already settled, in full</sub>
- **C-80** — A GUARD YOU HAVE NOT WATCHED FIRE IS A GUARD YOU HAVE NOT GOT, AND AN EDIT CAN...  <sub>Design decisions already settled, in full</sub>
- **C-81** — A STAGE, A ROW OR A KEY THAT NAMES A FUNCTION WHICH DOES NOT EXIST REPORTS NOTHING,...  <sub>Design decisions already settled, in full</sub>
- **C-82** — ONE POLYGON DOING TWO JOBS CHANGES BOTH WHEN YOU SHRINK IT  <sub>Design decisions already settled, in full</sub>
- **C-83** — A TEST FOR A PROMISE IS A MATRIX, NOT A CASE, and this is the DEFAULT rather than a...  <sub>The test suite's lessons, in full</sub>
- **C-84** — A GUARD MUST NOT REPAIR WHAT IT MEASURES, NOR RUN WHERE THERE IS NOTHING TO SEE  <sub>The test suite's lessons, in full</sub>
- **C-85** — WHEN A REPRODUCTION WILL NOT REPRODUCE, MEASURE THE SESSION THAT IS BROKEN  <sub>The test suite's lessons, in full</sub>
- **C-86** — A MATRIX CATCHES ONLY WHAT ITS CELLS MAY COMPLAIN ABOUT  <sub>The test suite's lessons, in full</sub>
- **C-87** — WHEN A CHANGE BREAKS A TEST, BISECT BY DISABLING RATHER THAN BY REASONING, after ONE...  <sub>The test suite's lessons, in full</sub>
- **C-88** — TWO OF THIS PROJECT'S INSTRUMENTS LIE, and both cost hours on 2026-08-18  <sub>The test suite's lessons, in full</sub>
- **C-89** — A WATCHER MAY ONLY ADOPT WHAT A PERSON LEFT BEHIND  <sub>The test suite's lessons, in full</sub>
- **C-90** — CLASS BOUNDS: THE RECORD HOLDS FOUR ENDS, AND TWO OF THEM ARE WEAKER THAN THE OTHER TWO  <sub>The test suite's lessons, in full</sub>
- **C-91** — A LIMIT MAY EXCLUDE, AND WHAT IT EXCLUDES IS DRAWN  <sub>The test suite's lessons, in full</sub>
- **C-92** — NO PIN COLUMN: A HEAVY OUTLINE ON THE BOX SAYS THE NUMBER IS YOURS  <sub>The test suite's lessons, in full</sub>
- **C-93** — A GUARD MEASURES THE GROUND, NOT THE BOX ROUND IT  <sub>The test suite's lessons, in full</sub>
- **C-94** — A CACHE OF ONE IS NO CACHE WHEN THERE ARE TWENTY-THREE OF ANYTHING  <sub>The test suite's lessons, in full</sub>
- **C-95** — A COPY REPRODUCES THE WHOLE CLASSIFICATION, AND THE RECORD GREW UNDER IT  <sub>The test suite's lessons, in full</sub>
- **C-96** — A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES, so NEVER hard-wrap one  <sub>The test suite's lessons, in full</sub>
- **C-97** — A CHECK THAT CAN ONLY CONFIRM IS NOT A CHECK  <sub>The test suite's lessons, in full</sub>
- **C-98** — A GLOB IS HOW A LOG'S DATE GETS SKIPPED  <sub>The test suite's lessons, in full</sub>
- **C-99** — WHEN TWO THINGS SHOULD DRAW THE SAME MAP, COMPARE WHAT THEY DREW, NOT WHAT THEY LOOK...  <sub>The test suite's lessons, in full</sub>
- **C-100** — A NAME THAT CARRIES A NUMBER IS SORTED AS TEXT, AND rc10 COMES BEFORE rc2  <sub>The test suite's lessons, in full</sub>
- **C-101** — A DEPENDENCY'S CHEAP ANSWER IS A CACHED ANSWER, AND A GUARD BUILT ON ONE IS HONEST...  <sub>The test suite's lessons, in full</sub>
- **C-102** — AND ITS TEST HAD BEEN EXERCISING THE HONEST PATH ALL ALONG  <sub>The test suite's lessons, in full</sub>
- **C-103** — A FIX APPLIED TO A TWIN THAT DOES NOT HAVE THE FAULT IS DEAD CODE THAT READS AS...  <sub>The test suite's lessons, in full</sub>
- **C-104** — A GUARD THAT LANDS WITHOUT A TEST OF ITS OWN LOOKS GUARDED, BECAUSE THE NEIGHBOUR IT...  <sub>The test suite's lessons, in full</sub>
- **C-105** — `styleChanged` FIRES ONLY ON `setRenderer`; AN EDIT MADE ON THE LIVE RENDERER IS...  <sub>The test suite's lessons, in full</sub>
- **C-106** — `ranges()` AND `categories()` HAND BACK COPIES, so editing one is a NO-OP on the...  <sub>The test suite's lessons, in full</sub>
- **C-107** — ABSENT IS NOT MOVED: when a NEW guard reads an OLD record, ask which paths leave...  <sub>The test suite's lessons, in full</sub>
- **C-108** — A GUARD COMPUTED AS A DELTA IS ARMED FOR ONE INVOCATION  <sub>The test suite's lessons, in full</sub>
- **C-109** — A LADDER MAY HOLD SEVERAL CLASSES WITH IDENTICAL BOUNDS, so a lookup by bounds must...  <sub>The test suite's lessons, in full</sub>
- **C-110** — WHEN CI TIMINGS MOVE, COMPARE THE SUSPECT ON A MACHINE YOU CONTROL BEFORE BELIEVING...  <sub>The test suite's lessons, in full</sub>
- **C-111** — WHEN A GUARD STARTS ANSWERING DIFFERENTLY, FOLLOW ITS RETURN VALUE INTO EVERY TUPLE...  <sub>The test suite's lessons, in full</sub>
- **C-112** — A REPAIR AIMED AT AN ACT MUST BE RE-AIMED AT THE ACT'S ABSENCE  <sub>The test suite's lessons, in full</sub>
- **C-113** — A GUARD WHOSE CONDITION IS RIGHT CAN STILL BE AIMED AT NOTHING  <sub>The test suite's lessons, in full</sub>
- **C-114** — AN INSTRUMENT THAT HOLDS A FILE CHANGES WHAT IT MEASURES, AND BYTES REMEMBER PAGES...  <sub>The test suite's lessons, in full</sub>
- **C-115** — RETIREMENT IS A FACT ABOUT THE OBJECT, NOT AN ABSENCE IN A REGISTRY  <sub>The test suite's lessons, in full</sub>
- **C-116** — A WIDGET THAT RETAINS LAYER OBJECTS MUST BE REBUILT WHEN LAYERS ARE REMOVED, AND A...  <sub>The test suite's lessons, in full</sub>
- **C-117** — A LAYER BUILT ON ANOTHER LAYER'S SOURCE IS THAT LAYER TO ANYTHING THAT LOOKS UP BY...  <sub>The test suite's lessons, in full</sub>
- **C-118** — ENUMERATE THE PRODUCERS OF A SECOND CLAIMANT, NOT JUST THE ONE YOU BUILT  <sub>The test suite's lessons, in full</sub>
- **C-119** — A DANGLING REFERENCE IS NOT A DISAGREEMENT, WHICH IS WHY NOTHING COMPLAINS  <sub>The test suite's lessons, in full</sub>
- **C-120** — BREAK EVERY ROUTE AT ONCE, OR THE CATALOGUE MEASURES THE OTHER ONE  <sub>The test suite's lessons, in full</sub>
- **C-121** — AN INERT MUTATION AND A REDUNDANTLY HELD ONE BOTH REPORT SURVIVED, AND THEY NEED...  <sub>The test suite's lessons, in full</sub>
- **C-122** — RANKING CANDIDATES CANNOT CHANGE A VERDICT; UNDER A CAP IT DECIDES WHAT WAS ASKED  <sub>The test suite's lessons, in full</sub>
- **C-123** — `mutation_check` APPLIES EXACTLY ONE REPLACEMENT, BY DESIGN, so a fact held at two...  <sub>The test suite's lessons, in full</sub>
- **C-124** — A REPAIR'S OWN REPAIR NEEDS THE SAME SUSPICION, AND THE FIRST ONE CAN BE WORSE THAN...  <sub>The test suite's lessons, in full</sub>
- **C-125** — A GUARD WHOSE PRECONDITION IS A LOSSY DIGEST IS ONLY AS GOOD AS WHAT THE DIGEST OMITS  <sub>The test suite's lessons, in full</sub>
- **C-126** — OWNERSHIP IS NOT A NAME PREFIX, AND AN ELEMENT ID IS A LETTER EVERY MAP SHARES  <sub>The test suite's lessons, in full</sub>
- **C-127** — A GATE THAT READS RAW SOURCE TEXT CAN BE MOVED BY A COMMENT  <sub>The test suite's lessons, in full</sub>
- **C-128** — A CONSENT DIALOGUE THAT ENUMERATES MUST BE DIFFED AGAINST WHAT THE CODE ASKS FOR  <sub>The test suite's lessons, in full</sub>
- **C-129** — A SITE NAMED BY READING IS A HYPOTHESIS, AND IT READS EXACTLY LIKE ONE SOMEBODY PROVED  <sub>The test suite's lessons, in full</sub>
- **C-130** — A GUARD THAT REBUILDS A LAYER FROM ITS SOURCE STRING LOSES EVERYTHING THE USER SET...  <sub>The test suite's lessons, in full</sub>
- **C-131** — A COUNT QUOTED TO A PERSON MUST BE ASKED OF THE GEOMETRY, NOT OF TWO TOTALS  <sub>The test suite's lessons, in full</sub>
- **C-132** — A PER-FILE FACT MUST NOT LIVE ON A SESSION-WIDE CONTROL  <sub>The test suite's lessons, in full</sub>
- **C-133** — A DISPLAY RULE IS ONLY DISPLAY-ONLY IF NOTHING RE-READS THE DISPLAY  <sub>The test suite's lessons, in full</sub>
- **C-134** — A SUITE CAN HOLD A CONTROL AT A VALUE NO USER HOLDS  <sub>The test suite's lessons, in full</sub>
- **C-135** — A RECORD SEEDED BY ADOPTION IS A RECORD THAT ASSUMES A PROJECT  <sub>The test suite's lessons, in full</sub>
- **C-136** — AN INTERMITTENT FAILURE UNDER LOAD CAN BE THE SUITE INTERMITTENTLY REACHING A REAL...  <sub>The test suite's lessons, in full</sub>
- **C-137** — A REPORT ABOUT A VERSION OR A BEHAVIOUR IS FIRST A QUESTION ABOUT WHICH BUILD IS...  <sub>The test suite's lessons, in full</sub>
- **C-138** — A CLAIM'S MECHANISM IS USUALLY RIGHT AND ITS HARM USUALLY IS NOT, AND THE DOOR IT...  <sub>The test suite's lessons, in full</sub>
- **C-139** — A CALLABLE THAT OUTLIVES ITS DIALOG MUST ASK BEFORE IT TOUCHES IT, AND A LAMBDA IS...  <sub>The test suite's lessons, in full</sub>
- **C-140** — A WIDTH IN PIXELS IS A CLAIM ABOUT A FONT, AND SETTING A FONT IS NOT SWITCHING A...  <sub>The test suite's lessons, in full</sub>
- **C-141** — A RESTORE IS A LANDING, FOR EVERYTHING THAT ASKS WHETHER THE CONTROLS DESCRIBE THE MAP  <sub>The test suite's lessons, in full</sub>
- **C-142** — A RECOVERY MUST REPORT WHICH OF ITS ROUTES ANSWERED, AND WHAT IS STAMPED IS WHAT IT...  <sub>The test suite's lessons, in full</sub>
- **C-143** — "ALREADY THERE" IS A QUESTION FOR THE FILE, NOT FOR A STRING THAT NAMES IT  <sub>The test suite's lessons, in full</sub>
- **C-144** — A SAVE THAT PUMPS THE EVENT LOOP MUST TAKE ITS BUTTONS DOWN, AND THE TWO ARE ONE...  <sub>The test suite's lessons, in full</sub>
- **C-145** — `isVisible` IS FALSE IN A WINDOW NOBODY HAS SHOWN, SO IT CANNOT ASK WHETHER...  <sub>The test suite's lessons, in full</sub>
- **C-146** — A TEST LEG THAT RUNS AFTER THE STATE IT IS ABOUT MEASURES NOTHING  <sub>The test suite's lessons, in full</sub>
- **C-147** — A BACKSLASH-NEWLINE INSIDE A NON-RAW ANCHOR IS A LINE CONTINUATION  <sub>The test suite's lessons, in full</sub>
- **C-148** — THE EIGHTEENTH WATCHER FAULT: A WORK LINE THAT CANNOT SHOW A DEAD WORKER  <sub>The test suite's lessons, in full</sub>
- **C-149** — AND THE FIFTEENTH, COPIED FORWARD WITHOUT ITS REASON  <sub>The test suite's lessons, in full</sub>
- **C-150** — WHEN THREE REPAIRS TO A MECHANISM FAIL, SUSPECT THE PROMISE  <sub>The test suite's lessons, in full</sub>
- **C-151** — PROVE THE QUANTITY THE FAILURE MEASURES, NOT ONE THAT SOUNDS EQUIVALENT  <sub>The test suite's lessons, in full</sub>
- **C-152** — A GUARD ON A PyQGIS CALL THAT RETURNS A TUPLE CAN NEVER FIRE  <sub>The test suite's lessons, in full</sub>
- **C-153** — A TEST THAT SUPPLIES ITS OWN INPUT MEASURES THE FUNCTION, NOT THE PRODUCT, AND CAN...  <sub>The test suite's lessons, in full</sub>
- **C-154** — AND A FIX THAT WIDENS A SCOPE RE-AIMS EVERY TRIAL THAT COMPARED AGAINST THE OLD ONE  <sub>The test suite's lessons, in full</sub>
- **C-155** — THE DROP HAS BEEN WRONG FOUR TIMES: THE MISSING FACT IS WHAT THE ARTEFACT DESCRIBES,...  <sub>The test suite's lessons, in full</sub>
- **C-156** — A QTabWidget LAYS OUT ONLY ITS CURRENT PAGE, so measuring the others measures the...  <sub>The test suite's lessons, in full</sub>
- **C-157** — A `processEvents()` LOOP LETS NO WALL TIME PASS, so a QgsTask never finishes  <sub>The test suite's lessons, in full</sub>
- **C-158** — A TEST'S POSITIVE CONTROL CAN BE THE DEFECT YOU ARE ABOUT TO FIX  <sub>The test suite's lessons, in full</sub>
- **C-159** — A LAYOUT PASS THAT WIDENS WHAT IT MEASURES IS A FEEDBACK LOOP; A MARGIN IS NOT  <sub>The test suite's lessons, in full</sub>
- **C-160** — A STACKED WIDGET'S MINIMUM IS THE LARGEST OF ITS PAGES, AND THAT IS WHY ONE TAB CAN...  <sub>The test suite's lessons, in full</sub>
- **C-161** — WHEN A CONTROL'S PARAMETER COMES FROM A GESTURE, THE HANDLE SHOULD BE A POSITION AND...  <sub>The test suite's lessons, in full</sub>
- **C-162** — A COMPARATOR THAT IS SENSITIVE TO REPRESENTATION CANNOT ANSWER A QUESTION ABOUT...  <sub>The test suite's lessons, in full</sub>
- **C-163** — AND AN EXACT QUESTION MUST NOT BE ASKED WITH A TOLERANCE  <sub>The test suite's lessons, in full</sub>
- **C-164** — A GUARD THAT COMPARES THREE OF TWENTY-SIX FIELDS IS A SECOND DEFINITION OF THE THING...  <sub>The test suite's lessons, in full</sub>
- **C-165** — A SINGLE-SHOT TIMER THAT IS "DROPPED" IS LOST, NOT LATE -- AND THE COMMENT SAYING...  <sub>The test suite's lessons, in full</sub>
- **C-166** — A `ResizeToContents` COLUMN RE-MEASURES ON EVERY `setItem`  <sub>The test suite's lessons, in full</sub>
- **C-167** — AN ENTRY MUST BREAK THE ROUTE THE GUARD WALKS, NOT A ROUTE  <sub>The test suite's lessons, in full</sub>
- **C-168** — `mutation_check` MUST RUN ITS CHILD OFFSCREEN, AND THE DOCUMENTED INVOCATION DID NOT  <sub>The test suite's lessons, in full</sub>
- **C-169** — WHEN YOU ADD A STEP TO A SEQUENCE, ASK WHAT IT RESETS  <sub>The test suite's lessons, in full</sub>
- **C-170** — A DEDUPE WRITTEN FOR AN UNREACHABLE HARM IS DELETED, NOT KEPT  <sub>The test suite's lessons, in full</sub>
- **C-171** — RE-WRAPPING A PARAGRAPH DISARMED A PROSE GATE  <sub>The test suite's lessons, in full</sub>
- **C-172** — A DOWNLOADED ARTEFACT HAS A FRESH MTIME AND AN OLD RESULT  <sub>The test suite's lessons, in full</sub>
- **C-173** — A TRIPLE-BACKTICK FENCE SHIFTS EVERY INLINE SPAN BELOW IT, AND A PROSE GOES BLIND...  <sub>The test suite's lessons, in full</sub>
- **C-174** — WHEN ONE FUNCTION IS MADE THE OWNER OF "WHAT IS X", CHECK EVERY OTHER KEY FOR TERMS...  <sub>The test suite's lessons, in full</sub>
- **C-175** — AN ARMED TIMER IS NOT A RUN THAT WILL START  <sub>The test suite's lessons, in full</sub>
- **C-176** — A GATE THAT OPENS A DOOR MUST ASK FOR WHAT IS BEHIND IT  <sub>The test suite's lessons, in full</sub>
- **C-177** — A HAND-KEPT LIST DRIFTS EVEN WHERE A COMMENT SAYS TO KEEP IT IN STEP  <sub>The test suite's lessons, in full</sub>
- **C-178** — A WANTED WRITE THAT FAILS STILL CLEARS, SO ENABLING THE WRITE IS HALF A REPAIR  <sub>The test suite's lessons, in full</sub>
- **C-179** — A TEST THAT MATCHES A PHRASE COPIED OUT OF THE PRODUCT IS BROKEN BY THE MAINTAINER'S...  <sub>The test suite's lessons, in full</sub>
- **C-180** — UPSTREAM MOVED TWELVE COMMITS WITHOUT BUMPING ITS VERSION, AND FIXED ONE OF OUR FINDINGS  <sub>The test suite's lessons, in full</sub>
- **C-181** — A CONTROL'S SHAPE SHOULD SAY WHAT IT DOES, AND A HOVER STATE IS NOT A SUBSTITUTE  <sub>The test suite's lessons, in full</sub>
- **C-182** — PROFILE THE THING A PERSON WAITS FOR, BECAUSE THE COST IS OFTEN NOT WHERE THE SUBJECT IS  <sub>The test suite's lessons, in full</sub>
- **C-183** — THE VENDOR-CLAIM GATE READS "commit <sha>" ANYWHERE IN THREE FILES, SO WRITING ABOUT...  <sub>The test suite's lessons, in full</sub>
- **C-184** — A RE-VENDOR'S REAL QUESTION IS ONE NO GATE HERE ASKS  <sub>The test suite's lessons, in full</sub>
- **C-185** — THE TWENTIETH AND TWENTY-FIRST WATCHER FAULTS ARE ONE RULE: KEY ON THE THING, NOT A...  <sub>The test suite's lessons, in full</sub>
- **C-186** — THREE MORE FROM THE SAME MORNING, ALL CAUGHT BY HAND-RUNNING THE WATCHER ONCE BEFORE...  <sub>The test suite's lessons, in full</sub>
- **C-187** — A DOCUMENTATION MERGE IS NOT A NO-OP FOR THE SUITE  <sub>The test suite's lessons, in full</sub>
- **C-188** — THE ENTRY DESCRIBING THE FENCE FAULT IS WHAT BLINDED THE GATE NEXT  <sub>The test suite's lessons, in full</sub>
- **C-189** — `lines[-1]` ON A FILE ENDING IN A NEWLINE REPLACES THE EMPTY STRING, SO THE EDIT...  <sub>The test suite's lessons, in full</sub>
- **C-190** — A WATCHER'S HEADLINE MUST CARRY WHAT IS LIVE, NOT WHAT MATTERS IN GENERAL  <sub>The test suite's lessons, in full</sub>
- **C-191** — A WIDGET INSIDE A LAYOUT DOES NOT KEEP A SIZE YOU HAND IT, SO THE WINDOW IS THE LEVER  <sub>The test suite's lessons, in full</sub>
- **C-192** — A FLOOR ON ONE PANE IS TAKEN OUT OF THE PANE BESIDE IT  <sub>The test suite's lessons, in full</sub>
- **C-193** — TWO SUFFICIENT FIXES TO ONE OUTCOME MAKE EVERY SINGLE-SITE ENTRY SURVIVE, AND THAT...  <sub>The test suite's lessons, in full</sub>
- **C-194** — A SETTLE RETURNS BEFORE THE RESULT IS ADOPTED, SO A PREMISE ASKED IN THE SAME BREATH...  <sub>The test suite's lessons, in full</sub>
- **C-195** — A FIX APPLIED WHERE THE FAULT CANNOT BE REACHED IS DEAD CODE THAT READS AS...  <sub>The test suite's lessons, in full</sub>
- **C-196** — AN OWNERSHIP QUESTION THAT OUR OWN ACT MAKES TRUE IS NOT AN OWNERSHIP QUESTION  <sub>The test suite's lessons, in full</sub>
- **C-197** — AND THE FIRST REPAIR FOR IT SPARED EVERYTHING, BECAUSE THE RECORD DOES NOT SPELL IT...  <sub>The test suite's lessons, in full</sub>
- **C-198** — A WIDGET THAT RE-DERIVES ITS VIEW TRANSFORM FROM WHAT IT DRAWS HAS MADE THE...  <sub>The test suite's lessons, in full</sub>
- **C-199** — THE DESIGN A CLAIM IS DRIVEN ON CAN REFUTE A REAL DEFECT  <sub>The test suite's lessons, in full</sub>
- **C-200** — AND I COMMITTED PAST A RED GATE, HAVING READ IT  <sub>The test suite's lessons, in full</sub>
- **C-201** — A LANDING THAT ARRIVES MID-GESTURE MUST WAIT FOR THE POINTER TO COME UP  <sub>The test suite's lessons, in full</sub>
- **C-202** — A FIGURE WITH NO INSTRUMENT BESIDE IT IS FOLKLORE, AND A READER WILL SAY SO  <sub>The test suite's lessons, in full</sub>
- **C-203** — THE TWENTY-SECOND WATCHER FAULT WAS CAUGHT BEFORE ARMING, WHICH IS THE FIRST TIME  <sub>The test suite's lessons, in full</sub>
- **C-204** — AND ALL FOUR WERE BUILT THE SAME DAY, with what each turned out to cost  <sub>The test suite's lessons, in full</sub>
- **C-205** — OPENING A GEOPACKAGE COSTS TIME PROPORTIONAL TO ITS LAYERS, AND A HELD HANDLE DOES...  <sub>The test suite's lessons, in full</sub>
- **C-206** — A COMPARISON ACROSS TWO RUNS ON A BUSY MACHINE IS NOT A MEASUREMENT  <sub>The test suite's lessons, in full</sub>
- **C-207** — OGR HANDS BACK A DATETIME IN ITS OWN FORMAT, SO A VALUE COPIED OUT OF A ROW IS A...  <sub>The test suite's lessons, in full</sub>
- **C-208** — ONE STORE, ONE MEANING -- AND A QLabel IS A STORE  <sub>The test suite's lessons, in full</sub>
- **C-209** — A HARNESS THAT MATCHES A SENTENCE THE PRODUCT SAYS IS RETUNED BY THE NEXT SENTENCE  <sub>The test suite's lessons, in full</sub>
- **C-210** — A GUARD OVER THE WHOLE TREE CANNOT TELL YOUR OWN EDIT FROM WHAT IT IS WATCHING FOR  <sub>The test suite's lessons, in full</sub>
- **C-211** — A WATCHER'S OWN SHELL IS PART OF THE WATCHER, AND `/bin/bash` HERE IS 3.2  <sub>The test suite's lessons, in full</sub>
- **C-212** — A FLAG READ BY ONE CONSUMER OUTLIVES THE JOURNEYS THAT CONSUMER NEVER RUNS ON  <sub>The test suite's lessons, in full</sub>
- **C-213** — WHEN A NAME GAINS A LABEL, SWEEP EVERY READER OF THE QUESTION, AND THE SILENT ONES FIRST  <sub>The test suite's lessons, in full</sub>
- **C-214** — AN ENVIRONMENT SCRIPT THAT PRINTS BARE ASSIGNMENTS NEEDS `set -a`, OR THE CHILD...  <sub>The test suite's lessons, in full</sub>
- **C-215** — A CANDIDATE'S OWN SUITE IS READ SHARD BY SHARD, AND THE PARTITION IS THE PROOF  <sub>The test suite's lessons, in full</sub>
- **C-216** — A DOCUMENTATION EDIT CANNOT INVALIDATE A CANDIDATE, AND KNOWING THAT IS WHAT MAKES...  <sub>The test suite's lessons, in full</sub>
- **C-217** — A WORKFLOW'S NAME IS NOT ITS CONTRACT, AND THIS ONE HAS BEEN MISREAD TWICE  <sub>The test suite's lessons, in full</sub>
- **C-218** — AND I EDITED A DOCUMENT THE RUNNING SUITE READS  <sub>The test suite's lessons, in full</sub>
- **C-219** — AN INSTRUMENT THAT DIES AFTER REPORTING LOOKS EXACTLY LIKE THE THING IT MEASURES DYING  <sub>The test suite's lessons, in full</sub>
- **C-220** — A DEPENDENCY THAT ANSWERS BY RETURN VALUE CANNOT BE CAUGHT BY `except`  <sub>The test suite's lessons, in full</sub>
- **C-221** — A WAIT ONLY AN OUTER FRAME CAN END IS NOT A WAIT  <sub>The test suite's lessons, in full</sub>
- **C-222** — AN "EMPTY" FILE IS A QUESTION ABOUT CONTENT, NOT ABOUT BYTES  <sub>The test suite's lessons, in full</sub>
- **C-223** — A TABLE KEYED BY A FAMILY DOES NOT GROW WITH THE FAMILY  <sub>The test suite's lessons, in full</sub>
- **C-224** — A PREDICATE THAT MERGES TWO FACTS IS RIGHT FOR A WAIT AND WRONG FOR A QUESTION  <sub>The test suite's lessons, in full</sub>
- **C-225** — A FRAME MUST NOT REPORT THE OUTCOME OF AN ACT IT CANNOT SEE  <sub>The test suite's lessons, in full</sub>
- **C-226** — A FILTER IS A VIEW, AND `getFeatures()` HONOURS ONE  <sub>The test suite's lessons, in full</sub>
- **C-227** — A RECORD FILLED BY A LANDING AND CLEARED BY NOTHING ANSWERS FOR A MAP IT HAS NEVER SEEN  <sub>The test suite's lessons, in full</sub>
- **C-228** — AND WHEN A RESUME STAMPS ONE STORE, IT STAMPS THE OTHER  <sub>The test suite's lessons, in full</sub>
- **C-229** — AND A DEPENDENCY'S REFUSAL CAN STOP BEING TRUE WHILE THE RULE IT JUSTIFIED STANDS  <sub>The test suite's lessons, in full</sub>
- **C-230** — THE TWENTY-FOURTH WATCHER FAULT: A JOB NAME HAS A SPACE IN IT  <sub>The test suite's lessons, in full</sub>
- **C-231** — A LAUNCH STATE BEATS THE CARRY, SO HANDING A KEY OVER IS NOT THE SAME ACT AS LETTING...  <sub>The test suite's lessons, in full</sub>
- **C-232** — A KEY THAT ENUMERATES TWO OF A DESIGN'S TERMS IS A SECOND DEFINITION OF THE DESIGN  <sub>The test suite's lessons, in full</sub>
- **C-233** — A QUESTION BUILT ON A MERGED PREDICATE MERGES THE SAME TWO STATES  <sub>The test suite's lessons, in full</sub>
- **C-234** — A CONTROL ONE ACT MOVES AS A SIDE EFFECT IS READ BY ANOTHER ACT AS A DECISION  <sub>The test suite's lessons, in full</sub>
- **C-235** — THE TWENTY-FIFTH WATCHER FAULT: ARMED THROUGH A PIPE, AND THE LESSON WAS MINE FROM...  <sub>The test suite's lessons, in full</sub>
- **C-236** — A PROBE'S CONTROL CAN MOVE THE THING BOTH ARMS ARE ABOUT  <sub>The test suite's lessons, in full</sub>
- **C-237** — AN ASSERTION THAT NAMES A MOMENT IS A CLAIM ABOUT WHEN ITS OWN READING WAS TAKEN  <sub>The test suite's lessons, in full</sub>
- **C-238** — A WAIT HELPER THAT DOES NOT WIDEN IS A CEILING SIZED ON THE FASTEST MACHINE THE...  <sub>The test suite's lessons, in full</sub>
- **C-239** — `findData` COMPARES THROUGH QVariant, SO A TUPLE NEVER MATCHES AN EQUAL TUPLE  <sub>The test suite's lessons, in full</sub>
- **C-240** — A LANDING IS HELD FOR A GESTURE, AND THE CLICK BEFORE THE PRESS IS NOT A GESTURE  <sub>The test suite's lessons, in full</sub>
- **C-241** — A PATCH THAT REWRITES ANOTHER PATCH'S OUTPUT TAKES ITS MARKER WITH IT  <sub>The test suite's lessons, in full</sub>
- **C-242** — A RATE QUOTED FROM TOO FEW DRAWS IS NOT A MEASUREMENT, AND I PUBLISHED TWO  <sub>The test suite's lessons, in full</sub>
- **C-243** — A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT  <sub>The test suite's lessons, in full</sub>
- **C-244** — CLEARING A PREVIEW AT THE DROP PUTS THE OLD PICTURE BACK FOR THE WHOLE OF AN...  <sub>The test suite's lessons, in full</sub>


## Hard rules: the accounts behind them
- **C-245** — A change of region dataset: what enforcing the seven rulings cost  <sub>Lessons learned here, in full</sub>

- **C-246** — The three scopes answering one act, and the A-B-A probe behind the group rulings  <sub>Lessons learned here, in full</sub>

- **C-247** — The two alternatives refused when the output group became the unit of work  <sub>Lessons learned here, in full</sub>

- **C-248** — What converting fifty-eight Save presses cost, and the four defects it found  <sub>Lessons learned here, in full</sub>

- **C-249** — The three grounds for _may_overwrite asking about the dataset rather than the group  <sub>Lessons learned here, in full</sub>

- **C-250** — Numbers stored as text: the measurement, the cache, and the fixture blind spot  <sub>Design decisions already settled</sub>

- **C-251** — What the doubled alphabet was measured at before it moved  <sub>Design decisions already settled</sub>

- **C-252** — The chooser and the panel answering one fact two ways, and the six splitters  <sub>Design decisions already settled</sub>

- **C-253** — The two registered tests that collided over a kept scheme  <sub>Design decisions already settled</sub>

- **C-254** — The four regressions round nine shipped, and the leg that found them  <sub>Design decisions already settled</sub>

- **C-255** — Why a modal refusal is the quietest exit, and harness fault eleven  <sub>Design decisions already settled</sub>

- **C-256** — Windows running install-and-load alone, and the instruction that ended it  <sub>Required practices: the accounts behind them</sub>

- **C-257** — The macos job missing from the check's own list, and the sixteen-day false sentence  <sub>Required practices: the accounts behind them</sub>

- **C-258** — The eighteen red pushes across six hours, and why every local gate was green  <sub>Required practices: the accounts behind them</sub>

- **C-259** — How release_notes.entry_for collapsed the categorized changelog shape  <sub>Required practices: the accounts behind them</sub>

- **C-260** — The guard that walks every version header, and the entry it stands on  <sub>Required practices: the accounts behind them</sub>

- **C-261** — The six boundaries icon mode was driven across, and how each was read  <sub>How we decide things: the accounts behind them</sub>

- **C-262** — The 48-design spread behind multi-class selection, and cairo measured against laves  <sub>Design decisions already settled</sub>


### C-1 — The unversioned zip the push gate itself wrote into dist/

<sub>Cut from `CLAUDE.md`, lines 95–118 of the
2026-09-05 revision.</sub>

  unversioned zip.) Two halves, and the first is the one that bites.
  `check_before_push` replays CI's `standards` job, one step of which
  is "The plugin still packages"; that runs `build.py`, which writes
  `dist/weavingspace_qgis.zip` into whatever worktree it is invoked
  from. So the PUSH GATE mutates the artefact directory, from an
  ungated tree, every time anybody runs it. Measured that day: an
  unversioned 649,327-byte zip sitting an HOUR NEWER than the gated
  `weavingspace_qgis-0.24.4rc5.zip` at 649,330 -- not the same bytes
  -- beside three versioned candidates and their receipts. Sorted by
  date, which is what a person does in a file browser, the first thing
  in a directory of gated artefacts was the one with no version, no
  receipt and no gate behind it.
  THE CANDIDATE PATH WAS ALREADY RIGHT, WHICH IS THE TELL: every
  pre-release attaches `weavingspace_qgis-<version>rc<n>.zip`, and
  only the RELEASE path attached an unversioned one. The convention
  existed and had been applied to half the process.
  AND THE README FOLLOWS THE ARTEFACT, not the other way round. The
  unversioned name was defended here on the ground that README tells
  people to download it; the maintainer's answer was that the README
  can and should change. A gated artefact's name is a fact about which
  tree it came from, and prose is the cheaper of the two to move.
  This is the same family as "a candidate number is spent by anything
  bearing it": one name over two trees confuses everybody, and an
  artefact with no name at all is that hazard with the label removed.


## Required practices: the accounts behind them

### C-2 — What a round of hunts costs, and the three invariants a sweep uses instead

<sub>Cut from `CLAUDE.md`, lines 200–217 of the
2026-09-05 revision.</sub>

  them.) Every rc round so far has reached for hunts by default, and
  the record says that is right only when the ground is FRESH: 573,967
  tokens bought one confirmed defect when a round was aimed at old
  code, and four hunts of eight landed on one line when it was aimed
  at new. A hunt samples the space by intuition and its real cost is
  the verification queue, which runs in the maintainer's context.
  THE ALTERNATIVE IS TO ENUMERATE WHAT HUNTS SAMPLE. This project's
  defects are not evenly distributed over shapes -- most of one day's
  ledger is ONE FACT HELD IN SEVERAL STORES, MENDED IN ONE -- and a
  shape that recurs that reliably can be swept mechanically, by three
  invariants that need no oracle and leave no claim to judge:
  AGREEMENT (every store holding a fact agrees about it), COLLATERAL
  (an act about one element moves no other), and RETURN (doing a thing
  and undoing it comes back). One flag covers every kind of act: a
  CONTROL act must change something, a BOUNDARY CROSSING -- closing
  the plugin and opening it again, saving and reopening, choosing a
  group -- must change nothing. Full argument, cost and first findings
  in docs/process/HUNT-RECORD.md under "WHAT TO RUN INSTEAD OF A HUNT".

### C-3 — Why publish_candidate refuses, and what ten hand-published candidates risked

<sub>Cut from `CLAUDE.md`, lines 308–320 of the
2026-09-05 revision.</sub>

  THE TOOL REFUSES rather than guesses, and each refusal is one of the
  ten hand-published candidates' chances to go wrong: no receipt
  matching the tree, so only a GATED candidate can be published; a tag
  already taken, since a candidate number is spent by anything bearing
  it; CI on that exact commit not green, because the body SAYS it is
  and a body claiming a verdict nobody read is worse than one that
  says nothing (override with `--despite-ci <reason>`, which prints
  the reason IN the release); and no notes, because a candidate
  nobody described is a candidate nobody knows what to test.
  THE NUMBERS IN THE BODY ARE READ, not typed: the suite and gallery
  counts come out of the testing report, and the CI sentence out of
  `gh`. Guarded by `test_a_candidate_is_published_only_when_it_is_
  gated`.

### C-4 — What the platform probe cost before it existed: Windows, 75 minutes in

<sub>Cut from `CLAUDE.md`, lines 367–375 of the
2026-09-05 revision.</sub>

  IT WAS PAID FOR ON 2026-08-29. The assignment table's columns were
  taught to grow to their content, the window's ceiling stopped
  binding on any platform whose fonts are wider than this Mac's, and
  Windows reported it SEVENTY-FIVE MINUTES into its job -- in three
  tests and two locales, every one quoting 1729px against a 1480px
  budget. The fix cost another round to confirm. Nothing local could
  have caught it: in the suite's own environment the window's minimum
  is SMALLER than the table's, so the cap has nothing to bind and the
  case is unreachable here at any font.

### C-5 — The three faults the macOS leg found on its first complete run

<sub>Cut from `CLAUDE.md`, lines 400–409 of the
2026-09-05 revision.</sub>

  THE MACOS LEG EARNED ITS PLACE ON ITS FIRST COMPLETE RUN, and the
  reason is worth keeping: it is the only leg that runs the package a
  macOS user actually installs, in a profile nobody has seeded, and
  it immediately found three faults this machine cannot show -- a
  bundled interpreter that will not start without PYTHONHOME, a
  QGIS_PREFIX_PATH that had been wrong for months and left QGIS with
  NO COLOUR RAMPS AT ALL, and eight palettes dropped as duplicates of
  ramps a fresh QGIS does not have. Each was masked here by a style
  library the plugin seeded years ago, which is the same masking that
  let the colourspace gate pass on one machine's profile.

### C-6 — Two widenings of the CI-parity check, and the sixteen days its promise was false

<sub>Cut from `CLAUDE.md`, lines 434–453 of the
2026-09-05 revision.</sub>

  corrected 2026-08-15 and proved by hushing it in a throwaway copy. That last clause was added
  2026-08-15 with the Windows job: a job whose invocation is
  rewritten into a shape the pattern no longer matches drops out of
  the existence check without failing anything, which is the
  matches-nothing-reports-nothing fault the mutation catalogue had
  found the same day. Nothing there is a hand-kept
  list, so the two cannot drift apart quietly.
  THAT LAST SENTENCE WAS FALSE FOR SIXTEEN DAYS and is true now. The
  stage list `EXPECTED_STAGES` in `release.py` IS hand-kept and was
  the only thing this check read, so a stage added there and
  forgotten got no CI job, no written exemption and no complaint --
  and two were already outside it, the release notes and the
  pre-commit secrets audit. The sibling test compares listed against
  called and never called against listed, so it could not see it
  either. `check_standards` now reads every `run(...)` name out of
  `release.py` and requires each to be listed, which is what makes
  the sentence true by construction. Found 2026-08-28 by an
  instruments audit that planted a stage the gate had to catch, with
  the control run first -- which is the practice to copy, because
  every claim it made came as a pair.

### C-7 — The three stages that left the release path in a day, and the two that stayed

<sub>Cut from `CLAUDE.md`, lines 585–602 of the
2026-09-05 revision.</sub>

- **A stage stays in the release path only while somebody reads its
  output and would act on it.** Three left within a day (2026-08-11
  and 12), about eighty minutes of every candidate between them: the
  new-code mutation guard, which quoted a blended figure it was told
  never to quote and could not finish inside the window it gated; the
  per-test coverage record, whose only consumer had just left; and
  the coverage report, half an hour that gates nothing by its own
  docstring and that six candidates in one night never once read.
  `--quick` was retired with the last of them, having nothing left to
  skip. What did NOT leave is the contrast worth remembering: the
  visual gallery at 7 seconds and the colourspace comparison at 16,
  because both catch a WRONG MAP, which is this software's
  characteristic failure -- a wrong map looks exactly like a right
  one. Twenty-three seconds against eighty minutes. Before adding
  anything to a release, and periodically for everything already in
  it, ask who reads the output and what they would do differently; if
  the answer is nobody, or nothing before the artefact ships, it
  belongs on demand or on somebody else's machine, reporting.

### C-8 — The third renderer: the changelog entry that ran on through the previous version

<sub>Cut from `CLAUDE.md`, lines 756–764 of the
2026-09-05 revision.</sub>

  AND A THIRD RENDERER IS THE ONE THAT CUTS THE ENTRY OUT. (Row 31
  of 2026-08-27.) The entry is delimited rather than stored: an entry
  ends at a lookahead for a line opening with digits. Opening the
  0.24.4 section INDENTED the previous version's header instead of
  stripping its `changelog=` prefix, so `    changelog=0.24.3 You
  decide...` was no longer a header to that pattern, and the 0.24.4
  entry ran on through the whole of 0.24.3 -- thirty-one bullets of
  an already-shipped release under this one's heading, and a field
  name in the middle of what the plugin manager displays.

### C-9 — The four faults heartbeats found on 2026-08-10

<sub>Cut from `CLAUDE.md`, lines 889–897 of the
2026-09-05 revision.</sub>

  a defect-finding instrument rather than a courtesy: on 2026-08-10
  four faults were found by beats and none by waiting for a job to
  finish -- a sweep reporting shards done from logs left by a run
  killed hours earlier, a catalogue sweep announcing CLEAN after
  judging one entry of 156 because its listing had crashed, a census
  measuring a tree that had since changed beside a second census, and
  a worker from an abandoned run still writing into the log a new run
  was appending to. Each would have produced a number somebody
  believed, and none showed up in a final "done" line. Full procedure

### C-10 — Why the new-code mutation guard stopped gating a candidate

<sub>Cut from `CLAUDE.md`, lines 946–964 of the
2026-09-05 revision.</sub>

  full reasoning in docs/MUTATION-LOOP.md.) It ran fifty minutes
  against 2,274 changed lines and reached 61.5%, and three things
  were wrong with it as a gate, none of them the threshold being
  inconvenient. It measured the WRONG THING: a blended figure over
  changed lines is what MUTATION-TESTING.md says never to quote,
  since logic runs high and Qt plumbing runs low, and that release
  was mostly plumbing (bridge 4/5 against dialog 10/17). It COST
  more than a candidate can carry: two mutants timed out at
  twenty-one minutes each, three more ran past twenty against
  covering sets of 153 and 221 tests, and fifty minutes bought 28
  verdicts of 80 — and the sample scales with the diff, so a big
  release is when it is slowest. And its RED meant "write tests over
  the next few days", which is a work list rather than a gate; this
  project already made that argument for the visual gallery and the
  catalogue sweep. `release.py` now prints what it would have
  sampled and names the dispatch command; the run happens on GitHub
  and its survivors are triaged into the NEXT candidate. What is not
  claimed is that survivors do not matter: ten came out of the
  half-run that prompted this and they are the 0.24.1 list.

### C-11 — The historical form of the new-code guard, when it still gated a release

<sub>Cut from `CLAUDE.md`, lines 965–981 of the
2026-09-05 revision.</sub>

- **The historical form of that rule, for context.** It used to be
  that `release.py` re-recorded per-test coverage and then ran
  `tools/mutate_auto.py --since <previous tag> --require 70`, which
  mutates ONLY the lines that changed and stopped the release if the
  tests written alongside them failed to catch 70% of those mutants.
  The sample SCALES with the diff — floor 12, one mutant per twenty
  changed lines, cap 80 (`release.mutation_sample_size`, pinned by
  its own test) — because a fixed dozen was sized for routine
  releases and became decorative against a 1,700-line round. With no
  release tag to diff against the guard cannot run and now says so
  LOUDLY; the baseline tag `pre-0.24.0` exists precisely so that
  state never recurs. Cost stays proportional to the change, so it
  runs every time, which is the point: a mutation score decays not
  through decisions but through changes that nobody measured. This
  does not replace the periodic full campaign — changed lines are
  where new gaps arrive, but a refactor elsewhere can quietly stop an
  old test reaching what it names, and only full sampling finds that.


## How we decide things: the accounts behind them

### C-12 — The window-height question nobody had asked

<sub>Cut from `CLAUDE.md`, lines 1080–1088 of the
2026-09-05 revision.</sub>

  DECISION THEY HAVE TO MAKE.** (2026-08-29, and it cost them two
  exchanges.) They asked that the window not take up the whole screen.
  That was written up as re-opening the settled layout rule of
  2026-08-09, needing a fourth priority ordered among three, and
  ending in a question put back to them: how much shorter than the
  screen? Their answer was that they had not meant anything about
  screen height and just did not want it filling the screen. The ask
  was a ceiling on GROWTH, today's size was fine, and no number was
  owed at all.


## Lessons learned here, in full

### C-13 — Label anchors: centroid for the visual centre; representative_point only as the...

<sub>Cut from `CLAUDE.md`, lines 1196–1204 of the
2026-09-05 revision.</sub>

- Label anchors: centroid for the visual centre; representative_point
  only as the inside-the-polygon fallback for concave shapes (it comes
  from a bbox-midheight scanline and reads off-centre).

**Testing.** The full record now lives in `docs/TESTING.md`, which is
REQUIRED READING before writing or changing tests, together with
`docs/MUTATION-TESTING.md` for the campaign that keeps the suite
honest. Both are binding, not background. The four that get violated
first, kept here so they are unmissable:

### C-14 — A test that PASSES is not a test that WORKS

<sub>Cut from `CLAUDE.md`, lines 1209–1228 of the
2026-09-05 revision.</sub>

- A test that PASSES is not a test that WORKS. It has to fail when the
  behaviour it names is broken, and the only way to know is to break
  it. Every test written to close a mutation gap gets an entry in
  `tools/mutation_check.py`, which does exactly that and runs at
  release. Six tests written in one session were verified to pass,
  and most of them then failed to kill the very mutants they were
  written for.
  **AND WHEN A BATCH OF TESTS IS WRITTEN IN ONE SITTING, POINT A HUNT
  AT THE TESTS, MUTATING PER ASSERTION.** The catalogue proves a
  test's PRIMARY axis and structurally cannot see the rest: it breaks
  one behaviour, the first assertion kills it, and the entry reports
  `caught` while the second and third axes sit dead. Measured here at
  one in five or six, three rounds running, and every time inside a
  test whose first assertion was live and well aimed. The trigger is
  the SITTING rather than any one test, and the procedure -- including
  how an adversarial reader gets it wrong in the other direction, by
  demanding a contract nobody agreed -- is in docs/TESTING.md under
  "THE TRIGGER". Added 2026-08-17 at the maintainer's asking, because
  the practice was already written down twice and skipped both times
  for want of a moment to do it.

### C-15 — A PAIRED ARTEFACT INHERITS THE IDENTITY OF WHAT IT IS PAIRED WITH, so every reader...

<sub>Cut from `CLAUDE.md`, lines 1241–1250 of the
2026-09-05 revision.</sub>

- **A PAIRED ARTEFACT INHERITS THE IDENTITY OF WHAT IT IS PAIRED
  WITH**, so every reader keyed on that identity silently gains a
  second answer, and every writer that maintained the original has a
  twin that does not. The no-data layer carries its element's
  `weavingspace_tile_id` because it belongs to that element -- and
  adoption, keyed on that id alone, let the twin OVERWRITE its own
  element, so the next Generate removed the twin and orphaned the real
  layer. Yesterday's map then sat on top of the new one for good.
  GREP THE PROPERTY, NOT THE FEATURE: every reader of the id, every
  per-element dict, every count of a group's children.

### C-16 — A NAME THE USER CAN EDIT IS NOT AN IDENTITY, AND MUST NEVER BE A KEY

<sub>Cut from `CLAUDE.md`, lines 1251–1268 of the
2026-09-05 revision.</sub>

- **A NAME THE USER CAN EDIT IS NOT AN IDENTITY, AND MUST NEVER BE A
  KEY.** Every record in `dialog.py` keys on a custom property except
  the output group, which was found with
  `findGroup(self._group_name)` -- so renaming the group in the layers
  panel, which is an ordinary thing to do, made it invisible and the
  next run built a rival over the same four GeoPackage tables, the
  abandoned group redrawing the new data under the old class breaks.
  Adoption had the same fault from the other side, skipping any group
  whose name it did not recognise. Both now ask the LAYERS: within a
  session by asking which group this dialog's own layers are in, and
  on reopening by looking for a group holding a layer that carries our
  custom property. Measured 2026-08-17 through both doors and guarded
  by `test_a_renamed_group_is_still_the_group_the_next_run_replaces`
  and `test_a_renamed_group_is_adopted_when_the_plugin_reopens`.
  The general form, which reaches past groups: anything a user can
  rename -- a layer, a group, a field alias, a file -- is a LABEL, and
  a label is what you show them, never what you look them up by. When
  a lookup takes a string, ask who else can change that string.

### C-17 — TARGETED RUNS CANNOT FIND WHAT THEY DO NOT NAME, and three candidate builds aborted...

<sub>Cut from `CLAUDE.md`, lines 1340–1350 of the
2026-09-05 revision.</sub>

- **TARGETED RUNS CANNOT FIND WHAT THEY DO NOT NAME**, and three
  candidate builds aborted proving it (2026-08-16). Each abort was the
  same fault -- something counts or renders an element and looks only
  at `_element_layer_ids` -- and each time it was fixed in the
  instances a keyword search turned up, because the keyword matched
  what had just been fixed. The tests that finally caught the worst of
  it mention neither colour nor class nor no data. Two habits follow:
  when a change alters what a map CONTAINS, grep every reader that
  counts, measures or renders it and fix the SET rather than the
  instance; and do not mistake a green subset for a green suite. The
  full suite in `release.py` is the only thing that found it.

### C-18 — Check upstream's actual semantics before reimplementing behaviour: "unclassed"...

<sub>Cut from `CLAUDE.md`, lines 1357–1366 of the
2026-09-05 revision.</sub>

- Check upstream's actual semantics before reimplementing behaviour:
  "unclassed" turned out to be matplotlib's linear Normalize (so 50
  equal intervals, not a new scheme), and categorical colours follow
  ListedColormap's sampling: code/(k-1) mapped through int(x*N),
  clamped — 5 on tab10 = entries 0,2,5,7,9. An earlier "derivation"
  used round() and got 0,2,4,7,9, painting the middle category purple
  instead of brown; only the colourspace comparison against an actual
  upstream render caught it. The reference is upstream's *rendered
  output*, not upstream's code read in a hurry, and certainly not
  intuition.

### C-19 — When batch-editing via heredoc Python scripts: assert every anchor BEFORE any write,...

<sub>Cut from `CLAUDE.md`, lines 1371–1386 of the
2026-09-05 revision.</sub>

- When batch-editing via heredoc Python scripts: assert every anchor
  BEFORE any write, and beware a trailing comma turning a string into
  a tuple (it aborted two patch runs here); for single replacements
  prefer the Edit tool. Two more ways this bit on 2026-08-13, both
  cheap to avoid. **A slice needs its end searched FORWARD from its
  start** -- `s.index(a)` and `s.index(b)` both search from zero, so
  if b occurs before a the slice `s[:start] + s[end:]` DUPLICATES a
  span instead of removing it, silently, in a file too large to
  eyeball. It happened to two files at once and was caught only by
  counting definitions afterwards. **And assert the postcondition, not
  just the anchor**: `assert "the_removed_name" not in s` before
  writing caught a bad edit that every anchor check had passed. When
  an assertion like that fires, do not widen it to get past -- one
  here was genuinely too broad (`n=n)` matches legitimate code) and
  narrowing it was right, but the reflex to loosen is how a guard
  becomes decoration.

### C-20 — When waiting on a long background run, key the wait on the PROCESS ENDING, not on...

<sub>Cut from `CLAUDE.md`, lines 1394–1402 of the
2026-09-05 revision.</sub>

- When waiting on a long background run, key the wait on the PROCESS
  ENDING, not on log text you predicted. A watcher polling for "tests
  recorded" sat in a sleep loop for twelve hours because the tool
  actually prints "recorded 75 tests", and its fallback pattern
  ("Error") missed the crash line too, which read "Fatal Python
  error". Silence from a watcher is not evidence that the work is
  still running. Wait on the pid, and if a log must be matched,
  include a case-insensitive alternation broad enough to catch the
  failure modes as well as the success line.

### C-21 — SEED a watcher with what is already true before it reports anything

<sub>Cut from `CLAUDE.md`, lines 1403–1415 of the
2026-09-05 revision.</sub>

- **SEED a watcher with what is already true before it reports
  anything.** Ten watcher faults on this project by 2026-08-12 and
  the last three were all this one: a poller started with an empty
  "seen" set announces its first sighting as news, so historical CI
  failures and a stage log from the previous night arrive as though
  they had just happened. Each was written within an hour of somebody
  reading the entry describing it, which is the actual finding: a
  watcher is written while attention is on the thing being watched,
  and that is exactly when nobody reviews it. Two other members of
  the family, for completeness -- key on the THING and not a snapshot
  of it (a watcher pinned to one commit sha sat silent while two more
  pushes superseded it), and report every terminal state rather than
  only success.

### C-22 — Two watchers must never share a log file

<sub>Cut from `CLAUDE.md`, lines 1416–1450 of the
2026-09-05 revision.</sub>

- **Two watchers must never share a log file.** The eleventh watcher
  fault here, 2026-08-14: a CI watcher was re-armed for a new commit
  while its predecessor was still running, both wrote to the same
  path, and the OLD one appended `FINISHED: cancelled` underneath the
  NEW one's header. Read literally, the file said the live run had
  been cancelled. It had not; the run it described was a different
  one, deliberately cancelled twenty minutes earlier. Key each
  watcher's output to WHAT IT WATCHES (the sha, the run id, the job
  name) rather than to what it is, and when a log looks wrong, ask the
  source directly before believing it. The file was annotated by hand
  rather than rewritten, because a log that silently corrects itself
  is worth less than one that says where it was unreliable.
  **The same fault twice in five days, and the second time it was a
  RELAUNCH.** 2026-08-14: a sharded suite was started, appeared to
  die, and was started again over the same `shardN.log` paths -- but
  one shard of the first run had outlived the kill, so two runs of
  the same shard, on two different commits, appended to one file. The
  counts stopped making sense before anybody wondered why. Two rules
  follow, both cheap. Key a run's logs to the RUN (a timestamp, the
  commit, anything unique), never to the shard number alone, so a
  second launch cannot land in the first one's file. And verify the
  kill rather than assuming it: `pgrep` for the work itself, not for
  the wrapper that started it, because a launcher can exit while what
  it launched carries on -- which this project already learned once
  from a stochastic hunt that relaunched itself with nohup.
  **And a watcher outlives the thing it watched.** 2026-08-14, the
  twelfth: a CI poller armed for `pre-0.24.1rc1` was still running two
  releases later and announced `CI GREEN <sha>` while the work was on
  `pre-0.24.3rc1`. Nothing about the message said which branch, so the
  obvious reading -- that the current branch had gone green on a
  machine nobody had pushed to -- was wrong and comfortable. The rule
  already exists ("stop the watcher when the work finishes"); what it
  needs is the other half, which is that every watcher NAMES ITS
  SUBJECT in each line it emits. A verdict without its branch is a
  verdict about whatever the reader is thinking of.

### C-23 — A WHOLESALE SPAN REWRITE TAKES ITS NEIGHBOURS

<sub>Cut from `CLAUDE.md`, lines 1451–1459 of the
2026-09-05 revision.</sub>

- **A WHOLESALE SPAN REWRITE TAKES ITS NEIGHBOURS.** Deleting
  everything between two anchors removed TWO tests on 2026-08-16, not
  the one intended, because another sat between them -- and one
  registration then named a function that no longer existed, which
  would have broken the suite at `main()`. It was caught by running
  the tests, not by the edit. After any span deletion, count the
  definitions and check BOTH directions of the registration list;
  `test_the_report_generators_survive_hostile_docstrings` asserts both
  and is the cheapest thing to run.

### C-24 — AND THE OPPOSITE EDIT IS QUIETER: A SECOND DEFINITION REPLACES THE FIRST AND NOTHING...

<sub>Cut from `CLAUDE.md`, lines 1460–1479 of the
2026-09-05 revision.</sub>

- **AND THE OPPOSITE EDIT IS QUIETER: A SECOND DEFINITION REPLACES THE
  FIRST AND NOTHING GOES MISSING.** Also 2026-08-16, hours later.
  Widening `_label_for` for the three kinds of absence was done by
  writing a NEW method below the old one instead of changing it.
  Python binds a name once per statement, so the last wins: the dead
  one sat above the live one, in its own place, with its own docstring
  describing behaviour the software no longer had. The survivor's
  fallback was the fixed word "no data" -- and the categorical branch
  calls it for EVERY row, so the window whose whole job is to say
  which value draws in which colour labelled forest, water and urban
  alike. A deletion leaves a hole somebody trips over; an addition
  leaves two plausible functions and no symptom at the site.
  `test_nothing_defines_the_same_name_twice` now checks the whole tree
  at module and class level, exempting the decorated idioms where
  redefining a name is Python's own (a property's setter, a
  `singledispatch` registration, `typing.overload`). WHEN A HELPER
  MUST ANSWER DIFFERENTLY FOR TWO CALLERS, that is the signal to look
  at the callers, not to write a second helper: the parentheses that
  mark the categorical catch-all now live at that call site, and the
  one method answers plainly.

### C-25 — A SIGNAL CONNECTED TO THE PROJECT OUTLIVES THE WINDOW THAT MADE IT, AND SO DOES A COMBO

<sub>Cut from `CLAUDE.md`, lines 1480–1505 of the
2026-09-05 revision.</sub>

- **A SIGNAL CONNECTED TO THE PROJECT OUTLIVES THE WINDOW THAT MADE
  IT, AND SO DOES A COMBO.** 0.24.3 added two hooks onto
  `QgsProject.instance()` -- `_settle_layer_choice` and the pair around
  `layersRemoved` -- and neither carried the retirement gate
  `_on_project_read` already had. A dialog the user has finished with
  stays connected until its C++ object is destroyed, which in a
  session that opens the plugin several times may be much later or
  never, so EVERY project change reached EVERY dialog ever opened and
  each rebuilt a full weave unit for a window nobody was looking at.
  Measured 2026-08-16: `_layers_removed` fired 231 times across 22
  dialogs, exactly sum(0..21) -- QUADRATIC in how often the plugin had
  been opened.
  THE FOURTH ROUTE WAS NOT A PROJECT SIGNAL AT ALL, and gating the
  first three left it open: `QgsMapLayerComboBox` re-emits
  layerChanged whenever the project's layers churn, and every retired
  dialog still owns a combo doing that. Only a guard test written
  afterwards found it, by counting rebuilds rather than trusting the
  three fixes. Unit rebuilds over one test: 461 at 0.24.2, 1,282 with
  the new hooks, 801 with the project gates, **173 once
  `_on_layer_changed` was gated too** -- below the baseline, because
  the gate also stops work 0.24.2 was doing for dead windows.
  So: when you connect a NEW signal to anything that outlives this
  dialog -- the project, the style library, a layer, or one of our own
  widgets that QGIS re-fires -- add `if _dialog_is_gone(self) or
  _live_dialog() is not self: return`, and grep for the other routes
  into the same handler before believing you have them all.

### C-26 — A GATE WHOSE EXIT NOBODY BRANCHES ON IS NOT A GATE EITHER, and the second visit pushed

<sub>Cut from `CLAUDE.md`, lines 1506–1517 of the
2026-09-05 revision.</sub>

- **A GATE WHOSE EXIT NOBODY BRANCHES ON IS NOT A GATE EITHER, and
  the second visit pushed.** 2026-08-25: `check_standards; echo; 
  check_before_push; echo; git commit && git push` -- both gates
  printed their failures, both echoes exited 0, and the commit chained
  off the ECHO. A tree the push gate had just called CI-red reached
  the public branch one command after the words appeared on screen,
  which is the 2026-08-15 fault with the pipe replaced by a
  semicolon. The failure was an orphaned anchor, fixed forward in the
  next commit; the rule is the same one, stated wider: capture the
  gate's OWN exit and branch on it (`STD=$?; [ "$STD" -ne 0 ] &&
  stop`) in the same script that would commit -- reading the words is
  not a gate, and neither is printing the number.

### C-27 — A GATE PIPED INTO ANYTHING IS NOT A GATE

<sub>Cut from `CLAUDE.md`, lines 1518–1527 of the
2026-09-05 revision.</sub>

- **A GATE PIPED INTO ANYTHING IS NOT A GATE.** `check_before_push |
  tail -2` returns TAIL's exit status, so a shell `&&` after it fires
  whatever the gate said. That is how a tree failing the standards
  check reached the branch on 2026-08-15, one command after the gate
  reported the failure on screen -- the words were right there and the
  exit code was gone. Run the gate on its own line and read its
  status, or use `set -o pipefail`; never let a pipe stand between a
  gate and the thing it gates. The same applies to `grep`-ing a test
  runner's output: the runner's verdict is lost the moment it is
  piped.

### C-28 — A WATCHER IS A PROGRAM, AND A PROGRAM CAN DIE

<sub>Cut from `CLAUDE.md`, lines 1529–1544 of the
2026-09-05 revision.</sub>

- **A WATCHER IS A PROGRAM, AND A PROGRAM CAN DIE.** The thirteenth
  fault here, 2026-08-15: a CI poller with associative arrays, a
  nested here-string loop and two embedded Python readers exited 1
  partway through a run, having reported two jobs of eleven. Its
  silence afterwards was indistinguishable from "nothing has changed
  yet", which is the same failure mode as every other entry in this
  list, reached by a new road -- the watcher's OWN complexity. It was
  survivable only because the harness reports a monitor's exit; a
  watcher launched any other way would simply have gone quiet.
  So: keep the script trivially simple, guard every external call so
  a transient failure cannot end the loop, and prefer re-deriving the
  whole state each pass over accumulating it in shell variables.
  When a watcher does die, ASK THE SOURCE DIRECTLY before saying
  anything about what it was watching -- the last line it printed is
  not the current state, and reporting it as though it were is how a
  green summary gets written over a red run.

### C-29 — A FALLBACK THAT APPENDS INSTEAD OF REPLACING, AND THE FIFTEENTH WATCHER FAULT

<sub>Cut from `CLAUDE.md`, lines 1546–1566 of the
2026-09-05 revision.</sub>

- **A FALLBACK THAT APPENDS INSTEAD OF REPLACING, AND THE FIFTEENTH
  WATCHER FAULT.** 2026-08-20: a nagging watcher was written to exit
  when its work list emptied, and it read the count as `left=$(grep -c
  . "$LIST" || echo 0)`. `grep -c` PRINTS `0` and EXITS 1 when nothing
  matches, so the guard meant for an unreadable file fired on the
  ordinary empty one and the substitution captured `0\n0`. `[ "$left"
  -eq 0 ]` then errors on a two-line string rather than being false,
  the exit branch never ran, and the loop went on emitting `0 still
  owed ... keep working` -- a line contradicting itself, which is the
  worst kind, because it reads as a bug in the reader.
  THE SHAPE, past shell: a fallback written with `||` runs when the
  command FAILS, not when it produces nothing, and a command that
  prints a perfectly good answer while exiting non-zero defeats it by
  adding to the output rather than replacing it. Ask of any `|| echo
  <default>` whether the command it guards can both succeed at
  printing and fail at exiting. And measure the empty case: one line
  in a terminal showed `left=[0\n0]` where an hour of reading had
  shown nothing.
  The rule this joins is already written above -- keep a watcher
  trivially simple, and prefer re-deriving the whole state each pass.
  This one was fourteen lines long and still found a new road.

### C-30 — AND THE MIRROR IMAGE: A LAUNCHER THAT FAILS MAY HAVE STARTED THE JOB FIRST

<sub>Cut from `CLAUDE.md`, lines 1580–1601 of the
2026-09-05 revision.</sub>

- **AND THE MIRROR IMAGE: A LAUNCHER THAT FAILS MAY HAVE STARTED THE
  JOB FIRST.** (2026-08-27.) `LOG=... && nohup python3 release.py
  --rc > "$LOG" 2>&1 &` mis-scoped its variable and reported an
  error, so the launch was read as having not happened and the
  candidate was launched again. The `&` had already backgrounded a
  release. TWO of them then ran for a quarter of an hour on one tree,
  each running the three-shard suite into the other's contention,
  sharing `dist/`, `reports/` and the candidate numbering, with the
  second truncating the log the first was writing past -- so the
  shard counts read off that log and reported as progress described a
  race. The rule above says an exit status describes the launcher
  rather than the job; this is the same sentence read the other way,
  and it is the more expensive direction. BEFORE RELAUNCHING
  ANYTHING, ASK WHAT THE FAILED LAUNCHER STARTED: `pgrep -f` for the
  work itself, never for the wrapper.
  AND THE READING THAT WOULD HAVE CAUGHT IT WAS POINTED AT THE WRONG
  PROCESS. The beat reported the parent's cpu, which for a sharded
  run is near zero however healthy it is, so cpu-against-elapsed --
  the one measurement that tells blocked from busy -- said neither
  for sixteen minutes. It sums the children now. When a watcher
  reports cpu, ask which process the figure is about; a parent that
  only waits is not the job.

### C-31 — READ THE LINE THAT ASSIGNS A TOOL'S VERDICT BEFORE TRUSTING THE WORD

<sub>Cut from `CLAUDE.md`, lines 1602–1612 of the
2026-09-05 revision.</sub>

- **READ THE LINE THAT ASSIGNS A TOOL'S VERDICT BEFORE TRUSTING THE
  WORD.** (2026-08-27.) The catalogue sweep prints `caught` or
  `ATTENTION`, and its own source is `verdict = "caught" if
  proc.returncode == 0 else "ATTENTION"` -- so ATTENTION mostly means
  a SURVIVOR, the word SURVIVED never appears in a sweep log at all,
  and `grep -c SURVIVED` answers zero however bad the news is. Read as
  "too slow to settle", 43 flags looked like contention across four
  shards; re-run one at a time on an idle machine they came back 0
  caught, 34 survived, 9 unjudgeable. A count of a word the tool never
  prints is a reassuring zero, which is the absence-of-evidence fault
  wearing a verdict's clothes.

### C-32 — AND A SUMMARY THAT NAMES WHAT IT SUMMARISES IS CAUGHT BY ANY FILTER LOOKING FOR IT

<sub>Cut from `CLAUDE.md`, lines 1613–1621 of the
2026-09-05 revision.</sub>

- **AND A SUMMARY THAT NAMES WHAT IT SUMMARISES IS CAUGHT BY ANY
  FILTER LOOKING FOR IT.** The same sweep ends with `NEEDS ATTENTION
  (re-run each alone): <every flagged name>`, so a `grep ATTENTION`
  over the log picks up the summary beside the verdicts -- and `sed`
  leaves a non-matching line untouched, so a whole sentence arrived as
  one "name" and the loop word-split it into fifty. It also put a
  count at "560 of 559". When you filter a log for a marker, exclude
  the line that REPORTS on the marker, and check any total against the
  count the run declared for itself.

### C-33 — `gh run list --commit` MATCHES THE FULL FORTY-CHARACTER SHA, AND A SHORT ONE RETURNS...

<sub>Cut from `CLAUDE.md`, lines 1622–1635 of the
2026-09-05 revision.</sub>

- **`gh run list --commit` MATCHES THE FULL FORTY-CHARACTER SHA, AND A
  SHORT ONE RETURNS NOTHING AT ALL.** (Same day, and it is the
  sixteenth watcher fault here.) A watcher keyed to `eb1ed8b` waited
  two hours and then reported that no run had ever been created; a
  second, written after reading that, reported the same within two
  minutes. Both were wrong. Asked with the full sha, `eb1ed8b` has
  `tests` and `mutation`, both green, and the live commit had two runs
  in flight the whole time. An empty list from a filter that cannot
  match is indistinguishable from an empty list because nothing
  exists, and the first diagnosis written from it -- that GitHub
  creates runs for pushes rather than commits, so an intermediate
  commit gets none -- was invented to explain an artefact and is
  simply false. `git rev-parse` the short sha before asking, or filter
  by `--branch` and compare `headSha` yourself.

### C-34 — A `PASS` LINE IS LOST TO A PIPE, SO SILENCE PLUS EXIT 0 IS NOT A PASS

<sub>Cut from `CLAUDE.md`, lines 1636–1644 of the
2026-09-05 revision.</sub>

- **A `PASS` LINE IS LOST TO A PIPE, SO SILENCE PLUS EXIT 0 IS NOT A
  PASS.** `tests/run_tests.py` ends through `os._exit`, so when stdout
  is not a terminal the buffered `PASS <name>` is discarded and
  `tools/run_some.py` exits 0 having said nothing, while a FAILURE's
  traceback reaches unbuffered stderr and survives. Read literally
  that is a run reporting nothing, and it looks exactly like success.
  `PYTHONUNBUFFERED=1` is what makes the verdict reach the pipe. Same
  `os._exit` that stopped `tools/coverage_report.py` writing a report
  at all until 2026-08-13.

### C-35 — AND THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE

<sub>Cut from `CLAUDE.md`, lines 1645–1653 of the
2026-09-05 revision.</sub>

- **AND THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE.** Tests run
  under `$QGIS_PY`; edits and `tools/mutation_check.py` run under
  `env -u PYTHONHOME -u PYTHONPATH python3`. Swapping them fails in
  two directions that both read as a broken test: `env -u ... python3`
  hands you the SYSTEM interpreter, which dies at `import qgis`, and a
  bare `python3` under a sourced QGIS environment dies at `Failed to
  import encodings` having applied no edit at all. Both were done in
  one proof script on 2026-08-27, which is why they are written
  together.

### C-36 — `exists` THEN `remove` IS A RACE, AND EVERYTHING HERE SHARDS

<sub>Cut from `CLAUDE.md`, lines 1654–1675 of the
2026-09-05 revision.</sub>

- **`exists` THEN `remove` IS A RACE, AND EVERYTHING HERE SHARDS.**
  (2026-08-28.) `tests/run_tests.py`'s `main()` cleared its scenario
  record by asking whether the file was there and then removing it.
  Three coverage recorders start within a second of each other; all
  three saw it, two removed it, and the third died with
  FileNotFoundError BEFORE RUNNING A SINGLE TEST. Nothing announced
  that: the survivors ran on, the progress count rose, and the record
  would have been missing a third of the suite -- which overstates
  survivors, because a test missing from the record is never offered
  the chance to notice a mutant. Asking the question cannot fix it;
  only not caring can (`contextlib.suppress(FileNotFoundError)`).
  IT WAS FOUND BY AN ASYMMETRY: one shard had recorded nothing while
  its siblings were at nineteen and thirty. So when work is sharded,
  read the shards SEPARATELY -- a total climbing healthily is the sum
  of two shards doing fine and one that died at startup.
  AND GUARD THE SHAPE RATHER THAN THE SITE. The family test scans
  `tests/` and `tools/` for the pattern, reading each file WHOLE
  because it spans two lines and no per-line grep can see it, and it
  immediately found a second instance in
  `tools/make_test_fixtures.py` -- a site likelier to be run once, and
  therefore exactly the one a repair at the reported site leaves
  standing.

### C-37 — A WATCHER THAT SUBSTITUTES "NOTHING" FOR A FAILED CALL REPORTS ITSELF TWICE

<sub>Cut from `CLAUDE.md`, lines 1676–1685 of the
2026-09-05 revision.</sub>

- **A WATCHER THAT SUBSTITUTES "NOTHING" FOR A FAILED CALL REPORTS
  ITSELF TWICE.** (Same day, the seventeenth watcher fault.) A CI
  poller deduplicated by comparing this pass's verdicts against the
  last, and guarded `gh` with `|| echo "[]"` so a transient failure
  could not kill the loop. That guard empties the comparison set, so
  the next successful poll finds everything new and re-announces a
  verdict already reported. The rule this project already carries --
  report change, not state -- has a precondition nobody wrote down:
  the record of what you have already said must survive a failed
  reading. On an error, keep the previous state and skip the pass.


## Design decisions already settled, in full

### C-38 — COLOUR BELONGS TO QGIS

<sub>Cut from `CLAUDE.md`, lines 1739–1796 of the
2026-09-05 revision.</sub>

- **COLOUR BELONGS TO QGIS.** Ramps come from QgsStyle, and where a
  name means something there already, QGIS's meaning wins. The plugin
  installs only palettes QGIS LACKS -- 36 of them, tab10, the
  matplotlib-only families and the eight ColorBrewer QUALITATIVE sets
  -- tagged "mapweaver", additive only.
  Settled by `/grill-me` on 2026-08-15 after measuring that 35 of the
  palette file's 63 entries were also stock ColorBrewer names, so they
  had never installed on any fresh QGIS since 0.23.0: the plugin's
  maps were already drawn with QGIS's colours and the project had
  simply not noticed.
  **"LACKS" IS ANSWERED BY THE STYLE LIBRARY, NEVER BY WHAT QGIS CAN
  GENERATE**, and getting that wrong the same evening cost eight
  palettes. The 35 were identified as ColorBrewer SCHEME names, which
  QGIS can synthesize through `QgsColorBrewerColorRamp`; eight of them
  -- Accent, Dark2, Paired, Pastel1, Pastel2, Set1, Set2, Set3 -- are
  not entries in `QgsStyle.defaultStyle()` at all. A fresh QGIS 4.0.3
  holds 35 ramps and every one is sequential or diverging, so dropping
  those eight removed every qualitative palette from every fresh
  install, and `get_ramp("Set2")` returned None. Restored the same
  night after macOS and Windows CI failed on it identically. The
  question to ask of any deduplication against a dependency is what it
  HAS, not what it could make. The colourspace gate passed only because the
  development machine's style library had been seeded by the plugin
  years earlier -- a gate certifying fidelity against a profile no
  user has.
  PARITY WITH THE LIBRARY IS A DESCRIPTION, NOT A PROMISE. The plugin
  defers to QGIS for renderers, the styling dock, the project format
  and the ramp list; colour is the same kind of thing. A user wanting
  matplotlib's exact palettes installs them; the plugin does not ship
  them under alternative names. Profiles already seeded keep what they
  have -- additive only has never meant destructive -- so a machine
  that installed an early version draws those 35 differently from a
  fresh one until its owner clears them.
  The comparison in `tools/visual_reference_report.py` is therefore
  handed THE COLOURS IN FORCE, exported beside the gallery by
  `tests/visual_tests.py`, and no longer asserts whose palette they
  are. It still tests where the breaks fall, how categories are
  sampled, the reduction, insetting, weaving and geometry -- and it
  cannot again pass because of one profile. What it gave up is covered
  by `test_the_ramp_a_row_names_is_the_ramp_the_map_draws`.
  **ITS REMAINING REDS ARE THE SAME FACT AGAIN, and they are not a
  Linux problem.** Measured the same night by holding everything
  constant but the profile: this Mac scores the "web-app parity" cases
  at dE mean 2.6-3.1 on its own seeded library, and at 3.7-4.1 with
  p90 6.7-7.1 on a THROWAWAY profile -- the Linux figures to the
  decimal. A fresh QGIS resolves Reds and YlGn to ColorBrewer-anchored
  gradients of nine stops, or five, where the seeded library holds the
  plugin's sixteen-stop versions, so the two differ EVERYWHERE rather
  than at edges. The earlier explanation, a platform offset blamed on
  antialiasing and missing fonts, was wrong.
  The 4.0 limit was therefore calibrated against renders from a
  profile no user has. Whether a parity comparison should still fail a
  build for that is the maintainer's decision and a real one:
  re-deriving a limit whose baseline was never representative is not
  the same act as loosening a threshold to get a green run, but it is
  near enough that nobody should make the change quietly. Reproduce in
  thirty seconds by rendering the gallery under
  `QGIS_CUSTOM_CONFIG_PATH=$(mktemp -d)` and scoring it.

### C-39 — AT MOST THREE SIGNIFICANT FIGURES IN ANY NUMBER BOX

<sub>Cut from `CLAUDE.md`, lines 1835–1873 of the
2026-09-05 revision.</sub>

- **AT MOST THREE SIGNIFICANT FIGURES IN ANY NUMBER BOX.**
  (Maintainer's rule, 2026-08-17, after a tester met spacing showing
  six decimal places of metres.) Figures rather than decimal places,
  deliberately: a figures rule bounds what a reader takes in whatever
  the magnitude, where a decimals rule lets 1234.567 through at four
  and clips 0.0008 to nothing.
  `dialog._limit_the_figures_on_show` sweeps every `QDoubleSpinBox`
  once at construction, so a control added next year obeys the rule
  without anybody remembering -- which the five-rules-in-five-places
  arrangement it replaced was not. THE STEP DECIDES AND THE CAP BOUNDS
  IT: a box shows the decimals its own `singleStep` needs, and never
  more than three figures. Counting from the VALUE instead gives every
  box sitting at zero three decimals, since zero has no digits to
  count, which is how the offset angle read "0.000" degrees on the
  first attempt.
  TWO GOOD REASONS TO DEPART, both real. Spacing spans 1e-6 to 1e12,
  so no construction-time setting suits a floor plan at half a metre
  and a country at fifty kilometres; it is exempt by identity (never
  by `objectName`, which is empty on every box here) and TRIMS ITS
  TEXT instead, in `SpacingSpinBox.textFromValue`, keeping six
  decimals of precision and printing none of the zeros it does not
  need.
  THE MECHANISM THAT PRECEDED IT ROUNDED A NUMBER A PERSON TYPED, and
  the mistake is the one to remember: it sized `decimals` from the
  spacing auto-fitting had computed, and a QDoubleSpinBox at zero
  decimals cannot REPRESENT 500.5. Typing 500.5 gave 501, typing
  215.509124 gave 216, and the map was tiled from the rounded number
  with nothing said. `decimals` governs display AND input AND
  storage, so ANY rule that lowers it to tidy a display destroys
  data; a display rule belongs in `textFromValue`, which touches
  neither the value nor the validator. Four tests said so and the
  branch carried it for a day because nothing ran them. And a box
  holding a number a PERSON TYPED, or one taken from the data, must
  not round it away: the class-bound boxes size their decimals from
  the data deliberately (catalogue entry
  `the-bound-box-is-sized-from-the-data`), since clipping a pinned
  -0.9276 to -0.928 would change the value the map is drawn from.
  Any such box declares its exemption at the site, with the reason
  there, and is still as tight as it honestly can be.

### C-40 — The Categorical colour editor (`category_editor.py`, the "Edit colours" column) lets...

<sub>Cut from `CLAUDE.md`, lines 1894–1938 of the
2026-09-05 revision.</sub>

- **The Categorical colour editor** (`category_editor.py`, the "Edit
  colours" column) lets a user set a colour per value. Settled by
  `/grill-me` on 2026-08-08; the decisions are the user's and should
  not be quietly revisited. Values come from the REGION layer, so the
  button works before anything is generated — accepting that at a
  coarse spacing it can list a value no tile carries. Colours are
  keyed `{tile_id: {field: {value: colour}}}`, so switching an
  element's variable away and back restores the work and two fields
  sharing a value name cannot bleed into each other. Choosing a ramp
  or importing a QML CLEARS that element's hand-picks for the current
  field, so the ramp control means what it says; the loss is reported,
  never silent. Overrides outrank both template and ramp in
  `make_categorized_renderer`, and the catch-all is editable under
  `bridge.NO_DATA_KEY`. The window is modal to the plugin dialog only,
  leaving the QGIS canvas live so the recolour can be watched. The
  editor NEVER holds a layer: it writes to the dialog's record and
  lets the restyle path find whatever layers exist, which is what
  makes it safe to use while a run is in flight. Two consequences that
  cost a bug each: the picks must be in `_signature` or the fast path
  skips the element as unchanged, and `_add_output_layers` must
  RE-READ them rather than trust the snapshot the run was launched
  with, or a colour chosen during a run is destroyed when it lands.
  They persist as a layer custom property so a saved project survives
  a QGIS restart. **Both consequences apply to the GRADUATED editor
  too, and saying "category colours" here is how that went unnoticed
  for five days.** The quant editor writes positional class colours
  and the ramp's display window through the same window, and
  `_add_output_layers` re-read only the categorical half until
  2026-08-13: a class colour picked during a run was destroyed when
  the run landed AND stamped absent onto `weavingspace_quant_style`,
  so reopening the project could not bring it back either. The rule
  is about HAND-PICKED COLOUR on either styling path, not about the
  categorical editor. When a rule here names one of a pair, check the
  other before believing it is a rule about one thing.
  **It happened a THIRD time on 2026-08-14**, and the third is the one
  that should settle the phrasing. Pinned bounds and copied ladders
  are written through that same window while a run can be in flight,
  and the landing re-read colours and the display window and not them
  -- so a pin made during a run was destroyed as the run landed and
  stamped absent onto the layer. The rule is not about colour and not
  about the editor: EVERYTHING the colour editor writes must be
  re-read at the landing, and anything added to that window later
  joins the list. It was found by the maintainer asking whether the
  new features had been tested for races, which is worth more than
  the fix.

### C-41 — A CATEGORICAL SCHEME COPIES LIKE A GRADUATED ONE, AND IT OVERWRITES

<sub>Cut from `CLAUDE.md`, lines 1939–1964 of the
2026-09-05 revision.</sub>

- **A CATEGORICAL SCHEME COPIES LIKE A GRADUATED ONE, AND IT
  OVERWRITES.** (Maintainer's rulings, 2026-08-20, after a tester
  reported the control simply missing: it was kept off the categorical
  half by two gates, the editor building its Copy row only where
  GRADUATED bounds exist and the categorized call site passing neither
  the targets nor the callback.) The copy takes the style, the ramp,
  the Reverse, the per-value colours, the catch-all and the class
  source, which travels as a FILE REFERENCE so the two elements go on
  agreeing -- accepting that a moved file then costs two elements
  rather than one.
  FOUR THINGS NEVER TRAVEL, and the first is the only one that would
  cost a map. THE VARIABLE: carrying it makes the target a duplicate
  of the source, and a map whose whole purpose is reading several
  variables against each other quietly loses one. THE OPACITY, as
  through every other change of scheme. THE OUTLINE, which decides
  whether tile EDGES are drawn and is not a colour. And THE RECORDS OF
  THE STYLE THE ROW IS NOT WEARING -- pinned bounds, breaks, floor,
  ceiling, the remembered class count, the single colour -- kept, and
  kept SILENTLY, so a row switched back to a quantitative style finds
  its work where it left it.
  VALUES THE RECEIVING COLUMN DOES NOT HOLD ARE KEPT rather than
  dropped, on the graduated precedent that a copy reproduces a
  classification and a silently shortened one does not. THE CASE IT IS
  REALLY FOR is a column typed numeric that is genuinely categorical
  -- land-cover codes and the like -- where the colours land because
  `_category_colours` keys on the value as TEXT.

### C-42 — A NEW REGION DATASET: THE RULE IS THE COLUMN NAME

<sub>Cut from `CLAUDE.md`, lines 1978–2008 of the
2026-09-05 revision.</sub>

- **A NEW REGION DATASET: THE RULE IS THE COLUMN NAME.** (Same day.)
  Changing the region layer KEEPS an element's setup where the new
  data has a column of that name and DROPS it where it does not, the
  element then auto-assigning as the recovery rule of 2026-08-15
  already says for a layer whose file has moved. The records
  themselves are left alone, which is free rather than sloppy: they
  are keyed by tile id AND FIELD, so a setup for an absent column sits
  idle and returns if the user switches back. The ruling governs what
  stays ACTIVE, not what is remembered.
  RECORDED HERE AS MEASURED SOUND, AND MEASURED BROKEN HOURS LATER, at
  every door. The two tests written that afternoon passed and both were
  VACUOUS: their fixture assigned a variable and never touched the
  STYLE chooser, so `_refresh_table` re-derived a quantitative style
  from the new column's type on every switch and nothing was ever
  RETAINED to be wrongly retained. Driven the way a user drives it --
  the style picked through the combo, which is what marks it as
  theirs -- a categorical scheme cut for four land-cover words came to
  rest on a column of areas in square metres and drew a colour for
  each. That is the colleague's report, live while three documents said
  the ground had been measured.
  THERE ARE THREE DOORS, not two, and the third is the one that speaks:
  a column DELETED in QGIS re-points its elements at a surviving column
  and TELLS the user so, which is right, while the scheme rode along
  outside that account. `_adapt_to_the_layer` re-defaults the row
  before the table is rebuilt, so the guard in `_refresh_table` cannot
  see it -- one ruling, three doors, and the third needs its own
  answer. All three are closed and each carries a registered test.
  WHAT THE EARLIER READING GOT RIGHT is the shape of its own
  correction: a fixture that leaves the plugin to DERIVE the thing
  under test measures the derivation. Written up in docs/TESTING.md
  beside the conditional-assertion fault it arrived with.

### C-43 — THE GROUP CHOOSER IS THE ONLY DOOR TO A NEW GROUP

<sub>Cut from `CLAUDE.md`, lines 2387–2410 of the
2026-09-05 revision.</sub>

- **THE GROUP CHOOSER IS THE ONLY DOOR TO A NEW GROUP.** (Maintainer's
  decision, 2026-08-29; built 2026-08-30.) Two controls armed one
  fact: the chooser's "Create new" entry, which is ONE-SHOT, and a
  "Create as new group" checkbox on Map options, which was a STANDING
  preference read at every landing. Nothing on screen said which was
  which, and the READERS DISAGREED -- five sites asked only the
  checkbox, one only the flag, and exactly one asked both, that one
  only since ledger row 36 of 2026-08-28, where the chooser went on
  describing a landing that would not happen.
  THE REASONING IS ABOUT THE INTERFACE RATHER THAN THE MECHANISM, and
  that is why it settles rather than patches: a control two panels
  from the chooser can never make the boundary between "once" and
  "always" read clearly, and a boundary that will never be clear is
  one nobody should have to hold in their head. It composes with
  ruling 1 of 2026-08-25, which made the group the unit of work and
  gave the chooser the job of saying where a run lands; a standing
  checkbox elsewhere was a second rule about the same fact.
  THE STANDING "ALWAYS NEW" BEHAVIOUR WENT WITH IT, deliberately.
  Asking for a second map is an act you perform when you want one.
  AND THE LANDING NEEDED A DELETION RATHER THAN A REWIRING, because
  `force_new` already read the flag as one of its four terms. The
  cost was in the SUITE, as predicted: twenty-four sites, eleven
  catalogue anchors of which two were retired outright, and two
  committed probes.

### C-44 — THREE TABS ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A BOX THAT STARTS...

<sub>Cut from `CLAUDE.md`, lines 2412–2435 of the
2026-09-05 revision.</sub>

- **THREE TABS ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A
  BOX THAT STARTS UNTICKED.** (Maintainer's ruling, 2026-08-30.)
  Messages, Topology and Legend are gated by an "Experimental
  features" checkbox on Map options -- the third tab, which is where
  the ruling put it. Until it is ticked the tabs cannot be activated
  and their titles are greyed; `QTabWidget.setTabEnabled` is both
  halves of that in one call, so "greyed" and "not activatable"
  cannot come apart later.
  THE TABS STAY VISIBLE rather than being removed: somebody should be
  able to see that there is more here and what ticking the box would
  give them.
  IT IS A PREFERENCE ABOUT THE PLUGIN, NOT A FACT ABOUT A MAP, so it
  does not go in a group's working state -- which would carry one
  person's appetite for experiments into another person's project
  through a saved file. That is the two-relationships framing in this
  file applied to a control.
  THE MESSAGES TAB SHIPPED FIRST, in 0.24.4 on the maintainer's ask
  of the same day. Everything the plugin has said this session, newest
  first, with the ANSWER beside any question -- because half this
  plugin's modals decide something, and a log holding the question
  alone describes a decision nobody can reconstruct. It exists because
  the message bar and the modals are two stores nothing brought
  together, which is harness fault eleven of this project's own record
  met from the user's side.

### C-45 — A SAVE PRESSED WHILE A RE-TILE IS COMING IS KEPT, NOT REFUSED

<sub>Cut from `CLAUDE.md`, lines 2485–2513 of the
2026-09-05 revision.</sub>

- **A SAVE PRESSED WHILE A RE-TILE IS COMING IS KEPT, NOT REFUSED.**
  (Maintainer's ruling, 2026-08-29, overruling a repair of the day
  before.) With live update on, changing the design arms the live
  timer, and a press inside that window used to write the map on
  screen -- the one the person had just changed away from. Ledger row
  54 closed that by REFUSING the press in words, on the reasoning that
  a press the dialog remembers is a promise about a map nobody has
  seen yet, and that the run lands in under a second.
  THE MAINTAINER'S REASON IS ONE NO MEASUREMENT HERE WOULD HAVE
  PRODUCED, and it generalises past this control: **most people will
  not read the sentence.** A refusal that depends on being read is a
  save that quietly did not happen, and the person closes QGIS
  believing their map is on disk. So the press is KEPT, the notice
  says the map will be saved after it is redrawn rather than asking
  for a second press, and `_honour_a_queued_save` performs it once the
  new map has landed.
  ASK OF ANY REFUSAL WHAT IT COSTS THE PERSON WHO DOES NOT READ IT.
  Where the answer is work lost, the refusal is the wrong shape and
  the act belongs deferred and completed; where it is a WRONG MAP
  drawn, a refusal is still right. The in-flight refusal is unchanged
  for exactly that reason -- what is on screen mid-run is the PREVIOUS
  map, so writing it answers a different question from the one the
  press asked, silently, over the file they have just named.
  THE MECHANISM IS THE THIRD DEFERRED KIND, and it obeys the rule the
  queued-press entry ends with: consumed by taking and clearing the
  intent at the point of use, never handed to a gated path, and asked
  from three places because a landing alone cannot cover a run that
  DECLINES -- the live tick has ten gates and `_generate` eight.
  Account in MAINTAINING.md under "Three queues".

### C-46 — AND THE SECOND ONE FOUND A COLLISION BETWEEN TWO SETTLED RULES

<sub>Cut from `CLAUDE.md`, lines 2515–2540 of the
2026-09-05 revision.</sub>

- **AND THE SECOND ONE FOUND A COLLISION BETWEEN TWO SETTLED RULES.**
  (2026-08-27, the run over the three rulings.)
  `test_a_ramp_you_are_offered_is_the_ramp_you_get` went red on its
  second half: a row turned categorical kept `YlGn`, "a ramp chosen
  for numbers". Neither the rule nor the code was wrong. The older
  rule is that a row ARRIVING in Categorized swaps a sequential ramp
  away, because a sequential ramp over categories is a cartographic
  error nobody asked for; ruling 4 of the same day remembers a ramp
  under THE MODE THE ROW IS IN. The test's own first half leaves row 1
  wearing YlGn as a CATEGORIZED row -- deliberately, that being its
  subject -- so under the ruling that row now remembers YlGn as its
  categorical choice, and the flip hands it back. The ruling's wording
  anticipates precisely this: it "would hand that back on the next
  flip -- and that is now the wanted answer, because the row wore it
  there and nobody took it off".
  WHAT TELLS THE TWO APART IS WHETHER THE ROW HAS A MEMORY FOR THE
  MODE IT IS ENTERING, and that sentence is the whole of the
  reconciliation. The second half is staged on a row that has never
  been categorized now, and both answers are asserted in the same
  test, because they differ by one thing only and a reader meeting one
  would take it for the whole rule.
  THE GENERAL FORM, which this file already carries from the other
  side: when a ruling changes what is REMEMBERED, look for the rules
  that DERIVE the same thing, and expect a test that stages the
  remembering to be the one that fails. Its fixture is no longer
  staging what its docstring names.

### C-47 — A FULL SUITE FINDS WHAT A TARGETED RUN CANNOT REACH, AND THE FIRST ONE HERE FOUND A...

<sub>Cut from `CLAUDE.md`, lines 2542–2557 of the
2026-09-05 revision.</sub>

- **A FULL SUITE FINDS WHAT A TARGETED RUN CANNOT REACH, AND THE FIRST
  ONE HERE FOUND A DOCUMENT.** (2026-08-27.) The first full suite ever
  to complete on `for-0.24.4/copy-select-all` returned 636 passed and
  1 failed, and the failure was `test_the_documents_numbers_match_the_
  code`: the element ceiling had split in two the previous day while
  the user guide went on naming one, so a tiling user was being told a
  limit an order of magnitude under what the plugin would draw for
  them. No test aimed at the ceiling work could have found it, because
  none of them reads the guide.
  TWO INSTRUMENTS EXITED 0 WITH THE ANSWER INSIDE THEM the same hour:
  the suite itself, which reports a failure and still exits clean
  through its runner, and the mutation catalogue, which REFUSED to
  judge eight entries for want of `QGIS_PY` and printed the command
  that fixes it. Both times the verdict was in the output and not in
  the status, which is this file's own standing rule met twice in one
  session.

### C-48 — WHEN YOU CHANGE A NAME OR A FORMAT, FIND EVERY READER -- BY SYMBOL AS WELL AS BY LITERAL

<sub>Cut from `CLAUDE.md`, lines 2586–2602 of the
2026-09-05 revision.</sub>

- **WHEN YOU CHANGE A NAME OR A FORMAT, FIND EVERY READER -- BY SYMBOL
  AS WELL AS BY LITERAL.** (2026-08-26, twice within an hour, on one
  small change.) Naming output groups for their dataset was swept
  through the suite by grepping the string "WeavingSpace tiles", which
  found six sites and mended them; the RELEASE GATE then failed on two
  more that pin the same name through `GROUP_BASE_NAME`. A name with a
  symbol has two spellings in a tree and a search for one is a search
  for half.
  THE OTHER FACE IS DECOMPOSITION. The group chooser composes its
  label as `<name> — <dataset>`, and six places in the suite recovered
  the name by splitting on that separator -- correct until the
  separator moved INSIDE the name, after which every group answered
  "WeavingSpace tiles". They share one helper now.
  SO ASK BOTH QUESTIONS: who writes this string, and who takes it
  apart? This file already says to grep every reader of a custom
  property and every route into a handler; a name and a label are the
  same rule wearing text.

### C-49 — A STAMP TAKEN AWAY FROM A LANDING MAY CARRY ONLY WHAT A LANDING DECIDED

<sub>Cut from `CLAUDE.md`, lines 2653–2677 of the
2026-09-05 revision.</sub>

- **A STAMP TAKEN AWAY FROM A LANDING MAY CARRY ONLY WHAT A LANDING
  DECIDED.** (2026-08-26, ledger rows 55-57, three regressions in one
  mechanism.) `_stamp_working_state` takes the design, the output path
  and the region from the launch snapshot when it is given one and
  from the LIVE CONTROLS when it is not -- which was harmless while
  landings were the only writers, and became three defects the day
  round nine added two writers that never stand at a landing. Move the
  design controls after a map lands and one adopted dock edit made the
  group claim a design its layers were never drawn at; switch the
  chooser and the group was filed under a dataset it was not made
  from, which is the fact the landing's refusal and the group binding
  both read. Those three keys are CARRIED from the record already on
  the group now, and only a landing may move them.
  TWO MORE CONDITIONS BELONG TO THE SWITCH-OUT STAMP ITSELF, and both
  are about attribution rather than timing. A dataset that has been
  REMOVED leaves nothing to stamp: the table is blank because its
  fields went with it -- a blank the plugin imposed -- and this
  handler runs for every dialog whose combo re-emits, including one
  the user has closed, so it wrote that blank over a good record and
  the next dialog opened in that project met a table describing
  nothing. And the group must be the OUTGOING DATASET'S OWN MAP, asked
  of the layers' stamps: `_group_of_our_layers` answers where this
  dialog's layers are, which is where the last run landed.
  ASK OF ANY WRITER THAT COPIES A RECORD: which moment is each field
  about, and does this writer stand at that moment?

### C-50 — A STRING THAT CARRIES A PATH INSIDE IT IS A PATH

<sub>Cut from `CLAUDE.md`, lines 2694–2717 of the
2026-09-05 revision.</sub>

- **A STRING THAT CARRIES A PATH INSIDE IT IS A PATH.** (2026-08-26,
  the Windows red of six CI rounds.) `same_destination` exists
  because one file has two spellings -- Windows short names, case
  folding, separators -- and it was applied faithfully to output
  PATHS while seven sites went on comparing LAYER SOURCES with `==`.
  A source only looks like an opaque token; it is a path plus
  `|layername=`, and a project save respells the path half. So a
  reopened project's own output group read as ANOTHER dataset's, and
  the guard protecting a kept result refused the ordinary recovery
  run -- through a MODAL, so the message bar stayed empty and the
  user met a Generate that wrote nothing and said nothing.
  `same_source` is the one owner now: file half through
  `same_destination`, tail case-folded.
  AN EIGHTH SITE WAS FOUND THE SAME NIGHT, and how it survived the
  sweep is the lesson. The seven were all a STAMP compared with a
  STAMP; the eighth compares a stamp with the SOURCE OF THE LAYER IN
  FORCE, in the gate that decides whether a saved record's pins and
  hand-picked colours may come home. Same question, same boundary, a
  different pair of operands -- so a search for the first shape found
  nothing, and three Windows-only reds turned on it. WHEN YOU FIND A
  FAMILY, SWEEP FOR THE QUESTION RATHER THAN FOR THE PHRASING.
  ASK OF ANY IDENTIFIER WHETHER A FILESYSTEM EVER TOUCHED IT. Where
  it did, the string that comes back is not the string that went
  out, and `==` is a bug waiting for the platform that shows it.

### C-51 — ATTRIBUTION BEATS DELTA, AND THREE NARROW GUARDS ARE THE SIGNAL TO STOP PATCHING ROUTES

<sub>Cut from `CLAUDE.md`, lines 2719–2739 of the
2026-09-05 revision.</sub>

- **ATTRIBUTION BEATS DELTA, AND THREE NARROW GUARDS ARE THE SIGNAL
  TO STOP PATCHING ROUTES.** (2026-08-26, ledger row 48, and it is
  the sharpest thing the bulletproofing round taught.) The
  categorized adoption walk asked what CHANGED -- adopt any colour
  differing from what the plugin would seed NOW -- and a landing that
  keeps a renderer over an unreadable class source makes that
  question lie: `expected` falls back to automatic colours while the
  map honestly wears the template, so the template's own colours were
  adopted as a person's hand-picks and outranked the template
  forever. THREE successive fixes each closed one route and left
  another: a skip in the landing's re-examination, a skip in the
  deferred-adoption replay, then a colour-precise marker -- and the
  reworked test caught a fresh route past every one. What ended it
  was asking the question the state can answer at ANY moment:
  `_painted_categories` records what the plugin itself painted, the
  categorical twin of `_painted_ladders`, so the walk asks WHOSE
  colour this is. All three narrow guards were then deleted.
  THE RULE: when the third narrow guard leaks, stop asking which
  route is missing and ask whether the question is right. This file
  already says the same about `_table_id_colours`, which was wrong
  six times until it stopped enumerating and read what the map draws.

### C-52 — A GUARD ADDED TO ONE DOOR BELONGS AT EVERY DOOR INTO THE SAME ROOM

<sub>Cut from `CLAUDE.md`, lines 2756–2791 of the
2026-09-05 revision.</sub>

- **A GUARD ADDED TO ONE DOOR BELONGS AT EVERY DOOR INTO THE SAME
  ROOM.** (2026-08-25, and it is the sharpest thing the group-unit
  build taught.) A regression showed that taking a group over while a
  run was IN FLIGHT erased the evidence the landing was about to read,
  so `self._task is not None` was added to `_bind_group_to_dataset`.
  Two other methods reach the same work -- `_on_group_chosen` and
  `_resume_from_gpkg` -- and neither got it, because the fix was made
  where the failure was REPORTED rather than where the behaviour
  lives. A hunt found the asymmetry within the hour, working backwards
  from harm.
  ITS PREDICTED HARM WAS MEASURED FALSE ON 2026-08-26, and correcting
  that here matters more than the tidiness of the rule. The hunt
  reasoned that picking a group mid-run would repoint the records the
  landing reads as `old_ids` and that the run would then remove the
  layers of the group just switched TO. The first half is true and the
  second is not: driven both ways -- another dataset's group, and the
  same dataset's other group, where the region stamps cannot tell them
  apart -- every layer survived, because the landing's own refusal to
  write over a map made from another dataset forces a new group and
  empties `old_ids` on the way past. `tools/probes/a_group_chosen_mid_
  run_deletes_its_map.py` is that measurement, and it is committed so
  nobody re-derives it.
  THE RULE IS UNTOUCHED BY THAT, and it is worth saying why rather
  than quietly rewriting the entry. The asymmetry is real, and it is
  held REDUNDANTLY rather than harmlessly -- exactly the state this
  file records from the other side, where an omission ruled benign
  went live three hours after a fix removed the accident that was
  hiding it. A guard that is missing and currently costs nothing is a
  countdown, not a defence.
  THE HABIT: when a guard goes in, grep for every caller of the thing
  it protects and ask which of them can be in the same state. This
  project already says the same about signals ("grep for the other
  routes into the same handler"), about clear sites ("enumerate what a
  clear site LEAVES"), and about pairs; this is the same rule wearing
  a fourth set of clothes, and the fourth time is the one that should
  make it a reflex.

### C-53 — A HARM NAMED BY READING IS A HYPOTHESIS, EXACTLY LIKE A SITE

<sub>Cut from `CLAUDE.md`, lines 2793–2815 of the
2026-09-05 revision.</sub>

- **A HARM NAMED BY READING IS A HYPOTHESIS, EXACTLY LIKE A SITE.**
  (2026-08-26, judging nine hunt claims.) This file already says that
  a location reasoned out of the source reads exactly like one
  somebody proved. Three of those nine described the code CORRECTLY --
  a guard really was missing from two of three doors, an embedded
  region really does load under a source string the gate can never
  match, both measured -- and not one of them costs a user anything,
  because in every case a second mechanism answers first.
  THE TELL IS THAT THE CLAIM STOPS AT THE LINE. A guard is missing:
  therefore what? Walk it to the end. Where the answer really is a map
  deleted, driving it says so unmistakably -- four layers of one
  dataset's tiles removed by a run on another, the same day. Where you
  cannot reach a loss, the honest finding is that the behaviour is
  HELD REDUNDANTLY, which names what would have to move before the
  asymmetry starts costing something; this project has already watched
  a masked omission go live three hours after the mask was removed.
  AND CHECK THE CLAIM'S DIRECTION, not only its subject. The one
  finding that mattered most was reported the wrong way round: a
  record and a layer stamp disagreed about which dataset a map came
  from, and the claim named the record as the wrong half where the
  record was right. Following the reading rather than the measurement
  would have moved the field that was already correct. Of one fact
  written twice, ask which of the two writers had a REASON.

### C-54 — A GATE CAN BE SATISFIED BY A SENTENCE DENYING IT

<sub>Cut from `CLAUDE.md`, lines 2817–2834 of the
2026-09-05 revision.</sub>

- **A GATE CAN BE SATISFIED BY A SENTENCE DENYING IT.** (2026-08-26.)
  `check_roadmap` is the first stage of every release and refuses a
  candidate while the version's section lists work; it decided that by
  searching for the words "nothing outstanding". The section carried,
  honestly, "the reason this section does not yet say 'nothing
  outstanding'" -- followed by a page of owed work -- and the gate read
  the denial as the declaration and cleared the tree.
  A QUOTED PHRASE IS A MENTION, NOT A STATEMENT, and stripping quoted
  spans before looking is what keeps the phrase prose-first (the
  reason it was chosen over a marker) while making it impossible to
  satisfy by discussing it. The general form joins "a check that can
  only confirm is not a check": when a gate reads PROSE for a
  decision, ask what the document says ABOUT that prose, because a
  file that explains its own conventions will quote them.
  It had never had a test. It has one now, which plants the exact
  sentence in all three quoting styles AND requires a plain
  declaration to still pass, since a gate nothing can satisfy is as
  useless as one anything can.

### C-55 — PRESENCE IS NOT ORDER, AND A CALL PUT BACK IN THE WRONG PLACE IS WORSE THAN ONE...

<sub>Cut from `CLAUDE.md`, lines 2836–2865 of the
2026-09-05 revision.</sub>

- **PRESENCE IS NOT ORDER, AND A CALL PUT BACK IN THE WRONG PLACE IS
  WORSE THAN ONE STILL MISSING.** (2026-08-26, and FOUR hunts of eight
  found it independently -- the most this method has ever converged
  here.) `_resume_from_gpkg`'s take-over branch was missing
  `_recover_the_source`; the repair added it AFTER
  `_apply_working_state`, where the twin calls it BEFORE and says why
  at its own call site: a variable cannot be restored to a column the
  region layer in force does not have.
  FOUR CONSEQUENCES, one per hunt. Every element's variable re-derived
  against the other dataset's columns, so the table described a map
  the layers did not draw. `same_data` computed against the stale
  chooser, so the pins and the categorical colours were skipped
  outright and a pinned ladder came back re-derived. The group then
  stamped with that loss. And `_take_over_group` adopting the resumed
  layers' stamps while `_memory_layer_id` still named the OTHER
  dataset, writing one map's hand-picked value strings into that
  dataset's bank and its GeoPackage -- ruling 8's cross-dataset leak,
  reached from a direction it was not written for.
  THE REPAIR TURNED VISIBLY WRONG INTO INVISIBLY WRONG, which is one
  hunt's phrase and the reason this is a rule rather than a ledger
  row: before it, the chooser sat on the wrong dataset where a person
  could see it; after it, every symptom moved inside the records.
  THE TELL: WHEN A TWIN'S CALL SITE CARRIES A COMMENT, THAT COMMENT IS
  USUALLY ABOUT THE POSITION. Copying the call and not the comment
  copies the half that does not encode the reasoning. This file
  already says to check a fix's ORDER against its twin rather than
  merely that the line is present; what is new is that the check
  survives being applied by somebody who knows the rule -- it was
  broken here in the same hour by the same hand that had just quoted
  it.

### C-56 — BEFORE CLEARING ON AN ABSENCE, ASK WHAT MAKES THE RECORD ABSENT

<sub>Cut from `CLAUDE.md`, lines 2867–2903 of the
2026-09-05 revision.</sub>

- **BEFORE CLEARING ON AN ABSENCE, ASK WHAT MAKES THE RECORD ABSENT.**
  (Same day, and it is the other half of the same evening.) A restore
  was taught to CLEAR a record where the incoming one is silent about
  it -- the cure for a real defect three hunts had reported, where one
  output group's colours rode onto another. But `_assignments` reports
  the pins, the hand-picked class colours and the ramp window as empty
  for ANY ROW NOT WEARING GRADUATED, and the categorical colours as
  empty for any row not wearing Categorized. So a record is silent
  about them whenever the element is merely on another style, which is
  not the same claim as "this group has none" -- and the clearing
  destroyed a pinned bound belonging to an element somebody had
  switched to categories, stamping its absence so a reopen could not
  recover it. That is the ruling of 2026-08-20 broken by the fix for
  a different one.
  SO ENUMERATE THE READERS THAT CAN PRODUCE THE ABSENCE. Here there
  were two: a person who chose nothing, and a mode that cannot carry
  the thing at all. This file already asks what an absent key MEANS
  when a guard READS one; deleting on that absence needs the same
  question asked harder.
  AND THE FIX WAS INERT UNTIL THE WHITELIST KNEW ABOUT IT.
  `WORKING_STATE_ELEMENT` is the record's real definition, `mode` was
  not in it, so the gate read None and cleared nothing whatever. Two
  tests going red is how that was found. WIDEN THE WHITELIST IN THE
  SAME COMMIT AS THE CODE THAT READS IT -- said here for the third
  time, after `_adopt_dock_bounds` and the copy.
  A FOURTH ON 2026-08-30, and the first where the rule was applied
  BEFORE the defect rather than after it: the topology edit list is
  not a widget, so it rides neither whitelist's table and is written
  and read by hand -- `_capture_working_state` and
  `_restore_recorded_topology_edits` went in together, with a test
  that sends the record through `json.dumps` because that is what the
  GeoPackage does to it, and a catalogue entry standing on the write
  and the read SEPARATELY. Two entries rather than one deliberately:
  either half alone leaves a record that is faithful in the file and
  dropped in silence on the way back, and an entry that can be
  satisfied by its sibling is an entry that reports `caught` about
  nothing.

### C-57 — WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE THAT ALREADY HELD...

<sub>Cut from `CLAUDE.md`, lines 2905–2923 of the
2026-09-05 revision.</sub>

- **WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE
  THAT ALREADY HELD THAT FACT.** (Same day, the round's last two
  findings, and the shape this project meets most often.) A restyle
  was taught to write the GROUP's record, with a comment arguing
  exactly why. The FILE's record was given its write hours later, by a
  different commit, on the landing path alone -- so it inherited the
  gap the first write had just closed: the file's STYLES were updated
  by a restyle and its RECORD was not, and a colleague opening that
  GeoPackage without the project resumed a design the user had
  abandoned, their first Generate repainting the map back to it. The
  file disagreed with itself.
  AND THE SECOND STORE IS SOMETIMES A WIDGET. A class source restored
  into `_class_choices` by a group switch was read by nobody, because
  `_sync_row` repopulated the combo without re-selecting it from the
  record -- and `_assignments` reads the WIDGET, so the next rebuild
  wrote the stale answer back over the restore. Its neighbour in the
  same table had been given that exact fix eight days earlier.
  The list of stores is short and never empty. It is the one nobody is
  looking at that costs the map.

### C-58 — A RECORD ASSEMBLED FROM TWO MOMENTS MUST SAY WHICH MOMENT EACH FIELD CAME FROM

<sub>Cut from `CLAUDE.md`, lines 2925–2952 of the
2026-09-05 revision.</sub>

- **A RECORD ASSEMBLED FROM TWO MOMENTS MUST SAY WHICH MOMENT EACH
  FIELD CAME FROM.** (Same day.) The working state deliberately takes
  its DESIGN from the launch snapshot and its ELEMENTS live, and both
  halves are right for good reasons written at the code.
  MEASURED ON 2026-08-26, AND THE FAULT WAS THE OTHER WAY ROUND. This
  entry said `region` travelled with the design half and therefore
  filed a new dataset's hand-picked colours under the old dataset's
  source. Driven -- switch the region layer mid-run, then read both
  stores -- the RECORD was right: it takes `region` from the launch
  snapshot, and the launch snapshot is what the tiles were drawn from.
  What was wrong was the second, quieter writer of the same fact:
  `_add_output_layers` read `weavingspace_region` off the region
  CHOOSER as the run landed, so every output layer claimed whichever
  dataset the user happened to be looking at. A's tiles came out
  stamped as B's; the chooser then labelled A's map with B's name, the
  binding handed that group to B, and the refusal whose whole job is
  to stop a landing writing over another dataset's map read the same
  wrong stamp and let a run on B replace it. Four of four layers
  destroyed. It is asked of `source_layer` now -- the layer this run
  tiled, which the landing has held as a parameter all along.
  SO THE RULE STANDS AND ITS EVIDENCE IS DIFFERENT. Ask of any record
  built from two readings: for each field, WHICH reading is it about?
  A field that describes the DATA belongs with the data's moment, and
  one that describes the DESIGN belongs with the design's. And where
  one fact is written TWICE, ask which of the two writers has a
  reason -- the hunt that reported this named the wrong half, and
  following the reading rather than the measurement would have moved
  the field that was already correct.

### C-59 — THE SIZE GUARD ASKS; ONLY WHAT IS NOT A SIZE IS REFUSED

<sub>Cut from `CLAUDE.md`, lines 2954–2987 of the
2026-09-05 revision.</sub>

- **THE SIZE GUARD ASKS; ONLY WHAT IS NOT A SIZE IS REFUSED.**
  (Maintainer's ruling, 2026-08-25: "Warning not absolute. Find a
  different approach to sentinel if appropriate.") Above
  `MAX_TILES_CONFIRM` a run is confirmed in ordinary words; above
  `MAX_TILES_HARD` the SAME question is put in stronger ones -- this
  may use all the computer's memory, QGIS may stop responding, save
  your project first -- with the safe button as the default, on the
  dependency-consent precedent. One question whose wording escalates
  by band, rather than two gates, because a second gate saying no at a
  second number is the arrangement that was already wrong once.
  WHAT THE REFUSAL STOOD ON was a comment claiming the run would
  exhaust memory and kill QGIS: a figure NOTHING IN THIS REPOSITORY
  MEASURES, and one the maintainer's own argument disposes of --
  different machines have different maximums, and different designs
  have different needs at the same tile count. It had already been
  wrong in the expensive direction, refusing a map the library renders
  in five seconds (ledger row 23, 2026-08-19).
  THE SENTINEL IS WHY IT COULD NOT SIMPLY SOFTEN, and this is the part
  that generalises. `MAX_TILES_HARD + 1` was ALSO the answer for two
  cases that are not about size: a unit whose vectors are degenerate,
  so the design does not repeat across the plane, and an estimate that
  comes back non-finite, which is what a layer with no CRS produces.
  Sharing a value meant sharing a SENTENCE -- both told somebody to
  try a larger spacing, which helps neither -- and it meant that
  softening the ceiling would turn a broken design into something a
  user clicks straight past. They are `bridge.UNTILEABLE` and
  `bridge.UNCOUNTABLE` now, NEGATIVE on purpose: every gate here asks
  `est > <ceiling>`, so a sentinel smaller than every ceiling cannot
  be waved through by a comparison somebody forgot to widen. It has to
  be handled explicitly or it does nothing at all.
  THE GENERAL FORM: when one value stands for several different
  answers, softening the treatment of any of them softens all of them.
  Ask what else shares a sentinel before changing what a threshold
  means.

### C-60 — A BLANK THE PLUGIN IMPOSED IS NOT A CHOICE THE USER MADE

<sub>Cut from `CLAUDE.md`, lines 2989–3010 of the
2026-09-05 revision.</sub>

- **A BLANK THE PLUGIN IMPOSED IS NOT A CHOICE THE USER MADE.** An
  element left on "---" stays unassigned through rebuilds, because
  cycling a default back in would undo a deliberate switching-off. But
  a table built when NO FIELDS were on offer leaves every row blank
  for a reason that has nothing to do with anybody's intent, and
  honouring those blanks is how a plugin opened before its data ends
  up refusing to draw and blaming the user for not assigning a
  variable -- the field report of 2026-08-15. `_fieldless_build`
  tells the two apart.
  THE SAME ROAD REACHES RECOVERY, which is where the rule had to be
  decided rather than inferred. A region layer whose file has moved
  loses its elements' variables; when the user then points the chooser
  at a live layer, the elements AUTO-ASSIGN as they would on any other
  day, rather than staying blank. That reverses the contract
  `test_a_project_whose_region_layer_has_moved` had held since it was
  written, and the test said so itself rather than quietly bending --
  it required the change to be re-decided, and the maintainer decided
  it on 2026-08-15. What the test now guards is sharper than what it
  gave up: the assignments must name columns THE NEW LAYER HAS, since
  carrying the lost layer's columns onto different data is the real
  harm nearby. Catalogue entry
  `a-blank-a-failure-imposed-is-not-a-choice`.

### C-61 — A constant numeric column gets ONE class, and a notice

<sub>Cut from `CLAUDE.md`, lines 3029–3100 of the
2026-09-05 revision.</sub>

- **A constant numeric column gets ONE class, and a notice.** Asked
  for five classes over a column that is 7 everywhere, QGIS returns
  five, all reading "7 - 7" in five different colours. The map was
  never wrong; the legend was, and the legend is what a reader trusts.
  `make_graduated_renderer` collapses to k=1 and the dialog reports
  it -- UNLESS the element is pinned, for which see the ruling below.
  (User instruction, 2026-08-09.)
  **THE GENERAL FORM WAS WITHDRAWN ON 2026-08-16, AND SO WAS THE
  NUDGE THAT BRIEFLY REPLACED IT. Read this before the history below
  it.** Reducing k re-samples
  the ramp: class i takes `ramp.color(i/(k-1))`, so a shorter ladder
  spreads its survivors across the whole ramp and every colour moves
  with nobody choosing to move it. Measured that day, five asked over
  four distinct values on Reds: the map drew the FOUR-class ladder
  exactly, and neither middle colour was one the five-class ladder
  would have used. It is also unstable -- a column that gains a value
  later re-colours every class -- which is the thing
  one-colour-one-meaning exists to forbid. The maintainer's rule is
  that an empty class is INVISIBLE, NOT DELETED.
  WHAT CURED THE ORIGINAL SYMPTOM WAS TRIED AND IS ALSO GONE, and this
  paragraph described it as current until 2026-08-18.
  `bridge._nudge_off_shared_bounds` moved every finite-width range's
  upper bound down by one unit in the last place where the classifier
  had returned DEGENERATE ranges, so a value on a shared boundary fell
  into the degenerate range that means exactly it. It was withdrawn
  hours after the reduction was, in the same afternoon, and the
  function no longer exists -- `unworn_classes` says "the experiment
  is gone" at its own docstring. Measured 2026-08-18 on {10 x8, 20,
  30} at k=5: three degenerate ranges, no bound moved, and 20 lands in
  class 4. The three withdrawn attempts and what each taught are in
  docs/TESTING.md under "Three ways to move a class boundary"; what
  survives is that an empty class is INVISIBLE, NOT DELETED, and that
  emptiness is reported in words.
  A BINDING FILE THAT NAMES A DELETED FUNCTION IS WORSE THAN ONE THAT
  SAYS NOTHING, because it is read as the current design and its
  mechanism looked for. This one contradicted itself: the withdrawal
  was already recorded four hundred lines above.
  IT IS SCOPED, and the scope is the whole safety of it: on ordinary
  data every range has width, nothing is degenerate, and no bound
  moves. Shrinking bounds generally would push any value sitting
  exactly on a break up into the next class, reversing QGIS's
  convention across every classed map for no benefit.
  The ONE-VALUE COLLAPSE survives as a deliberate carve-out
  (maintainer's ruling the same day): five ranges all reading "7 - 7"
  in five colours is a legend claiming variation the data lacks, and
  marking four of them would not cure that.
  A PIN OUTRANKS IT (maintainer's ruling, 2026-08-17, ledger row 43).
  Pinned bounds give a constant column REAL ranges, so the sentence
  the collapse exists to prevent cannot be produced, and the two doors
  into a pinned ladder had disagreed: a copied ladder of -5/10/25/40
  drew five classes while the same bounds as pins drew one, silently,
  with the pin accepted and stamped. `bridge.py` reads
  `if distinct == 1 and not pinned_here`.
  The break values are otherwise QGIS's own, moved by an ulp its label
  formatter rounds away, so the legend still reads "1 - 5", the
  renderer is an ordinary graduated one, and pressing Classify
  restores QGIS's untouched answer.
  **The history of the withdrawn reduction, kept because the first
  attempt at it failed too and the reasons still instruct.**
  Five classes over three distinct values puts two swatches in the
  legend that no tile uses and draws the highest value mid-grey
  (measured 2026-08-13 with a render context); upstream's own
  `_plot_subsetted_gdf` reduces k in exactly that case. It was
  implemented and reverted the same night, because it counted the
  distinct values on the ELEMENT layer, which holds only that
  element's tiles -- so two elements carrying the same variable could
  draw different class counts, and
  `test_metamorphic_variable_permutation` failed at once. What made
  the second attempt work is the entry below: the count and the
  breaks both come from the whole map now, so every element agrees.
  Nineteen tests moved on the first attempt, which is the measure of
  how deep the assumption ran.

### C-62 — ONE COLOUR MEANS ONE THING, wherever it appears — and the rule is about MEANING, not...

<sub>Cut from `CLAUDE.md`, lines 3101–3170 of the
2026-09-05 revision.</sub>

- **ONE COLOUR MEANS ONE THING, wherever it appears — and the rule is
  about MEANING, not about breaks.** That wording matters and cost a
  year: it was written down as being about class BREAKS, so when the
  graduated half was fixed on 2026-08-14 nobody looked at the
  categorized half, which had the identical fault and had been
  shipping since 0.23.0. Categorical colours follow ListedColormap
  sampling — code/(k-1) through int(x * N) — so the NUMBER of
  categories decides which colours are drawn, and a value one element
  happens not to contain re-colours everything after it. Measured
  2026-08-15: four elements on one column and one tab10 ramp, three
  finding six values and the fourth five, so `#1f77b4` meant 'bare' on
  three elements and 'crops' on the fourth. Settled by `/grill-me` the
  same day. If a rule here names a mechanism, ask what it is FOR
  before deciding what it covers.
  Both halves work the same way: the whole map's values decide, the
  element's own values are what it draws. A graduated element wears
  breaks cut once from the region; a categorical element takes each
  value's colour from that value's position in the region's sorted
  list while carrying ONLY the categories it actually holds — listing
  a value no tile of it draws would tell a reader something false
  about that element. The Classes cell on a categorized row reports
  what its own element draws, so rows sharing a column may read 6, 6,
  6, 5 and all four are true; no notice is raised when they differ,
  because elements differ routinely and a warning that fires
  constantly is one people learn to ignore. HAND-PICKED colours stay
  per element: what this rule forbids is a colour shifting with
  nobody choosing it, and a hand-pick is a person choosing. A
  reopened project is trusted rather than repainted, so a project
  saved before this keeps its old colours until something re-seeds.
  Class breaks
  are cut ONCE, from the region layer's values, and every element
  carrying that column wears them. Until 2026-08-14 they were cut
  from each ELEMENT layer, which holds only that element's tiles:
  measured on QGIS 4.0.3 at n=12 with k=5 and no reduction involved,
  four elements carrying one variable produced four different
  legends (element a's second class ran 3.4-14.0 where element c's
  ran 4.0-13.6), so one colour meant four different numbers on a map
  whose whole purpose is reading elements against each other. It
  survived because the standard fixture asks for more classes than it
  has distinct values, which collapses quantile breaks onto the
  values themselves and makes elements agree by accident.
  This DEPARTS from upstream, which classifies each element's subset
  separately, and the departure is deliberate under the rule that the
  plugin may have its own ideas where they fit this kind of map.
  Three consequences to keep straight. The user's region layer is
  never filtered for it: the null workaround hides rows, so the
  values are copied into a geometry-less scratch layer the plugin
  owns (`bridge.classification_source`), built once per column rather
  than once per element. Unclassed rides the same rule, its fifty
  steps spanning the whole column's range rather than one element's.
  And the reference comparison stays a real differential because
  `TiledMap.render` accepts the same breaks through
  `classification_kwds` -- computed there by mapclassify over the
  region, never read off our renderers -- except where a case maps
  DIFFERENT columns to different elements, since those kwargs are
  broadcast to every element and one set of bins cannot be right for
  all of them. Guarded by
  `test_one_variable_gets_one_legend_wherever_it_appears`.
  **PINNING IS AN EXCEPTION TO THIS RULE, and the maintainer decided
  so deliberately.** A pinned bound moves the breaks on the element
  that carries it, so a colour on that element can stop meaning the
  numbers it means elsewhere -- which is precisely what the rule
  above forbids when nobody chose it. The difference is that
  somebody did choose it. A pin is a person saying "this break is
  mine", exactly as a hand-picked colour is, and the rule has always
  been about a colour shifting with NO ONE deciding. So a pin is not
  a hole in one-colour-one-meaning; it is the same carve-out as a
  hand-pick, arriving through a different control. Read the rule as:
  the plugin never moves a meaning on its own, and a person may.
  (Maintainer's ruling, 2026-08-15.)

### C-63 — CLASS BOUNDS A PERSON SET, and the record that holds them

<sub>Cut from `CLAUDE.md`, lines 3171–3253 of the
2026-09-05 revision.</sub>

- **CLASS BOUNDS A PERSON SET, and the record that holds them.**
  Added 0.24.3, settled by `/grill-me`. A user may PIN the first
  and/or last class and type its inner bound: the samples inside a
  pinned class leave the pool, the scheme cuts the row's count minus
  one class per pin, and the pinned classes are put back around the
  result with the outermost computed edge SNAPPED to the pin so the
  ladder has no gap. Done by extending the subset string
  `make_graduated_renderer` already sets and restores for nulls, so
  QGIS keeps deciding every break we do not pin. A user may also COPY
  a whole classification to another element, which is every boundary
  pinned at once and shares the same record.
  **That record holds two things and they are not the same claim**:
  the boundary VALUES a person set, and a per-end PIN FLAG saying
  which ends they pinned. For pins alone the two coincide; a copy
  separates them, and collapsing them would make every copy look
  fully pinned and leave "unpin" with nothing to do. A copy therefore
  DEGRADES TO ITS PINS: a new class count or scheme retires the
  copied values and keeps the flags and their bounds, since a pin is
  a smaller and more durable statement than an imported ladder.
  Keyed by tile id AND field like the hand-picked colours, stamped on
  the layer because nothing on a renderer records that a break was
  chosen rather than computed, and carried in both signatures.
  What is REFUSED is only what cannot be DRAWN, and there are three:
  crossed bounds, nothing left for the middle to cut, and a ladder
  asked to carry more pinned boundaries than its k-1. A BOUND OUTSIDE
  THE DATA IS NOT ONE OF THEM. It was until 2026-08-17, when the
  maintainer met the refusal and reversed it: giving one pair of
  limits to several variables is exactly the thing somebody wants,
  since it is how a colour comes to mean the same number on every map,
  which is this plugin's own claim about what these maps are for. Such
  a bound draws perfectly well; its outer class simply goes unworn,
  which `unworn_classes` already computes.
  THE GROUPING WAS THE ERROR AS MUCH AS THE POLICY, and that is the
  part that generalises: listed in one sentence beside the undrawable
  three, a preference reads as a rule, and nobody re-examines it.
  When you find four refusals written together, ask whether they are
  the same kind of thing.
  Relaxing the guard was also only half the fix --
  `_apply_pinned_bounds` built the outer class from the column's own
  extreme, so the ladder snapped back to the data and the accepted
  number changed nothing visible. Guarded by
  `test_a_pin_may_sit_outside_the_data_it_classifies`, which caught
  exactly that, because it drove the renderer rather than the guard.
  What is ACCEPTED and explained is a pin leaving fewer distinct
  values than classes -- that is the reduction above, and two answers
  to one question is what these rules exist to avoid.
  **EQUAL INTERVALS ARE CUT FROM THE PIN, NOT STRETCHED TO IT.**
  (Maintainer's rule, 2026-08-17: with Equal intervals or Unclassed
  every class has the SAME WIDTH, and the one exception is a pinned
  end, whose class takes whatever width the user's bound gives it.)
  Measured false the day it was stated, and the MECHANISM was the
  fault rather than the arithmetic: the scheme cut k-pins classes
  from the samples between the pins, which is each column's own data,
  and `_apply_pinned_bounds` then stretched the outermost computed
  class out to reach the pin. Two columns pinned alike to -5..40 at
  k=5 drew widths 0, 10, 4, 31, 0 and did not agree with each other.
  So the middle is cut over the span the pins declare. Equal widths
  follow by construction, the gap the stretch existed to close cannot
  open, and two columns with the same limits draw the SAME LADDER --
  which is the whole reason for giving them the same limits. The
  stretch still runs and is a no-op there, deliberately, so the outer
  pinned classes go on being built in one place for every scheme.
  Two consequences. The DISTINCT-VALUE REDUCTION is exempted on that
  path: three classes over -5..40 are the same three whatever the
  column holds, so reducing k would hand a sparse column a different
  ladder from a full one under identical limits. And the rule reaches
  Equal intervals and Unclassed ONLY -- quantiles, Jenks and pretty
  breaks are statements about where the data sits, so cutting them
  over a span the data does not occupy would mean nothing. Guarded by
  `test_equal_intervals_stay_equal_under_a_pin` over three columns,
  including one whose middle holds too few distinct values to fill
  the ladder, and by two catalogue entries.
  Two things the map may then show that nothing else here would. A
  copied ladder can leave classes the receiving column cannot reach;
  those are KEPT rather than dropped, because a copy reproduces a
  classification and a silently shortened one does not, and
  `empty_classes_message` says in words how many are empty, on the
  count `unworn_classes` measures from the ladder actually drawn.
  The swatch
  hatched those stripes as well until 2026-08-17; see the entry
  below. And a pinned row is NOT Custom: its
  colours are still its ramp's, so the cell goes on naming the ramp
  and the swatch merely BOXES the pinned end.

### C-64 — What ELEVEN defects taught about that feature pair, 2026-08-15

<sub>Cut from `CLAUDE.md`, lines 3254–3286 of the
2026-09-05 revision.</sub>

- **What ELEVEN defects taught about that feature pair, 2026-08-15.**
  Six hunts pointed at the pinned bounds and copy-to alone found
  eleven, every one a wrong map rather than a crash, and four rules
  come out of them that generalise past this feature.
  A RECORD HOLDING TWO CLAIMS must be tested with both in force: the
  pin record holds copied boundary VALUES and per-end pin FLAGS, each
  worked alone, and together the pin did nothing while the button
  stayed down and the number was stamped.
  TWO DOORS INTO ONE STATE, one guarded, is where the next one lives:
  `pin_problem` used to refuse every pin on a constant column -- it does
  NOT since the out-of-data guard was lifted on 2026-08-17, and the
  same stale sentence survives in the suite at the test that records
  this lesson -- a copy is not
  guarded that way, and the colouring branch downstream had been
  written for the guarded door -- so a copied ladder on a one-value
  column drew flat placeholder grey.
  A CONTROL MUST BE ABLE TO REPRESENT ITS DOMAIN, which every guard
  here checked past: the bound box had a fixed range of 1e12 and six
  decimals, so a province area in square metres pinned an order of
  magnitude out and a rate pinned at zero, both silently, because
  `pin_problem` is asked about the number the CONTROL produced.
  A UNIT-TESTED MECHANISM PLUS AN UNDRIVEN CALLER IS A MOTIONLESS
  AXIS: `bridge.unworn_classes` was careful and covered, and the
  dialog path calling it had never once produced hatching, because
  the swatch was painted before the restyle and asked its question of
  the previous map. When a feature's promise is visual, drive it to
  the pixels. (The hatching itself was withdrawn on 2026-08-17; the
  lesson is about the shape and outlives the feature.)
  Two consequences are now settled behaviour rather than accident.
  A copy CHECKS each pin flag against the receiving column and leaves
  behind what that column cannot reach, saying so; and an Unclassed
  source's fifty never reaches `_class_counts`, which is the record
  that means CHOSEN.

### C-65 — A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE

<sub>Cut from `CLAUDE.md`, lines 3288–3309 of the
2026-09-05 revision.</sub>

- **A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE.** Four
  defects on 2026-08-17 were controls silently refusing what a person
  typed, and each was invisible to `setValue`, which clamps without
  complaint. The mechanisms differ and the tell is identical:
  a validator refusing a keystroke past `maximum` (the pinned-bound
  box at 100x the data; the Ramp Display Range's two percent boxes,
  each clamped by the OTHER's current value, so from a window of
  (0, 40) typing 60 kept SIX); `decimals` lowered to tidy a display,
  so Rotate at zero places turned 22.5 into 22; and a
  `valueChanged` HANDLER THAT REWRITES ITS OWN BOX -- `_skip_zero_scale`
  fired per keystroke because keyboard tracking was on, so typing
  -0.5 announced a landing on zero after the leading nought and the
  design came back UN-MIRRORED at a size that looks exactly right.
  So: any box whose `valueChanged` is watched by something that
  writes back to it needs `setKeyboardTracking(False)`; a no-crossing
  rule between two boxes is enforced when the number is COMPLETE, not
  by clamping ranges, because a validator is asked one keystroke at a
  time and `6` is a prefix of `60`; and a control must be able to
  represent its whole domain, which is where this rule started.
  TEST BY TYPING. Every guard on every one of those four drove
  `setValue` or `stepBy` and passed throughout; one docstring even
  said "dragging or stepping", so typing was never in view.

### C-66 — WHEN A FIX IS WRITTEN INTO TWO PATHS IN ONE COMMIT, DIFF THE TWO HUNKS AGAINST EACH...

<sub>Cut from `CLAUDE.md`, lines 3323–3340 of the
2026-09-05 revision.</sub>

- **WHEN A FIX IS WRITTEN INTO TWO PATHS IN ONE COMMIT, DIFF THE TWO
  HUNKS AGAINST EACH OTHER**, not each against its own neighbourhood.
  2026-08-17: `_add_output_layers` retires an undrawable pin and THEN
  stamps, saying at that line why ("the last moment before the value
  is stamped"); `_restyle_only` stamped and then retired. Both calls
  were born in one commit and the order was reversed on one side, so
  the twin's own explanation sat fifteen hundred lines from the path
  that got it wrong. The user was told the bound "has been
  recalculated" while the retired number went onto the layer anyway,
  so reopening the project restored a pin the row showed and the map
  ignored.
  A SECOND RULE FROM THE SAME BLOCK: **one dedup set must not gate
  two different things.** `field in said` was filled by whether a
  LEGEND NOTICE had fired for a column and it also gated the PIN
  RETIREMENT, which is per element -- so an element's dead pin was
  retired or kept according to what an earlier element had happened
  to trigger. Same act, opposite answers, decided by something no
  user can see.

### C-67 — A GUARD THAT ASKS ABOUT ONE THING MUST NOT STAND IN FRONT OF AN EXIT THAT IS ABOUT...

<sub>Cut from `CLAUDE.md`, lines 3354–3376 of the
2026-09-05 revision.</sub>

- **A GUARD THAT ASKS ABOUT ONE THING MUST NOT STAND IN FRONT OF AN
  EXIT THAT IS ABOUT ANOTHER.** Three defects in one day, 2026-08-17,
  all this shape, and each cost a user their work rather than a crash.
  A COLOUR comparison at the head of `_graduated_layer_edited` stood in
  front of every `embed_style` exit, so a break retyped in QGIS reached
  the map, the project and the .qgz and never the GeoPackage a
  colleague opens -- since 2026-08-10, and invisible because the map
  was right. A "nothing nameable moved" test stood in front of the
  same. And the in-flight gate in `_on_layer_style_edited` stood in
  front of the TABLE learning that an element had begun deferring, so
  the landing read that as the user taking the element back and
  re-seeded it: a style pasted 250 ms into a run was destroyed, while
  the same paste a second either side survived.
  THE HABIT: at every early `return`, `continue` or `break`, name what
  the guard is FOR and then read what lies below it. Where the two are
  about different things, the exit belongs above the guard or the guard
  needs narrowing. This is the twin of the entry above it -- inserting
  a step BEFORE a handler can turn its opening guard from a
  fall-through into a return, which is how one commit disabled another
  five hours later without touching a line of it.
  ALL THREE WERE FOUND BY HUNTS AND NONE BY THE SUITE, on a build that
  had passed 481 tests, the gallery, the colourspace comparison and
  both CI jobs. A gate measures whether known behaviour still holds.

### C-68 — A REPRODUCTION CAN STOP REPRODUCING BECAUSE A NEIGHBOURING RULE CHANGED, AND THE...

<sub>Cut from `CLAUDE.md`, lines 3378–3393 of the
2026-09-05 revision.</sub>

- **A REPRODUCTION CAN STOP REPRODUCING BECAUSE A NEIGHBOURING RULE
  CHANGED, AND THE DEFECT IS NOT DEAD -- ITS DOOR HAS MOVED.**
  2026-08-18, writing the guard for `_restyle_only`. Its committed
  probe reached pin retirement by moving the Classes spinner, and that
  route had been REFUSED hours earlier when a class count stopped
  being allowed to destroy a pin. Run as it stood, the probe now shows
  nothing, and the obvious reading -- "this cannot happen any more" --
  would have left two defects unguarded.
  What still reached the code was a record holding bounds the data
  cannot support, which is what a reopened project or a copied ladder
  hands over. So the guard stages the RECORD rather than the control.
  ASK WHICH DOOR THE PROBE USED AND WHETHER THAT DOOR IS STILL OPEN.
  Where it has been closed, the question is which other doors reach
  the same room, not whether the room still exists. A probe is
  evidence about one route; it was never evidence about the whole of
  a behaviour.

### C-69 — CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO, AND WRONG WHEN THE PLUGIN MERELY...

<sub>Cut from `CLAUDE.md`, lines 3395–3417 of the
2026-09-05 revision.</sub>

- **CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO, AND WRONG WHEN
  THE PLUGIN MERELY STOPPED DECIDING.** (2026-08-18, three defects in
  the deferral family.) `_stamp_category_colours` clears both stamped
  records when there is nothing to record, which stops a layer
  carrying stale choices and is correct. `_assignments` reports a
  DEFERRING row with its picks and pins as None -- indistinguishable
  at that site from a user who cleared everything -- so restyling an
  element in QGIS erased its pinned bounds and hand-picked colours
  from the saved project while the open window still showed them.
  The same boundary was got wrong in the other direction twice more:
  the landing took the OLD layer's opacity for a deferring element
  when the Opacity cell stays live throughout, and
  `_restyle_no_data_layer` repainted a deferring element's paired
  layer when the landing carries that renderer across. Deferral means
  the plugin stops deciding an element's SYMBOLOGY. It does not mean
  the plugin stops deciding anything, and every rule about where that
  line falls has now been wrong at least once.
  THE TWO PATHS NEED DIFFERENT REPAIRS, and that is the part that
  generalises: on a RESTYLE the layer survives, so the records are
  left alone; on a RE-TILE the element gets a NEW layer, and leaving a
  new layer alone means the records are never written at all, so they
  must be CARRIED. Fixing one mends one route and the probe goes on
  failing on the other.

### C-70 — A GATE THAT CHECKS HALF OF WHAT IT NAMES IS WORSE THAN NO GATE, because the other...

<sub>Cut from `CLAUDE.md`, lines 3419–3433 of the
2026-09-05 revision.</sub>

- **A GATE THAT CHECKS HALF OF WHAT IT NAMES IS WORSE THAN NO GATE**,
  because the other half is then believed to be checked. 2026-08-18:
  `sync_release_content.check_vendor_claims` promises in its own
  docstring that "prose claims about the vendored library match the
  recorded stamp", and did `stamp.split()[0]` -- the VERSION alone.
  The stamp is written "0.0.7.89 (bf1bbbf)" precisely because upstream
  does not always bump the version when the code moves, which is what
  MAINTAINING.md tells a re-vendorer, so the half that exists FOR that
  reason was the half nothing compared. Two documents named a
  superseded commit for eight days past a green gate.
  This is the sibling of "a rule that asserts its own enforcement must
  BE enforced". When you write a checker, enumerate what its own
  sentence promises and check each clause; and guard the gate itself,
  as `test_the_documents_numbers_match_the_code` now does by planting
  a wrong commit and requiring the checker to object.

### C-71 — WHEN A FIX WIDENS A CALL SO IT STOPS IGNORING X AND Y, ENUMERATE EVERY KEY OF THE...

<sub>Cut from `CLAUDE.md`, lines 3435–3452 of the
2026-09-05 revision.</sub>

- **WHEN A FIX WIDENS A CALL SO IT STOPS IGNORING X AND Y, ENUMERATE
  EVERY KEY OF THE RECORD THE CALLER COULD HAVE READ.** 2026-08-17 and
  18: `_table_id_colours` built each element's preview colour from the
  ramp NAME, and was wrong SIX TIMES -- a deferring element's layer,
  the Ramp Display Range, the row's Reverse, hand-picked class and
  category colours, a column with nothing to classify, and a constant
  column that the renderer colours from the middle of the window.
  Two were reported, a third was found by reading the line beside
  them, and three more arrived afterwards from hunts. Each repair
  added another condition to the same `elif`.
  A HUNT NAMES WHAT IT MEASURED; IT IS NOT A CENSUS. Three of the six
  colour keys `_assignments` carries were still unread after the
  commit that was supposed to settle it. The rule that finally closed
  the family was to stop enumerating: the preview READS WHAT THE MAP
  DRAWS, and falls back to the row's records only before there is a
  map. When one expression has been wrong three times, the question is
  not which condition is missing but whether it should be asking the
  question at all.

### C-72 — THE PLUGIN'S TABLE FOLLOWS THE LAYER'S RENDERER, AND THE SCOPE OF THAT IS THE WHOLE...

<sub>Cut from `CLAUDE.md`, lines 3454–3497 of the
2026-09-05 revision.</sub>

- **THE PLUGIN'S TABLE FOLLOWS THE LAYER'S RENDERER, AND THE SCOPE OF
  THAT IS THE WHOLE OF ITS SAFETY.** (Maintainer's ruling, 2026-08-17,
  on a field report against rc5: breaks retyped in QGIS's Symbology
  panel, then a style pasted across four element layers, reached the
  plugin not at all -- the rows went on describing THE MAP THE PLUGIN
  LAST DREW while QGIS drew something else, and the next Generate
  destroyed the lot.)
  It was ONE fault rather than three, and the tester established that
  themselves by setting the affected rows to a numeric style and
  repeating the paste. `_element_is_deferring` asks only whether a
  renderer is of a KIND the chooser can NAME, so deferring -- the only
  route by which a QGIS-side change reached the table -- opens only for
  renderers the plugin cannot express. A nameable renderer replaced by
  another nameable one was silently dropped.
  The ruling, chosen between following, deferring on any outside edit,
  and turning dock edits into pins: the row FOLLOWS the layer wherever
  the plugin can name what the layer holds, and defers only where it
  cannot. Pins could not have carried it -- the tester's element
  disagreed on the class COUNT and the RAMP as well as the breaks, and
  a pin names a bound. `_row_follows_the_renderer` reads the field, the
  style, the class count and the ramp back into the row BEFORE the
  colour handlers run, since each of those returns early when the row
  and the layer disagree.
  **A MECHANISM THAT MAKES A ROW DESCRIBE A LAYER IS SAFE ONLY WHERE
  THE ROW CAN REPRODUCE THAT LAYER**, and that is the part worth
  carrying past this feature. Run unscoped, the follow took a SINGLE
  SYMBOL somebody had mixed in the dock and made the row say "Single
  colour" -- which changes the assignment, which re-seeds the element
  on the next Generate, which paints the plugin's own colour over
  theirs. A hand-set #0b1e2d came back #3c8bc2. A field, a scheme, a
  class count and a named ramp are reproducible; an arbitrary fill is
  not, and describing it throws it away while looking like agreement.
  Single symbols keep the older and correct rule: hand styling survives
  unless the element's assignment changed.
  TWO SMALLER TRAPS, both found by the FULL suite and neither by a
  subset of eighteen tests aimed straight at this machinery. A widget
  written with signals blocked is not a row that CHANGED: `_refresh_table`
  restores a mode only when `style_touched` is set, so the followed
  style reverted at the first spacing change. And a row that moves with
  no signal must have its signature re-recorded, or the next restyle
  compares the layer against a row it has never seen and re-seeds the
  renderer it just followed.
  Guarded by `test_a_row_follows_a_style_pasted_onto_its_layer_in_qgis`,
  which drives the paste AND a Generate, and by three catalogue entries.

### C-73 — WHEN A FIX THREADS A "WHO FIRED THIS" ARGUMENT THROUGH A FAMILY OF HANDLERS, GREP...

<sub>Cut from `CLAUDE.md`, lines 3499–3517 of the
2026-09-05 revision.</sub>

- **WHEN A FIX THREADS A "WHO FIRED THIS" ARGUMENT THROUGH A FAMILY OF
  HANDLERS, GREP THE CALLS THEY MAKE TO EACH OTHER.** 2026-08-17, and
  found by two independent hunts within an hour of each other, not by
  the suite. Giving an Unclassed end two pin controls meant every
  handler had to learn which control fired, so `source` was threaded
  through three signatures and every call site updated -- except one
  handler calling ANOTHER handler, `self._bound_edited(which)` inside
  `_bound_moved`. That call was an UNCHANGED CONTEXT LINE in the diff
  and therefore invisible in review, and it was on the branch taken
  only when the end is ALREADY pinned. The fallback then picked the
  first registered control, which is the strip, so the Pin column's
  box took the first number typed and silently discarded every one
  after it while the strip went on working.
  Two habits follow. The call sites you must check are not only the
  ones the SIGNALS reach: a family of handlers calls itself, and those
  calls do not appear in a search for the signal. And a fallback for
  "nobody said which" is exactly where a missing argument hides, since
  it turns a bug into a plausible answer -- prefer failing loudly to
  guessing when the caller should have known.

### C-74 — AN UNCLASSED END IS NAMED BY TWO CONTROLS, AND THEY MUST AGREE

<sub>Cut from `CLAUDE.md`, lines 3518–3544 of the
2026-09-05 revision.</sub>

- **AN UNCLASSED END IS NAMED BY TWO CONTROLS, AND THEY MUST AGREE.**
  (Maintainer's instruction, 2026-08-17, reversing a decision of the
  same week.) Unclassed used to get no Pin column -- fifty faded
  slivers are a preview, and pinning row 0 of fifty is a strange way
  to say "the ramp starts at 10" -- so a clamp strip above the table
  said it better. It does say it better, and it was still reported as
  "pins do not work on unclassed". The reason is worth keeping,
  because it generalises past pins: A USER LEARNS A CONTROL IN ONE
  PLACE AND LOOKS FOR IT THERE. Meeting fifty faded rows and no Pin
  column, they conclude the feature is absent rather than moved. So
  the row now carries BOTH, and the strip's better wording is a
  second way in rather than the only one.
  THE COST IS A CLASSIC OF THIS CODEBASE: one piece of state, two
  descriptions. `_pin_widgets` maps each end to a LIST of (pin, box)
  pairs and `_register_pin` wires every one, so the handlers know
  which control fired; `_sync_pin_controls` then moves the others,
  with signals blocked, or setting a control right would fire the
  handler that set it right. Before this the registry held ONE pair
  per end, so a second builder would have left the first control
  wired, clickable, and applying the other's number.
  Guarded by `test_an_unclassed_row_pins_from_either_control`, which
  drives BOTH ways round and asserts the table's printed bounds and
  the pin's own PIXELS change, and by
  `test_two_pin_controls_agree_across_a_run_landing`, which pins
  mid-run because that is the moment this editor's state has been
  destroyed before. Three catalogue entries, the two sync calls
  anchored separately.

### C-75 — ONE HATCHING NOW, AND THE OTHER WAS WITHDRAWN

<sub>Cut from `CLAUDE.md`, lines 3545–3583 of the
2026-09-05 revision.</sub>

- **ONE HATCHING NOW, AND THE OTHER WAS WITHDRAWN.** Thin 45-degree
  diagonals say "no pin can go here" in the PIN COLUMN, and that is
  the only place they are drawn. The ramp swatch used the same mark
  for "no tile wears this class" until 2026-08-17, when the
  maintainer ruled it out: users are not used to it, so it confuses
  rather than helps. The emptiness is reported in words instead, by
  `empty_classes_message`, on the count `unworn_classes` measures.
  THAT SENTENCE WAS FALSE FOR A DAY and is the reason this one is
  precise: the removal named `few_values_message` as carrying the
  whole job, which fires on a column having fewer distinct values
  than classes -- neither necessary nor sufficient for a class going
  unworn, disagreeing in four cases of six -- and it deleted
  `unworn_classes`'s only caller in the same commit. The maintainer
  ruled on 2026-08-17 that the signal was meant to stay, so
  `dialog._classes_nothing_wears` asks the element's own renderer and
  the notice is composed from what it measures. WHEN A REMOVAL IS
  JUSTIFIED BY "X NOW CARRIES THE WHOLE JOB", RUN X AGAINST EVERY
  CASE THE REMOVED THING COVERED.
  THAT REVERSES PART OF A RULING MADE THE DAY BEFORE, and the pair is
  worth keeping together because the two answer DIFFERENT QUESTIONS.
  On 2026-08-16 the question was whether two hatchings could be told
  apart from each other, and the answer was that they could -- one
  texture saying "nothing available here" covers both honestly, and a
  second texture would ask somebody to distinguish two patterns at
  twelve pixels. That reasoning was sound and is untouched. The 17th
  asked a different question: whether the mark is legible to somebody
  MEETING IT for the first time. It is not. A design can be
  self-consistent and still fail its first reader, and answering the
  second question does not require the first to have been wrong.
  THE AMBIGUITY THAT WAS REAL WAS ARITHMETIC, not vocabulary, and it
  is the lesson worth carrying past the feature: the swatch's
  diagonals were drawn UNCLIPPED, each stroke a full swatch-height
  long and starting a height before the stripe, so marking ONE class
  painted a 49px band around a stripe 12.8px wide. Measured on the
  shipped 64x18 swatch at five classes: hatching class 3 put 44
  pixels into class 2 against 58 into class 3. When a drawn signal
  reads as ambiguous, measure where its ink actually lands before
  redesigning what it means -- a vocabulary argument is the more
  interesting explanation and was the wrong one.

### C-76 — A tiles inset that swallows elements is refused in terms of the inset

<sub>Cut from `CLAUDE.md`, lines 3584–3598 of the
2026-09-05 revision.</sub>

- **A tiles inset that swallows elements is refused in terms of the
  inset.** Insetting shrinks every tile by a fixed distance, so past
  some value the narrower elements disappear. Left to itself the
  library's overlay refuses the surviving slivers and the user meets
  "ValueError: You have passed make_valid=False along with 1978
  invalid input geometries"; when every element goes, the table
  empties and the variable guard fires instead, telling them to assign
  a variable to a design with nowhere to put one. Both are true of
  something and neither is about the control they just moved.
  `bridge.inset_collapse_message` names the inset, and `_generate`
  checks it BEFORE the variable guard. It is asked only when the inset
  is non-zero, so a collapse from another cause is never blamed on it;
  the comparison is safe to refuse a run on because declared n equals
  the distinct tile-id count for 247 of 247 catalogue designs with no
  inset (measured 2026-08-13).

### C-77 — The plugin follows the layer, and adapts where the answer is unambiguous

<sub>Cut from `CLAUDE.md`, lines 3599–3636 of the
2026-09-05 revision.</sub>

- **The plugin follows the layer, and adapts where the answer is
  unambiguous.** QGIS is live and the dialog is not modal to it, so a
  user can delete features, simplify geometry in place, rename or
  retype a field, reassign a CRS or filter the layer while the plugin
  is pointed at it. Both signatures therefore carry a fingerprint of
  what the layer CONTAINS, and the dialog connects to the layer's own
  signals for edits a fingerprint cannot see (a value retyped, a
  vertex moved inside the bounding box). Where an edit makes a setting
  untrue AND there is exactly one sensible response, the dialog makes
  it and says so: an element whose column has gone RE-DEFAULTS to a
  surviving field AND GIVES UP THE STYLE SOMEBODY CHOSE FOR IT (losing
  a column costs an element its variable, not its place on the map --
  unassigned draws as flat fill, so a deletion in QGIS would quietly
  cost the map two of its four variables; and a scheme cut for one
  column says nothing about another, so a categorical one left standing
  on a numeric column draws a colour for every distinct value, which is
  ledger row 9 of 2026-08-20), a
  column added in QGIS is offered straight away, the spacing is
  re-derived when the CRS changes, and the region layer being removed
  is reported rather than silently emptying the chooser. What it does
  NOT do is treat a vanished column and a new one as a rename: that is
  a coin flip that would map data nobody asked for. `repaintRequested` is
  deliberately not listened to in general, because it fires on style
  changes and re-tiling on those is the cost the restyle fast path
  exists to avoid.
  **What neither mechanism sees is an edit made straight through the
  DATA PROVIDER, and that is a stated limit rather than a bug.**
  Measured 2026-08-13: rewriting every value through
  `dataProvider().changeAttributeValues` leaves the count, the extent,
  the field names and the CRS identical and fires no watched signal,
  so the tiles keep the old values and a full Generate changes
  nothing. Scripts and other plugins write this way routinely.
  Following it would mean polling the data or widening the fingerprint
  to something that costs a scan on every debounce tick, and the
  maintainer's decision was to document it instead; the docstring that
  used to claim the case was covered has been corrected. Anybody
  reversing that decision is choosing what the scan costs, not
  discovering a gap.

### C-78 — NULLs are kept out of class breaks, and that is a WORKAROUND with an expiry test

<sub>Cut from `CLAUDE.md`, lines 3637–3662 of the
2026-09-05 revision.</sub>

- **NULLs are kept out of class breaks, and that is a WORKAROUND with
  an expiry test.** QGIS's classifier counts a NULL as zero while its
  own `minimumValue()` excludes nulls, so QGIS disagrees with itself
  and the classifier wins: a column with gaps gets a spurious 0-0
  class and every break shifted toward zero, on a map that looks
  perfectly plausible. Measured identically on the memory provider and
  on a GeoPackage through OGR (QGIS 4.0.3, 2026-08-09), so it reaches
  real data. `make_graduated_renderer` corrects the INPUT rather than
  the output: it hides the nulls with a subset string, lets QGIS's own
  classifier run, and restores the layer. Reimplementing quantiles,
  equal intervals, Jenks and pretty breaks here would mean owning four
  algorithms and inventing new ways to disagree with the styling panel
  the user opens next. It is safe because the layer being filtered is
  the ELEMENT OUTPUT layer, which the plugin creates and owns — never
  the user's region layer — and a provider that refuses the subset
  falls through to the old behaviour, since wrong breaks beat no map.
  The corrected breaks survive a project save and reload, a GeoPackage
  reopened elsewhere, and the plugin's own restyle path; they revert
  only if the user presses **Classify** in QGIS's Graduated panel,
  which recomputes with nulls counted as zero. That is why the notice
  exists as well as the fix. **When QGIS fixes this**,
  `test_qgis_still_counts_nulls_as_zero` fails — it asserts the bug,
  deliberately, going straight to QGIS. Treat that failure as good
  news: delete the marked block in `make_graduated_renderer` and the
  canary, keep `missing_values_message`, and do NOT relax the
  assertion to make the suite green. (User instruction, 2026-08-09.)

### C-79 — The dependency consent dialogue states what can be checked

<sub>Cut from `CLAUDE.md`, lines 3663–3679 of the
2026-09-05 revision.</sub>

- **The dependency consent dialogue states what can be checked.**
  `deps.py` downloads wheels from PyPI where QGIS lacks the scientific
  stack or carries a version below the floor — most often Linux, where
  QGIS uses the system Python, but the trigger is "missing OR too old"
  and can fire anywhere. That is the most intrusive thing this plugin
  does and the thing a QGIS plugin repository reviewer will examine
  hardest, so the dialogue (`plugin.dependency_consent_box`) names the
  packages, the source (PyPI), the exact destination folder, what is
  NOT touched, how to undo it, and what declining costs — and the
  buttons say what they do, with the SAFE one as the default so a
  stray Return cannot start a download. It is built as its own
  function rather than inline so it can be tested and photographed
  without owning a machine that happens to be missing a package;
  `test_the_dependency_consent_says_what_it_will_do` asserts each
  promise. If you change the wording, keep every one of those
  elements: they are what make it consent rather than a prompt.
  (User instruction, 2026-08-09.)

### C-80 — A GUARD YOU HAVE NOT WATCHED FIRE IS A GUARD YOU HAVE NOT GOT, AND AN EDIT CAN...

<sub>Cut from `CLAUDE.md`, lines 3711–3729 of the
2026-09-05 revision.</sub>

- **A GUARD YOU HAVE NOT WATCHED FIRE IS A GUARD YOU HAVE NOT GOT, AND
  AN EDIT CAN REPORT SUCCESS WITHOUT LANDING.** (2026-09-04.) A stage
  table reported TWO calls to a constructor against its parent's one.
  The matcher was suspected, a guard was written to refuse two
  functions of one name, the probe was re-run, the guard did not fire
  -- and docs/PERFORMANCE.md then recorded the matcher as CLEARED on
  the strength of that silence. The guard was never in the file: not in
  the commit that claimed it, not in HEAD, not in the working tree. The
  edit script asserted its anchors, printed its success line, and the
  result did not persist.
  WRITTEN FOR REAL IT FIRED AT ONCE, and the row had been summing a
  CHILD constructor into its parent -- 1.059s claimed where the
  constructor costs 0.654s of which the grid is 0.388s. This file
  already says a test that passes is not a test that works; what this
  adds is that the same is true of an EDIT, and that the absence of a
  complaint is not a verdict. VERIFY THE EDIT LANDED -- grep the file
  for the thing you just wrote -- rather than trusting the script that
  wrote it, which is the assert-the-postcondition rule arriving one
  level up.

### C-81 — A STAGE, A ROW OR A KEY THAT NAMES A FUNCTION WHICH DOES NOT EXIST REPORTS NOTHING,...

<sub>Cut from `CLAUDE.md`, lines 3730–3745 of the
2026-09-05 revision.</sub>

- **A STAGE, A ROW OR A KEY THAT NAMES A FUNCTION WHICH DOES NOT EXIST
  REPORTS NOTHING, AND THAT READS AS COSTING NOTHING.** (Same day.) A
  generation profile listed a stage under a name no function has -- the
  no-data split is not called what the probe called it -- so the row
  never appeared, its work read as free, and docs/PERFORMANCE.md
  honestly listed that split as UNMEASURED the whole time the probe
  claimed to measure it. It refuses such a stage now, asked of the
  SOURCE rather than of the profile, because a function that exists and
  was not called on this journey is a legitimate absence and only a
  name that cannot exist is a fault. This is "a check that can only
  confirm is not a check" arriving inside an instrument.
  AND ITS DISAMBIGUATOR REPEATED THE FAULT ONE LAYER DOWN. Telling two
  same-named methods apart by a hard-coded LINE NUMBER worked until the
  next edit above them shifted it, after which both rows matched
  nothing and printed nothing. A line number written down is a
  hand-kept number; resolve it by parsing for the class.

### C-82 — ONE POLYGON DOING TWO JOBS CHANGES BOTH WHEN YOU SHRINK IT

<sub>Cut from `CLAUDE.md`, lines 3755–3769 of the
2026-09-05 revision.</sub>

- **ONE POLYGON DOING TWO JOBS CHANGES BOTH WHEN YOU SHRINK IT.** (Same
  day, patch 4.) The tiling grid's extent said which cells were WANTED
  and also PHASED the lattice, since the meshgrid origin comes from its
  own bounds. Shrinking it moved every tile: one design drew 2,772
  tiles both ways with 2,622 differing, every one still touching the
  region. Nothing was lost and the whole pattern moved, which is a
  different map rather than a cheaper one. The repair is two polygons,
  one per job.
  AND HALF OF ALL DESIGNS HID IT. The origin is the centre less half
  the ceiling of twice the radius, so a phase shift appears only when
  that ceiling moves by an ODD amount. A guard written on a design
  where the two radii agree reported the phase fault as INERT -- which
  reads exactly like a test too weak to notice one. When a fault turns
  on an arithmetic parity, the fixture must be named and the reason
  written at it.


## The test suite's lessons, in full

### C-83 — A TEST FOR A PROMISE IS A MATRIX, NOT A CASE, and this is the DEFAULT rather than a...

<sub>Cut from `CLAUDE.md`, lines 3940–3956 of the
2026-09-05 revision.</sub>

- **A TEST FOR A PROMISE IS A MATRIX, NOT A CASE, and this is the
  DEFAULT rather than a technique to reach for occasionally.** Where
  the thing under test is a family of behaviours -- "edit the
  symbology in QGIS and the plugin follows", "a number you type is the
  number used" -- enumerate the atomic actions as ROUTES, cross them
  with synthetic data SHAPES chosen for failure modes rather than
  realism, and add an axis for what happens NEXT, because arrival and
  survival are different promises. Run a spine of every route against
  two canonical shapes every time, sample the rest under a printed
  seed, keep the full crossing behind a flag, and report every failing
  cell rather than the first. Measured 2026-08-18: 36 cells, 58
  seconds, and 17 of them fail when the fix is removed. The guard this
  replaced changed field, class count and ramp TOGETHER and had passed
  for weeks while a retyped boundary reached nothing -- ONE COMPOUND
  CHANGE IS NOT COVERAGE OF MANY SMALL ONES. Written up at length in
  docs/TESTING.md; apply it when improving an existing test too, since
  a test that already passes is where a hole hides best.

### C-84 — A GUARD MUST NOT REPAIR WHAT IT MEASURES, NOR RUN WHERE THERE IS NOTHING TO SEE

<sub>Cut from `CLAUDE.md`, lines 3958–3969 of the
2026-09-05 revision.</sub>

- **A GUARD MUST NOT REPAIR WHAT IT MEASURES, NOR RUN WHERE THERE IS
  NOTHING TO SEE.** (2026-08-19, three in one sitting, every one
  caught by the catalogue rather than by reading.) A visual guard hid
  and re-showed the mark to get a contrast -- calling the very methods
  the mutation removed, so it mended the product and then measured the
  mended product. Its replacement ran after the surrounding test had
  given every bound back, so nothing was marked and the loop never
  executed. A third handed edge pairs to the icon builder, proving the
  DRAWING while the dialog asked for two ends of four. Drive the
  product, read the pixels, COUNT WHAT YOU LOOKED AT, and state the
  check as its inverse -- "name anything that draws nothing" rather
  than "the mark is drawn". Full shapes in docs/TESTING.md.

### C-85 — WHEN A REPRODUCTION WILL NOT REPRODUCE, MEASURE THE SESSION THAT IS BROKEN

<sub>Cut from `CLAUDE.md`, lines 3970–3981 of the
2026-09-05 revision.</sub>

- **WHEN A REPRODUCTION WILL NOT REPRODUCE, MEASURE THE SESSION THAT
  IS BROKEN.** (2026-08-19.) Six reproductions of a reported defect
  were built here, against the reporter's own data, and every one
  worked. Two dumps behind `WEAVINGSPACE_ADOPT_DUMP` and one run by
  the person holding the failure answered it in a minute: the dump was
  EMPTY, so the plugin had never been told, because that session's
  Generate had failed and `styleChanged` is connected only when a run
  lands or a group is adopted. A reproduction that will not reproduce
  is a signal about the DIFFERENCE between two sessions; budget the
  instrument early rather than a seventh attempt. An empty dump is
  evidence only where the dump is known to fire -- here, because other
  lines from the same function appeared in the same terminal.

### C-86 — A MATRIX CATCHES ONLY WHAT ITS CELLS MAY COMPLAIN ABOUT

<sub>Cut from `CLAUDE.md`, lines 3982–3995 of the
2026-09-05 revision.</sub>

- **A MATRIX CATCHES ONLY WHAT ITS CELLS MAY COMPLAIN ABOUT.**
  (2026-08-19.) The symbology matrix crosses twelve routes with nine
  shapes, three aftermaths and three schemes, and it caught NONE of
  three defects that landed in one evening -- an affordance drawn
  under the widget that covers it, a ceiling with no edge to mark, a
  bound of 1e9 elided out of its box. The routes were all exercised.
  Every complaint a cell could make was about a RECORD, a layer, a
  stamp or a notice; nothing in it ever looked at a picture or asked
  whether a number could be typed back.
  So before adding cells, ask what a cell is ALLOWED TO NOTICE: an
  axis that crosses a question the verdict cannot ask is an axis that
  cannot fail. Every cell now also asks that what the record holds is
  MARKED where a user looks and DISPLAYED in full and typable back.
  Full reasoning in docs/TESTING.md.

### C-87 — WHEN A CHANGE BREAKS A TEST, BISECT BY DISABLING RATHER THAN BY REASONING, after ONE...

<sub>Cut from `CLAUDE.md`, lines 3997–4005 of the
2026-09-05 revision.</sub>

- **WHEN A CHANGE BREAKS A TEST, BISECT BY DISABLING RATHER THAN BY
  REASONING, after ONE hypothesis fails.** Insert an early `return` at
  successive points through the new code; the first point that turns
  PASS into FAIL contains the culprit. To decide which FILE is at
  fault, swap the whole file for its last-good version. On 2026-08-18
  this bracketed a defect to a single statement after four plausible
  theories had each been implemented and each been wrong, and the
  culprit's own log then named what it wrote -- the plugin's own
  ladder, recorded as though a user had typed it.

### C-88 — TWO OF THIS PROJECT'S INSTRUMENTS LIE, and both cost hours on 2026-08-18

<sub>Cut from `CLAUDE.md`, lines 4007–4018 of the
2026-09-05 revision.</sub>

- **TWO OF THIS PROJECT'S INSTRUMENTS LIE, and both cost hours on
  2026-08-18.** `print()` inside a Qt signal handler goes nowhere under
  a test that captures output, so an empty dump read as proof the code
  never ran when it ran every time -- AN EMPTY LOG IS NOT EVIDENCE OF
  ABSENCE. And a plain `python3` heredoc run AFTER sourcing the QGIS
  environment dies at bootstrap and applies NO edit, so the run that
  follows measures the unmodified file and reports fiction; use
  `env -u PYTHONHOME -u PYTHONPATH python3`, the same hazard that
  kills `release.py` and `mutation_check.py`. Related: an anchor
  matching TWICE applies nothing while the run still reports a result,
  and the categorized and graduated handlers share identical text.
  Assert the match count and parse the file after every edit.

### C-89 — A WATCHER MAY ONLY ADOPT WHAT A PERSON LEFT BEHIND

<sub>Cut from `CLAUDE.md`, lines 4020–4032 of the
2026-09-05 revision.</sub>

- **A WATCHER MAY ONLY ADOPT WHAT A PERSON LEFT BEHIND.** Anything
  that reads state off a layer and records it must run at REST: not
  while the dialog is writing renderers (`_applying_style`), not while
  a run is in flight (`_task`), and not while a landing is still being
  reconciled (`_preserved_this_run`). During any of those the record
  and the layer are transiently out of step, and what sits on the
  layer is nobody's decision. Adoption recorded the plugin's own
  five-class ladder as a user's, pinned it, and a twelve-class
  reclassification made in the dock became five. Also: a getter-shaped
  name is not a getter -- `_current_graduated_classes` BUILDS a
  renderer -- and work added to a signal handler must not precede the
  work already there, since an exception in a Qt slot is swallowed and
  takes the rest of the handler with it.

### C-90 — CLASS BOUNDS: THE RECORD HOLDS FOUR ENDS, AND TWO OF THEM ARE WEAKER THAN THE OTHER TWO

<sub>Cut from `CLAUDE.md`, lines 4034–4057 of the
2026-09-05 revision.</sub>

- **CLASS BOUNDS: THE RECORD HOLDS FOUR ENDS, AND TWO OF THEM ARE
  WEAKER THAN THE OTHER TWO.** (Maintainer's decisions, 2026-08-19.)
  `pinned` gained `floor` and `ceiling` beside `low`, `high` and
  `breaks`. `low` and `high` name BOUNDARIES BETWEEN CLASSES -- the
  first class's upper and the last class's lower -- so each takes its
  class out of the pool the scheme cuts from, can cross its
  neighbour, and can be refused. `floor` and `ceiling` name the EDGES:
  no boundary moves, no class leaves the pool, and nothing can be
  refused for crossing. Keep them in separate registries. Putting an
  edge into `_pins_in_force` would corrupt the `k` arithmetic, which
  must stay 0, 1 or 2 -- one set gating two different things, which
  this project has paid for before.
  THE WHITELIST IN `_adopt_dock_bounds`'s RESTORE PATH IS THE
  RECORD'S REAL DEFINITION. A key missing from it is dropped in
  SILENCE on every reopen, so the record is right all session and
  wrong the moment the project comes back. When you widen the record,
  widen that line in the same commit.
  A LADDER RETYPED IN QGIS KEEPS THE ENDS A PERSON TYPED. The 0.24.3
  ledger argued the low end was harmless because the same areas fall
  in the same class; that is true about colour and FALSE ABOUT WHAT
  THE LEGEND SAYS, and it only ever considered the bottom. What is
  dropped is the pair of edges when NOTHING survives them -- a ladder
  retyped far from the data would otherwise adopt a ceiling that
  excludes every value and leave the element with no classes at all.

### C-91 — A LIMIT MAY EXCLUDE, AND WHAT IT EXCLUDES IS DRAWN

<sub>Cut from `CLAUDE.md`, lines 4059–4077 of the
2026-09-05 revision.</sub>

- **A LIMIT MAY EXCLUDE, AND WHAT IT EXCLUDES IS DRAWN.** A floor or
  ceiling inside the data puts values out of bounds, and those areas
  become a FOURTH KIND OF ABSENCE beside no data and the two
  infinities: drawn, in a colour a user picks, with their own legend
  line. Left to a graduated renderer an excluded value gets no symbol,
  which on a map of areas is a HOLE -- indistinguishable from a tiling
  gap and from a missing value, three facts wearing one appearance.
  THREE OF THE FOUR KINDS ARE FACTS ABOUT THE DATA AND THE FOURTH IS A
  CHOICE, which decides precedence: a value's own nature is asked
  first, so an infinity excluded by a ceiling is reported as an
  infinity. `bridge.absence_kind` is the one owner of that question;
  it replaced three copies in two files that each enumerated the keys
  by hand.
  A LIMIT IS A GEOMETRY CHANGE, because excluding values moves tiles
  onto the paired layer and `_restyle_only` can neither make nor
  unmake one. So the split PREDICATE is what learns about limits, not
  the split: it feeds the geometry signature, and answering no there
  sends a limit change down the restyle path where the exclusion is
  recorded, believed and never drawn.

### C-92 — NO PIN COLUMN: A HEAVY OUTLINE ON THE BOX SAYS THE NUMBER IS YOURS

<sub>Cut from `CLAUDE.md`, lines 4079–4098 of the
2026-09-05 revision.</sub>

- **NO PIN COLUMN: A HEAVY OUTLINE ON THE BOX SAYS THE NUMBER IS
  YOURS.** (Maintainer's instruction, 2026-08-19.) One convention for
  all four ends rather than two, no table width, and nobody reading a
  glyph at twelve pixels. A middle class simply has no spin box, which
  says "you cannot set this" the way every other table does. A cross
  inside the box gives a bound back, and typing the computed number
  back does the same -- compared at the box's DISPLAYED precision, or
  an edge of 3.0999999 can never be retyped and the second route is
  decorative. Painted, not stylesheeted: a stylesheet border REPLACES
  the platform frame rather than adding to it. Measured 47 dark pixels
  unmarked against 533 marked; a mark nobody can see is a flag.
  UNCLASSED NAMES ITS FLOOR AND CEILING, NOT TWO PINS, which reverses
  part of the ruling of 2026-08-17 deliberately. That ruling gave
  Unclassed a Pin column because a user met fifty faded rows and
  reported the feature missing -- right when a pin was the only
  control for an end. The original objection, that pinning row 0 of
  fifty is a strange way to say "the ramp starts at 10", is answered
  by a control that says exactly that. The strip's label had been
  wrong since it was written: "Ramp starts at" drove the LOW PIN,
  which on fifty steps is the ramp's start plus a fiftieth of the span.

### C-93 — A GUARD MEASURES THE GROUND, NOT THE BOX ROUND IT

<sub>Cut from `CLAUDE.md`, lines 4110–4137 of the
2026-09-05 revision.</sub>

- **A GUARD MEASURES THE GROUND, NOT THE BOX ROUND IT.** (2026-08-19,
  ledger row 23, and it cost a colleague their map rather than a
  little time.) The size guard estimated tiles from a CIRCLE enclosing
  the region's bounding rectangle, while the library tiles that circle
  and then CLIPS to the polygons. New Zealand is two long islands in a
  rectangle that is mostly sea -- 11.8% of that circle -- so the guard
  said 585,765 tiles where 70,659 were drawn and REFUSED a design the
  library renders in five seconds.
  FOUR MODELS WERE MEASURED against what is really drawn, because a
  region is not one shape: adjacent cells cut from a raster share
  edges needing no allowance, separated cells each carry their own.
  The bounding-box edge came out 1.20x on the first and 0.98x -- UNDER
  -- on the second; each polygon's own perimeter 6.25x and 2.38x; the
  DISSOLVED boundary 1.28x and 1.68x. Only the last is generous on
  both, and a guard that under-counts waves through a run that then
  takes the machine.
  THE GENERAL FORM, which reaches past this guard: a perimeter summed
  per row is a property of HOW THE DATA WAS CUT INTO ROWS rather than
  of the ground it covers, and so is a bounding box. When an estimate
  stands on the shape of the input, ask whether it is standing on the
  geometry or on the table.
  AND ITS FIXTURES MUST BE SPARSE. Every region fixture in this suite
  is a dense square, where the circle and the ground differ only by
  pi/2 and any honest threshold accepts both -- which is why nothing
  here ever caught it. The guard asserts its fixture IS sparse before
  comparing anything, and computes what the old arithmetic would have
  said, so its threshold cannot be one the current code merely happens
  to meet.

### C-94 — A CACHE OF ONE IS NO CACHE WHEN THERE ARE TWENTY-THREE OF ANYTHING

<sub>Cut from `CLAUDE.md`, lines 4139–4157 of the
2026-09-05 revision.</sub>

- **A CACHE OF ONE IS NO CACHE WHEN THERE ARE TWENTY-THREE OF
  ANYTHING.** (2026-08-19, ledger row 4.) `_classification_values`
  REPLACED its cache dict on every miss, on the sound reasoning that a
  stale fingerprint's values must never sit there being wrong -- and
  replacing it threw away every OTHER column's entry at the same time.
  With one element that is free; with twenty-three elements on
  twenty-three columns the hit rate is ZERO, so one keystroke rescanned
  3,011 features twenty-three times. Measured on the reporter's own
  data: 119,352 calls per tick at 0.24.2 against 1,041,176 at HEAD,
  172 ms of CPU against 3,543, one Generate at 2.5s against 62.7.
  THE SUITE COULD NOT SEE IT: four elements over thirty-six features
  against twenty-three over three thousand is a factor of 481 with no
  change of shape, so the cost was real all along and never large
  enough to show. WHEN A FIX IS ABOUT STALENESS, ASK WHAT ELSE IT
  DISCARDS -- the safety property here needed only that entries whose
  fingerprint has moved go, not that everything go.
  AND ITS GUARD COUNTS CALLS ACROSS SEVERAL COLUMNS. A one-column test
  reads zero warm scans whatever the code does, since there is nothing
  to evict it, and would pass with the cache deleted outright.

### C-95 — A COPY REPRODUCES THE WHOLE CLASSIFICATION, AND THE RECORD GREW UNDER IT

<sub>Cut from `CLAUDE.md`, lines 4159–4176 of the
2026-09-05 revision.</sub>

- **A COPY REPRODUCES THE WHOLE CLASSIFICATION, AND THE RECORD GREW
  UNDER IT.** (2026-08-19, ledger rows 21 and 22.) `_copy_classification`
  built its record from breaks and pin flags and never read `floor` or
  `ceiling`, then wrote that record WHOLESALE -- so a copy left the
  source's range behind AND destroyed the target's. The case that
  justified out-of-data bounds at all was giving one pair of limits to
  several variables, and the control built for it could not do it.
  WHEN A RECORD GAINS A KEY, GREP EVERY SITE THAT ENUMERATES ITS KEYS.
  `_adopt_dock_bounds`'s restore whitelist was widened the same day and
  is documented as "the record's real definition"; the copy was not,
  and nothing pointed at it.
  AND THE FIX MOVED THE COPY ONTO A PATH THAT REFUSES IT: a limit is a
  GEOMETRY change, so `_restyle_only` declines the element -- and the
  restyle is what writes the stamp. A copy of breaks alone came back
  stamped and the identical copy carrying a range stamped nothing, so
  it reached the map and would have died at the next reopen. WHEN A FIX
  MOVES A CHANGE FROM ONE PATH ONTO ANOTHER, ASK WHAT THE OLD PATH WAS
  DOING FOR IT BESIDES THE OBVIOUS.

### C-96 — A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES, so NEVER hard-wrap one

<sub>Cut from `CLAUDE.md`, lines 4178–4192 of the
2026-09-05 revision.</sub>

- **A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES, so NEVER hard-wrap
  one.** Release notes written at the usual 72 columns arrive as
  literal line breaks, and on a phone that means a sentence broken
  mid-clause -- "nothing is promoted," ending a line, `main` starting
  the next -- because the renderer never gets to wrap to the viewport.
  Write each paragraph as ONE long line and let the reader's width
  decide; keep hard newlines only for headings and list items, which
  need them. Seen on rc9, 2026-08-18, and fixed by unwrapping.
  This is the SAME fault as the changelog's, from the other side: that
  entry is hard-wrapped because QGIS's plugin manager shows metadata
  text AS IT STANDS and would run a long line off the panel. TWO
  SURFACES, OPPOSITE RULES, and the deciding question is always
  whether the renderer reflows. Check a release page NARROW -- a phone
  or a half-width window -- before believing it reads, exactly as the
  changelog is checked in both renderers.

### C-97 — A CHECK THAT CAN ONLY CONFIRM IS NOT A CHECK

<sub>Cut from `CLAUDE.md`, lines 4194–4203 of the
2026-09-05 revision.</sub>

- **A CHECK THAT CAN ONLY CONFIRM IS NOT A CHECK.** Unwrapping the rc9
  release notes, the script reported "unwrapped: 14 blocks" and I read
  that as success -- but the number needed was how many were still
  WRONG, and nine of eleven paragraphs had been skipped because they
  open with bold and my list-item guard matched `*`. A count of things
  PROCESSED says nothing about things FIXED. State the check as its
  inverse -- show me anything still broken -- so a clean run is an
  assertion rather than an absence. The same fault appears in tests as
  a shape-blind expectation, and in probes as an empty log read as
  proof.

### C-98 — A GLOB IS HOW A LOG'S DATE GETS SKIPPED

<sub>Cut from `CLAUDE.md`, lines 4209–4224 of the
2026-09-05 revision.</sub>

- **A GLOB IS HOW A LOG'S DATE GETS SKIPPED.** (2026-08-19, and the
  THIRD time this project has read a stale log as current.) The rule
  already written is that every excerpt from a log must be dated
  before it is read. What defeats it in practice is
  `grep reports/stage-logs/*.log`, which sweeps up every run there has
  ever been: two failures from a stage log three days old were
  reported as the current candidate's, and the candidate was in fact
  clean. The run's own logs were sitting beside them under a
  timestamped name.
  SO NAME THE RUN, NEVER THE DIRECTORY. This project already keys
  every log to its run for exactly this reason -- a timestamp and a
  pid -- and that discipline is worth nothing if the reader globs.
  When you go looking for a running job's output, build the pattern
  from the job you started rather than from the folder it writes to,
  and if you cannot say which run a line came from, you have not read
  it yet.

### C-99 — WHEN TWO THINGS SHOULD DRAW THE SAME MAP, COMPARE WHAT THEY DREW, NOT WHAT THEY LOOK...

<sub>Cut from `CLAUDE.md`, lines 4226–4240 of the
2026-09-05 revision.</sub>

- **WHEN TWO THINGS SHOULD DRAW THE SAME MAP, COMPARE WHAT THEY DREW,
  NOT WHAT THEY LOOK LIKE.** (2026-08-19, comparing the plugin against
  the library on the maintainer's own data.) The two paint with
  different colours by construction -- a two-colour matplotlib
  colormap against seeded QGIS renderers -- so pixels would report a
  difference that means nothing. Per-element TILE COUNTS mean
  everything: 70,659 tiles both sides and the same number on every one
  of twenty-three elements is the same map, and no oracle was needed
  to say so.
  AND THE COMPARISON ANSWERED A DIFFERENT QUESTION THAN IT WAS ASKED.
  The question was how long each takes; the answer was that the plugin
  would not draw it at all, because the size guard refused. A
  performance question is worth asking of real data for that reason
  alone: it drives the whole path at a size no fixture reaches, and
  what it finds need not be a time.

### C-100 — A NAME THAT CARRIES A NUMBER IS SORTED AS TEXT, AND rc10 COMES BEFORE rc2

<sub>Cut from `CLAUDE.md`, lines 4242–4262 of the
2026-09-05 revision.</sub>

- **A NAME THAT CARRIES A NUMBER IS SORTED AS TEXT, AND rc10 COMES
  BEFORE rc2.** (2026-08-19, ledger row 25.) `release.py` named the
  candidate it had just built by sorting `dist/weavingspace_qgis-*rc*.zip`
  and taking the last entry. On the tenth candidate of 0.24.3 -- the
  first two-digit candidate this project has ever built -- the zip went
  out as `0.24.3rc10` while its dossier and receipt were written as
  `rc9`, ON TOP OF the published rc9's own. One name over two trees,
  which is precisely the harm `next_candidate` exists to prevent,
  arriving from the end nobody was watching. The same glob spanned
  every VERSION, so a 0.25.0 candidate would have been named from a
  leftover 0.24.3 one.
  THE DEEPER FAULT IS THAT THE FACT HAD TWO DERIVATIONS. `next_candidate`
  parses the number and takes `max() + 1`, and was right the whole
  time; naming re-derived the same fact in another file by another
  route. A rule with two implementations has two behaviours the day
  one of them is wrong, which this file already says about generated
  documents and about `shipped_files()`. It is `build.latest_candidate`
  now, beside its sibling and sharing what counts as an artefact.
  AND A FIXTURE MUST REACH THE CASE: nine candidates satisfy both
  derivations, so the guard stages TEN and computes what the text sort
  would have said, requiring it to disagree.

### C-101 — A DEPENDENCY'S CHEAP ANSWER IS A CACHED ANSWER, AND A GUARD BUILT ON ONE IS HONEST...

<sub>Cut from `CLAUDE.md`, lines 4269–4289 of the
2026-09-05 revision.</sub>

- **A DEPENDENCY'S CHEAP ANSWER IS A CACHED ANSWER, AND A GUARD BUILT
  ON ONE IS HONEST ONLY AFTER SOMETHING INVALIDATES IT.** (2026-08-20,
  ledger row 32.) `compat.layer_data_is_available` asked a layer
  whether it was valid and its provider whether it was valid, and its
  own Returns block promised that caught "a layer whose file has been
  deleted ... including the case where the layer itself still claims
  to be valid". Measured on QGIS 4.0.3, moving a GeoPackage out from
  under an open layer: isValid True, provider True, featureCount 36 --
  and `getFeatures()` yielding NOTHING. Only after an explicit
  `reload()` does the provider admit False and the count fall to -2,
  and nothing reloads a layer a user has not touched. So the guard
  passed, the run went on, and the refusal that reached the user was
  about their DATA when the fact was that their FILE had moved.
  THE HABIT: when a guard asks a dependency whether something is still
  true, ask what would have to HAPPEN for that answer to be refreshed.
  Where the answer is "somebody must act", the cheap question measures
  the last time somebody acted, not the world. The honest question
  here costs one feature: ask for it, and see whether it comes back.
  This is the third appearance of "a gate that checks half of what it
  names", and the first where the other half was a staleness rather
  than a missing clause.

### C-102 — AND ITS TEST HAD BEEN EXERCISING THE HONEST PATH ALL ALONG

<sub>Cut from `CLAUDE.md`, lines 4290–4298 of the
2026-09-05 revision.</sub>

- **AND ITS TEST HAD BEEN EXERCISING THE HONEST PATH ALL ALONG.** The
  sibling guard called `reload()` in its own setup before asking
  anything -- which is the one act that makes QGIS tell the truth, and
  the one act a user never performs. A test whose SETUP repairs the
  condition it is about passes forever; this project already knows
  that shape from a visual guard that called `show()` on the thing the
  mutation had hidden, and it arrives here wearing a data provider.
  Read a test's arrangement for calls that would refresh, reset or
  reopen the very thing under test.

### C-103 — A FIX APPLIED TO A TWIN THAT DOES NOT HAVE THE FAULT IS DEAD CODE THAT READS AS...

<sub>Cut from `CLAUDE.md`, lines 4299–4311 of the
2026-09-05 revision.</sub>

- **A FIX APPLIED TO A TWIN THAT DOES NOT HAVE THE FAULT IS DEAD CODE
  THAT READS AS PROTECTION.** (2026-08-20, ledger row 34.) The rule
  that a colour equal to the renderer's SOURCE SYMBOL is QGIS's clone
  rather than somebody's decision is right on the graduated path, and
  was written onto the categorized path in the same edit out of the
  usual and correct suspicion about pairs. Measured,
  `make_categorized_renderer` sets no source symbol at all, so that
  guard could never fire: it would have sat in the catalogue as a
  permanent survivor and in the source as a claim that a door was
  watched. It was deleted and the measurement left at the site with
  what would reopen it. THE PAIRS RULE CUTS BOTH WAYS -- check whether
  the twin HAS the fault before giving it the fix, and when it does
  not, say so where the next person will look for the symmetry.

### C-104 — A GUARD THAT LANDS WITHOUT A TEST OF ITS OWN LOOKS GUARDED, BECAUSE THE NEIGHBOUR IT...

<sub>Cut from `CLAUDE.md`, lines 4312–4320 of the
2026-09-05 revision.</sub>

- **A GUARD THAT LANDS WITHOUT A TEST OF ITS OWN LOOKS GUARDED,
  BECAUSE THE NEIGHBOUR IT RE-ANCHORED STILL PASSES.** The edge rule
  for pinned bounds went in on 2026-08-19, correctly re-anchoring the
  catalogue entry standing on the line it changed -- and that entry
  proves ends are adopted AT ALL, not that they are kept off the
  ladder's edge. The commit therefore read as fixed-and-guarded while
  the new rule had nothing measuring it. When an edit re-anchors an
  entry, ask what that entry actually asserts: re-anchoring keeps an
  OLD claim true and never states the new one.

### C-105 — `styleChanged` FIRES ONLY ON `setRenderer`; AN EDIT MADE ON THE LIVE RENDERER IS...

<sub>Cut from `CLAUDE.md`, lines 4322–4342 of the
2026-09-05 revision.</sub>

- **`styleChanged` FIRES ONLY ON `setRenderer`; AN EDIT MADE ON THE
  LIVE RENDERER IS SILENT, AND ITS `triggerRepaint()` IS THE ONLY
  TRACE.** (2026-08-20, ledger row 28, reported four times before it
  was measured.) The styling panel installs a whole renderer for some
  acts (adding a class, Classify, a paste) and edits the held renderer
  in place for others (a plain colour change) -- so the plugin
  followed the first kind and was structurally deaf to the second,
  while MAINTAINING.md asserted the opposite in as many words. The
  dock then calls `triggerRepaint()`, because the canvas has no other
  way to learn, and THAT emits `repaintRequested`. Element layers now
  listen to it, debounced, with three gates that each failed a test
  before it existed: our own repaints (`_applying_style`), the echo of
  a heard `setRenderer` edit (it fires both signals, and handling it
  twice adopts the displaced ladder), and a row that has moved (the
  layer is merely BEHIND a pending restyle, and reconciling then
  adopts our own outgoing style as somebody's picks). The REGION
  layer's `repaintRequested` stays unconnected -- that rule is about
  re-tiling and is untouched. The general lesson: when a dependency's
  signal is documented here as covering a family of edits, ask which
  member of the family was actually measured; this one had been
  measured only for the member that happens to announce itself.

### C-106 — `ranges()` AND `categories()` HAND BACK COPIES, so editing one is a NO-OP on the...

<sub>Cut from `CLAUDE.md`, lines 4343–4353 of the
2026-09-05 revision.</sub>

- **`ranges()` AND `categories()` HAND BACK COPIES, so editing one is
  a NO-OP on the layer -- and a probe that does it measures nothing.**
  (2026-08-20, twice in one hour: a signal probe's row and a guard's
  first draft.) `ranges[0].symbol().setColor(...)` recoloured a
  temporary; the renderer never changed; "no signal fired" was
  reported about an edit that had not happened. Stage in-place edits
  through the renderer's own `updateRangeSymbol`/`updateCategorySymbol`
  and ASSERT the edit reached the layer before asserting anything
  else. This is the fixture-that-cannot-move trap inside an
  instrument, and it is the sibling of the freed-temporary segfault
  this file already records about the same getters.

### C-107 — ABSENT IS NOT MOVED: when a NEW guard reads an OLD record, ask which paths leave...

<sub>Cut from `CLAUDE.md`, lines 4355–4371 of the
2026-09-05 revision.</sub>

- **ABSENT IS NOT MOVED: when a NEW guard reads an OLD record, ask
  which paths leave that record deliberately empty.** (2026-08-20,
  found by three hunts independently.) A guard added the day before
  skipped an element whose row signature differed from
  `_last_signatures` -- right in itself, since between a control
  change and the restyle that answers it the layer is merely BEHIND.
  It asked with `!= self._last_signatures.get(tile_id)`, and
  `_adopt_existing_group` leaves that record EMPTY on purpose, saying
  so in its own docstring: the dialog cannot know which assignments
  produced layers it has only just met. So `.get()` answered None for
  every adopted element, None never equals a real signature, and the
  new route was shut in every REOPENED project -- the commonest
  journey there is, and the one whose docstring promises hand styling
  survives. A missing entry is the absence of evidence; reading it as
  evidence of change inverts the guard exactly where the record is
  emptiest. Ask of any `.get()` in a guard what an absent key MEANS,
  and write the answer at the line.

### C-108 — A GUARD COMPUTED AS A DELTA IS ARMED FOR ONE INVOCATION

<sub>Cut from `CLAUDE.md`, lines 4372–4419 of the
2026-09-05 revision.</sub>

- **A GUARD COMPUTED AS A DELTA IS ARMED FOR ONE INVOCATION.**
  (2026-08-20, ledger row 2, and it defeated a guard written the
  previous day.) `count_moved` was measured across
  `_row_follows_the_renderer` INSIDE ONE HANDLER CALL, to stop a class
  added in QGIS having its shuffled colours adopted. It is true on the
  signal carrying the change and FALSE on every signal after it,
  because the follow has already brought the row up to date and there
  is no delta left to see. Measured: a hand-picked colour survived the
  class being added and, one bare repaint later, the record held four
  colours with the user's displaced a class and three of the plugin's
  own recorded as theirs, stamped into the project. THREE routes reach
  the second pass -- a later repaint, a re-tile landing, and the
  window-activation backstop added in the same commit as the guard.
  So: when you add a guard that reads state the caller has just
  changed, ENUMERATE EVERY ROUTE TO A SECOND PASS in that same commit,
  and prefer a question the state can answer at any moment over one
  that asks "did this change just now".
  THE OBVIOUS DURABLE REPLACEMENT WAS TRIED AND WITHDRAWN the same
  hour, and its shape is worth not repeating: comparing the ladder's
  BOUNDS against what the row would draw is correct in the reported
  case and over-reaches everywhere else, because once a class has been
  added in the dock the ladder differs from ours PERMANENTLY and no
  hand-pick would ever be adopted for that element again.
  **SETTLED BY `/grill-me` THE SAME DAY, and the first thing the
  grilling did was reject the question.** The ledger asked whose
  LADDER it is, offering "theirs, so the element defers" against
  "ours, so store it". Those are not peers: deferral is INFERRED
  afresh from `bridge.expressible_style`, never stored, on a
  maintainer's condition of 2026-08-15, and a six-class graduated
  ladder is perfectly expressible -- so nothing about a
  reclassification makes an element defer, and taking that limb would
  have overturned that rule AND the follow ruling of 2026-08-17.
  The live question was narrower: not whose ladder, but which COLOURS
  on it the plugin put there. The maintainer chose the narrow reading.
  **THE PLUGIN NOW STORES THE LADDER IT PAINTED**, in
  `dialog._painted_ladders`, and asks of each class whether the colour
  is one of its own -- a question the state can answer at ANY moment,
  which is what a delta could not do. Written wherever the plugin
  paints and at group adoption; NEVER on a follow, which runs before
  attribution and would record the dock's ladder as ours. Not stamped:
  a reopened project re-derives its baseline from the layer, which
  keeps the record out of the restore whitelist. An ABSENT entry means
  "never seen" and DECLINES, which is neither "ours" nor "theirs".
  WHAT MAKES IT ANSWERABLE IS A MEASUREMENT: on QGIS 4.0.3, `addClass`
  inserts a degenerate `(0.0, 0.0)` class at index 0 wearing the
  source symbol's grey, and EVERY SURVIVING CLASS KEEPS ITS BOUNDS BIT
  FOR BIT. So a colour can be matched back to the class it was painted
  on exactly, with no tolerance.

### C-109 — A LADDER MAY HOLD SEVERAL CLASSES WITH IDENTICAL BOUNDS, so a lookup by bounds must...

<sub>Cut from `CLAUDE.md`, lines 4420–4432 of the
2026-09-05 revision.</sub>

- **A LADDER MAY HOLD SEVERAL CLASSES WITH IDENTICAL BOUNDS, so a
  lookup by bounds must not stop at the first match.** (2026-08-20,
  and it was a defect in the fix above, caught within the hour.) A
  constant column, a tied column and `{1, 5, 9}` at k=5 all produce
  degenerate ranges, and `addClass` then inserts another `(0.0, 0.0)`
  class -- which collides with any fixture whose first real class is
  also degenerate. Returning on the first match compared the plugin's
  own colour against the placeholder grey sharing its bounds, called
  it changed, and adopted it. FOUR PASSING TESTS DID NOT SEE IT; what
  found it was driving the product and PRINTING THE RECORD at each
  stage, which is this project's own prescription and was still not
  the first thing tried. Guarded by
  `a-ladder-may-hold-two-classes-at-one-bound`.

### C-110 — WHEN CI TIMINGS MOVE, COMPARE THE SUSPECT ON A MACHINE YOU CONTROL BEFORE BELIEVING...

<sub>Cut from `CLAUDE.md`, lines 4433–4449 of the
2026-09-05 revision.</sub>

- **WHEN CI TIMINGS MOVE, COMPARE THE SUSPECT ON A MACHINE YOU
  CONTROL BEFORE BELIEVING THE ORDERING.** (2026-08-20.) Windows ran
  89 minutes against a 53-59 minute history; the largest grower was
  2.6x; and it was the one test that most exercises the path a fix
  landed the same day had opened. Every piece fitted. Measured
  locally, sequentially, in clean worktrees: 151s before against 147s
  after. The fix costs nothing. The tell was in the CI data all along
  -- several tests SHRANK in the same run, one by 57 seconds, and a
  uniform slowdown does not do that.
  TWO HABITS. Six minutes of local measurement beat a conclusion that
  would have sent somebody optimising a path that is not slow, or
  narrowing a repaint route doing exactly what it should. And RECORD
  THE HYPOTHESIS BEFORE THE VERDICT LANDS: written afterwards it would
  have been fitted to whatever number turned up, and writing it first
  is what made it falsifiable. The Windows job's own variance is worth
  knowing if a ceiling is ever sized against it: 53 to 89 minutes on
  near-identical trees, a 68% spread, far wider than the Linux legs.

### C-111 — WHEN A GUARD STARTS ANSWERING DIFFERENTLY, FOLLOW ITS RETURN VALUE INTO EVERY TUPLE...

<sub>Cut from `CLAUDE.md`, lines 4450–4476 of the
2026-09-05 revision.</sub>

- **WHEN A GUARD STARTS ANSWERING DIFFERENTLY, FOLLOW ITS RETURN VALUE
  INTO EVERY TUPLE IT IS A MEMBER OF, not only into its callers.**
  (2026-08-20, a regression from the previous day's own fix.)
  `compat.layer_data_is_available` was corrected to answer False for a
  moved file. That answer is also a term in `_layer_fingerprint`,
  which is a term in `_geometry_signature` and a CACHE KEY -- so a
  moved file made the fingerprint read `("unavailable",)`,
  `_restyle_only` bailed, and `_apply_style_change` discarded the
  refusal in silence: a colour picked after the source vanished was
  recorded, never painted and never mentioned, where before it
  repainted correctly because a restyle needs nothing from the region
  layer. The hunt that found it reported that the questions its brief
  actually asked -- the cost, the empty layer -- were both clean, and
  the defect was two hops away. A guard's callers are the easy half;
  the hard half is everywhere its ANSWER travels as data.
  **AND THE FINGERPRINT WAS ONLY HALF OF IT.** Fixed, the ramp still
  did not reach the map, because `_maybe_live_generate` asks the same
  availability question at its sixth gate and returned in front of its
  own repaint exit -- the guard-about-one-thing-in-front-of-an-exit-
  about-another shape, for the fourth time in this file. It refuses
  the TILING now and tries `_restyle_only()` first; nothing may fall
  through it, since `_extent_in_working_units` sits a few lines below
  and a dead extent segfaults QGIS. `_generate`'s own check needed
  NOTHING -- its fast path is already above it -- so the twin was
  measured and left alone rather than given a symmetrical repair, and
  a catalogue entry reverses its order so the asymmetry is guarded
  rather than remembered.

### C-112 — A REPAIR AIMED AT AN ACT MUST BE RE-AIMED AT THE ACT'S ABSENCE

<sub>Cut from `CLAUDE.md`, lines 4477–4491 of the
2026-09-05 revision.</sub>

- **A REPAIR AIMED AT AN ACT MUST BE RE-AIMED AT THE ACT'S ABSENCE.**
  (2026-08-27, two hunts from different directions in one afternoon.)
  On 2026-08-26 the stale-table drop was taught to take a saved STYLE
  with the table it removes, which mends every case where something is
  deleted. Both of the day's file-residue defects are cases where
  NOTHING IS DELETED: once because the record of what to delete lives
  on a WINDOW rather than in the file, so a dialog that never adopted
  the output GeoPackage knows of nothing to drop; once because two
  column names sanitise to ONE table, so the table is replaced and
  nothing ever looks stale -- while `layer_styles` is keyed by the
  style's NAME, and the row written for the abandoned column sits
  beside the new one carrying its whole QML.
  So ask of any repair that fires on an act: what happens on the
  journey where that act never occurs? The drop was right and its
  coverage was the question nobody put.

### C-113 — A GUARD WHOSE CONDITION IS RIGHT CAN STILL BE AIMED AT NOTHING

<sub>Cut from `CLAUDE.md`, lines 4493–4509 of the
2026-09-05 revision.</sub>

- **A GUARD WHOSE CONDITION IS RIGHT CAN STILL BE AIMED AT NOTHING.**
  (2026-08-27.) The queued restamp's new guard reads `_fieldless_build`,
  and that flag was measured TRUE at exactly the moment the defect
  fires. Its first test passed anyway with the guard mutated away,
  because the journey it drove -- a recolour to a SINGLE SYMBOL --
  never reaches the adoption that queues the restamp at all. A single
  symbol is deliberately not followed (the scope of the follow ruling
  of 2026-08-17), so the test was aimed at a door the act never opens.
  The catalogue found it; reading did not. The repair was to drive the
  recolour the way this suite's other adoption tests drive it: clone
  the renderer the layer already has, move ONE class's colour, install
  the clone.
  AND THE PREMISE CHECK LIED FIRST. The rewritten test then failed on
  its own premise, which read `layer.renderer().ranges()[0].symbol()`
  -- the freed-temporary pattern this file already records twice. A
  premise that cannot be trusted is worse than none, because its
  failure is read as the product's.

### C-114 — AN INSTRUMENT THAT HOLDS A FILE CHANGES WHAT IT MEASURES, AND BYTES REMEMBER PAGES...

<sub>Cut from `CLAUDE.md`, lines 4511–4522 of the
2026-09-05 revision.</sub>

- **AN INSTRUMENT THAT HOLDS A FILE CHANGES WHAT IT MEASURES, AND
  BYTES REMEMBER PAGES NOBODY REFERENCES.** (2026-08-27, twice inside
  one test.) A guard read a GeoPackage through a `QgsVectorLayer` it
  left alive, and the open handle made the NEXT run fail at the sqlite
  level: zero tables, read as the product's fault. Rewritten to read
  the file's raw BYTES, it then found an abandoned colour sitting in
  sqlite's freelist -- present with the dataset open, absent once
  everything had let go, with the style row itself gone in both
  readings.
  THE FILE A COLLEAGUE RECEIVES IS THE FILE AFTER IT IS CLOSED, and
  that is the only moment a byte-level claim about it means anything.
  Read through OGR and release at once, or clear the project first.

### C-115 — RETIREMENT IS A FACT ABOUT THE OBJECT, NOT AN ABSENCE IN A REGISTRY

<sub>Cut from `CLAUDE.md`, lines 4524–4540 of the
2026-09-05 revision.</sub>

- **RETIREMENT IS A FACT ABOUT THE OBJECT, NOT AN ABSENCE IN A
  REGISTRY.** (2026-08-27.) Every long-lived handler here is gated by
  "am I the dialog in charge", and that record was only ever cleared
  by SUCCESSION -- so a plugin the user DISABLED left it naming a
  dialog they had disposed of, which went on adopting dock edits,
  rewriting the project's group record and speaking into QGIS's
  message bar about controls in a window there was no longer any way
  to open, until QGIS restarted.
  THE OBVIOUS LEVER IS THE WRONG ONE AND WAS MEASURED SO. The gate
  reads "if there IS a live dialog and it is not me, drop", so None
  means "nobody has said" and clearing the record makes EVERY dialog
  believe it is in charge rather than none: the sentence the fix had
  just been written for came straight back. `_dialog_is_gone` answers
  the retirement now, because it is the question every handler puts
  first. And closing the WINDOW deliberately does not retire, since
  `open_dialog` reuses the object -- a closed window is a hidden one
  somebody may bring back with its map intact.

### C-116 — A WIDGET THAT RETAINS LAYER OBJECTS MUST BE REBUILT WHEN LAYERS ARE REMOVED, AND A...

<sub>Cut from `CLAUDE.md`, lines 4542–4564 of the
2026-09-05 revision.</sub>

- **A WIDGET THAT RETAINS LAYER OBJECTS MUST BE REBUILT WHEN LAYERS
  ARE REMOVED, AND A DEAD POINTER'S ADDRESS GETS REUSED.**
  (2026-08-27, found by the saving branch's first full suite.) The
  region chooser keeps the plugin's own output out of its list
  through `setExceptedLayerList`, which stores the layer OBJECTS.
  That list was rebuilt at construction, at a project read, at a
  resume and after a landing -- and never when layers were REMOVED.
  So after File > New the combo went on excluding a set of destroyed
  pointers, and a layer allocated where a dead one had been was
  excluded for being somebody else: the chooser offers NOTHING while
  the project plainly holds a polygon layer, and Generate refuses for
  want of a region with nothing on screen to explain it.
  THE SWEEP IS THE TRANSFERABLE PART. Ask which widgets are handed
  layer OBJECTS that they keep: here `setExceptedLayerList` is the
  only one, since `setLayer` names a current layer whose lifetime the
  combo follows and `setFilters` takes flags. One member, swept
  rather than assumed.
  AND IT IS GUARDED BY THE SUITE RATHER THAN BY AN ENTRY, deliberately
  and in writing at the fix: the harm needs an address to be reused,
  so the test that caught it fails in a full run and passes when run
  alone. An entry would report SURVIVED most times it was judged,
  which is a false negative and worse than no entry -- the one shape
  this catalogue must not carry.

### C-117 — A LAYER BUILT ON ANOTHER LAYER'S SOURCE IS THAT LAYER TO ANYTHING THAT LOOKS UP BY...

<sub>Cut from `CLAUDE.md`, lines 4566–4580 of the
2026-09-05 revision.</sub>

- **A LAYER BUILT ON ANOTHER LAYER'S SOURCE IS THAT LAYER TO ANYTHING
  THAT LOOKS UP BY SOURCE.** (2026-08-27.) The map-unit outlines layer
  is built on the REGION'S OWN SOURCE, deliberately, since nothing is
  copied; and it carries `weavingspace_output`, which is what keeps it
  out of the region chooser. Each fact is right alone and they collide
  in a walk that filters by neither: recovery took whichever layer
  QGIS's map yielded first with a matching source, and `setLayer` on a
  layer the combo EXCLUDES leaves the chooser empty -- then returned,
  in front of its own two fallbacks. A resume reported success beside
  a blank chooser, every element's variable lost, and a Generate that
  launched nothing and said nothing.
  WHEN YOU RESOLVE AN IDENTIFIER TO AN OBJECT, ASK WHO ELSE ANSWERS TO
  IT, and whether the answer is one the caller is ALLOWED to use. Then
  check that the assignment took: a `setLayer` that did not land must
  fall through rather than return as though it had.

### C-118 — ENUMERATE THE PRODUCERS OF A SECOND CLAIMANT, NOT JUST THE ONE YOU BUILT

<sub>Cut from `CLAUDE.md`, lines 4582–4596 of the
2026-09-05 revision.</sub>

- **ENUMERATE THE PRODUCERS OF A SECOND CLAIMANT, NOT JUST THE ONE YOU
  BUILT.** (2026-08-27.) The paired-layer rule of 2026-08-16 says a
  paired artefact inherits the identity property of the thing it is
  paired with, so every lookup keyed on that property gains a second
  answer. Its fix enumerated the plugin's own twin and stopped there.
  QGIS's own DUPLICATE LAYER copies custom properties, so a copy of an
  output layer claims its element too -- and adoption, keeping the
  LAST claimant in panel order, adopted a copy sitting below the
  original. The next Generate replaced the copy and left the user's
  real layer standing over the new map, under an identical name, never
  updated again, with nothing said.
  NOTHING IS DELETED ON A GUESS: the two layers are indistinguishable,
  a GeoPackage-backed copy shares even its source, and keeping a copy
  of yesterday's map is a reasonable thing to do. The first in panel
  order wins and the plugin SAYS which one it will replace.

### C-119 — A DANGLING REFERENCE IS NOT A DISAGREEMENT, WHICH IS WHY NOTHING COMPLAINS

<sub>Cut from `CLAUDE.md`, lines 4598–4619 of the
2026-09-05 revision.</sub>

- **A DANGLING REFERENCE IS NOT A DISAGREEMENT, WHICH IS WHY NOTHING
  COMPLAINS.** (2026-08-27.) An element may take its classes from
  another element's LAYER, and the choice is stored as
  `layer:<layer id>` -- while a re-tile gives every element a new
  layer with a new id. So one Generate after the choice, the token
  named an object that no longer existed: the donor read as an
  UNREADABLE class source, the follower kept the colours it already
  had under the keep-the-map promise, and two elements went on drawing
  one column in two sets of colours for good. Every mechanism behaved
  exactly as designed.
  References are repointed as the layers are replaced -- in the record
  AND in the combo, since `_assignments` reads the WIDGET and healing
  the record alone was measured to last until the next rebuild. The
  donor's CONTENT is stamped too, as a QML class source has been since
  2026-08-13; a reference stamped by name alone can never notice the
  thing it points at moving.
  WHAT IS STILL OPEN, and is a ruling rather than a defect: a donor
  that MOVES is followed one run late, because the landing reads its
  template from the donor's outgoing layer while the donor is being
  re-seeded in the same pass. Curing it decides the ORDER elements are
  seeded in, and two elements may take their classes from each other
  -- driven 2026-08-27, and it settles rather than churning.

### C-120 — BREAK EVERY ROUTE AT ONCE, OR THE CATALOGUE MEASURES THE OTHER ONE

<sub>Cut from `CLAUDE.md`, lines 4621–4633 of the
2026-09-05 revision.</sub>

- **BREAK EVERY ROUTE AT ONCE, OR THE CATALOGUE MEASURES THE OTHER
  ONE.** (2026-08-27, three times in a day.) A fix written as two
  guards -- skip our own output AND check the chooser took -- survives
  having either one mutated, because the other still sends the walk to
  its fallbacks. An older entry that had caught for weeks began to
  SURVIVE the moment a new writer covered the same ground. And an
  entry aimed at the recorder half of a two-site fix passed with that
  half deleted outright, because the arm deciding the carry made the
  recorder's case unreachable.
  A SURVIVOR IS INFORMATION, NOT A NUISANCE: it says the behaviour is
  held redundantly, or that the entry is aimed at a case nothing can
  reach. Both are worth knowing, and the answer is the same -- mutate
  the SHARED thing, or say at the entry why it now needs both halves.

### C-121 — AN INERT MUTATION AND A REDUNDANTLY HELD ONE BOTH REPORT SURVIVED, AND THEY NEED...

<sub>Cut from `CLAUDE.md`, lines 4661–4670 of the
2026-09-05 revision.</sub>

- **AN INERT MUTATION AND A REDUNDANTLY HELD ONE BOTH REPORT SURVIVED,
  AND THEY NEED OPPOSITE REPAIRS.** (Same day.) An entry excluding
  modes from the no-data split was mutated by adding a literal to a
  list read from `mode` -- while deferral lives in `mode_raw`, so the
  mutation matched nothing and changed nothing. That reads exactly
  like a test too weak to notice. THE DISCRIMINATOR IS TO KILL THE
  SITE OUTRIGHT: if the test then fails, the site is live and the
  mutation was inert; if it still passes, something else is answering.
  Four attempts went into that entry before the question was put that
  way round.

### C-122 — RANKING CANDIDATES CANNOT CHANGE A VERDICT; UNDER A CAP IT DECIDES WHAT WAS ASKED

<sub>Cut from `CLAUDE.md`, lines 4696–4705 of the
2026-09-05 revision.</sub>

- **RANKING CANDIDATES CANNOT CHANGE A VERDICT; UNDER A CAP IT DECIDES
  WHAT WAS ASKED.** Sampling "the eight most focused" tests covering a
  line by the SIZE of their coverage record put region outlines and
  legend labels to a mutation about layer removal, and "0 of 8 notice"
  read as evidence. Rank by word overlap with the mutated line first,
  as `rank_covering_tests` does, always include the entry's own test,
  and PRINT what the cap dropped.
  AND A NEGATIVE FROM A CAPPED SEARCH IS NEVER EVIDENCE OF ABSENCE. A
  test that fails under the mutation genuinely notices; silence only
  says the answer was not in the sample.

### C-123 — `mutation_check` APPLIES EXACTLY ONE REPLACEMENT, BY DESIGN, so a fact held at two...

<sub>Cut from `CLAUDE.md`, lines 4715–4723 of the
2026-09-05 revision.</sub>

- **`mutation_check` APPLIES EXACTLY ONE REPLACEMENT, BY DESIGN**, so
  a fact held at two DISTANT sites cannot be guarded by any single
  entry. The run signature's identity and fingerprint terms are 47
  lines apart, and an anchor spanning both breaks on any edit between
  them. Where the sites are adjacent, widen the anchor; where they are
  not, the honest record is a retirement with the measurement and the
  redundancy written at the test. Whether the tool should take a LIST
  of replacements is a real question about campaign machinery and is
  recorded in ROADMAP.md rather than decided in passing.

### C-124 — A REPAIR'S OWN REPAIR NEEDS THE SAME SUSPICION, AND THE FIRST ONE CAN BE WORSE THAN...

<sub>Cut from `CLAUDE.md`, lines 4725–4741 of the
2026-09-05 revision.</sub>

- **A REPAIR'S OWN REPAIR NEEDS THE SAME SUSPICION, AND THE FIRST ONE
  CAN BE WORSE THAN THE DEFECT.** (2026-08-28, the moved-data notice,
  wrong three ways in one evening and every one of them mine.) It kept
  ONE reading in a session-wide slot and compared it against whichever
  dataset the region chooser held, so returning to an earlier map
  through the group chooser told somebody their file disagreed with
  itself when nothing had been touched. THE FIRST FIX FOR THAT TRADED A
  FALSE ALARM FOR A MISSED ONE: carrying the layer id ALONGSIDE one
  reading silenced the notice on a map whose data really had moved. The
  readings are keyed BY DATASET now, which is the shape this file
  already states twice -- a fact about a subject belongs keyed by that
  subject -- arriving for the third time in two days.
  AND A NOTICE CANNOT BE TESTED BY SILENCE. The quiet arm passes just
  as well when the sentence has been deleted outright, so the guard
  asserts BOTH answers in one test: quiet where nothing moved, speaking
  where it did. Where a rule has two answers, a reader meeting one
  takes it for the whole rule.

### C-125 — A GUARD WHOSE PRECONDITION IS A LOSSY DIGEST IS ONLY AS GOOD AS WHAT THE DIGEST OMITS

<sub>Cut from `CLAUDE.md`, lines 4742–4753 of the
2026-09-05 revision.</sub>

- **A GUARD WHOSE PRECONDITION IS A LOSSY DIGEST IS ONLY AS GOOD AS
  WHAT THE DIGEST OMITS.** (Same day.) The same notice read
  `_layer_fingerprint` -- the feature count, the extent, the field
  names, the CRS -- none of which an ordinary VALUE EDIT moves. So the
  case it was written for, and quoted in its own commit message
  ({7,17,27,37} beside a map drawn from {0,1,2,3}), was the one case it
  could not report: a keystroke unrelated to whether the data had moved
  decided whether anybody was told. It carries a per-dataset edit count
  beside the fingerprint now. THE COUNTERFACTUAL PAIR IS THE TECHNIQUE
  WORTH COPYING -- two journeys corrupting the data identically,
  differing by one keystroke, so the guard's own machinery supplies the
  positive control.

### C-126 — OWNERSHIP IS NOT A NAME PREFIX, AND AN ELEMENT ID IS A LETTER EVERY MAP SHARES

<sub>Cut from `CLAUDE.md`, lines 4754–4767 of the
2026-09-05 revision.</sub>

- **OWNERSHIP IS NOT A NAME PREFIX, AND AN ELEMENT ID IS A LETTER EVERY
  MAP SHARES.** (Same day.) The stale-table drop scoped itself to "this
  map's own elements" and decided that by `tiles_<id>`, so saving into
  a GeoPackage holding a colleague's map DELETED their `tiles_a_*` and
  `tiles_b_*` while leaving their `tiles_zz_*` and their own tables --
  one line after a question promising to "leave the rest of the file
  alone", and against the method's own Returns block. It is asked of
  the FILE now, through one helper both the question and the drop
  share.
  AND THE ANSWER IS TAKEN BEFORE THE WRITE. Ownership is partly "have
  we saved here in this session", which the very press about to happen
  makes true of any file at all -- so asking afterwards answers yes for
  a stranger's GeoPackage. When a guard reads state the act is about to
  change, take the reading first and pass it in.

### C-127 — A GATE THAT READS RAW SOURCE TEXT CAN BE MOVED BY A COMMENT

<sub>Cut from `CLAUDE.md`, lines 4768–4778 of the
2026-09-05 revision.</sub>

- **A GATE THAT READS RAW SOURCE TEXT CAN BE MOVED BY A COMMENT.**
  (Same day.) `test_pypi_provisioning_is_reached_only_through_consent`
  holds a hard rule by indexing three markers in `plugin.py` and
  requiring their ORDER. A note added above the consent call, mentioning
  `provision_from_pypi` to explain what it fetches, put the download's
  index before the dialogue's and failed the gate with the code
  perfectly correct. It tokenizes and strips comments now.
  THE FAMILY IS THE ROADMAP GATE'S, from the other side: there a
  sentence QUOTING the phrase could satisfy the gate; here a sentence
  mentioning a marker could break it. When a gate reads prose for a
  decision, decide what counts as prose.

### C-128 — A CONSENT DIALOGUE THAT ENUMERATES MUST BE DIFFED AGAINST WHAT THE CODE ASKS FOR

<sub>Cut from `CLAUDE.md`, lines 4779–4793 of the
2026-09-05 revision.</sub>

- **A CONSENT DIALOGUE THAT ENUMERATES MUST BE DIFFED AGAINST WHAT THE
  CODE ASKS FOR.** (Same day, and it is a HARD RULE breached since the
  initial commit.) The box named the missing scientific packages;
  `provision_from_pypi` also fetches the pure-python support
  distributions the main ones import at runtime -- its own docstring
  says so -- so somebody who read "Missing or too old: geopandas" and
  approved had SEVEN distributions fetched from pypi.org, against
  metadata.txt's promise that the plugin "shows exactly what it would
  fetch and asks first". The box is handed the full list now, computed
  by the same question the loop asks.
  ITS REGISTERED TEST COULD NOT SEE IT, which is the transferable half:
  the test asserted the box names what it was HANDED. A dialogue's
  promise is about what the software DOES, so the comparison has to
  reach the code's own requests -- recorded by stubbing the seam where
  the decision is taken, not the network.

### C-129 — A SITE NAMED BY READING IS A HYPOTHESIS, AND IT READS EXACTLY LIKE ONE SOMEBODY PROVED

<sub>Cut from `CLAUDE.md`, lines 4802–4813 of the
2026-09-05 revision.</sub>

- **A SITE NAMED BY READING IS A HYPOTHESIS, AND IT READS EXACTLY LIKE
  ONE SOMEBODY PROVED.** (2026-08-20, the same defect.) Where that
  refusal lived was worked out from the source, written into the
  handover, and copied from there into ROADMAP.md, MAINTAINING.md and
  docs/TESTING.md in one documentation round -- all four naming
  `_generate`, which a debounced tick never reaches, and all four
  calling the refusal silent when it says a sentence that is false.
  One dump line at each of that path's ten gates answered it in a
  single run. So: when you write down WHERE a defect is, say how you
  know; and where a path can refuse for ten reasons, make each one
  NAME ITSELF -- live update pausing without saying why has cost this
  project two diagnoses now.

### C-130 — A GUARD THAT REBUILDS A LAYER FROM ITS SOURCE STRING LOSES EVERYTHING THE USER SET...

<sub>Cut from `CLAUDE.md`, lines 4823–4831 of the
2026-09-05 revision.</sub>

- **A GUARD THAT REBUILDS A LAYER FROM ITS SOURCE STRING LOSES
  EVERYTHING THE USER SET ON THE LAYER.** (2026-08-28.) A CRS somebody
  assigned -- the ordinary repair for a shapefile with no `.prj` --
  lives on the layer, never in `source()`. The outlines overlay was
  rebuilt from the string, so it drew in the FILE's system while the
  tiles drew in the assigned one, fourteen thousand kilometres away
  and zero ink pixels over the map. GREP FOR `QgsVectorLayer(
  something.source()`, not for the word CRS: subset strings, scale
  ranges, custom properties and names are all in the same position.

### C-131 — A COUNT QUOTED TO A PERSON MUST BE ASKED OF THE GEOMETRY, NOT OF TWO TOTALS

<sub>Cut from `CLAUDE.md`, lines 4832–4840 of the
2026-09-05 revision.</sub>

- **A COUNT QUOTED TO A PERSON MUST BE ASKED OF THE GEOMETRY, NOT OF
  TWO TOTALS.** (2026-08-28.) The icon-mode sentence subtracted a TILE
  count from an AREA count to say which elements were short. A unit's
  tile sits off the centre it was placed at, so the difference is not
  the number of uncovered areas in either direction: it named b, c and
  d while a was missing from three areas and b from none. Where a
  project has already corrected a count twice -- this one had -- check
  the third against the map rather than against the code, because the
  test guarding it was written from the same arithmetic.

### C-132 — A PER-FILE FACT MUST NOT LIVE ON A SESSION-WIDE CONTROL

<sub>Cut from `CLAUDE.md`, lines 4841–4858 of the
2026-09-05 revision.</sub>

- **A PER-FILE FACT MUST NOT LIVE ON A SESSION-WIDE CONTROL.**
  (2026-08-28, round ten, and it was a repair of mine that put it
  there.) "Include the source data" is one checkbox and the answer it
  stands for belongs to a FILE: whether THAT GeoPackage carries a copy
  of the region. Reading the box alone meant a recipient who had never
  touched it stripped the copy a sender had deliberately included --
  the drop was written for the act of unticking and fired for the
  act's ABSENCE. Setting the box from the file's record cured that and
  bought two new harms in one line: the recipient's own next Save
  copied THEIR private region out unasked, and a person who had ticked
  the box on purpose had it silently unticked by opening any file
  without a copy in it.
  THE SHAPE IS GENERAL. When a control's value is asked about a
  subject the control does not name -- a file, a layer, an element --
  keep the fact keyed by that subject and let the control mean what it
  has always meant, which is a standing preference. Then say which one
  wins: here the file's record wins while the person has not spoken,
  and a deliberate untick still means exactly what it says.

### C-133 — A DISPLAY RULE IS ONLY DISPLAY-ONLY IF NOTHING RE-READS THE DISPLAY

<sub>Cut from `CLAUDE.md`, lines 4859–4872 of the
2026-09-05 revision.</sub>

- **A DISPLAY RULE IS ONLY DISPLAY-ONLY IF NOTHING RE-READS THE
  DISPLAY.** (2026-08-28.) `MarkableSpinBox.textFromValue` abbreviates
  a large number to "1.02M" and its docstring says it touches neither
  the stored value nor the validator. True of everything this project
  does and FALSE OF QT, which calls `interpret()` on Return and reads
  the display back through `valueFromText`. So pressing Return in a
  bound box, typing nothing, replaced a floor of 1,015,001 with
  1,020,000, moved every class break and moved four more of fifty
  areas out of range -- shipped in v0.24.3, on any column above about
  1e5 or below about 1e-4.
  This file already says a display rule belongs in `textFromValue`
  because `decimals` governs storage as well as display. What it did
  not say is that the framework may complete the circle anyway. Ask of
  any formatting override: who else calls the reader?

### C-134 — A SUITE CAN HOLD A CONTROL AT A VALUE NO USER HOLDS

<sub>Cut from `CLAUDE.md`, lines 4873–4881 of the
2026-09-05 revision.</sub>

- **A SUITE CAN HOLD A CONTROL AT A VALUE NO USER HOLDS.**
  (2026-08-28.) Every resume test in this suite unticks live update,
  which is ON by default -- so the whole family was driven at a
  setting nobody has, and pressing Load with the default re-tiled the
  opened map into memory a second later and emptied the saved file.
  The hunt that found it swept all four debounce windows first and
  ruled every one out; the hiding place was not a race but a default.
  ASK OF ANY TEST FAMILY WHICH CONTROL IT HOLDS CONSTANT, and whether
  a person holds it there.

### C-135 — A RECORD SEEDED BY ADOPTION IS A RECORD THAT ASSUMES A PROJECT

<sub>Cut from `CLAUDE.md`, lines 4882–4893 of the
2026-09-05 revision.</sub>

- **A RECORD SEEDED BY ADOPTION IS A RECORD THAT ASSUMES A PROJECT.**
  (2026-08-28.) The stale-table drop took its candidates from the
  session's own record of what it had written, plus the tables of
  elements the map still has -- and a DROPPED element is in neither.
  Its docstring called that "the shrank-design case the session record
  covers", which holds only while there is a group to adopt: that
  record is seeded by adoption and cleared when a project is replaced.
  Close QGIS without saving the .qgz, reduce the design, save to the
  same file, and the dropped elements' tables, columns and VALUES stay
  in the file somebody sends on. The file's own record is asked now.
  The general question: when a rule leans on a record, ask what SEEDS
  that record and what a journey without the seeding act looks like.

### C-136 — AN INTERMITTENT FAILURE UNDER LOAD CAN BE THE SUITE INTERMITTENTLY REACHING A REAL...

<sub>Cut from `CLAUDE.md`, lines 4894–4947 of the
2026-09-05 revision.</sub>

- **AN INTERMITTENT FAILURE UNDER LOAD CAN BE THE SUITE INTERMITTENTLY
  REACHING A REAL DEFECT.** (2026-08-28.) A per-test coverage
  re-record failed one test of 645, in a shard running beside two
  others on a loaded machine. Everything about it said harness: the
  candidate's own suite had passed it an hour earlier, it passed alone
  plain, alone under the recorder's instrumentation twice, and nine
  times across three concurrent copies. One failure against fourteen
  clean runs is exactly what flakiness looks like, and this file
  already carries the rule that a test tuned in one harness is
  re-tuned by another.
  IT WAS A DEFECT, and the tell was in the log rather than in the
  odds: `_settle` waits on the EVENT -- no task, no live timer, no
  preview timer -- and reports a timeout in different words, so the
  dialog had genuinely finished and the orphans were still there. A
  failure that survives the thing settling is not a race the test lost.
  WHAT SETTLED IT WAS STAGING THE CONDITION RATHER THAN CHASING THE
  FREQUENCY. The suite's case presses Generate about 150 ms after
  putting a run in flight and hopes the run is still going; on this
  Mac it usually is not. A probe that checked `_task is not None` in
  the same breath as the press reproduced it FIRST TIME, on both arms,
  deterministically. Where a case depends on a window, do not measure
  how often you land in it -- close the window.
  AND THE HARM WAS OVERSTATED, MEASURED THE SAME DAY. A person cannot
  reach it: `generate_btn.setEnabled(False)` runs before the task
  starts, and the only two sites that re-enable it are `_finish_run`
  and the zombie recovery, which clears `_task` first. Driven at a
  fine spacing and read mid-flight -- `task=True`, button disabled, a
  real `click()` setting nothing, a direct `_generate()` setting
  `_press_pending` at once. So the state is produced by the SUITE and
  not by a user: `test_two_generates_with_different_families_keep_
  their_elements_apart`, the test that failed under load, calls
  `dlg._generate()` three times, as `test_race_double_generate` has
  since long before this.
  THE FIX STANDS AS DEFENCE IN DEPTH and the mechanism below is exact;
  what was wrong was the sentence around it, written in four documents
  and in a candidate's tester notes that told people to press a button
  the interface greys out for the whole run. This is this file's own
  rule about a site named by reading, arriving at a HARM instead: the
  mechanism was measured and the reachability was assumed, and only
  one of those was checked. ASK OF ANY DEFECT WHETHER THE JOURNEY THAT
  REACHES IT IS ONE A PERSON CAN DRIVE, and measure that as separately
  as you measure the mechanism.
  THE DEFECT ITSELF IS THIS FILE'S OWN SHAPE: one flag gating two
  different things. `_generate` queued a press on `_live_pending`,
  `_finish_run` honoured that by starting the LIVE timer, and
  `_maybe_live_generate` returns at its second gate whenever live
  update is off -- so with the box unticked a button press was
  remembered and then thrown away in silence, the map keeping the
  elements of the run in flight while the table asked for the new
  design. A deferred live tick and a deferred button press are not
  the same fact. Guarded by `test_a_generate_pressed_during_a_run_is_
  not_swallowed`, which drives BOTH arms because the live-on arm was
  correct throughout, and by the catalogue entry
  `a-queued-press-is-a-press-not-a-live-tick`.

### C-137 — A REPORT ABOUT A VERSION OR A BEHAVIOUR IS FIRST A QUESTION ABOUT WHICH BUILD IS...

<sub>Cut from `CLAUDE.md`, lines 4949–4987 of the
2026-09-05 revision.</sub>

- **A REPORT ABOUT A VERSION OR A BEHAVIOUR IS FIRST A QUESTION ABOUT
  WHICH BUILD IS INSTALLED.** (2026-08-29.) The maintainer reported
  that the title bar "no longer shows the rc version properly". The
  plugin was right at every step: `_plugin_version()` reads `version=`
  out of the INSTALLED `metadata.txt`, `build.py` substitutes the
  candidate label into the copy inside the archive, and the published
  `0.24.4rc5` zip genuinely carries `version=0.24.4rc5`. What was
  wrong was the copy on the machine -- of two QGIS profiles, `default`
  held the candidate (whole plugin written at the candidate's own
  build time) and `testing` held a plain `0.24.4` written wholesale
  an hour and a half later. The title bar was faithfully reporting a
  build that was not the candidate.
  ASK WHAT IS INSTALLED BEFORE READING ANY CODE. One loop over
  `build.installed_copies()` printing each profile's `version=` line
  and its mtime answers it in seconds, and it is the same rule as
  measuring the session that is broken rather than building a seventh
  reproduction -- arriving at an INSTALL rather than at a dump.
  AND TWO HYPOTHESES OF MINE WERE WRONG BEFORE THAT ONE, both caught
  by checking rather than by reasoning. `build.py` INSTALLS ONLY UNDER
  `--rc`: the install block sits inside `if args.rc:` and returns
  before the plain path, so the packaging check cannot have overwritten
  a profile, and the gate's own log confirmed it printed no `updated`
  line. The profiles are also not symlinks or hard links into the
  working tree.
  IT WAS IDENTIFIED ON 2026-08-30, by taking a reading BEFORE
  overwriting the evidence -- the maintainer had asked for the
  candidate to be put back, which would have destroyed it. The build
  in that profile was BYTE-IDENTICAL to the unversioned
  `dist/weavingspace_qgis.zip` across all 31 members, against exactly
  one differing member versus the rc5 zip. So an UNGATED artefact had
  been installed over a gated candidate, and the title bar had been
  reporting it faithfully ever since. Nothing in the tree installs an
  unversioned zip, so it was a hand-run of `install_into`.
  THE LESSON IS THE ORDER. A fix that overwrites the evidence is a
  diagnosis you will never make: the reading cost five minutes and
  turned an open ledger row into a closed one, and it turned the
  unversioned-artefact rule from a tidiness argument into a measured
  harm. When an instruction would destroy the state a question is
  about, take the measurement first and say that you did.

### C-138 — A CLAIM'S MECHANISM IS USUALLY RIGHT AND ITS HARM USUALLY IS NOT, AND THE DOOR IT...

<sub>Cut from `CLAUDE.md`, lines 4988–5009 of the
2026-09-05 revision.</sub>

- **A CLAIM'S MECHANISM IS USUALLY RIGHT AND ITS HARM USUALLY IS NOT,
  AND THE DOOR IT NAMES IS WHEREVER THE HUNT WAS STANDING.**
  (2026-08-29, taking sixteen owed claims to the end.) This file
  already says a harm named by reading is a hypothesis. What a whole
  verification session adds is the RATE: of fourteen claims closed,
  three had their harm corrected and one its door widened, while the
  mechanism each named was exact.
  THE HARM IS USUALLY QUIETER AND LATER than the claim says. "The
  recipient's first Generate repaints the follower" was really "the
  follower keeps the colours it inherited, and stops following its
  donor from then on" -- nothing looks wrong at all until somebody
  moves the donor, which may be days later. A control arm on the
  LINK rather than on today's colours is what showed it.
  AND THE DOOR IS WORTH ONE EXTRA ARM. A claim reported at the Load
  door bit hardest on the reopened-plugin door, which the hunt had no
  reason to try and which the code's own docstring calls something
  users do constantly. One arm, and it doubled what the repair was
  worth.
  TWO OF THE FOURTEEN WERE CLOSED BY A FIX WRITTEN FOR ANOTHER
  CLAIM, both checked on the tree the hunt read rather than assumed
  -- and both still owed a GUARD at their own door, because a claim
  that has stopped reproducing is not a claim that is tested.

### C-139 — A CALLABLE THAT OUTLIVES ITS DIALOG MUST ASK BEFORE IT TOUCHES IT, AND A LAMBDA IS...

<sub>Cut from `CLAUDE.md`, lines 5011–5039 of the
2026-09-05 revision.</sub>

- **A CALLABLE THAT OUTLIVES ITS DIALOG MUST ASK BEFORE IT TOUCHES
  IT, AND A LAMBDA IS NOT A BOUND METHOD.** (2026-08-29, a
  reproducible SEGMENTATION FAULT.) Qt drops a connection to a bound
  METHOD when the receiving QObject dies. A LAMBDA is an ordinary
  Python object: Qt keeps it alive and goes on calling it, and
  reaching `self.anything` through a deleted sip wrapper crashes the
  process rather than raising -- so it happens BEFORE any handler's
  own retirement gate can run. `cleared` and `readProject` are PROJECT
  signals and reach every dialog a session has ever opened; an element
  layer outlives the dialog that made it.
  THREE SITES, ONE SHAPE, and each was written by somebody who knew
  the rule: a handler with no gate at all that queued
  `singleShot(0, lambda: setattr(self, ...))`; a closure that DID
  guard and wrote to `self` on the line above the guard; and two layer
  signals plus the project read connected to bare lambdas. The second
  is this file's own row 25 of 2026-08-27 met again -- A GUARD WHOSE
  WHOLE JOB IS BEING SAFE ON A DEAD OBJECT MAY NOT TOUCH THAT OBJECT
  BEFORE ASKING WHETHER IT IS DEAD.
  WHAT IT COST is worth stating because it is not a wrong map: in a
  sharded suite it is a shard that stops with no verdict at all, and
  in QGIS it is the application closing on somebody who has opened the
  plugin a few times and then chosen File > New. It was found by
  running twelve tests in one process, not by any single test.
  GUARDED BY THE SHAPE. `test_nothing_long_lived_is_connected_to_a_
  bare_lambda` parses `dialog.py` and refuses a bare lambda on any
  signal from something the dialog does not own, or on any timer. Its
  scope is exactly the hazard, so it needs no exemptions: a lambda on
  a WIDGET's own signal is safe, the widget being a child that dies
  with its parent.

### C-140 — A WIDTH IN PIXELS IS A CLAIM ABOUT A FONT, AND SETTING A FONT IS NOT SWITCHING A...

<sub>Cut from `CLAUDE.md`, lines 5041–5062 of the
2026-09-05 revision.</sub>

- **A WIDTH IN PIXELS IS A CLAIM ABOUT A FONT, AND SETTING A FONT IS
  NOT SWITCHING A PLATFORM.** (2026-08-29, and the second half is the
  part that will catch somebody again.) The assignment table's nine
  column widths were constants measured against the 9pt Sans Serif
  that `QT_QPA_PLATFORM=offscreen` supplies -- which every runner and
  every CI job sets. At a desktop 13pt the same columns need 1096px
  against the 947 they were pinned to, so every cell but one elided:
  "Quant: Equal inter..." on the chooser whose whole job is saying
  which style a row wears. They grow to their content now.
  I READ THE SLACK AT THE WRONG FONT AND SAID SO OUT LOUD, which is
  why this is here: the Colour ramp cell has 8px spare at 9pt and is
  10px SHORT at 13pt, and I offered "narrow the columns" as though
  there were room. A figure taken from the harness font is a figure
  about the harness.
  AND A FONT IS NOT A PLATFORM. Setting `QApplication.setFont` under
  offscreen reproduces the column metrics and NOT the window
  assembly: the dialog's minimum size hint reads 1279 at both 9pt and
  13pt, while cocoa gives 1334. So a guard can check what a COLUMN
  needs anywhere, and no guard here or on CI can see the window's own
  overshoot at all -- which is why the ceiling was re-derived from the
  measurement rather than defended by a check, and why the test says
  so instead of implying otherwise.

### C-141 — A RESTORE IS A LANDING, FOR EVERYTHING THAT ASKS WHETHER THE CONTROLS DESCRIBE THE MAP

<sub>Cut from `CLAUDE.md`, lines 5064–5084 of the
2026-09-05 revision.</sub>

- **A RESTORE IS A LANDING, FOR EVERYTHING THAT ASKS WHETHER THE
  CONTROLS DESCRIBE THE MAP.** (2026-08-28.) `_last_geometry_sig` is
  how `_restyle_only` knows the tiles on screen are the tiles these
  controls ask for, and only `_add_output_layers` ever set it -- so on
  a map this dialog did not DRAW the restyle path was unreachable at
  its first line. A colour picked in the editor went into the record,
  the map kept what it had, and nothing was said: on a map opened with
  Load, and on one adopted by reopening the plugin, which is a journey
  the adoption's own docstring calls something users do constantly.
  IT IS SET WHERE THE RECORD IS APPLIED, which is the one place all
  three doors pass through and the moment the claim becomes true --
  the controls have just been written FROM the group's own record, so
  they describe the map its layers hold, exactly as a landing's
  snapshot describes what it drew. A group with no record never
  reaches that line and keeps a null signature, which is the honest
  answer rather than an omission.
  THE GENERAL FORM, and this project has the mirror of it already: ask
  of any record whose meaning is "these two things agree" WHO ELSE
  brings them into agreement. A landing is the obvious writer; a
  restore is the quiet one, and a fact only the obvious writer sets is
  a fact that is false on every journey the other one owns.

### C-142 — A RECOVERY MUST REPORT WHICH OF ITS ROUTES ANSWERED, AND WHAT IS STAMPED IS WHAT IT...

<sub>Cut from `CLAUDE.md`, lines 5086–5113 of the
2026-09-05 revision.</sub>

- **A RECOVERY MUST REPORT WHICH OF ITS ROUTES ANSWERED, AND WHAT IS
  STAMPED IS WHAT IT LANDED ON.** (2026-08-29, ledger row 23, and the
  two halves of that claim turned out to be one mechanism.) A
  self-contained GeoPackage records the region its SENDER drew from,
  which on their machine is an ordinary layer and on the recipient's
  is a path that does not exist -- so the data comes back from the
  copy inside the file, and the record and the layer in force stop
  describing the same thing. Both resume branches stamped the group
  with the RECORD, so nothing in the recipient's project ever answered
  to it: `_point_the_chooser_at` walks for a layer matching that
  source, finds none, and leaves the chooser silently wherever it was.
  WITH TWO SENDERS' MAPS OPEN THAT IS THE OTHER SENDER'S DATA.
  Returning to the first map through the group chooser took its group,
  its design and its output path -- and the second sender's region, so
  the next Generate re-tiled it from their data and the output path
  being RIGHT is what made it worse: the next Save would have written
  that over the first sender's own file.
  `_recover_the_source` returns the source it landed on now, and the
  stamps fall back to the record only where it landed on NOTHING --
  which keeps the reason the code was written that way, since a failed
  recovery must not file the resumed group under whatever dataset the
  chooser happens to hold. Both answers are asserted in one test,
  because a reader meeting either alone would take it for the whole
  rule.
  THE GENERAL FORM: where one fact has a RECORDED value and a
  RESOLVED one, ask which of them a later lookup will be able to
  find. A record describes where something came from; only the
  resolution describes where it IS.

### C-143 — "ALREADY THERE" IS A QUESTION FOR THE FILE, NOT FOR A STRING THAT NAMES IT

<sub>Cut from `CLAUDE.md`, lines 5115–5147 of the
2026-09-05 revision.</sub>

- **"ALREADY THERE" IS A QUESTION FOR THE FILE, NOT FOR A STRING THAT
  NAMES IT.** (2026-08-29, ledger row 35.) A save treats a layer whose
  source already names a table in this file as saved already --
  correctly, since the second press on any map meets it -- and it
  asked the SOURCE STRING, which nobody rewriting the file can change.
  So when a colleague saved the shared GeoPackage while this map was
  open, moving one element to another column, that element was skipped
  as though it had been written AND its name went into the written
  set; the stale-table drop then removed the table the colleague HAD
  written, since it belongs to an element this map has and was not
  among the names just written. THE ELEMENT LEFT THE FILE ALTOGETHER,
  both people lost it, and the plugin said "Saved".
  NOTHING CAN BE WRITTEN IN ITS PLACE, and measuring that is what
  decided the repair's shape rather than any preference: a layer whose
  table was dropped under it answers `isValid` True, `dataProvider().
  isValid()` True and `featureCount()` 40, and yields ZERO features.
  This is the cached-answer trap of ledger row 32 met for the third
  time, and writing such a layer would replace a real table with an
  empty one.
  SO THE SAVE WRITES WHAT IT CAN, REMOVES NOTHING, AND SAYS SO. The
  drop's candidates are this session's record and the file's own, and
  its reasoning holds only while nobody else has touched the file:
  once a table has gone from under us, a table that looks like our
  abandoned one is just as likely to be their current one. Nothing is
  deleted on a guess.
  IT NEEDED TWO PROCESSES AND A RENDEZVOUS, because a running QGIS
  serves its own cached pages and the drop is gated on the file being
  the saver's own -- the first arrangement had the colleague meeting
  somebody else's file, where their drop returns at its first line and
  the precondition never existed at all. The SUITE stages the file
  state instead: what a colleague leaves behind is a state, not a
  race, and where a case depends on a window the answer is to close
  the window rather than to measure how often you land in it.

### C-144 — A SAVE THAT PUMPS THE EVENT LOOP MUST TAKE ITS BUTTONS DOWN, AND THE TWO ARE ONE...

<sub>Cut from `CLAUDE.md`, lines 5149–5186 of the
2026-09-05 revision.</sub>

- **A SAVE THAT PUMPS THE EVENT LOOP MUST TAKE ITS BUTTONS DOWN, AND
  THE TWO ARE ONE DECISION.** (Maintainer's decision 3, 2026-08-29.)
  Every call the save's write loop makes is one of QGIS's or OGR's own
  per-layer APIs, and each opens the GeoPackage, so the seconds grow
  with the layers already in the file: 134 of them at the 256-element
  ceiling, with a 50 ms heartbeat recording ZERO beats. Making the
  save a single OGR session is a rewrite of the writer, moved into
  0.24.4 on the maintainer's decision of 2026-09-01 that quadratic
  time in saving and loading is unacceptable to ship;
  what a person meets in the meantime is a window that says what it is
  doing rather than one that looks like a hang.
  THE PUMP IS AT THE TOP OF THE BODY, where none of that loop's four
  `continue`s can skip it: a bar that stops moving on the elements
  that are skipped says the save has hung. And turning the event loop
  is exactly what would otherwise let somebody press Save or Generate
  into a half-written file, so both controls go down for the duration
  and are put back AS THEY WERE FOUND rather than enabled -- a save
  can be pressed while Generate is already refusing for its own
  reasons.
  THAT SENTENCE NAMED TWO CONTROLS WHERE THE INTERFACE HAS THREE, and
  the third is the one it cost. LOAD arrived on 2026-08-27, on the row
  beneath Save, AFTER this was written -- and it was never taken down,
  at either of the two acts that pump. Measured 2026-09-02 at every
  one of a write's twelve beats: Save down, Generate down, Load LIVE
  throughout. A click delivered by the save's own pump repoints every
  element layer mid-loop, so the already-saved skip stops recognising
  them and the other map's tiles go into this file's tables, and the
  record captured after the loop names the OTHER FILE as this one's
  output path.
  SO THE CONTROLS ARE A LIST NOW, `CONTROLS_A_PUMP_TAKES_DOWN`, taken
  and given back by one owner that both acts call. WHEN A
  JUSTIFICATION ENUMERATES THE DOORS IT CLOSES, COUNT THE DOORS -- and
  count them again whenever the interface gains one, because a
  sentence naming two controls goes on reading correctly for ever
  while a third sits beside them.
  THE COST IS UNTOUCHED AND THAT IS THE DECISION, not an omission.
  Responsiveness and cost are different questions, and answering the
  cheap one first is what stops a rewrite being done in a hurry.

### C-145 — `isVisible` IS FALSE IN A WINDOW NOBODY HAS SHOWN, SO IT CANNOT ASK WHETHER...

<sub>Cut from `CLAUDE.md`, lines 5188–5197 of the
2026-09-05 revision.</sub>

- **`isVisible` IS FALSE IN A WINDOW NOBODY HAS SHOWN, SO IT CANNOT
  ASK WHETHER SOMETHING IS HIDDEN.** (2026-08-29.) A guard for the
  save's progress bar asserted `not progress.isVisible()` before and
  after, and BOTH halves passed with the repair mutated away -- the
  entry SURVIVED and said so. Offscreen, every widget in an unshown
  window answers False whatever anybody set; `setVisible` moves the
  explicit hidden flag, and `isHidden` is a question such a window can
  answer honestly. This project already carries the same trap about
  `grab()` and about probing state programmatically; this is it met
  from the ASKING side, and the catalogue is what found it.

### C-146 — A TEST LEG THAT RUNS AFTER THE STATE IT IS ABOUT MEASURES NOTHING

<sub>Cut from `CLAUDE.md`, lines 5199–5212 of the
2026-09-05 revision.</sub>

- **A TEST LEG THAT RUNS AFTER THE STATE IT IS ABOUT MEASURES
  NOTHING.** (2026-08-29, paying back the catalogue triage's second
  bad trade.) A re-tile leg asserting that a taken-back element is
  re-seeded ran on the element the arm ABOVE had just reclaimed --
  whose layer wore the plugin's own renderer, so the landing found
  nothing to carry and the assertion held whatever the gate said. The
  repair is an ORDER: put the element back into QGIS's hands, move the
  spacing FIRST so the restyle path declines, and only then pick the
  style back, so the layer still holds the dock's renderer when the
  run lands. Pick first and the restyle re-seeds in place, and the
  re-tile that follows meets an element that was never deferring.
  BOTH PREMISES ARE ASSERTED, so the arm cannot go quietly back to
  measuring nothing. Ask of any leg what STATE it needs and whether
  the step before it destroys that state.

### C-147 — A BACKSLASH-NEWLINE INSIDE A NON-RAW ANCHOR IS A LINE CONTINUATION

<sub>Cut from `CLAUDE.md`, lines 5214–5225 of the
2026-09-05 revision.</sub>

- **A BACKSLASH-NEWLINE INSIDE A NON-RAW ANCHOR IS A LINE
  CONTINUATION.** (2026-08-29.) A catalogue entry anchored on a source
  line ending in `\\` stored it as ONE collapsed line and matched
  nothing. `r"""..."""` keeps it. The tool refused by name rather than
  reporting a clean sweep, which is the whole reason `mutation_check`
  will not judge an absent anchor -- and the same reason
  `check_standards` fails on one.
  ITS SIBLING IS THE INDENTATION: wrapping a loop in `try/finally`
  moves every anchor inside it by two spaces, and EIGHT entries went
  orphaned in one edit. The gate named them, they were re-indented,
  and every one was RE-PROVED rather than assumed -- an anchor that
  matches again can still be aimed at nothing.

### C-148 — THE EIGHTEENTH WATCHER FAULT: A WORK LINE THAT CANNOT SHOW A DEAD WORKER

<sub>Cut from `CLAUDE.md`, lines 5227–5237 of the
2026-09-05 revision.</sub>

- **THE EIGHTEENTH WATCHER FAULT: A WORK LINE THAT CANNOT SHOW A DEAD
  WORKER.** (2026-08-29.) The five-minute beat reported running work
  through `ps | ... | head -2`, so with a release parent and THREE
  test shards it showed the parent and ONE shard. It was accurate and
  useless: this project has already been caught by a total climbing
  healthily while one shard had died at startup, and a watcher capped
  at one worker cannot report that however carefully it is read. It
  prints every worker with its own elapsed and cpu now, so a shard
  sitting at 0:00 beside siblings at minutes is visible at a glance.
  ASK OF ANY WATCHER WHETHER ITS OUTPUT CAN EXPRESS THE FAILURE, not
  merely whether it is correct about what it shows.

### C-149 — AND THE FIFTEENTH, COPIED FORWARD WITHOUT ITS REASON

<sub>Cut from `CLAUDE.md`, lines 5239–5253 of the
2026-09-05 revision.</sub>

- **AND THE FIFTEENTH, COPIED FORWARD WITHOUT ITS REASON.** The same
  beat carried `owed=$(grep -c ... || echo "?")`, which is the exact
  fault this file has recorded since 2026-08-20: `grep -c` PRINTS `0`
  and EXITS 1 when nothing matches, so the fallback APPENDS to a
  perfectly good answer instead of replacing it. The beat duly
  reported "0\n? owed" the moment the owed list emptied -- and what
  emptied it was the edit recording that the work was done.
  IT CAME BACK BECAUSE THE LINE WAS COPIED AND THE REASON WAS NOT.
  That is the argument for writing the reason AT the line rather than
  only in this file: a rule in a binding document does not travel into
  the next throwaway script, and the fifteenth fault is the one this
  project has now paid for twice.
  Both are fixed in a NEW file rather than by editing the running one,
  because bash reads a script incrementally from a byte offset and
  editing one mid-loop can make it execute garbage.

### C-150 — WHEN THREE REPAIRS TO A MECHANISM FAIL, SUSPECT THE PROMISE

<sub>Cut from `CLAUDE.md`, lines 5255–5280 of the
2026-09-05 revision.</sub>

- **WHEN THREE REPAIRS TO A MECHANISM FAIL, SUSPECT THE PROMISE.**
  (2026-08-29, and it cost most of an afternoon.) The assignment
  table's columns were taught to grow to their content, and the same
  commit asserted that no column ever elides. Both halves were written
  on this machine, where the columns and the window's 1480px budget
  never meet. Windows opened at 1729px, then 1790px, then 1729px
  again.
  FOUR REPAIRS WENT INTO THE MECHANISM. Bounding the table's minimum
  by live widget widths, which is not a meaningful subtraction before
  a layout pass; by the window's minimum less the table's, which is
  self-consistent and INERT, because A WINDOW OPENS AT ITS sizeHint
  AND A MINIMUM NEVER BOUNDS A PREFERRED SIZE; by a feedback loop on
  `sizeHint()`, which is not meaningful before assembly and so never
  fired; and finally by capping the columns' SUM, which worked.
  AND THE FIFTH CHANGE WAS THE ONE THAT MATTERED, and it was not to
  the code. With the sum capped the window FITTED on Windows and the
  no-elide promise failed instead: 'Style' wants 295px there against
  184 here, so the columns alone want about 1200px inside a 1480px
  window that also holds everything else. The two clauses cannot both
  hold where the fonts are wider, and the maintainer's ruling had
  already said which wins -- "widen the columns; ceiling near 1480".
  The assertion now permits eliding exactly where the budget binds.
  THIS FILE ALREADY SAYS three failed attempts mean the approach is
  wrong; what this adds is that the approach may be the ASSERTION
  rather than the code. A promise written on one machine is a claim
  about that machine's fonts.

### C-151 — PROVE THE QUANTITY THE FAILURE MEASURES, NOT ONE THAT SOUNDS EQUIVALENT

<sub>Cut from `CLAUDE.md`, lines 5282–5294 of the
2026-09-05 revision.</sub>

- **PROVE THE QUANTITY THE FAILURE MEASURES, NOT ONE THAT SOUNDS
  EQUIVALENT.** (Same day, and it is why the four repairs above each
  looked finished.) The guard for the ceiling measured
  `minimumSizeHint()`; the tests that were failing measure
  `dlg.width()` after `show()`. It passed on every one of those
  repairs, so each looked proved. Rewriting it to measure what the
  failure measures reproduced the fault LOCALLY at 3587px -- in a
  state I had told the maintainer was unreachable on this machine,
  and which took one line to reach: force every column to 400px, and
  this machine is in the position wide fonts put Windows in.
  ASK OF ANY GUARD: is this the number the red run prints? Where it
  is not, the guard is about something else, however reasonable it
  looks.

### C-152 — A GUARD ON A PyQGIS CALL THAT RETURNS A TUPLE CAN NEVER FIRE

<sub>Cut from `CLAUDE.md`, lines 5296–5313 of the
2026-09-05 revision.</sub>

- **A GUARD ON A PyQGIS CALL THAT RETURNS A TUPLE CAN NEVER FIRE.**
  (2026-08-30, and it cost this project categorical colour on every
  text column.) `if not provider.addFeatures(features):` reads as
  careful code. PyQGIS returns `(ok, features)`, and a two-element
  tuple is TRUTHY however `ok` reads -- measured `(False, [...])`,
  truthy, with zero features added. So the shared classification
  source came back EMPTY for any text column, and `if not everywhere:
  everywhere = values` then silently restored the per-element
  sampling that the one-colour-one-meaning ruling of 2026-08-15
  abolished. One colour meant different values on different elements
  of one map, and the same wrong renderers went into the saved file.
  Text is what categorical mapping is FOR.
  THE SWEEP: any PyQGIS setter or writer whose success you branch on
  -- `addFeatures`, `changeAttributeValues`, `deleteFeatures` and
  their kin -- may hand back a tuple or a bare bool depending on the
  call and the version. Unpack explicitly, or test
  `isinstance(x, tuple)` and take `x[0]`; never truth-test the return
  whole. And ask of any guard you did not watch fire whether it CAN.

### C-153 — A TEST THAT SUPPLIES ITS OWN INPUT MEASURES THE FUNCTION, NOT THE PRODUCT, AND CAN...

<sub>Cut from `CLAUDE.md`, lines 5314–5328 of the
2026-09-05 revision.</sub>

- **A TEST THAT SUPPLIES ITS OWN INPUT MEASURES THE FUNCTION, NOT THE
  PRODUCT, AND CAN HIDE A SHIPPED DEFECT FOR MONTHS.** (Same day, and
  it is the transferable half of the entry above.)
  `test_one_colour_means_one_value_across_elements` -- the guard for a
  settled ruling -- passes `classify_from=layer`, the region layer,
  which is A SOURCE THE DIALOG NEVER SUPPLIES. The ruling was
  therefore verified against a FUNCTION while the product handed over
  something else entirely, and no differential crossed the gap:
  file-against-map agrees, because both sides carry the same wrong
  colours. This project already knows that a fixture leaving the
  plugin to DERIVE the thing under test measures the derivation; this
  is the mirror -- a fixture that SUPPLIES the thing under test
  measures nothing about how the product produces it. Ask of any test
  whose subject is a value: who computes this value in the shipped
  path, and does my test make them do it?

### C-154 — AND A FIX THAT WIDENS A SCOPE RE-AIMS EVERY TRIAL THAT COMPARED AGAINST THE OLD ONE

<sub>Cut from `CLAUDE.md`, lines 5329–5340 of the
2026-09-05 revision.</sub>

- **AND A FIX THAT WIDENS A SCOPE RE-AIMS EVERY TRIAL THAT COMPARED
  AGAINST THE OLD ONE.** (Same day, and the fix exposed it within the
  hour.) With maps painted map-wide, the reopen path's adoption trial
  was still computed from each ELEMENT's own values, so it reproduced
  nothing and the walk "recovered" every ramp colour as somebody's
  HAND-PICKS. After a reopen those rows read Custom, picks outrank
  the ramp, and one later edit left one colour meaning two things.
  Its graduated twin is safe BY LUCK, which is worth knowing rather
  than trusting: class colours are a function of the class COUNT,
  categorical colours of the map-wide VALUE LIST. When you widen what
  a value is computed FROM, grep every site that recomputes the same
  value to compare against it.

### C-155 — THE DROP HAS BEEN WRONG FOUR TIMES: THE MISSING FACT IS WHAT THE ARTEFACT DESCRIBES,...

<sub>Cut from `CLAUDE.md`, lines 5341–5367 of the
2026-09-05 revision.</sub>

- **THE DROP HAS BEEN WRONG FOUR TIMES: THE MISSING FACT IS WHAT THE
  ARTEFACT DESCRIBES, NOT WHETHER WE MAY REMOVE IT.** (2026-08-30.)
  `_write_or_drop_the_topology` decides whether a saved unit and dual
  belong in the file. v1 dropped whenever the experimental box was
  unticked -- and the box is unticked on EVERY new dialog, so opening
  a saved map and pressing Save DELETED its motif. v2 guarded with a
  per-file memory plus a count of box touches, and ticking the box to
  LOOK at the tab counted as speaking about the file. v3 drops only
  where a build has ASSESSED this design and found no topology -- but
  with the box off no build runs, so ignorance is the PERMANENT state
  of the common journey and v3 makes ignorance mean "spare": save
  laves, switch to a design with no topology at all, Save, and the
  file keeps the laves motif while its record says
  `topology_written: True`.
  WHAT ALL THREE SHARE is that each asks whether we MAY drop, and none
  records WHAT THE TABLES ARE ABOUT. The fact needed is not "does this
  design have a topology", which needs a build nobody has run, but
  "WHICH DESIGN DO THE TABLES IN THIS FILE DESCRIBE" -- which the file
  can answer for itself, and which makes staleness DETECTABLE rather
  than inferred. Write the design key beside the tables at write time;
  drop when it differs from the design being saved; leave alone when
  absent.
  THIS FILE ALREADY SAYS three failed attempts mean the approach is
  wrong. What the fourth adds is the diagnostic: when every attempt is
  a different answer to one question, ask whether the QUESTION is
  answerable from the state you are asking it in. None of the three
  could be, and no fifth patch would have been either.

### C-156 — A QTabWidget LAYS OUT ONLY ITS CURRENT PAGE, so measuring the others measures the...

<sub>Cut from `CLAUDE.md`, lines 5368–5384 of the
2026-09-05 revision.</sub>

- **A QTabWidget LAYS OUT ONLY ITS CURRENT PAGE, so measuring the
  others measures the container.** (2026-08-30, and I reported the
  result to the maintainer before re-measuring it.) Sweeping every tab
  for controls stretched to the window returned 640px for a Save
  button, a Load button, a Clear button, two combos and a spin box
  across three tabs -- and 640px was the PAGE WIDTH. Those pages had
  never been current, so nothing in them had been through a layout
  pass and every child reported its parent's size, which reads exactly
  like a control with no width of its own.
  THE TELL WAS THE UNIFORM NUMBER, which this file already names: a
  verdict that comes back identical for every input is almost always
  the instrument. Six controls of four different kinds do not agree to
  the pixel. Made current and pumped, the same sweep found two tabs
  clean and one control 48px over.
  SO: `setCurrentIndex`, pump, THEN measure -- and the same caution
  reaches any stacked widget, any collapsed dock and anything else
  whose children Qt does not lay out until somebody looks at it.

### C-157 — A `processEvents()` LOOP LETS NO WALL TIME PASS, so a QgsTask never finishes

<sub>Cut from `CLAUDE.md`, lines 5385–5393 of the
2026-09-05 revision.</sub>

- **A `processEvents()` LOOP LETS NO WALL TIME PASS, so a QgsTask
  never finishes.** (Same day.) A probe pumped four hundred
  iterations waiting for the topology build and concluded no topology
  could be built -- on a design whose own `can_build` answered True.
  The build runs on another thread and its callback needs the event
  loop AND some seconds; spinning the loop supplies the first and none
  of the second. Wait on the EVENT with a real `sleep` between passes
  and a ceiling sized from a measured figure, which is this file's
  standing rule about ceilings arriving inside a probe.

### C-158 — A TEST'S POSITIVE CONTROL CAN BE THE DEFECT YOU ARE ABOUT TO FIX

<sub>Cut from `CLAUDE.md`, lines 5394–5407 of the
2026-09-05 revision.</sub>

- **A TEST'S POSITIVE CONTROL CAN BE THE DEFECT YOU ARE ABOUT TO
  FIX.** (Same day.) `test_no_design_control_is_stretched_to_the_
  window` proved its own measurement was live by asserting the region
  chooser DOES take the width, "meant to take the width going". What
  that meant in practice was that the chooser had no width of its own
  and took whatever the STYLE handed it -- 861px under Fusion, a 33px
  stub under macOS. Giving it a width in characters made the control
  unable to fail, so the guard went red on a repair of the very thing
  it was guarding.
  A POSITIVE CONTROL IS A CLAIM ABOUT THE PRODUCT, not scaffolding.
  When one starts failing, ask whether it was standing on something
  that was wrong -- this file already records the same shape from the
  other side, where a fix removed the footing a green oracle had been
  resting on.

### C-159 — A LAYOUT PASS THAT WIDENS WHAT IT MEASURES IS A FEEDBACK LOOP; A MARGIN IS NOT

<sub>Cut from `CLAUDE.md`, lines 5408–5422 of the
2026-09-05 revision.</sub>

- **A LAYOUT PASS THAT WIDENS WHAT IT MEASURES IS A FEEDBACK LOOP; A
  MARGIN IS NOT.** (Same day, and it is the fourth failed repair to
  this one layout.) Two form blocks stacked in a QVBoxLayout end their
  label columns a few pixels apart, because a group box frames its own
  form and that inset is unknowable before a layout pass. Measuring
  the real right edges at show time and widening the short labels to
  reach the furthest is the obvious repair and it RUNS AWAY: a wider
  label grows its form's shared column, which moves the edge being
  aimed at, so the next show does it again -- 1296px to 1618px in one
  run.
  MOVING THE FORM'S LEFT MARGIN settles instead, because a margin does
  not feed a label's width, and the pass is flagged so even a wrong
  reading could only be taken once. The general question for any
  self-correcting layout pass: does the quantity I am adjusting feed
  the quantity I am measuring?

### C-160 — A STACKED WIDGET'S MINIMUM IS THE LARGEST OF ITS PAGES, AND THAT IS WHY ONE TAB CAN...

<sub>Cut from `CLAUDE.md`, lines 5423–5433 of the
2026-09-05 revision.</sub>

- **A STACKED WIDGET'S MINIMUM IS THE LARGEST OF ITS PAGES, AND THAT
  IS WHY ONE TAB CAN SET THE WHOLE WINDOW'S SIZE.** (Same day,
  maintainer's ask that the first tab open narrower.) The Design tab
  needs 550px and Data & colours 1004 because of the assignment
  table, so the window opened at 1296 whichever tab was in front, and
  a floor of 1180px in `_fit_to_design` made sure of it. Qt's own
  lever is a size policy: the page in front is `Preferred` and the
  others `Ignored`, so the stack follows the current page. The window
  opens at 825px now and GROWS when a wider tab is chosen.
  GROW-ONLY IS A DECISION rather than an omission: a window that also
  contracted would resize under the pointer on every tab click.

### C-161 — WHEN A CONTROL'S PARAMETER COMES FROM A GESTURE, THE HANDLE SHOULD BE A POSITION AND...

<sub>Cut from `CLAUDE.md`, lines 5434–5448 of the
2026-09-05 revision.</sub>

- **WHEN A CONTROL'S PARAMETER COMES FROM A GESTURE, THE HANDLE SHOULD
  BE A POSITION AND NOT A DELTA.** (Same day, recorded before it is
  built.) A drag that reports how far it has travelled has to pass
  that through a LEVER to become a parameter, and the lever is a gain
  factor nobody can see: half the edge's length was too twitchy, the
  full length still turned a 35px drag into a scale factor of 0.28.
  Every such number is tuned by somebody guessing.
  A HANDLE THAT IS A POSITION HAS NO LEVER. Put the end of a line
  where you want it and the scale factor is the distance from the
  middle over what it was; the angle of the handle about the middle
  IS the rotation. The geometry follows the pointer exactly, nothing
  needs tuning, and the handle becomes a READOUT as well as a control
  -- it already sits where the current value puts it. Reach for
  absolute before relative whenever the parameter has a geometric
  meaning on screen.

### C-162 — A COMPARATOR THAT IS SENSITIVE TO REPRESENTATION CANNOT ANSWER A QUESTION ABOUT...

<sub>Cut from `CLAUDE.md`, lines 5449–5473 of the
2026-09-05 revision.</sub>

- **A COMPARATOR THAT IS SENSITIVE TO REPRESENTATION CANNOT ANSWER A
  QUESTION ABOUT APPEARANCE.** (2026-08-31, and it is the third wrong
  instrument in one function.) `_same_shape` exists to say whether a
  manipulation moved anything a person could see, and it asked
  `shapely.equals_exact`, which compares COORDINATE SEQUENCES: two
  rings covering identical ground read as different the moment one of
  them begins at another vertex. `transform_geometry` re-grids the unit
  it hands back and restarts those rings, so on archimedean 4.8.8 a
  manipulation that matched no class at all moved a coordinate by FIVE
  HUNDRED map units while the symmetric difference stayed at 2.4e-4.
  The comparison answered "something changed", the report stayed
  silent, and the registered test written to catch that silence failed.
  THE TWO EARLIER INSTRUMENTS FAILED THE OTHER WAY and are recorded at
  the function: areas rounded to nine places (an ABSOLUTE tolerance
  against tiles of area 62,500), then areas at all (a statistic is not
  a shape -- `push_vertex` moves vertices while leaving every area
  identical). What answers is the GROUND: symmetric difference over the
  unit's own area, measured at 1.5e-9 to 2.5e-9 for a manipulation that
  matched nothing against 1.9e-4 to 1.4e-1 for every real edit, which
  is three orders of clear air either side of the threshold.
  ASK OF ANY COMPARATOR WHAT IT IS ACTUALLY COMPARING -- the thing, or
  the way the thing is written down. Vertex order, ring direction, a
  start point, key order, whitespace and float formatting are all
  representation, and a dependency that rebuilds an object is entitled
  to change every one of them without changing anything.

### C-163 — AND AN EXACT QUESTION MUST NOT BE ASKED WITH A TOLERANCE

<sub>Cut from `CLAUDE.md`, lines 5475–5488 of the
2026-09-05 revision.</sub>

- **AND AN EXACT QUESTION MUST NOT BE ASKED WITH A TOLERANCE.** (Same
  day, the other half of the same defect.) Whether a design holds the
  class an edit names is answerable EXACTLY, from the topology, by
  name, before any geometry exists. `apply` instead handed the selector
  to the library -- which walks its edges asking `label in selector`
  and simply matches none, neither raising nor complaining -- and then
  tried to infer from the resulting SHAPE whether anything had
  happened. Every difficulty above followed from that inference.
  THE TELL IS A MEASUREMENT STANDING IN FOR A LOOKUP. Where the state
  can answer a question directly, a threshold is not a cheaper way to
  ask it, it is a different and weaker question that inherits every
  fault of the instrument. The same shape reaches past geometry: asking
  whether a file changed by comparing bytes where a record could say
  so, or whether a control moved by watching a repaint.

### C-164 — A GUARD THAT COMPARES THREE OF TWENTY-SIX FIELDS IS A SECOND DEFINITION OF THE THING...

<sub>Cut from `CLAUDE.md`, lines 5499–5524 of the
2026-09-05 revision.</sub>

- **A GUARD THAT COMPARES THREE OF TWENTY-SIX FIELDS IS A SECOND
  DEFINITION OF THE THING IT GUARDS, AND IT GOES STALE.**
  (2026-08-31, and TWO hunts found it independently by different
  routes -- the most this method has converged here.) The save's
  staleness guard asked whether "the design on screen is the one the
  map was drawn at" by comparing family, element count and the
  topology edit list, while the KEY it writes beside the motif hashes
  `_topology_stamp()` -- the spacing and every modifier included. So
  any design term outside those three moved the key while the guard
  reported agreement, and the two harms are opposite and both silent:
  measured, spacing 500 to 900 with no Generate then Save kept a unit
  of area 797,396 beside tiles drawn at 246,110 with the record still
  saying 500, and the same journey moving the tile inset DELETED motif
  and dual from a file whose tiles carry them.
  THE REPAIR IS ONE OWNER, NOT A WIDER LIST. `_capture_design` is now
  the single answer to "what is the design", and both the record's
  writer and the guard call it -- so the comparison cannot drift the
  day somebody adds a modifier, which is exactly how the narrow
  version was born. A guard that ENUMERATES the fields of a record is
  a copy of that record's definition; ask instead whether the owner
  can be called.
  ITS FIRST REPAIR WAS WORSE THAN THE DEFECT, and only a two-arm
  verification caught it: asking `_geometry_signature` instead refused
  the CONTROL journey too, so no motif was written on either path. An
  edited landing adopts its unit AFTER the run, so that signature
  legitimately differs from the one the map was drawn at.

### C-165 — A SINGLE-SHOT TIMER THAT IS "DROPPED" IS LOST, NOT LATE -- AND THE COMMENT SAYING...

<sub>Cut from `CLAUDE.md`, lines 5526–5540 of the
2026-09-05 revision.</sub>

- **A SINGLE-SHOT TIMER THAT IS "DROPPED" IS LOST, NOT LATE -- AND THE
  COMMENT SAYING OTHERWISE IS THE WORSE HALF.** (Same day, in a repair
  written hours earlier by the same hand.) A gate refusing a live tick
  while a save writes returned without re-arming `_live_timer`, which
  is `setSingleShot(True)` and had just FIRED to reach the gate; its
  only two `start()` sites are a fresh control change and
  `_finish_run`. Meanwhile `_preview_timer` is not gated, so the
  preview and the assignment table followed the new design while the
  map did not, with nothing said -- measured, element count 4 to 6
  left the table showing a..f over a map holding a..d.
  THE COMMENT CLAIMED "the redraw is a moment late rather than lost".
  A false comment is worse than none: the next reader believes it
  instead of checking, and this one was believed for hours by its own
  author. When you write that something recovers by itself, name the
  mechanism that recovers it and check that mechanism can still fire.

### C-166 — A `ResizeToContents` COLUMN RE-MEASURES ON EVERY `setItem`

<sub>Cut from `CLAUDE.md`, lines 5542–5558 of the
2026-09-05 revision.</sub>

- **A `ResizeToContents` COLUMN RE-MEASURES ON EVERY `setItem`.**
  (Same day, and it was a regression introduced by that morning's own
  fix.) The Messages tab's answer column was pushed off the viewport,
  so three columns were given resize MODES -- which cured the layout
  and cost ten to eighteen SECONDS per message once the log reached
  its 500-row ceiling, on the main thread, with live update making the
  plugin speak on every tweak. Measured at the ceiling: 8,563ms at
  Qt's default precision, 412ms with `setResizeContentsPrecision(20)`,
  and 5ms once the modes are SUSPENDED across the bulk rewrite and
  restored in a `finally`. Below the ceiling every arrangement is 4ms.
  THE CEILING IS THE CASE, AND A PROBE THAT FILLS PAST IT MEASURES
  NOTHING. `said.record` trims to 500, so a log already at 500 keeps
  its ROW COUNT UNCHANGED and every write is an overwrite -- which is
  what makes the columns re-measure. A first probe filled to 560, read
  4.8ms either way, and the catalogue entry aimed at the bound duly
  SURVIVED. The probe could not reach its own case, which is this
  file's oldest testing fault wearing a row count.

### C-167 — AN ENTRY MUST BREAK THE ROUTE THE GUARD WALKS, NOT A ROUTE

<sub>Cut from `CLAUDE.md`, lines 5560–5569 of the
2026-09-05 revision.</sub>

- **AN ENTRY MUST BREAK THE ROUTE THE GUARD WALKS, NOT A ROUTE.**
  (Same day, twice, and it cost four attempts on one entry.) A gate
  was given three callers -- the shelf writer, the family handler and
  the element-count handler -- and an entry mutating any ONE of them
  survived, because changing the element count REPOPULATES the family
  list and the family handler re-asks anyway. The three calls are kept
  as defence in depth, because which door fires today is incidental;
  the ENTRY was re-aimed at the single line where the answer is
  DECIDED. When an entry survives, ask whether it is aimed at a door
  or at the decision.

### C-168 — `mutation_check` MUST RUN ITS CHILD OFFSCREEN, AND THE DOCUMENTED INVOCATION DID NOT

<sub>Cut from `CLAUDE.md`, lines 5571–5580 of the
2026-09-05 revision.</sub>

- **`mutation_check` MUST RUN ITS CHILD OFFSCREEN, AND THE DOCUMENTED
  INVOCATION DID NOT.** (Same day, three diagnostic rounds.) The
  command this file gives -- `env -u PYTHONHOME -u PYTHONPATH python3
  tools/mutation_check.py` -- passes no `QT_QPA_PLATFORM`, while the
  suite always sets `offscreen`. Most entries do not care; one that
  measures LAYOUT does, this project's own record saying a font is not
  a platform. Two font entries came back UNJUDGEABLE and read exactly
  like broken tests; they caught on the first run once the child got
  an offscreen platform. `child_environment()` now `setdefault`s it,
  so the trap is closed at the tool rather than remembered here.

### C-169 — WHEN YOU ADD A STEP TO A SEQUENCE, ASK WHAT IT RESETS

<sub>Cut from `CLAUDE.md`, lines 5582–5596 of the
2026-09-05 revision.</sub>

- **WHEN YOU ADD A STEP TO A SEQUENCE, ASK WHAT IT RESETS.**
  (Same day, found by a hunt auditing a harness rather than a
  product.) The topology matrix grew a baseline Generate, placed
  between choosing a manipulation and clicking Apply. That Generate
  lands a topology build, the landing calls `set_unit`, and
  `_refresh_classes` then resets the class combo to the first vertex
  class and refills the verb list with vertex verbs only -- so every
  chosen EDGE verb was silently replaced by `push_vertex` and three
  cells could not fail. Demonstrated by breaking all three edge
  manipulations into no-ops: identical verdicts, while the sibling
  `immediately` cell went red under the same mutation.
  IT IS THE SELECT-THEN-ACT FAULT THE CELL'S OWN DOCSTRING RECORDS AS
  FIXED, re-entering through a step added later. A sequence that
  encodes an order is broken by anything inserted into it, and the
  insertion looks harmless because it is about something else.

### C-170 — A DEDUPE WRITTEN FOR AN UNREACHABLE HARM IS DELETED, NOT KEPT

<sub>Cut from `CLAUDE.md`, lines 5598–5609 of the
2026-09-05 revision.</sub>

- **A DEDUPE WRITTEN FOR AN UNREACHABLE HARM IS DELETED, NOT KEPT.**
  (Same day.) `_report_quietly` does not deduplicate, so a new notice
  on a gate reachable from every live tick looked certain to repeat --
  a warning that fires constantly being one people learn to ignore. A
  guard went in. The catalogue reported SURVIVED, and driving the live
  path with the gate dumps on said why: the key that gate compares
  carries the MODIFIERS, so moving the control changes it and each
  move honestly re-defers rather than re-explaining; four slider moves
  produced no second arrival at all. The mechanism was right and the
  harm was not, which is this project's own calibration arriving on
  its own repair. The dedupe was removed, with the measurement left at
  the site and the property it rested on held by a test arm.

### C-171 — RE-WRAPPING A PARAGRAPH DISARMED A PROSE GATE

<sub>Cut from `CLAUDE.md`, lines 5611–5623 of the
2026-09-05 revision.</sub>

- **RE-WRAPPING A PARAGRAPH DISARMED A PROSE GATE.** (Same day.) A
  guard finds a sentence in the user guide with a regular expression
  whose gaps were mostly literal spaces. Correcting a number made the
  word shorter, the paragraph was re-wrapped to tidy the ragged line,
  and the newline landed between "fifty-six" and "for a tiling" --
  where a literal space cannot match. The test failed with its own
  "this check has silently stopped checking anything", which is the
  right words in the right place and is why that assertion exists.
  EVERY GAP IS `\s+` NOW. A pattern that reads a sentence spanning a
  line break must not depend on WHERE the break falls, because
  re-wrapping is an edit nobody thinks of as semantic. Same family as
  the roadmap gate, from the other side: there a declaration was
  invisible because it had been wrapped through the middle.

### C-172 — A DOWNLOADED ARTEFACT HAS A FRESH MTIME AND AN OLD RESULT

<sub>Cut from `CLAUDE.md`, lines 5625–5637 of the
2026-09-05 revision.</sub>

- **A DOWNLOADED ARTEFACT HAS A FRESH MTIME AND AN OLD RESULT.**
  (Same day, the nineteenth watcher fault here and a new road.) The
  night's beat picks the newest failing log with `find -mmin -240`,
  which is the right guard against a glob sweeping up every run there
  has ever been -- and it assumes mtime is when the WORK happened.
  Pulling CI's shard logs down with `gh run download` put three files
  carrying a superseded run's failures into the beat's own directory,
  stamped with the minute they arrived, and the beat reported a fixed
  rc6 failure as tonight's trouble. The window filter cannot see it,
  because every fact it reads is genuinely fresh. Put somebody else's
  log where your watcher does not read, or name it so the pattern
  misses it -- and retire your OWN superseded logs, since a directory
  of stale failing logs makes any watcher lie.

### C-173 — A TRIPLE-BACKTICK FENCE SHIFTS EVERY INLINE SPAN BELOW IT, AND A PROSE GOES BLIND...

<sub>Cut from `CLAUDE.md`, lines 5639–5659 of the
2026-09-05 revision.</sub>

- **A TRIPLE-BACKTICK FENCE SHIFTS EVERY INLINE SPAN BELOW IT, AND A
  PROSE GOES BLIND FROM THERE DOWN.** (2026-08-31, found by re-reading
  the procedural documents at the maintainer's asking, which is a
  direction docs/process/HUNT-RECORD.md carries a row for.) A fence
  line carries THREE backticks; a span pattern needs a non-backtick
  between a pair, so the first two cannot pair and the THIRD opens a
  span running to the next backtick. After that, every real span reads
  as prose and every scrap of prose reads as a span: on a three-line
  document two ordinary script references went invisible while "Then" and
  "and" were collected as commands.
  MEASURED ACROSS THE GATED DOCUMENTS: fifteen references hidden,
  TWELVE of them in MAINTAINING.md, which contributed ONE where it
  carries thirteen -- and the one the gate could not see named
  a gitignored path under dev/instruments that does not exist. That is the rc6 CI failure's SIBLING, left standing
  because the repair went to the instance CI named rather than
  sweeping for the question.
  THE PER-DOCUMENT CHECK COULD NOT CATCH IT EITHER: a document that
  contributes SOMETHING passes. Ask of any gate that reads prose what
  its own markup does to its reading, and blank fenced blocks with
  SPACES rather than removing them, so every offset -- and every line
  number a failure quotes -- is unchanged.

### C-174 — WHEN ONE FUNCTION IS MADE THE OWNER OF "WHAT IS X", CHECK EVERY OTHER KEY FOR TERMS...

<sub>Cut from `CLAUDE.md`, lines 5661–5680 of the
2026-09-05 revision.</sub>

- **WHEN ONE FUNCTION IS MADE THE OWNER OF "WHAT IS X", CHECK EVERY
  OTHER KEY FOR TERMS THAT WERE NEVER X TERMS.** (2026-08-31, found by
  TWO hunts independently -- one from the boundaries, one backwards
  from harm.) `_capture_design` was extracted that morning as the one
  answer to "what is the design", and the save's staleness guard was
  moved onto it. The FILE's key went on hashing `_topology_stamp()`,
  which is built from `_unit_kwargs()` and carries `crs` off the region
  layer -- the one stamp term `_capture_design` cannot see. So
  reassigning a layer's CRS, the ordinary repair for a shapefile with
  no `.prj`, moved the key while the guard reported agreement, the drop
  read that as staleness, and nothing wrote a replacement.
  THE DIRECTION WAS CHECKED RATHER THAN FOLLOWED, which is what made
  the repair narrow: `make_unit` at EPSG:3857 and EPSG:27700 gives
  identical tile WKT and identical topology classes, and the tables are
  written in unit space with no CRS at all -- so the CRS describes
  nothing about them and the KEY was the wrong half, not the guard.
  The term left the FILE's key only; the stamp keeps it, because it
  also judges whether a landed build still describes the design on
  screen, and widening the repair into that question would change a
  second thing while measuring one.

### C-175 — AN ARMED TIMER IS NOT A RUN THAT WILL START

<sub>Cut from `CLAUDE.md`, lines 5682–5697 of the
2026-09-05 revision.</sub>

- **AN ARMED TIMER IS NOT A RUN THAT WILL START.** (2026-08-31.)
  `_queue_live` arms the live timer on every output-affecting change
  WHATEVER the checkbox says, and `_maybe_live_generate` then declines
  at its second gate. `_a_queued_run_would_redraw` read only the timer
  where its sibling `_a_live_run_will_follow` asks about the checkbox
  on its FIRST LINE -- two readings of one question, one of which had
  never learned the other's opening move. A Save pressed inside the
  debounce with live update off was kept, the person was told the map
  would be saved once redrawn, nothing redrew it, and the write landed
  on the design they had changed AWAY from; closing the window in that
  second cleared the intent and wrote nothing at all.
  THE RULE THIS JOINS is the project's own about deferred work: ask
  what CONSUMES a remembered intent, and whether that consumer can
  DECLINE for a reason having nothing to do with the act deferred.
  WHEN A PROJECT DOCUMENTS ONE READING AS "A SECOND READING OF ONE
  QUESTION", DIFF THE TWO TERM BY TERM.

### C-176 — A GATE THAT OPENS A DOOR MUST ASK FOR WHAT IS BEHIND IT

<sub>Cut from `CLAUDE.md`, lines 5699–5710 of the
2026-09-05 revision.</sub>

- **A GATE THAT OPENS A DOOR MUST ASK FOR WHAT IS BEHIND IT.**
  (2026-08-31, found by two hunts independently.) `opt_experimental`
  reached `_gate_experimental_tabs` and a touch counter; the topology
  build runs only from `_rebuild_unit`. So the gate OPENED the Topology
  tab and nothing filled it -- an empty class chooser beside an ENABLED
  Apply button -- and after a design change made with the box off, the
  tab offered the classes of a design nobody was looking at, so the
  edge somebody clicked was not the edge that moved.
  THE COST RULING SURVIVES BY HANGING THE WORK ON THE BOX rather than
  on the tab: the tick IS the asking, so nobody who has not asked pays
  the 0.75-4.4s. When a control gates VISIBILITY, ask what fills what
  it reveals, and whether that filler has any idea the control exists.

### C-177 — A HAND-KEPT LIST DRIFTS EVEN WHERE A COMMENT SAYS TO KEEP IT IN STEP

<sub>Cut from `CLAUDE.md`, lines 5712–5730 of the
2026-09-05 revision.</sub>

- **A HAND-KEPT LIST DRIFTS EVEN WHERE A COMMENT SAYS TO KEEP IT IN
  STEP.** (2026-08-31, twice in one day.) `check_standards.USER_FACING`
  decides which files the hard rules are enforced over, and its own
  comment asks that it match `text_review`'s SOURCES and DOCUMENTS.
  `metadata.txt` joined the review queue on 2026-08-12 and never joined
  this one -- so the `changelog=` and `about=` entries, which QGIS's
  plugin manager displays and which `release_notes.py` puts at the top
  of the GitHub release body, were unchecked for a HARD RULE and for
  Canadian spelling. Measured by planting one sentence in both places:
  caught in README.md, clean in the changelog.
  AND `sandbox.INCLUDE_FILES` carried CLAUDE.md and MAINTAINING.md but
  not README.md or ROADMAP.md, though the suite reads all four -- so
  any catalogue entry whose test touches them came back UNJUDGEABLE,
  which that list's own comment calls worse than a failure.
  THE REPAIR IS TO GUARD THE RULE, NOT THE INSTANCE: a test comparing
  the two lists cannot go quiet the next time a file joins one and not
  the other, which is exactly how both of these arose. Assert both
  lists are non-trivial while you are there -- two empty sets agree
  perfectly.

### C-178 — A WANTED WRITE THAT FAILS STILL CLEARS, SO ENABLING THE WRITE IS HALF A REPAIR

<sub>Cut from `CLAUDE.md`, lines 5732–5745 of the
2026-09-05 revision.</sub>

- **A WANTED WRITE THAT FAILS STILL CLEARS, SO ENABLING THE WRITE IS
  HALF A REPAIR.** (2026-08-31, and it is the third failed repair to
  one method in one day.) `_write_or_drop_the_topology` refused to
  write a motif while the experimental box was unticked, and stopping
  it asking the box changed nothing observable: on the commonest
  journey nothing has BUILT a topology, so `wanted` stayed false. Given
  a synchronous build, `wanted` went true -- and the both-or-neither
  test then found `_topology_dual` empty, declined the write, and the
  clear below ran exactly as before. The only evidence was a dump line.
  SO WHEN YOU ENABLE A GUARDED WRITE, ENUMERATE EVERYTHING THE WRITE
  ITSELF DEMANDS. Here the dual had to be built AND STAMPED beside the
  unit, which is a requirement written at the write and not at the
  gate. THREE REPAIRS FAILED BEFORE I READ WHAT THE BRANCH DID, having
  quoted this file's own rule about that twice the same day.

### C-179 — A TEST THAT MATCHES A PHRASE COPIED OUT OF THE PRODUCT IS BROKEN BY THE MAINTAINER'S...

<sub>Cut from `CLAUDE.md`, lines 5747–5759 of the
2026-09-05 revision.</sub>

- **A TEST THAT MATCHES A PHRASE COPIED OUT OF THE PRODUCT IS BROKEN BY
  THE MAINTAINER'S OWN EDIT.** (2026-08-31, and the route is new.) An
  arm counted messages containing `"cannot carry"`. The maintainer
  reworded that notice, `tools/text_review.py --apply` wrote the new
  sentence into the source, and the filter matched nothing -- so the
  arm counted zero and its "at most once" assertion held whatever the
  code did. This file already says to compose an expected sentence from
  the function the product uses; where the sentence is a LITERAL and
  there is no function, match on what the sentence is ABOUT (here the
  control's name, "Topology tab"), never on a phrase from inside it.
  THE APPROVAL PIPELINE IS THE DELIVERY MECHANISM, which is what makes
  this worth its own entry: approving prose is the act that silently
  retunes every test transcribing it.

### C-180 — UPSTREAM MOVED TWELVE COMMITS WITHOUT BUMPING ITS VERSION, AND FIXED ONE OF OUR FINDINGS

<sub>Cut from `CLAUDE.md`, lines 5761–5776 of the
2026-09-05 revision.</sub>

- **UPSTREAM MOVED TWELVE COMMITS WITHOUT BUMPING ITS VERSION, AND
  FIXED ONE OF OUR FINDINGS.** (2026-08-31.) The vendored stamp reads
  `0.0.7.89 (bf1bbbf)`; upstream's head is `6190917` with `topology.py`
  at +179/-207 and `_tiling_geometries.py` at +44/-67 -- and the
  version string is `0.0.7.89` at BOTH ends. That is exactly why the
  stamp records a commit as well as a version, and why the standing
  rule says to compare both before running the suite.
  `b3650e0` is *"fixed bug in zigzag edges code where it was doubling
  up tiling vertices"*, two lines: the endpoints were added once as
  `edge.vertices[0]`/`[-1]` and again from `ls.coords`, which includes
  them. This project measured that independently on 2026-08-30 and had
  it recorded as a conversation to have; it is answered at the source.
  THE RE-VENDOR IS ITS OWN ROUND, by the maintainer's decision: twelve
  commits touching `topology.py` heavily is not a licence-header bump,
  and the tab, the manipulations, the edit shelf and the topology
  matrix all stand on that module.

### C-181 — A CONTROL'S SHAPE SHOULD SAY WHAT IT DOES, AND A HOVER STATE IS NOT A SUBSTITUTE

<sub>Cut from `CLAUDE.md`, lines 5779–5801 of the
2026-09-05 revision.</sub>

- **A CONTROL'S SHAPE SHOULD SAY WHAT IT DOES, AND A HOVER STATE IS
  NOT A SUBSTITUTE.** (Maintainer's rulings, 2026-08-31, on finding the
  Topology tab unusable: it "should be easy to use and easy to learn",
  it "has to be perceivable", and "hover states aren't as good as
  shapes that make sense ... like visually make sense for what they
  do".) The tab's handles were a square, a circle and a diamond whose
  meanings existed only in the source. A hover label was the obvious
  repair and is the wrong one -- a hover has to be DISCOVERED before it
  can teach anything, and a first-time reader never hovers. Each handle
  is a small picture of its own effect now.
  AND PERCEIVABLE CAME FIRST, BECAUSE NONE OF IT MATTERS AT THE WRONG
  SIZE. The view was fitting the whole PATCH -- 36 tiles for a
  four-tile unit -- so the thing being edited was drawn at a third of
  the size the panel could give it, and the handles were a cluster of
  rings a few pixels across. Fitting the unit was worth more than every
  other change to that drawing put together.
  AND EVERY INTERACTION BELONGS ON THE THING ITSELF: one of the five
  manipulations was reachable only through a chooser and a button, so
  the drawing offered four of the five acts it is about.
  THE GENERAL RULE, which reaches past this tab: when a control's
  meaning lives in the code rather than in its appearance, adding an
  explanation is the second-best repair. The first is to make the shape
  mean the thing.

### C-182 — PROFILE THE THING A PERSON WAITS FOR, BECAUSE THE COST IS OFTEN NOT WHERE THE SUBJECT IS

<sub>Cut from `CLAUDE.md`, lines 5803–5824 of the
2026-09-05 revision.</sub>

- **PROFILE THE THING A PERSON WAITS FOR, BECAUSE THE COST IS OFTEN
  NOT WHERE THE SUBJECT IS.** (2026-08-31, asked whether the symmetry
  work could speed up tiling the plane.) It cannot -- covering the
  plane is TRANSLATION, and that half is already vectorised: 191,184
  tiles are built in 2.7s of numpy and STRtree, which is upstream
  having taken this project's own optimisation. What the profile
  actually named was `_aggregate_series_pure_python` at 2.16s of
  `get_tiled_map`'s 3.92s -- a pandas groupby walking 63,684 groups in
  Python because `tile_map.py` passes the FUNCTION `pd.Series.idxmax`
  to `.agg()` instead of the string. Measured 41x to 191x depending on
  size, growing with the map; end to end, `get_tiled_map` at 86,768
  tiles went from 2.68s to 0.94s.
  THE DOMAIN WAS THE WRONG PLACE TO LOOK. The question was about
  symmetry, the code is about geometry, and the answer was a pandas
  idiom -- which no amount of reasoning about tilings would have
  reached. This is the same rule as diagnosing by cpu-against-elapsed
  rather than by the stack that looks guilty, arriving at a library.
  AND MEASURE WHAT THE ALTERNATIVE COSTS AS WELL AS WHAT IT SAVES: the
  `overlay` beside it looked equally replaceable, a centroid `sjoin`
  doing it eight times faster -- and it answers a DIFFERENT QUESTION,
  which 4.4% of tiles would notice. A speed-up that changes 8,467
  tiles' data is a ruling, not an optimisation.

### C-183 — THE VENDOR-CLAIM GATE READS "commit <sha>" ANYWHERE IN THREE FILES, SO WRITING ABOUT...

<sub>Cut from `CLAUDE.md`, lines 5826–5841 of the
2026-09-05 revision.</sub>

- **THE VENDOR-CLAIM GATE READS "commit <sha>" ANYWHERE IN THREE
  FILES, SO WRITING ABOUT SOMEBODY ELSE'S COMMIT TRIPS IT.**
  (2026-08-31, met while mending the claims the re-vendor had made
  stale.) `check_vendor_claims` compares every `commit <hex>` in
  README.md, MAINTAINING.md and CLAUDE.md against the stamp -- which is
  what makes it catch a document naming the vendor's old commit, and
  what makes it complain about a sentence that merely MENTIONS another
  one. Recording in MAINTAINING.md which upstream commit had merged our
  patch turned a correct sentence into a failing gate, in the same edit
  that fixed the real claim.
  IT IS THE ROADMAP GATE'S OWN SHAPE, from the other side: there a
  sentence QUOTING the phrase could satisfy a gate, here a sentence
  mentioning a sha can break one. The cheap rule is to name a commit
  WITHOUT the word before it in those three files, and the general one
  is this file's own -- when a gate reads prose for a decision, decide
  what counts as prose, and expect to be its next false positive.

### C-184 — A RE-VENDOR'S REAL QUESTION IS ONE NO GATE HERE ASKS

<sub>Cut from `CLAUDE.md`, lines 5843–5867 of the
2026-09-05 revision.</sub>

- **A RE-VENDOR'S REAL QUESTION IS ONE NO GATE HERE ASKS.**
  (2026-08-31, upstream bf1bbbf to 6190917.) The colourspace comparison
  scores the plugin against `TiledMap.render` from THE SAME vendored
  library, so a change upstream moves both sides together and they go
  on agreeing -- "a differential cannot see a fault its expected side
  shares", arriving at the dependency. The suite asks whether the
  plugin's own rules hold. Neither asks whether the library's OUTPUT
  moved, which is the one thing a re-vendor can change under a user.
  SO COMPARE TWO CHECKOUTS, design by design, through
  `catalog.make_unit` -- the door the dialog uses, since the product is
  where the arguments are parsed and the defaults chosen.
  `tools/probes/the_re_vendor_moved_no_map.py` is that instrument, and
  it is committed for the reason every probe here is: the instrument
  that names one defect names the next.
  MEASURED: 588 of 590 designs identical; `square-colouring 6` and `8`
  shifted origin by about 34 map units at spacing 500, same tiles, same
  ids, same area. The gallery draws no square colourings, so nothing
  published moved.
  AND ITS FIRST DRAFT WAS AIMED WRONGLY, which is the transferable
  half: it put an older `weavingspace` on `sys.path` and imported the
  CURRENT `weavingspace_qgis` beside it, so both arms would have
  measured whichever vendor won the path. Two checkouts remove the
  question, and the premise asserts the arms loaded different library
  FILES -- two arms reading one library agree perfectly and mean
  nothing.

### C-185 — THE TWENTIETH AND TWENTY-FIRST WATCHER FAULTS ARE ONE RULE: KEY ON THE THING, NOT A...

<sub>Cut from `CLAUDE.md`, lines 5869–5891 of the
2026-09-05 revision.</sub>

- **THE TWENTIETH AND TWENTY-FIRST WATCHER FAULTS ARE ONE RULE: KEY ON
  THE THING, NOT A SNAPSHOT OF IT.** (2026-08-31, both mine, both
  within ten minutes of arming a watcher, and both while the candidate
  was building.) This file already carries that rule from 2026-08-12,
  where a poller pinned to one commit sha sat silent while two more
  pushes superseded it. It came back twice in one morning.
  A WATCHER KEYED TO RUN IDS GOES BLIND AT THE NEXT PUSH. The beat
  named two CI run ids, which was accurate when it was written and
  false the moment a push created a third and fourth: it would have
  gone on reporting the old pair in flight while the runs answering for
  the tree in front of it were invisible. It lists runs BY BRANCH now
  and prints each one's own head sha.
  AND THE CI POLLER PRINTED A SHA IT NO LONGER FOLLOWED. Its own source
  is the evidence -- `SHA=$(git rev-parse HEAD)` captured ONCE at
  arming time and printed on every line, with `--limit 1` so it only
  ever looked at the newest run. It duly announced a run belonging to
  `8cbdff8` under the label `92cfaab`. A verdict with the wrong subject
  is a verdict about whatever the reader is thinking of, which is the
  twelfth fault's own sentence arriving at a SHA rather than a branch.
  THE CHEAP CHECK, before arming anything: name what would have to
  happen for this watcher's subject to change, and ask whether the
  watcher would notice. A push, a relaunch, a new run, a superseded
  commit -- if the answer is no, it is keyed to a snapshot.

### C-186 — THREE MORE FROM THE SAME MORNING, ALL CAUGHT BY HAND-RUNNING THE WATCHER ONCE BEFORE...

<sub>Cut from `CLAUDE.md`, lines 5893–5913 of the
2026-09-05 revision.</sub>

- **THREE MORE FROM THE SAME MORNING, ALL CAUGHT BY HAND-RUNNING THE
  WATCHER ONCE BEFORE ARMING IT.** That is the practice this file has
  been recommending since the tenth fault, and it is the first time it
  has been done here before rather than after.
  `gh` GIVES A RUNNING JOB AN EMPTY STRING CONCLUSION, NOT NULL, and
  jq's `//` falls through only on null or false -- so
  `.conclusion // .status` printed `macos=` for every job still going,
  which is the one state that line exists to show. Test the empty
  string explicitly.
  AN UNANCHORED `FAIL` FILTER NAMED A CLEAN SHARD. The word appears
  inside test names ("a failed stage is not remembered"), so a log
  reading `242 passed, 0 failed` was reported as the newest failing
  one. A watcher whose alarms are mostly false is one people learn to
  silence, and it takes the true alarms with it.
  AND THE SHARD BLOCK GLOBBED, which is the stale-log fault for the
  fourth time. `release.py` CLEARS its stage logs when the suite
  finishes, so `ls | tail -3` fell back to a run from two days earlier
  and reported 2,621-minute-old logs as this run's. THE AGE LINE IS
  WHAT CAUGHT IT -- print an age beside anything read off disk, bound
  the search to the run, and SAY when there is nothing rather than
  reading somebody else's.

### C-187 — A DOCUMENTATION MERGE IS NOT A NO-OP FOR THE SUITE

<sub>Cut from `CLAUDE.md`, lines 5915–5930 of the
2026-09-05 revision.</sub>

- **A DOCUMENTATION MERGE IS NOT A NO-OP FOR THE SUITE.** (Same day.)
  `test_every_documented_command_still_exists` opens CLAUDE.md,
  MAINTAINING.md, README.md and ROADMAP.md, which is exactly why those
  four are in `STAGE_DEPENDS` -- a documentation edit really can break
  a test, and it is the kind of change that feels as though it cannot.
  So a docs branch merged into a candidate's branch gets the prose
  gates run over the MERGED tree before the push, not merely
  `check_standards` in the worktree it was written in. Cheap: three
  tests, 160 quotations, 38 scripts and 19 long flags, in under a
  minute.
  AND THE RECEIPT CLAIM IS MEASURED RATHER THAN REASONED. "No shipped
  file moved, so the candidate's receipt still holds" is a reading
  until `release.tree_digest()` is recomputed and compared with the
  receipt, which is one line and settles it. The digest deliberately
  ignores documentation, so the answer is nearly always yes -- and
  nearly always is not a thing to publish an artefact on.

### C-188 — THE ENTRY DESCRIBING THE FENCE FAULT IS WHAT BLINDED THE GATE NEXT

<sub>Cut from `CLAUDE.md`, lines 5932–5964 of the
2026-09-05 revision.</sub>

- **THE ENTRY DESCRIBING THE FENCE FAULT IS WHAT BLINDED THE GATE
  NEXT.** (2026-08-31, hours after the fence repair, and found by
  planting a control rather than by reading.) This morning's lesson was
  written as a bullet opening `- **A ` followed by three literal
  backticks and the word FENCE. `_prose_outside_fences` toggles only on
  a line that STARTS with the fence, and that line starts with a dash --
  so the three backticks stayed in the prose, and three is ODD. The
  span pattern pairs positionally over the whole document, so from that
  line to the end of the file every backtick pairs with the wrong
  neighbour.
  WHAT IT COST IS EXACTLY WHERE IT HURTS: the end of CLAUDE.md is where
  this project appends every new lesson. A quoted path added there
  formed no span at all -- its opening backtick was consumed closing
  the runaway span, and the leftover opened one that never closed.
  MEASURED, RED AND GREEN. With the odd count in place, a planted
  reference to a script under tools/ that does not exist -- described
  here rather than quoted, since this gate refuses a quoted path and
  cannot tell a demonstration from a recommendation -- sat at the end
  of the file and PASSED, reporting the same 160 quotations it reports
  on a clean tree. With the sentence rewritten to DESCRIBE the delimiter -- "a
  triple-backtick fence" -- the same plant fails with the file, the
  line and the name. Both documents carrying that sentence were odd;
  the other four were balanced.
  THE TELL WAS A COUNT THAT DID NOT MOVE. Adding sixteen backtick spans
  to the file left "160 quotations, 38 scripts, 19 long flags"
  unchanged, which is this file's own rule that a uniform verdict is
  almost always the instrument -- met as a verdict that would not
  BUDGE.
  SO: DESCRIBE A DELIMITER, DO NOT QUOTE IT, which is the rule this
  project already keeps for a path that no longer exists. And a
  document whose backtick count is odd is a document the gate reads
  wrongly from somewhere onward; the parity is one command to check and
  worth checking whenever a lesson is appended.

### C-189 — `lines[-1]` ON A FILE ENDING IN A NEWLINE REPLACES THE EMPTY STRING, SO THE EDIT...

<sub>Cut from `CLAUDE.md`, lines 5966–5986 of the
2026-09-05 revision.</sub>

- **`lines[-1]` ON A FILE ENDING IN A NEWLINE REPLACES THE EMPTY
  STRING, SO THE EDIT APPENDS INSTEAD OF REPLACING.** (2026-08-31, and
  it reached the point of publication.) A paragraph of a candidate's
  release notes was rewritten by assigning to `lines[-1]` after
  `read().split("\n")`. A file ending in a newline yields a final EMPTY
  element, so the assignment replaced nothing and put the new paragraph
  AFTER the old one -- and the body carried the broken draft and its
  replacement, one after the other.
  WHAT LET IT THROUGH WAS THE VERIFICATION. It was `tail -1`, which
  showed the corrected paragraph and said nothing whatever about the
  broken one two lines above it. That is this file's own rule --
  ASSERT THE POSTCONDITION, NOT JUST THE ANCHOR -- with the anchor
  replaced by "the new text is present", which is the weaker half of
  the same question.
  SO ASSERT WHAT SHOULD BE GONE. `assert old not in text` and, where
  the thing is a section, assert HOW MANY of it remain: the repair
  here checks the broken phrase is absent AND that exactly one such
  paragraph exists. What caught it in the end was `--dry-run` printing
  the body, which is the standing rule about verifying against what
  ships rather than what you wrote, doing its job one step before a
  public page.

### C-190 — A WATCHER'S HEADLINE MUST CARRY WHAT IS LIVE, NOT WHAT MATTERS IN GENERAL

<sub>Cut from `CLAUDE.md`, lines 5988–6003 of the
2026-09-05 revision.</sub>

- **A WATCHER'S HEADLINE MUST CARRY WHAT IS LIVE, NOT WHAT MATTERS IN
  GENERAL.** (2026-08-31, the truncation fault three times in one day
  and the third is the interesting one.) A notification is TRUNCATED,
  so a line below the cut is a line nobody reads. First the candidate's
  CI run printed last, which hid a failing mutation leg for half an
  hour and a passing one for five minutes. Moving the candidate's runs
  to the top fixed that -- until the candidate was PUBLISHED, after
  which its two runs were green and static while the only moving thing
  on the branch, the tip's own round, sat below the fold again.
  THE HEADLINE IS ABOUT WHAT CAN STILL CHANGE. It names the tip as well
  as the candidate now, and drops the tip line when the two are the
  same commit. Ask of any watcher not merely whether its output CAN
  express the failure, but whether the reader REACHES that part of it
  -- and re-ask it whenever the thing being watched reaches a resting
  state, because a headline that was right while something was in
  flight becomes furniture the moment it settles.

### C-191 — A WIDGET INSIDE A LAYOUT DOES NOT KEEP A SIZE YOU HAND IT, SO THE WINDOW IS THE LEVER

<sub>Cut from `CLAUDE.md`, lines 6005–6017 of the
2026-09-05 revision.</sub>

- **A WIDGET INSIDE A LAYOUT DOES NOT KEEP A SIZE YOU HAND IT, SO THE
  WINDOW IS THE LEVER.** (2026-08-31, and THREE of four failed attempts
  at one guard turned on this alone.) A test that resizes a child to
  its own floor measures nothing: the layout hands that child whatever
  is left over on the next pass, and the resize is gone before
  anything can read it. What actually pins a pane is the WINDOW'S
  minimum, which is composed from every pane's floor plus what sits
  beside them -- measured here at 1025x450, below which the dialog
  will not go, holding the drawing at 420x346 however small a size it
  is asked for. So a mutation lowering a child's own floor can change
  nothing observable, and its entry survives while the code is
  genuinely wrong-headed. Drive the window, then READ the child's size
  rather than assuming it took.

### C-192 — A FLOOR ON ONE PANE IS TAKEN OUT OF THE PANE BESIDE IT

<sub>Cut from `CLAUDE.md`, lines 6018–6030 of the
2026-09-05 revision.</sub>

- **A FLOOR ON ONE PANE IS TAKEN OUT OF THE PANE BESIDE IT.** (Same
  day.) The Topology tab's drawing had a 180px floor and got exactly
  180px of an 825px window, because the column of controls beside it
  claims its own preferred width first -- so the floor was not a floor
  but the whole allowance. Raising it to 420 without giving that
  column a floor of its own MOVED THE COMPLAINT rather than answering
  it: 71px of viewport for content wanting 271. And the horizontal
  scrollbar there is deliberately off, so a column narrower than its
  content does not scroll, it CLIPS -- the controls are simply gone,
  with nothing on screen to say so.
  ASK OF ANY SIZE FLOOR WHERE THE ROOM COMES FROM, and measure the
  neighbour in the same breath. A scroll area is only a safety net in
  the direction its scrollbar is enabled.

### C-193 — TWO SUFFICIENT FIXES TO ONE OUTCOME MAKE EVERY SINGLE-SITE ENTRY SURVIVE, AND THAT...

<sub>Cut from `CLAUDE.md`, lines 6031–6045 of the
2026-09-05 revision.</sub>

- **TWO SUFFICIENT FIXES TO ONE OUTCOME MAKE EVERY SINGLE-SITE ENTRY
  SURVIVE, AND THAT IS INFORMATION.** (Same day, four attempts before
  the question was put the right way round.) Two independent repairs
  kept a pair of handles outside the hit test's reach, and the test
  asserts the OUTCOME, so mutating either one left the assertion
  true. Each attempt read as a weak test and none of them was. The
  discriminator is to undo BOTH by hand and watch the number move:
  worst gap 41.5px as it stands, 28.7 with one undone, 32.7 with the
  other, 12.9 with both. The sites were ninety lines apart, so no
  anchor could span them, and the honest record is the retirement with
  every figure written at the test -- plus the thin one named, since
  28.7 against a 26.0 requirement is a 2.7px margin and is what a
  later change would eat first. This project already has the rule; what
  is new is the METHOD for telling redundancy from weakness, which is
  to break every route at once rather than to write a fifth entry.

### C-194 — A SETTLE RETURNS BEFORE THE RESULT IS ADOPTED, SO A PREMISE ASKED IN THE SAME BREATH...

<sub>Cut from `CLAUDE.md`, lines 6046–6057 of the
2026-09-05 revision.</sub>

- **A SETTLE RETURNS BEFORE THE RESULT IS ADOPTED, SO A PREMISE ASKED
  IN THE SAME BREATH READS THE OLD STATE.** (Same day.) A guard
  asserted, immediately after waiting for the topology build to go
  quiet, that the design no longer carried a topology -- and the
  assertion failed while a direct measurement of the very same dialog
  said it should pass. The waiter returns when no build is IN FLIGHT;
  the edited unit is adopted a beat later. So the premise was asking
  about the un-edited design and answering, quite correctly, that it
  still had one. ORDER A PREMISE BEHIND THE EVIDENCE THAT THE ACT
  LANDED: assert first that the thing moved, then assert what follows
  from its having moved. Two contradictory measurements of one object
  are usually two moments, not two answers.

### C-195 — A FIX APPLIED WHERE THE FAULT CANNOT BE REACHED IS DEAD CODE THAT READS AS...

<sub>Cut from `CLAUDE.md`, lines 6059–6071 of the
2026-09-05 revision.</sub>

- **A FIX APPLIED WHERE THE FAULT CANNOT BE REACHED IS DEAD CODE THAT
  READS AS PROTECTION, AND I WROTE ONE WITHIN AN HOUR OF WRITING THE
  RULE'S OTHER HALF.** (2026-09-01.) A margin pass returned early for
  want of a layout pass, under a comment promising to try again later
  while nothing scheduled a later, so it was taught to re-arm a timer.
  Measured afterwards, an unshown dialog's first labels already report
  640px, so `width() <= 0` is not reached by not laying a window out
  and the timer could never have fired. The repair was withdrawn and
  re-aimed at the READING instead: ask for the layout, take the
  measurement, apply the margins, then check once that they took --
  bounded at one repeat, because a margin does not feed a label's
  width. MEASURE THE BRANCH BEFORE REPAIRING IT; a condition that
  looks reachable is a hypothesis like any other.

### C-196 — AN OWNERSHIP QUESTION THAT OUR OWN ACT MAKES TRUE IS NOT AN OWNERSHIP QUESTION

<sub>Cut from `CLAUDE.md`, lines 6073–6088 of the
2026-09-05 revision.</sub>

- **AN OWNERSHIP QUESTION THAT OUR OWN ACT MAKES TRUE IS NOT AN
  OWNERSHIP QUESTION.** (2026-09-01, found by the stochastic hunt and
  widened by a second.) `_this_map_owns_the_file` answers True as soon
  as the file is in `_gpkg_tables_written`, which OUR FIRST PRESS puts
  there -- so a colleague's GeoPackage is theirs on press one and ours
  on press two, and every remover gated on that answer was handed a
  licence on the second press. Their element tables went; a second
  hunt then found their embedded copy of their own data going the same
  way through a different remover; a third remover took the same
  argument with nobody having walked it to a harm. THREE REMOVERS AND
  ONE MENDED IS THIS FILE'S OWN SIGNAL TO FIX THE QUESTION: the answer
  is taken once, before any write, and remembered per file, with a
  file that did not exist counting as ours by construction -- without
  which a file we CREATE reads as somebody else's for ever. The
  overwrite question keeps the live reading, deliberately, since
  asking on every press is noise.

### C-197 — AND THE FIRST REPAIR FOR IT SPARED EVERYTHING, BECAUSE THE RECORD DOES NOT SPELL IT...

<sub>Cut from `CLAUDE.md`, lines 6090–6100 of the
2026-09-05 revision.</sub>

- **AND THE FIRST REPAIR FOR IT SPARED EVERYTHING, BECAUSE THE RECORD
  DOES NOT SPELL IT `variable`.** The drop was taught to name
  candidates from the file's own record rather than match them by
  prefix, composing table names through `bridge.element_table_name`
  from `element.get("variable")` -- a key `WORKING_STATE_ELEMENT` does
  not have, since it is `var`. The candidate set was therefore empty
  and this map's own orphans were spared along with the colleague's
  tables. Re-proving two orphaned catalogue entries is what caught it:
  both came back UNJUDGEABLE, which means their tests had gone red.
  THE WHITELIST IS THE RECORD'S REAL DEFINITION AND IS WHERE A KEY IS
  READ FROM, never from memory.

### C-198 — A WIDGET THAT RE-DERIVES ITS VIEW TRANSFORM FROM WHAT IT DRAWS HAS MADE THE...

<sub>Cut from `CLAUDE.md`, lines 6102–6114 of the
2026-09-05 revision.</sub>

- **A WIDGET THAT RE-DERIVES ITS VIEW TRANSFORM FROM WHAT IT DRAWS HAS
  MADE THE TRANSFORM AN OUTPUT OF THE GESTURE.** (2026-09-01, reported
  by a hunt from the pixels and verified here from the numbers.) The
  Topology view fits to what it is drawing, and during a drag that is
  the PREVIEW; a drag freezes its origin and the unit's span at the
  press and reads later positions as fractions of that frame. So a fit
  taken mid-gesture closes a loop -- the preview moves the geometry,
  the fit re-measures a larger extent, the scale falls, the same screen
  point means a larger displacement. Held still through six repaints,
  a recorded nudge went 0.104, 0.207, 0.280, 0.318, 0.342, 0.356 while
  the scale fell 0.6138 to 0.5541. The frame is held for the length of
  a gesture now. ASK OF ANY PAINT-TIME FIT WHETHER A GESTURE'S FROZEN
  ORIGIN OUTLIVES IT.

### C-199 — THE DESIGN A CLAIM IS DRIVEN ON CAN REFUTE A REAL DEFECT

<sub>Cut from `CLAUDE.md`, lines 6116–6126 of the
2026-09-05 revision.</sub>

- **THE DESIGN A CLAIM IS DRIVEN ON CAN REFUTE A REAL DEFECT.**
  (2026-09-01, twice in one afternoon, both mine.) A vertex drag past
  its control's range records an out-of-range value on `archimedean
  4.8.8` and cannot on `laves 3.3.4.3.4`, where the library refuses
  the oversized nudge before anything is recorded; and a drag's frame
  drifts when a VERTEX is held and not when an EDGE is scaled, since
  only the first grows the extent the fit re-measures. Both of my
  first probes came back clean and both would have been filed as
  refutations. VARY THE DESIGN BEFORE BELIEVING A NEGATIVE, and where
  a guard depends on which design it runs on, NAME the design in the
  test and assert the premise that makes the case arise.

### C-200 — AND I COMMITTED PAST A RED GATE, HAVING READ IT

<sub>Cut from `CLAUDE.md`, lines 6128–6137 of the
2026-09-05 revision.</sub>

- **AND I COMMITTED PAST A RED GATE, HAVING READ IT.** (2026-09-01.)
  `check_standards` printed exit 1 and the commit ran anyway, because
  the chain was `check; echo; git commit` and the commit branched off
  the ECHO. That is this file's own entry about a gate whose exit
  nobody branches on, made by somebody who had quoted it the same day.
  Capture the status and branch on it IN THE SCRIPT THAT WOULD COMMIT.
  What the gate had caught was two catalogue entries orphaned by the
  repair, one of which then needed narrowing because
  `record = bridge.read_working_state(path)` appears three times in
  `dialog.py`.

### C-201 — A LANDING THAT ARRIVES MID-GESTURE MUST WAIT FOR THE POINTER TO COME UP

<sub>Cut from `CLAUDE.md`, lines 6139–6158 of the
2026-09-05 revision.</sub>

- **A LANDING THAT ARRIVES MID-GESTURE MUST WAIT FOR THE POINTER TO
  COME UP.** (2026-09-01, found FROM A RUNNER.) `show_topology` clears
  the drag preview and the chosen thing, which is right for a rebuild
  and wrong while somebody is dragging: a topology build finishing
  under their hand put the un-edited design back, dropped the
  highlight saying what they were aiming at, and left the drop to
  commit an edit out of a record they could no longer see. It shows
  here about one run in eight, and all three CI platforms failed the
  drag guard on its own PREMISE -- "the drag drew no preview at all",
  730 passed and 1 failed, three times over. From a distance that
  reads as a flaky test; the stack named the topology task's own
  callback. THE PANEL HOLDS THE LANDING NOW and settles it at the
  drop, discarding it where the gesture committed an edit, since that
  record makes the dialog chain and land again within the tick. It
  asks `gesture_in_progress`, which is the same method the frozen
  frame asks, so the two halves of one rule cannot come apart.
  ASK OF ANY BACKGROUND RESULT WHETHER IT MAY LAND ON A GESTURE, and
  where an intermittent failure is on a PREMISE rather than an
  assertion, suspect something erasing the state the premise is about
  rather than a slow machine.

### C-202 — A FIGURE WITH NO INSTRUMENT BESIDE IT IS FOLKLORE, AND A READER WILL SAY SO

<sub>Cut from `CLAUDE.md`, lines 6240–6257 of the
2026-09-05 revision.</sub>

- **A FIGURE WITH NO INSTRUMENT BESIDE IT IS FOLKLORE, AND A READER
  WILL SAY SO.** (2026-09-01, from a colleague reading the symmetry
  note.) Their two comments were "I have no idea what code it's
  running to find that the hex 7-colouring is especially egregious"
  and "what did it do with the rough implementations it claims to have
  written". Both were fair: the note quoted timings and a comparison
  without naming the probe behind either, and the rough
  implementations it described were committed inside one of those
  probes with nothing pointing at them. Every figure now names its
  probe, the note gives the one command that runs any of them, and it
  says why those implementations live in `tools/probes/` rather than
  in the plugin -- neither is a feature anybody has decided to build,
  and a half-implementation under `weavingspace_qgis/` reads as one.
  THE RULE: when a document quotes a measurement, name the code that
  made it in the same sentence, and re-run it before quoting it again.
  Re-measured that day, the nineteen seconds came back at 21.0 and
  21.2 against 4.2 for `hex-colouring 4`, which is what turns a number
  into evidence.

### C-203 — THE TWENTY-SECOND WATCHER FAULT WAS CAUGHT BEFORE ARMING, WHICH IS THE FIRST TIME

<sub>Cut from `CLAUDE.md`, lines 6259–6267 of the
2026-09-05 revision.</sub>

- **THE TWENTY-SECOND WATCHER FAULT WAS CAUGHT BEFORE ARMING, WHICH IS
  THE FIRST TIME.** (2026-09-01.) `gh` reads the repository from the
  WORKING DIRECTORY, so a watcher launched from a scratch folder asks
  about nothing, gets an empty answer, and reports nothing -- which is
  indistinguishable from a quiet branch. A hand-run before arming
  showed the silence in thirty seconds; the same hand-run had already
  caught a quoting error in its own reader. The practice this file has
  recommended since the tenth fault works, and the cost of it is one
  minute.

### C-204 — AND ALL FOUR WERE BUILT THE SAME DAY, with what each turned out to cost

<sub>Cut from `CLAUDE.md`, lines 6269–6304 of the
2026-09-05 revision.</sub>

- **AND ALL FOUR WERE BUILT THE SAME DAY, with what each turned out to
  cost.** (2026-09-01, after the grilling above.)
  THE LABEL/KEY SEPARATION WAS THE ONE THE OTHERS SAT ON, and it
  touched more than the catalogue: `family_combo` was built with
  `addItems(names)`, so 13 product sites and 121 suite sites treated
  the chooser's TEXT as the design's identity. The suite drives
  `_choose_family` now, because `setCurrentText` on a non-editable
  combo selects only an exact match and does NOTHING otherwise --
  silently -- so every one of those sites would have gone on testing
  whichever design happened to be selected.
  MULTI-CLASS SELECTION FIXED AN OLDER DEFECT ON THE WAY: the
  highlight compared a class label against the selection with `==`, so
  "every edge", whose datum has always been the whole group, lit
  nothing at all. Membership is what both need.
  THE SYMMETRY GATE IS SCOPED TO `push_vertex` AND TO THE MEASUREMENT.
  `directions_a_class_may_move` stacks (L - I) over a vertex's
  stabiliser modulo the lattice and returns 2 minus the rank; it
  agrees with what the manipulation does on every class measured --
  0.0000 of the unit where it says zero -- and it is asked only of the
  push, since a nudge is an arbitrary displacement and moves those
  same classes by 0.2. Its guard refuses to pass if every class
  answers the same way, which is what stops a gate that greys
  everything looking like one that works.
  THE DUAL NEEDED SOMETHING THE LIBRARY DOES NOT HAVE, and the
  workaround is written to the dependency procedure: measurement and
  removal criteria at the site, a canary asserting the gap, and a note
  to upstream in `docs/process/`. `Tileable.__init__` accepts a
  `tiles=` keyword, stores it, and overwrites it with a default unit,
  which was measured rather than assumed.
  AND THE TEST THAT MATTERED WAS THAT IT TILES. A thing that looks
  like a Tileable is not one: through `Tiling`, the promoted dual lays
  181 tiles over a 3km region for laves 3.3.4.3.4 and 84 for
  archimedean 4.8.8. My first reading said ZERO for every design and
  was the instrument -- a TiledMap holds its geometry in `map`, not
  `tiles` -- which is this file's own rule that a uniform verdict is
  almost always the instrument, met for the third time this week.

### C-205 — OPENING A GEOPACKAGE COSTS TIME PROPORTIONAL TO ITS LAYERS, AND A HELD HANDLE DOES...

<sub>Cut from `CLAUDE.md`, lines 6306–6327 of the
2026-09-05 revision.</sub>

- **OPENING A GEOPACKAGE COSTS TIME PROPORTIONAL TO ITS LAYERS, AND A
  HELD HANDLE DOES NOT ANSWER IT.** (2026-09-01, measured against GDAL
  directly for the first time.) That sentence had stood in four
  documents since 2026-08-29, INFERRED from the shape of the save's own
  growth rather than asked of the dependency -- a cause named by
  reading, which reads exactly like one somebody proved. Asked
  directly, on files of 8 to 256 tiny tables: an OGR update open runs
  1.99ms to 38.12ms and a QgsVectorLayer on one table 13.7ms to
  184.3ms, both doubling as the table count doubles. So a loop that
  opens the file once per element is quadratic in the element count,
  which is what made a 256-element save take 134 seconds.
  AND THE CHEAP REPAIR WAS RULED OUT BEFORE THE EXPENSIVE ONE WAS
  BUILT. Keeping a python-side handle alive across the act saves
  nothing at all -- 0.91 to 1.02 of the plain cost -- so GDAL's shared
  dataset cache is not the lever and the repair had to be a genuine
  single session. Ten minutes of measurement against a rewrite of a
  writer is the trade this project should make every time.
  WHAT IS AND IS NOT CLOSED: the writing and the style embedding are
  one session each now; the REPOINTING is not, because every layer
  genuinely needs its own provider, and it is about 33 seconds at the
  ceiling. That residue is measured and written at its own loop rather
  than left for somebody to rediscover.

### C-206 — A COMPARISON ACROSS TWO RUNS ON A BUSY MACHINE IS NOT A MEASUREMENT

<sub>Cut from `CLAUDE.md`, lines 6329–6339 of the
2026-09-05 revision.</sub>

- **A COMPARISON ACROSS TWO RUNS ON A BUSY MACHINE IS NOT A
  MEASUREMENT.** (Same day, and it nearly put a wrong number in a
  commit message.) A 32-element save read 1.1s in one run and 2.9s in
  the next ON IDENTICAL CODE, with the machine's load average between
  18 and 37 all session. This project's rule is already to reproduce a
  number with BOTH ARMS IN ONE RUN; what today adds is that the rule
  binds even when the change is structural and obviously right, because
  the figure you quote is the one somebody else will check.
  PREFER A CALL COUNT WHERE ONE CARRIES THE SAME CLAIM. "The style
  writer went from 256 calls to one" is immune to what else the machine
  was doing; "32.97s to 0.56s" is not.

### C-207 — OGR HANDS BACK A DATETIME IN ITS OWN FORMAT, SO A VALUE COPIED OUT OF A ROW IS A...

<sub>Cut from `CLAUDE.md`, lines 6341–6351 of the
2026-09-05 revision.</sub>

- **OGR HANDS BACK A DATETIME IN ITS OWN FORMAT, SO A VALUE COPIED OUT
  OF A ROW IS A DISPLAY RATHER THAN WHAT WAS STORED.** (Same day.)
  Writing this project's own `layer_styles` rows meant reproducing what
  QGIS puts there, so the columns were read off a file QGIS had written
  -- and the update_time copied from that reading was OGR's rendering,
  not the stored text. GDAL then warned "Non-conformant content for
  record N in column update_time ... successfully parsed" on every
  later read of every file the plugin writes. The column's own default
  is ISO and conformant, so the honest answer was to say nothing and
  let it fire. This is the project's own rule about comparing what a
  file HOLDS rather than how it renders, met from the WRITING side.

### C-208 — ONE STORE, ONE MEANING -- AND A QLabel IS A STORE

<sub>Cut from `CLAUDE.md`, lines 6371–6380 of the
2026-09-05 revision.</sub>

- **ONE STORE, ONE MEANING -- AND A QLabel IS A STORE.** (2026-09-01.)
  The Topology tab was given a sentence saying a build was coming, and
  it went into `note`, which already means "the answer, or the reason
  there is none". The suite's `_settle_topology` treats a non-empty
  note as an answer having ARRIVED, so every waiter returned before
  the build landed and a registered test read a class list that did
  not exist yet. It has its own label now, cleared by `set_unit`
  wherever a build lands. This project's commonest defect is one fact
  in two stores; this is its mirror -- two facts in one store -- and
  it arrives most easily in a widget nobody thinks of as state.

### C-209 — A HARNESS THAT MATCHES A SENTENCE THE PRODUCT SAYS IS RETUNED BY THE NEXT SENTENCE

<sub>Cut from `CLAUDE.md`, lines 6382–6392 of the
2026-09-05 revision.</sub>

- **A HARNESS THAT MATCHES A SENTENCE THE PRODUCT SAYS IS RETUNED BY
  THE NEXT SENTENCE.** (Same day, and it had been true of every save
  test in the suite.) `press_save` waited out a deferred press by
  matching "will be saved afterwards" in what the plugin said. A
  SECOND kind of deferral -- a save waiting on a topology -- says
  something else, so the wait never happened and a guard failed with
  the product behaving exactly as ruled. It asks `_save_pending` now,
  which is the promise itself and is set by every kind. The recorded
  form of this fault was a MAINTAINER REWORDING a notice; what today
  adds is that a new code path retunes it just as well, and nobody is
  editing prose when it happens.

### C-210 — A GUARD OVER THE WHOLE TREE CANNOT TELL YOUR OWN EDIT FROM WHAT IT IS WATCHING FOR

<sub>Cut from `CLAUDE.md`, lines 6394–6405 of the
2026-09-05 revision.</sub>

- **A GUARD OVER THE WHOLE TREE CANNOT TELL YOUR OWN EDIT FROM WHAT IT
  IS WATCHING FOR.** (Same day, twice in one hour.) A chain proving
  catalogue entries asserted the tree was restored by asking `git diff
  --quiet` over everything, and stopped on a document I had
  regenerated myself twenty minutes earlier. Scoped to the
  directories the catalogue mutates and baselined against what was
  ALREADY dirty, it runs. Then the same shape again: `git diff
  --quiet -- weavingspace_qgis` reported "not restored" because my own
  deliberate work lives there. THE QUESTION IS NEVER "IS THE TREE
  CLEAN" BUT "IS ANYTHING HERE THAT I DID NOT PUT THERE" -- for a
  mutating job, a baseline taken before it starts; for shipped source,
  a grep for the marker the mutation leaves.

### C-211 — A WATCHER'S OWN SHELL IS PART OF THE WATCHER, AND `/bin/bash` HERE IS 3.2

<sub>Cut from `CLAUDE.md`, lines 6407–6422 of the
2026-09-05 revision.</sub>

- **A WATCHER'S OWN SHELL IS PART OF THE WATCHER, AND `/bin/bash` HERE
  IS 3.2.** (2026-09-01, the twenty-third watcher fault.) A standing
  beat tracked "failures I have already reported" in an associative
  array. Bash 3.2 has none, so `seen[$name]` is an INDEXED array whose
  subscript is evaluated as ARITHMETIC -- and a log called
  `suite_175817_shard0.log` is not arithmetic. The script died on its
  first pass, before printing anything a reader could act on, which is
  the one failure mode a watcher must not have. State that survives a
  pass now lives in FILES.
  AND THE FIX FOR THE FAULT IT REPLACED WAS ALREADY THERE: the same
  loop reads `grep -c` without a `|| echo 0` fallback, because that
  command PRINTS 0 and EXITS 1 when nothing matches, so a fallback
  appends to a good answer rather than replacing it. That is the
  fifteenth fault, which this project has now paid for twice; the
  reason is written at the line rather than only here, which is what
  stops it travelling into the next throwaway script.

### C-212 — A FLAG READ BY ONE CONSUMER OUTLIVES THE JOURNEYS THAT CONSUMER NEVER RUNS ON

<sub>Cut from `CLAUDE.md`, lines 6433–6452 of the
2026-09-05 revision.</sub>

- **A FLAG READ BY ONE CONSUMER OUTLIVES THE JOURNEYS THAT CONSUMER
  NEVER RUNS ON.** (2026-09-01, found by writing the guard for a
  button added the same day.) The waiting window's Cancel sets
  `_save_cancelled`, which `write_gpkg_layers` reads BETWEEN TABLES
  and answers with a rollback. That is exact for a cancel during a
  WRITE -- and the commonest wait is for a REDRAW or a topology build,
  where nothing ever opens the file, so nothing ever reads the flag.
  Left standing it stopped the person's NEXT save: the writer halted
  at its first table, rolled back, and said "The save was stopped, so
  the map was not written" to somebody who had stopped nothing.
  THE SHAPE IS THIS FILE'S OWN DEFERRED-WORK RULE WEARING A FLAG.
  That rule asks what CONSUMES a remembered intent and whether the
  consumer can decline; this is the other end of it -- what CLEARS a
  remembered intent on the journeys where the consumer never runs at
  all. Enumerate those journeys in the same commit, and write the
  answer at the line rather than in a document.
  AND IT WAS FOUND BY THE GUARD RATHER THAN BY READING, which is the
  argument for writing the guard before believing the repair: four
  axes of that button were asserted, three passed, and the fourth --
  a later save still works -- went red on the first run.

### C-213 — WHEN A NAME GAINS A LABEL, SWEEP EVERY READER OF THE QUESTION, AND THE SILENT ONES FIRST

<sub>Cut from `CLAUDE.md`, lines 6454–6475 of the
2026-09-05 revision.</sub>

- **WHEN A NAME GAINS A LABEL, SWEEP EVERY READER OF THE QUESTION, AND
  THE SILENT ONES FIRST.** (Same day.) The label/key separation of the
  morning gave `laves 3.3.4.3.4` the displayed name
  `laves 3.3.4.3.4 (cairo)`, and the product moved cleanly: items
  carry the key as data, records store the key, one owner answers
  "which design is this". SIX SITES IN THE SUITE did not, and only one
  of the six was turned up by the search that found the first.
  FIVE FAILED LOUDLY, which is the helper doing its job: `_choose_family`
  refuses a design the chooser does not offer, where `setCurrentText`
  had been selecting nothing in silence and leaving each test to
  measure whichever design happened to be current. That is a work list
  rather than a regression.
  THE SIXTH SKIPPED IN SILENCE and cost far more. The topology matrix
  guards each cell with "is this family on offer", asked of the
  chooser's TEXT, and a cell that answered no was counted and NOT
  named -- so 15 of 35 cells survived and the failure listed one skip
  of nineteen. Its own accounting was thorough; what defeated it was a
  cheap guard at the top of the loop, written about the fixture rather
  than about the product, which is exactly the kind nobody re-reads.
  SO THE SWEEP IS FOR THE QUESTION -- which design is this -- and not
  for the string that happened to break; and any skip added to a loop
  carries its reason, or it is a cell that never existed.

### C-214 — AN ENVIRONMENT SCRIPT THAT PRINTS BARE ASSIGNMENTS NEEDS `set -a`, OR THE CHILD...

<sub>Cut from `CLAUDE.md`, lines 6477–6485 of the
2026-09-05 revision.</sub>

- **AN ENVIRONMENT SCRIPT THAT PRINTS BARE ASSIGNMENTS NEEDS `set -a`,
  OR THE CHILD NEVER SEES THEM.** (Same day, caught before it cost
  anything.) `tools/macos_qgis_env.sh` prints KEY=value lines, so a
  plain eval sets SHELL variables and exports nothing -- and the run
  then dies with "No module named 'encodings'" while the shell
  believes PYTHONHOME is set, which reads as a broken interpreter
  rather than a missing export. The reason lives at the line in the
  session's own helper, because a rule in a binding document does not
  travel into the next throwaway script.

### C-215 — A CANDIDATE'S OWN SUITE IS READ SHARD BY SHARD, AND THE PARTITION IS THE PROOF

<sub>Cut from `CLAUDE.md`, lines 6487–6497 of the
2026-09-05 revision.</sub>

- **A CANDIDATE'S OWN SUITE IS READ SHARD BY SHARD, AND THE PARTITION
  IS THE PROOF.** (2026-09-01, the rc10 candidate.) The stage line
  says one number and the log carries three: 250, 249 and 249 tests,
  each shard naming the SAME total of 748. That agreement is what
  makes a slice a partition rather than three overlapping runs -- the
  first sharded run this project ever made read 285, 285 and 286, and
  slices that disagree about the size of the whole mean something ran
  twice or not at all. A total climbing healthily is also what a shard
  dying at startup looks like from outside, which this project has met
  once. So the three numbers are quoted rather than their sum,
  wherever a green suite is claimed.

### C-216 — A DOCUMENTATION EDIT CANNOT INVALIDATE A CANDIDATE, AND KNOWING THAT IS WHAT MAKES...

<sub>Cut from `CLAUDE.md`, lines 6499–6511 of the
2026-09-05 revision.</sub>

- **A DOCUMENTATION EDIT CANNOT INVALIDATE A CANDIDATE, AND KNOWING
  THAT IS WHAT MAKES THE HOUR AFTER ONE USABLE.** The receipt digests
  exactly the files that SHIP, taken with `build.py`'s own
  `shipped_files()`, and it deliberately ignores tests, tooling and
  documentation -- because those cannot change what a reviewer
  installed, and a gate that fired on a comment in the suite is a gate
  people learn to route around. So the write-up, the roadmap and the
  lessons can all be finished while CI answers, and the candidate
  standing in `dist/` is still the artefact its receipt describes.
  WHAT DOES INVALIDATE IT is any shipped byte, which includes
  `metadata.txt` -- so a changelog correction after a candidate is a
  new candidate, which is the trade the approved-prose-goes-stale rule
  is really about.

### C-217 — A WORKFLOW'S NAME IS NOT ITS CONTRACT, AND THIS ONE HAS BEEN MISREAD TWICE

<sub>Cut from `CLAUDE.md`, lines 6513–6532 of the
2026-09-05 revision.</sub>

- **A WORKFLOW'S NAME IS NOT ITS CONTRACT, AND THIS ONE HAS BEEN
  MISREAD TWICE.** (2026-09-01, on the maintainer asking whether the
  mutation gate had been tightened.) It had not, and nothing about it
  had moved since 2026-08-19. Read off `.github/workflows/mutation.yml`
  rather than off the prose about it: both measuring steps carry
  `continue-on-error`, so no survivor can redden that workflow and the
  decision of 2026-08-11 holds exactly as written. What exits 1 is the
  step that records which tests touch which lines -- the WHOLE SUITE,
  three ways, refusing a partial record because one missing shard
  never offers its tests the chance to notice a mutant and so
  overstates survivors in one direction only.
  IT HAS STOPPED TWO CANDIDATES AND BEEN RIGHT BOTH TIMES, rc7 and
  rc10, and neither red was a survivor. The confusion is entirely the
  NAME on the red, which is why the honest split -- per job rather
  than per workflow -- is recorded as a conflict for a grilling rather
  than changed in passing.
  THE HABIT: when a gate's behaviour surprises you, open the gate,
  not the document that describes it. Three of this project's own
  documents describe that workflow, and none of them said which of its
  steps can fail.

### C-218 — AND I EDITED A DOCUMENT THE RUNNING SUITE READS

<sub>Cut from `CLAUDE.md`, lines 6543–6555 of the
2026-09-05 revision.</sub>

- **AND I EDITED A DOCUMENT THE RUNNING SUITE READS.** (Same day, and
  it is the tree-lock rule with the roles reversed.) That rule is
  usually stated about SOURCE -- do not edit what a gate is measuring
  -- and `STAGE_DEPENDS` names CLAUDE.md, MAINTAINING.md, README.md
  and ROADMAP.md for exactly this reason: `test_every_documented_
  command_still_exists` opens them, so a documentation edit really can
  turn a running candidate red, and it is the kind of change that
  feels as though it cannot. Nothing came of it here, checked rather
  than hoped by running that test on the edited tree while the
  candidate was still in its suite. The habit: while a candidate is
  reading the working tree, documentation is not automatically safe --
  it is safe from the RECEIPT, which digests only what ships, and not
  from the SUITE.

### C-219 — AN INSTRUMENT THAT DIES AFTER REPORTING LOOKS EXACTLY LIKE THE THING IT MEASURES DYING

<sub>Cut from `CLAUDE.md`, lines 6556–6569 of the
2026-09-05 revision.</sub>

- **AN INSTRUMENT THAT DIES AFTER REPORTING LOOKS EXACTLY LIKE THE
  THING IT MEASURES DYING.** (2026-09-01.) A two-arm probe printed
  both its readings and then took a SEGMENTATION FAULT at interpreter
  teardown, holding dialogs alive past `exitQgis`. Nothing about that
  crash concerns the product, and a reader meeting the last line of
  the log would have every reason to think otherwise. It prints a
  sentinel now -- both arms reported, teardown complete -- so a
  truncated run is distinguishable from a finished one, which is this
  file's own rule that a check must state its own completeness rather
  than leave it to be inferred.
  AND ITS EXIT STATUS WAS READ FROM A PIPE, which said 0 while the
  probe had segfaulted: the status belonged to `tail`. That is the
  gate-behind-a-pipe fault arriving at a PROBE rather than a gate, and
  the sentinel is what tells the two apart when the status cannot.

### C-220 — A DEPENDENCY THAT ANSWERS BY RETURN VALUE CANNOT BE CAUGHT BY `except`

<sub>Cut from `CLAUDE.md`, lines 6570–6591 of the
2026-09-05 revision.</sub>

- **A DEPENDENCY THAT ANSWERS BY RETURN VALUE CANNOT BE CAUGHT BY
  `except`.** (2026-09-02, and it was the sharpest defect of the
  campaign's first day.) `write_gpkg_layers` wrapped its commit in a
  `try`, with a comment explaining that a commit which will not go
  through leaves the file as it was. OGR does not raise there: it
  returns an `OGRErr`, and the code took the answer on trust. So with
  a shared read transaction open on the file -- a colleague, a script,
  a sync client, or QGIS itself elsewhere -- every table went in, the
  COMMIT was refused, `written` still named all of them, and the
  caller repointed every element layer at a table that had never been
  created. The person was told "Saved" and the map on screen emptied.
  THE ROLLBACK BRANCH BESIDE IT ALREADY KNEW, which is the tell worth
  copying: it clears `written` and says at the line that otherwise
  "the caller would repoint layers at tables that went away". When one
  arm of a pair carries that sentence and the other does not, the
  other is the defect.
  AND THE TWO WAYS A LOCK CAN BITE ARE NOT THE SAME. A WRITE lock held
  by another process fails at the first feature, which this code
  reports correctly; only a SHARED READ transaction lets every table
  through and refuses the commit. The first route measured came back
  honest, and stopping there would have filed the claim as not
  reproducing.

### C-221 — A WAIT ONLY AN OUTER FRAME CAN END IS NOT A WAIT

<sub>Cut from `CLAUDE.md`, lines 6592–6606 of the
2026-09-05 revision.</sub>

- **A WAIT ONLY AN OUTER FRAME CAN END IS NOT A WAIT.** (Same day.)
  `_save_the_map` turns the event loop once per element behind its
  progress bar, so a close or a quit arriving during a write is
  delivered by THAT WRITE'S OWN PUMP -- and the hold it reaches then
  runs NESTED INSIDE the write, spinning until `_saving_now` clears,
  which only the suspended frame beneath it can do. The window sat
  frozen for the whole 180-second ceiling with its bar on "preparing
  to save", and its only control threw the map away. Measured through
  both doors with the ceiling shortened and said so: 5.1s against a
  control's 0.16s.
  THE QUESTION TO ASK OF ANY WAIT: which frame clears the thing I am
  waiting for, and can it run while I spin? Where the answer is no,
  the honest exit is the one the stack already guarantees -- here the
  save lands the moment the hold returns, so the act is let through
  and the map is written.

### C-222 — AN "EMPTY" FILE IS A QUESTION ABOUT CONTENT, NOT ABOUT BYTES

<sub>Cut from `CLAUDE.md`, lines 6607–6616 of the
2026-09-05 revision.</sub>

- **AN "EMPTY" FILE IS A QUESTION ABOUT CONTENT, NOT ABOUT BYTES.**
  (Same day.) The ownership question decided whether a GeoPackage was
  somebody else's with `os.path.getsize(path) > 0`, and a data source
  OGR has created and nothing has written to is 65,536 bytes of header
  holding no layer. So a stub left by a cancelled or failed first save
  read as a stranger's work -- and the answer is CACHED for the
  session, so every remover scoped to our own files stayed off.
  Measured with a control: after the stub, shrinking a four-element
  design to two left two elements' tables, columns and VALUES in the
  file a colleague receives. It asks `bridge.gpkg_tables` now.

### C-223 — A TABLE KEYED BY A FAMILY DOES NOT GROW WITH THE FAMILY

<sub>Cut from `CLAUDE.md`, lines 6617–6627 of the
2026-09-05 revision.</sub>

- **A TABLE KEYED BY A FAMILY DOES NOT GROW WITH THE FAMILY.** (Same
  day.) `_drag_moved` answers "did this gesture ask for anything" per
  manipulation, because each has its own idea of nothing -- zero
  travel for a nudge, half a degree for a rotation, one per cent for a
  scale. It was written when a vertex carried ONE handle; the push
  rail arrived the next day under the ruling that every manipulation
  is reachable on the drawing, and the fall-through answered False for
  it. A drag somebody watched move under their hand was thrown away in
  silence. WHEN A HANDLE LIST, A VERB LIST OR A MODE LIST GAINS A
  MEMBER, GREP EVERY TABLE KEYED BY THAT LIST -- and guard the SHAPE,
  so the next member is covered by whoever adds it.

### C-224 — A PREDICATE THAT MERGES TWO FACTS IS RIGHT FOR A WAIT AND WRONG FOR A QUESTION

<sub>Cut from `CLAUDE.md`, lines 6628–6646 of the
2026-09-05 revision.</sub>

- **A PREDICATE THAT MERGES TWO FACTS IS RIGHT FOR A WAIT AND WRONG
  FOR A QUESTION.** (2026-09-02, found by two hunts independently and
  from opposite directions, which is the strongest confirmation this
  method produces.) `_a_save_is_outstanding` answers "is there a save
  that has been asked for and not finished", deliberately merging a
  PROMISE made with the KEEPING of it, because to the person who
  pressed the button they are one act. That is exactly right for the
  hold, which waits for either to end. It is wrong for the CLOSE, which
  asks a QUESTION -- and whose Close arm answered only the first half:
  it cleared `_save_pending`, already False during a write, reported
  "Closed without saving", and let the write run on to completion over
  the file the person had just declined. Every element layer was
  repointed at that file, so the map in their project ended up backed
  by it, and "Saved to ..." was said immediately after the sentence
  promising the opposite.
  SO WHEN A REPAIR TEACHES A GUARD A NEW STATE, READ THE CALLER'S
  PRECONDITION IN THE SAME BREATH. One name for two acts is fine while
  every caller wants both; the day one caller wants only one of them,
  the name stops carrying the difference and nothing says so.

### C-225 — A FRAME MUST NOT REPORT THE OUTCOME OF AN ACT IT CANNOT SEE

<sub>Cut from `CLAUDE.md`, lines 6647–6660 of the
2026-09-05 revision.</sub>

- **A FRAME MUST NOT REPORT THE OUTCOME OF AN ACT IT CANNOT SEE.**
  (Same day, the other end of the same mechanism.) `write_gpkg_layers`
  asks `should_stop` BETWEEN TABLES, so a Cancel landing during the
  styling or the repointing -- 13.0s of a 256-element save -- cannot
  be served and the write finishes. That much is settled and correct.
  What was not is that the hold then reported it: resuming, it read
  `_saving_now` as False, unable to tell a write that had just
  FINISHED from a wait in which nothing was ever opened, and said "the
  map was not written" beside the save's own report that it was.
  THE FIX IS A MOMENT RATHER THAN A CONDITION: record whether a write
  was under way AT THE PRESS, which is the only moment that can be
  known, and leave the report to the frame that can see the answer --
  here the writer, which speaks in both cases. Ask of any two frames
  reporting one act which of them actually watched it happen.

### C-226 — A FILTER IS A VIEW, AND `getFeatures()` HONOURS ONE

<sub>Cut from `CLAUDE.md`, lines 6661–6683 of the
2026-09-05 revision.</sub>

- **A FILTER IS A VIEW, AND `getFeatures()` HONOURS ONE.** (Same day,
  found by the specification hunt.) A person who sets a filter on an
  element layer in QGIS -- the Query Builder in Layer Properties --
  had every tile it hides written OUT of their saved GeoPackage at the
  next Save, permanently, under the word "Saved". Measured on three
  arms in one run: between two saves a table went from 41 rows to 3,
  and across a re-tile -- where the plugin carries the filter onto the
  new layer deliberately -- the same table went to ZERO, the filter
  naming feature ids the new tiling never produced.
  WHICH OF THE TWO A FILTER IS WAS SETTLED BY THE PLUGIN'S OWN WORDS
  rather than by preference: the line that carries a subset across a
  re-tile says it says which features to DRAW. So it comes off for the
  write and goes back in the save's own `finally`, since the cancel
  branch returns between the two and an exception may leave by neither
  door -- a save that silently cleared somebody's filter would trade
  one loss for another.
  AND IDENTITY THAT LIVES IN A SOURCE STRING GAINS A NEW TAIL THE
  MOMENT A USER TOUCHES THE LAYER. `same_source` compares the whole
  tail, rightly, for every other question it answers; a subset lives
  in that tail, so a filtered layer stopped matching the table it was
  plainly reading from. The save asks its own question without the
  subset now, and `same_source` is left alone -- it also decides which
  group a dataset owns and whether a landing may write over one.

### C-227 — A RECORD FILLED BY A LANDING AND CLEARED BY NOTHING ANSWERS FOR A MAP IT HAS NEVER SEEN

<sub>Cut from `CLAUDE.md`, lines 6684–6701 of the
2026-09-05 revision.</sub>

- **A RECORD FILLED BY A LANDING AND CLEARED BY NOTHING ANSWERS FOR A
  MAP IT HAS NEVER SEEN.** (Same day, found by backwards-from-harm at
  the end of a list that had ranked it fifteenth.) `_element_tables`
  is written when a map LANDS and cleared by neither the Load door nor
  a group switch, so a session that has drawn any map carries THAT
  map's table names -- and an opened map's elements share their ids
  with it. The save took its names from that record and asked the
  layer's own source only where the record was silent, so a person who
  drew a map, opened a saved one with Load and pressed Save got a file
  whose table was NAMED for one variable and HELD another, with the
  sender's table dropped. The file contradicted its own record.
  THE COMMENT AT THAT LINE ALREADY CALLED THE SOURCE "the only witness
  that has not been through this session", WHICH IS THE TELL: an
  authority subordinated to the record it exists to correct. The
  witness is asked for every element now, and the record answers only
  where it has nothing to say -- which costs the drawn map nothing,
  since its layers read from MEMORY at the first save and from those
  very names afterwards.

### C-228 — AND WHEN A RESUME STAMPS ONE STORE, IT STAMPS THE OTHER

<sub>Cut from `CLAUDE.md`, lines 6702–6716 of the
2026-09-05 revision.</sub>

- **AND WHEN A RESUME STAMPS ONE STORE, IT STAMPS THE OTHER.** (Same
  day, found by the hunt aimed at the same morning's repairs, which is
  that direction's eleventh outing for eleven.) A resume stamps the
  GROUP's record with the region the recovery LANDED ON, and it must:
  a self-contained file records the SENDER'S own path and nothing on
  the recipient's machine answers to it. It never re-stamped the
  LAYERS, and `_our_groups` asks the layers -- so the two disagreed,
  `theirs` came back empty, and the binding let go of the map just
  opened. A Generate then built a rival group beside it and a Save
  wrote that rival into the opened map's own tables.
  IT REPRODUCED AT BOTH DOORS, which is what said whose defect it was:
  the fresh branch does it too, so the flag that reveals it decides
  only whether the binding is REACHED, and the repair belongs on the
  stamp. A claim's own note that "if the twin shares the exposure the
  repair belongs elsewhere" is worth driving rather than reading.

### C-229 — AND A DEPENDENCY'S REFUSAL CAN STOP BEING TRUE WHILE THE RULE IT JUSTIFIED STANDS

<sub>Cut from `CLAUDE.md`, lines 6717–6734 of the
2026-09-05 revision.</sub>

- **AND A DEPENDENCY'S REFUSAL CAN STOP BEING TRUE WHILE THE RULE IT
  JUSTIFIED STANDS.** Measured 2026-09-02 with the plugin out of the
  way: a `QgsVectorLayer` on `path|layername=tiles_b_v1`, copied into
  `tiles_b_v1` through an open OGR update transaction the way
  `bridge._write_one_layer` does, wrote 40 of 40 features, raised
  nothing, and committed `OGRERR_NONE`. The skip that treats a layer
  already reading from its destination as saved already was justified
  by "asking OGR to write a layer into the table it is reading from is
  asking it to overwrite a layer with itself, which it refuses" -- and
  that refusal was `QgsVectorFileWriter`'s, which the single-session
  rewrite of 2026-09-01 stopped going through. The line stays, its
  remaining job being cost rather than correctness, and its catalogue
  entry is retired with the measurement.
  THE SHAPE, and it is the dependency procedure read backwards: a
  workaround gets a canary because the bug may be fixed under it. A
  JUSTIFICATION deserves the same suspicion, because the mechanism it
  names may stop being reached under it -- and nothing fails when that
  happens, which is why it is found by a hunt rather than by a gate.

### C-230 — THE TWENTY-FOURTH WATCHER FAULT: A JOB NAME HAS A SPACE IN IT

<sub>Cut from `CLAUDE.md`, lines 6735–6746 of the
2026-09-05 revision.</sub>

- **THE TWENTY-FOURTH WATCHER FAULT: A JOB NAME HAS A SPACE IN IT.**
  (2026-09-02, mine, in a watcher armed at the maintainer's asking to
  reach a green candidate.) The reading was `for job in $JOBS` over
  lines like `suite (4.0.3)=success`, which the shell splits at the
  space -- so every line arrived as `tests (4.0.3)=success` and there
  was no telling the SUITE from the INSTALL. Both are green far more
  often than not, so the log read plausibly and said nothing. The
  names have their spaces replaced before the split now.
  IT IS THE NAME-YOUR-SUBJECT RULE MET INSIDE ONE LINE rather than
  across a branch: a verdict whose subject is ambiguous is not a
  measurement, and a watcher that reports twelve jobs under six names
  is reporting half of what it read.

### C-231 — A LAUNCH STATE BEATS THE CARRY, SO HANDING A KEY OVER IS NOT THE SAME ACT AS LETTING...

<sub>Cut from `CLAUDE.md`, lines 6748–6769 of the
2026-09-05 revision.</sub>

- **A LAUNCH STATE BEATS THE CARRY, SO HANDING A KEY OVER IS NOT THE
  SAME ACT AS LETTING IT FALL THROUGH.** (2026-09-02, ledger rows 22
  and 23, and the second is my own repair's defect found within the
  hour by the hunt replenished onto it.) `_stamp_working_state` merges
  a launch state OVER the record already on the group, so a resume
  that hands `region_crs` across unconditionally stamps the FILE's
  answer onto a group whose own record a LANDING wrote. Row 22 was the
  key falling through to the live chooser, which put a stranger's
  system on somebody's region; row 23 was the repair for it taking the
  carry away, so a file older than the key left the group saying
  nothing at all and a file carrying the earlier defect's value had
  that copied back over a record that was right.
  THREE STORES, IN THE ORDER OF WHAT EACH KNOWS, is the shape that
  settled it: the RESOLUTION (the layer a recovery landed on), then
  the GROUP's own record, then the FILE's. Ask of any fact with more
  than one holder not merely which writer has a reason, but which of
  them was standing at the moment the fact is about.
  AND THE DOOR THAT LOOKS HELD IS A COUNTDOWN. The already-open door
  was held by the carry rather than immune, which is why both doors
  are written the same way and why the catalogue entry stands on the
  twin: an entry on a line held by somebody else's mechanism can only
  ever survive.

### C-232 — A KEY THAT ENUMERATES TWO OF A DESIGN'S TERMS IS A SECOND DEFINITION OF THE DESIGN

<sub>Cut from `CLAUDE.md`, lines 6771–6793 of the
2026-09-05 revision.</sub>

- **A KEY THAT ENUMERATES TWO OF A DESIGN'S TERMS IS A SECOND
  DEFINITION OF THE DESIGN.** (2026-09-02, ledger row 24, and THREE
  hunts of one round reached it from three directions -- backwards
  from harm, the specification itself, and the stochastic sessions,
  which is the strongest confirmation this method produces.)
  `topology_edits.shelf_key` was the family and the element count, and
  "Map the dual instead" moves neither -- so a design and its dual
  shared one shelf, and an edit made on the dual was replayed onto the
  design's own like-named edge the moment the box came off. This file
  already carries the rule from the save's staleness guard, where a
  guard comparing three of twenty-six fields went stale; what row 24
  adds is that the same fault arrives in a KEY, where nothing reads as
  a comparison at all.
  THE TERM IS A SUFFIX so that nothing already saved moves, and the
  RESTORE takes it from the record rather than from the controls, for
  the reason the family and the count already do.
  AND WHAT IS NOT REPAIRED IS RECORDED AS A RULING: every other design
  term is still outside that key, and a scale modifier was measured
  turning two edge classes into four, so a named class comes to
  describe a disjoint set of edges. Widening the key would put
  somebody's edits away on an ordinary spacing tweak, which is a
  decision about when edits go quiet rather than a fix to make in
  passing.

### C-233 — A QUESTION BUILT ON A MERGED PREDICATE MERGES THE SAME TWO STATES

<sub>Cut from `CLAUDE.md`, lines 6795–6810 of the
2026-09-05 revision.</sub>

- **A QUESTION BUILT ON A MERGED PREDICATE MERGES THE SAME TWO
  STATES.** (Maintainer's ruling, 2026-09-02: "a panel's close button
  shouldn't stop a save, it should prompt whether to interrupt save".)
  Ledger row 5 mended `_a_save_is_outstanding` for merging a promise
  with the keeping of it -- right for a WAIT, wrong for a QUESTION --
  and the repair taught the Close arm to stop a write. The QUESTION
  above it went on merging them, so somebody answering about a promise
  they no longer wanted was taken to have said "throw away the write
  you are half way through".
  SO A REPAIR AT A PREDICATE IS NOT FINISHED UNTIL THE SENTENCES
  ABOVE IT ARE READ. There are two questions now, and the write's one
  has the safe answer as its default on the dependency-consent
  precedent. What No does is written at the code rather than implied,
  because the wording leaves it open: the write is not interrupted and
  the window closes, since a close arriving on the write's own pump
  cannot wait for the frame beneath it.

### C-234 — A CONTROL ONE ACT MOVES AS A SIDE EFFECT IS READ BY ANOTHER ACT AS A DECISION

<sub>Cut from `CLAUDE.md`, lines 6812–6831 of the
2026-09-05 revision.</sub>

- **A CONTROL ONE ACT MOVES AS A SIDE EFFECT IS READ BY ANOTHER ACT AS
  A DECISION.** (Maintainer's ruling, 2026-09-02: "the save should
  happen first. then the load".) A Save kept while a re-tile is coming
  is a promise, and `_honour_a_queued_save` re-reads the output
  chooser at the moment of the write so that somebody who changes
  their mind about where the map goes is obeyed. A LOAD moves that
  same chooser and means nothing of the kind -- it says where the map
  being OPENED lives -- so a Load inside the promise's window consumed
  the promise against the other file and the person's own map was
  never written.
  THE RULING IS AN ORDER RATHER THAN A QUESTION, which is what makes
  it cost no new prose: the Load is DEFERRED behind the promise and
  performed when the promise ends, kept or dropped. That is the FOURTH
  deferred kind, and it follows the family's rule -- taken and cleared
  at the point of use, and cleared at the close, since a deferred act
  belongs to the session that asked for it.
  AND AN ORDER IS TWO CLAIMS. "The save first, then the load" is
  satisfied in appearance by a repair that protects the save and
  swallows the Load, which leaves a button that does nothing, so each
  half carries its own catalogue entry.

### C-235 — THE TWENTY-FIFTH WATCHER FAULT: ARMED THROUGH A PIPE, AND THE LESSON WAS MINE FROM...

<sub>Cut from `CLAUDE.md`, lines 6833–6844 of the
2026-09-05 revision.</sub>

- **THE TWENTY-FIFTH WATCHER FAULT: ARMED THROUGH A PIPE, AND THE
  LESSON WAS MINE FROM THAT MORNING.** (2026-09-02.) A watcher was
  launched as its script piped into `tail`, which buffers to EOF -- so
  a watcher running perfectly well printed NOTHING, and the maintainer
  said so before any beat arrived. The identical fault is written in
  docs/TESTING.md the same day, from hand-running one into a pipe.
  THE HALF THAT IS NEW IS WHERE IT ARRIVED. The rule had been learned
  at the HAND-RUN and applied there faithfully; arming is a second
  moment, and the pipe was added in the same breath as a `tail -40`
  meant to keep the output short. Redirect a watcher to a FILE and
  read the file -- and where the harness reports a background job's
  own output, remember that the job's exit is what flushes a pipe.

### C-236 — A PROBE'S CONTROL CAN MOVE THE THING BOTH ARMS ARE ABOUT

<sub>Cut from `CLAUDE.md`, lines 6846–6858 of the
2026-09-05 revision.</sub>

- **A PROBE'S CONTROL CAN MOVE THE THING BOTH ARMS ARE ABOUT.**
  (2026-09-02, verifying row 24.) The control for "an ordinary design
  change moves the shelf key" changed the ELEMENT COUNT -- which
  repopulates the family list and lands on whatever that count offers,
  so `hex-slice 4#4` became `square-colouring 5#5` and every later
  reading was about a design nobody had chosen. A family change is the
  control that moves one term only.
  AND A HELPER THAT MIRRORS AN OLD SIGNATURE GOES ON PRINTING THE OLD
  ANSWER. The same probe computed the key itself rather than asking
  the product, so after the repair it reported the key unchanged and
  read as though nothing had landed. Ask the product its own question;
  a reimplementation in the instrument is a second definition, which
  is the very fault row 24 is about.

### C-237 — AN ASSERTION THAT NAMES A MOMENT IS A CLAIM ABOUT WHEN ITS OWN READING WAS TAKEN

<sub>Cut from `CLAUDE.md`, lines 6860–6884 of the
2026-09-05 revision.</sub>

- **AN ASSERTION THAT NAMES A MOMENT IS A CLAIM ABOUT WHEN ITS OWN
  READING WAS TAKEN.** (2026-09-02, CI's coverage leg on rc13's own
  commit, and it spent that candidate.) `a build that lands mid drag
  does not wipe the gesture` failed on its main assertion rather than
  on a premise -- "the panel adopted a new topology mid-gesture" -- on
  one shard of three, each naming the same total of 772, while the
  same test passed in the candidate's own local suite. The product was
  innocent: the test read the topology the panel holds BEFORE the
  clicks that find a handle, those clicks turn the event loop, and this
  test deliberately does not drain the queued build first because its
  subject IS a landing arriving under a pointer. A landing in that
  window is adopted correctly, no gesture being in progress, so the
  captured value went stale and correct behaviour was reported as the
  defect.
  STAGED RATHER THAN ARGUED, both arms in one run by
  `tools/probes/which_moment_the_drag_guard_reads.py`: with a landing
  delivered before the press the old reading fails and a reading taken
  at the press holds, and in BOTH arms the mid-gesture landing is
  refused. The repair is a MOMENT rather than a wait -- the subject is
  read inside the helper that presses, where nothing can move it,
  since a landing arriving with the pointer down is held. A settle
  would have been the obvious repair and is the one this test's own
  comment forbids.
  AND ALL THREE CATALOGUE ENTRIES WERE RE-PROVED after it, because a
  repair to a test is exactly where a guard stops being able to fail.

### C-238 — A WAIT HELPER THAT DOES NOT WIDEN IS A CEILING SIZED ON THE FASTEST MACHINE THE...

<sub>Cut from `CLAUDE.md`, lines 6886–6909 of the
2026-09-05 revision.</sub>

- **A WAIT HELPER THAT DOES NOT WIDEN IS A CEILING SIZED ON THE
  FASTEST MACHINE THE SUITE WILL EVER RUN ON.** (2026-09-02, rc14, and
  it spent a second candidate in two days.) Every allowance in this
  suite is `CONTENTION` times something -- 2.5 for a sharded run times
  each platform's declared slowness, so a three-shard Linux job gets
  seven and a half times this Mac's patience. FOUR SHARED WAITERS HAD
  NO SUCH FACTOR, including `_settle`, the oldest and most-called of
  them. CI's 4.0.3 leg duly failed `a drag is measured in the frame it
  began in` on its PREMISE after ninety seconds -- while the next
  topology test on the same runner passed in 4.3 seconds, which is
  what says the tab was healthy and the number was this machine's.
  THE GUARD IS OVER THE SHAPE AND DERIVES ITS OWN LIST, because a
  hand-kept list of waiters drifts the first time somebody adds a
  fifth -- the fault this file already records of `USER_FACING` and of
  `sandbox.INCLUDE_FILES`. It proved itself on its first run by naming
  a fourth waiter three hand repairs had missed, which is the only
  evidence a new guard's liveness ever has.
  AND A PREMISE THAT FIRES ON A MACHINE NOBODY CAN LOG INTO MUST SAY
  WHAT IT FOUND. "A topology build never stopped being outstanding"
  names four possible causes and reports none, so ninety seconds of
  runner time bought no information; `_why_the_topology_tab_is_busy`
  reads all four and both premise sites now carry its answer. This is
  the project's own rule about instrumenting a child process before it
  crashes, arriving at an ASSERTION MESSAGE.

### C-239 — `findData` COMPARES THROUGH QVariant, SO A TUPLE NEVER MATCHES AN EQUAL TUPLE

<sub>Cut from `CLAUDE.md`, lines 6911–6922 of the
2026-09-05 revision.</sub>

- **`findData` COMPARES THROUGH QVariant, SO A TUPLE NEVER MATCHES AN
  EQUAL TUPLE.** (2026-09-02, and the first repair built on it changed
  nothing whatever.) The topology class chooser carries `(target,
  label)` as its item data; `combo.findData(wanted)` answers -1 for a
  pair that is plainly in the list, while the verb chooser's own
  `findData` beside it works perfectly -- because its data is a
  STRING. The repair looked right, ran, and the probe reported the
  identical before-and-after, which is the shape this file already
  names: a verdict that will not budge is almost always the
  instrument. Compare `itemData(i)` in Python where the data is not a
  primitive, and ask of any Qt lookup whose argument is a Python
  object whether Qt has any way to know what equality means for it.

### C-240 — A LANDING IS HELD FOR A GESTURE, AND THE CLICK BEFORE THE PRESS IS NOT A GESTURE

<sub>Cut from `CLAUDE.md`, lines 6924–6949 of the
2026-09-05 revision.</sub>

- **A LANDING IS HELD FOR A GESTURE, AND THE CLICK BEFORE THE PRESS IS
  NOT A GESTURE.** (2026-09-02, macOS CI at `743e73b`.) The ruling of
  2026-09-01 holds a build that lands mid-drag until the pointer comes
  up, and `gesture_in_progress()` is true from the press to the
  release -- so the window between the CLICK that chooses a class and
  the PRESS that grabs its handle is uncovered, and a landing there
  applies at once. Two things then went, and NEITHER REPAIR WORKS
  ALONE: a refilled combo sits on its first entry, so the class
  somebody chose became whichever sorts first; and the handles
  re-seated on the FIRST member of the class, 177 pixels from the
  click, so the press found nothing to grab. Repair the second only
  and the handles come back to the nearest member of the WRONG class.
  Two halves, two catalogue entries, both proved.
  THE HALF THAT GENERALISES IS THE WINDOW. When a rule is written
  about a gesture, ask what the state looks like just BEFORE the
  gesture begins -- a selection made and not yet acted on is state a
  person can see and lose, and no in-progress guard covers it.
  AND THE REPAIR EXPOSED A FIXTURE THAT COULD NOT SELECT WHERE IT
  CLICKED: with an edge class kept across a rebuild, an edge handle
  sits over the vertex an aimer wants, `_handle_at` is asked first, so
  the click GRABS and leaves the edge selected -- reported as
  "nudge_vertex is not offered while holding a edge", which is a
  sentence about the fixture wearing a complaint about the product.
  The hazard was written in the aimer's own docstring and only one of
  its two paths acted on it. WHEN A DOCSTRING NAMES A HAZARD, CHECK
  EVERY PATH THROUGH THAT FUNCTION HONOURS IT.

### C-241 — A PATCH THAT REWRITES ANOTHER PATCH'S OUTPUT TAKES ITS MARKER WITH IT

<sub>Cut from `CLAUDE.md`, lines 6951–6981 of the
2026-09-05 revision.</sub>

- **A PATCH THAT REWRITES ANOTHER PATCH'S OUTPUT TAKES ITS MARKER WITH
  IT.** (2026-09-04, found by the suite rather than by reading.)
  `vendor_weavingspace.py` decides whether a patch is already in a file
  by looking for its own `new` text, which doubles as the marker. Patch
  6 anchors on the block patch 3 produces and renames the frame it
  binds; patch 5b rewrites the tail of the method patch 4b produces. So
  on the tool's own fixed-point check -- our vendor fed back as its
  upstream, where every patch must report "already present" -- both
  earlier patches reported ANCHOR NOT FOUND, which is the sentence
  reserved for an anchor UPSTREAM has moved and the one message a
  re-vendorer has to be able to trust. A re-vendor from pristine
  upstream was never affected, and that is exactly why nothing else
  could see it: measured at the commit before patch 4 the tool is its
  own fixed point, 5 patches and 0 needing attention, and at HEAD it
  exited 1.
  THE MARKER IS THE SMALLER PIECE THE LATER PATCH LEAVES STANDING, named
  beside the patch that made it necessary, and it is kept honest by two
  assertions rather than by a list: it must be text this patch writes,
  and it must NOT be text the anchor already carries -- without the
  second, the patch reads as already present against pristine upstream
  and silently never applies. Both refusals were watched firing.
  AND THE FIRST REPORT WORDING CLAIMED A HISTORY IT COULD NOT KNOW:
  "already present (in the form patch 6 leaves)" fires just as well on a
  tree where patch 6 has not run, because the mark is in both forms.
  Say which QUESTION was asked, not which past is assumed -- a report is
  read by somebody who has no other way to tell that the narrower check
  was the one that ran.
  THE GENERAL FORM: when one transformation's output is another's input,
  the earlier one's "have I already done this" test is about text the
  later one owns. Ask of any idempotence check whether anything
  downstream is entitled to rewrite the thing it looks for.

### C-242 — A RATE QUOTED FROM TOO FEW DRAWS IS NOT A MEASUREMENT, AND I PUBLISHED TWO

<sub>Cut from `CLAUDE.md`, lines 6983–7005 of the
2026-09-05 revision.</sub>

- **A RATE QUOTED FROM TOO FEW DRAWS IS NOT A MEASUREMENT, AND I
  PUBLISHED TWO.** (2026-09-04, chasing the topology matrix's one
  failing cell.) The cell reproduced on the second of two attempts, and
  I reported it as DETERMINISTIC; the next run of the same probe
  answered in 1.43s both times. Then a two-arm comparison came back 2
  of 8 at HEAD against 0 of 8 at the commit before this session's
  tiling patches, which reads exactly like a verdict on those patches
  -- and HEAD then produced 0 of 16 on its own, which disposes of it.
  Four failures in eighty-six attempts, clustered in one twenty-minute
  window: 16 attempts at that rate expect less than one, so the control
  arm was never able to say anything.
  AND THE RUN STAGED TO SETTLE IT WAS VOID FOR A SEPARATE REASON worth
  keeping: one arm met a load average of 13 and the other 250, because
  the load I staged was not the only load on the machine. A comparison
  whose CONDITIONS are not reported beside its numbers is not one
  anybody can check, and this file already says the machine is part of
  the measurement.
  THE HABIT: before reporting a rate, ask how many draws would be
  needed to tell it from zero, and print the conditions of every arm
  beside its verdict. An intermittent defect's ARMS are the last thing
  to trust and its MECHANISM the first -- what actually settled this
  was one reading at the moment of failure, the task `Queued` with the
  thread pool idle, which no amount of rate-chasing would have given.

### C-243 — A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT

<sub>Cut from `CLAUDE.md`, lines 7007–7024 of the
2026-09-05 revision.</sub>

- **A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT.**
  (Same day, and it is the other half of the entry above.) The stall's
  CAUSE is undiagnosed -- QGIS accepts a topology build, leaves it
  `Queued`, and never starts it -- and the state it leaves was measured
  exactly: a task the dialog believes is in flight, reading Queued,
  with `active=0` on the pool. That state is stageable even though the
  condition is not, because a QgsTask never handed to the manager IS
  it, deterministically. So the guard was measured before it was
  written and its test closes the window rather than counting how often
  it opens.
  WHAT KEEPS SUCH A GUARD HONEST is scope and wording. It asks about
  STARTING, never about duration, so nothing slow can reach it; it
  SAYS rather than cancels, so a pool busy with somebody else's work
  gets a sentence that is still true; and the sentence goes where a
  reason belongs. THE OPPOSITE ANSWER IS GUARDED SEPARATELY, because a
  rule with two answers is taken for one by whoever meets the first --
  a build under way must NOT be reported as never started, or the tab
  tells somebody their healthy nineteen-second design was abandoned.

### C-244 — CLEARING A PREVIEW AT THE DROP PUTS THE OLD PICTURE BACK FOR THE WHOLE OF AN...

<sub>Cut from `CLAUDE.md`, lines 7026–7048 of the
2026-09-05 revision.</sub>

- **CLEARING A PREVIEW AT THE DROP PUTS THE OLD PICTURE BACK FOR THE
  WHOLE OF AN ASYNCHRONOUS REBUILD.** (2026-09-04, a field report
  against 0.24.4rc15 confirmed and repaired.) `_commit_the_drag` opened
  by clearing the drag preview, which reads as tidy -- the gesture is
  over, so put the transient thing away -- and the answer that replaces
  it arrives SECONDS LATER off another thread. In between the view
  falls back to the un-edited design: 1.676s on the default design,
  with the settled drawing identical to the preview that had just been
  discarded, and nineteen seconds on `hex-colouring 7`. The user's
  words were "it reverts for a second and then a few seconds later
  updates correctly", which is exactly what it does.
  THE RULE: a transient picture is cleared by the thing that REPLACES
  it, not by the act that requested the replacement. Ask of any
  "cleanup" at the end of a gesture what will be on screen between it
  and the answer, and how long that is.
  AND THE DISCARD PATHS ARE NOT THE SAME PATH. Where nothing was
  recorded there IS no answer coming, so the transient thing must go at
  once or it describes something no record holds -- which made this a
  decision per exit rather than one line moved, and the exits are
  journeys rather than lines: an entry aimed at the no-travel exit
  SURVIVED because the test's discard arm was a click, which leaves at
  the first exit and never reaches it. A SURVIVOR NAMED THE ARM THAT
  WAS MISSING, which is what a survivor is for.

### C-245 — A change of region dataset: what enforcing the seven rulings cost

<sub>Cut from `CLAUDE.md`, lines 1640–1685 of the 2026-09-05 revision.</sub>

  A LANDING NEVER WRITES OVER A MAP MADE FROM ANOTHER DATASET, and
  that is ruling 2 finishing the job it started. Making a second
  output group the ordinary result of a demo left ADOPTION's older
  assumption wrong -- it takes the newest group and runs at
  construction, before the user has chosen anything -- so reopening a
  project holding two datasets' maps and generating on the first
  DELETED the second. Every output layer carries
  `weavingspace_region` now (the region's source, which survives a
  reopen where a layer id does not), and the landing refuses a group
  whose stamps name another dataset. Output made before the stamp
  carries none and keeps the older rules. When a ruling starts
  producing a SECOND artefact by default, re-drive every path that
  assumed one.
  AND THE CHOOSER IS NOT THE ONLY DOOR. Two hunts of 2026-08-25
  found the same defect from different directions: REMOVING the region
  layer and picking another skipped every protection, so Generate
  overwrote the previous dataset's GeoPackage unasked. `switched`
  asked about the WATCHED LAYER OBJECT, which a removal nulls; and
  the layer COUNT decided which of two routes ran, so the same act
  answered differently in a project with two polygon layers and one
  with three. It asks about the DATASET IN FORCE now
  (`_memory_layer_id`), and the bank swap RETURNS on an empty chooser
  rather than banking and forgetting -- the second fault, which hid
  the first. When a rule is about "the thing in force", ask what NULLS
  the record you are reading, and whether the answer is a user's act
  or somebody else's cleanup.
  WHAT COUNTS AS "A CHANGE OF DATASET" WAS DRAWN BY THE FULL SUITE on
  the rulings' first whole run, which failed three tests the targeted
  runs had all passed: leaving a dataset THIS SESSION HAS BUILT FROM.
  One clause, and it covers all three failures. A recovery is not a
  switch -- reopening a project whose region file moved and pointing
  at live data re-finds the same work -- because a reopened session
  has not landed anything yet. A combo AUTO-LANDING in a busy project
  is not a dataset the user chose, for the same reason. And a
  pre-generate fiddle is a first choice: nothing is built, so there
  is nothing to protect. A SECOND CLAUSE WAS TRIED AND DELETED:
  liveness of the outgoing layer, whose catalogue entry could only
  survive, since every measured journey is decided by the landing
  alone -- and in the one it would change, land a run then lose the
  source then pick new data, protecting the landed result is what the
  rulings ask anyway. `switched_from_work` in `_on_layer_changed` is
  the one place the boundary lives; the retained-scheme question
  deliberately stays on the plain switch, because it is about what
  the TABLE carries rather than about protecting output.

### C-246 — The three scopes answering one act, and the A-B-A probe behind the group rulings

<sub>Cut from `CLAUDE.md`, lines 1661–1672 of the 2026-09-05 revision.</sub>

  WHAT THE REPORT FOUND, and the probe confirmed on this branch: the
  design travels a change of dataset intact, the value-laden records
  are banked per dataset, and the output group is remembered nowhere
  -- three scopes answering ONE act in three ways, none of them named
  anywhere on screen. A-B-A leaves THREE groups, the first and third
  stamped for the same dataset, so one dataset already owns two maps
  with nothing to tell them apart. Returning to a dataset gives its
  colours and pins back and somebody else's design. The colleague's
  diagnosis is the sentence to keep: inferring all of this "is OK as
  far as it goes, but it's too hard to be reliable and not produce
  weird seeming behaviour relatively often".

### C-247 — The two alternatives refused when the output group became the unit of work

<sub>Cut from `CLAUDE.md`, lines 1725–1739 of the 2026-09-05 revision.</sub>

  WHAT WAS REJECTED, recorded so nobody re-litigates it silently. The
  colleague offered a genuine alternative -- REWIND TO ONE SHOT: work
  on the current dataset, save it as now so it can be reloaded but not
  resumed, and forget everything on an unsaved switch. It had the
  strongest single argument in the room, that nine of the eleven
  defects of 2026-08-25 were in exactly the machinery it deletes. It
  was not taken because it costs the one behaviour the colleague
  himself singled out as working (symbology coming back on a return)
  and makes the several-datasets demo worse rather than better, which
  is the session the whole report came from. THE MIDDLE OPTION was
  also refused: keep inferring and mend the asymmetries by putting the
  design in the per-dataset bank. It is much the cheapest, and it
  fails on its own terms -- A-B-A would then move the design under the
  user TWICE, where a design you SELECT never moves on its own.

### C-248 — What converting fifty-eight Save presses cost, and the four defects it found

<sub>Cut from `CLAUDE.md`, lines 1797–1817 of the 2026-09-05 revision.</sub>

  WHAT EACH CARRIES, because a ruling written down reads exactly like
  a ruling implemented. Rulings 3, 4 and 5 -- the output path, the
  ramp memory and the seeding order -- each have a registered test and
  catalogue entries proved `caught`, with ONE exception measured to a
  close at the entry itself: the restyle half of ruling 5 is HELD
  REDUNDANTLY rather than unproved, by a class source stamped on the
  donor's content and by the reseeded term behind it. Rulings 1 and
  2 -- saving as a positive act, and the untick that drops the
  source -- carry twenty proved entries between them and a matrix of
  eleven routes to a press.
  WHAT THE CONVERSION COST AND FOUND, kept because it is the argument
  for doing it that way again. Fifty-eight Save presses went in by
  script where the old code's write used to happen; twenty-four tests
  were converted BY HAND because what they assert changed rather than
  moved; four tests were written that did not exist. It found FOUR
  REAL DEFECTS, three on ordinary journeys -- a run claiming a save it
  never made, a Save during the first run telling somebody to press
  Generate, a region chooser excluding a newly loaded layer for being
  allocated where a destroyed one had been, and a map opened with Load
  being DESTROYED by being saved. Ledger rows 27 to 30.

### C-249 — The three grounds for _may_overwrite asking about the dataset rather than the group

<sub>Cut from `CLAUDE.md`, lines 1813–1826 of the 2026-09-05 revision.</sub>

  AND `_may_overwrite` ASKS ABOUT THE DATASET, NOT THE GROUP, which
  leaves one case silent: a SECOND map of the SAME dataset, saved
  onto the first map's file, replaces it without a question. Three
  things decide that -- the file's record carries `region` and
  `output_path` and no group identity at all, so the question is not
  available to ask; the ruling's own boundary is "a file the plugin
  did not write", and that is a file the plugin wrote from that data;
  and the chooser is a save-mode dialogue, so the platform has
  already asked about replacing an existing file. The method's own
  docstring claimed the group until this was noticed, which is this
  file's "a gate that checks half of what it names" met again, from
  the documentation side. If the group should be the unit, the record
  needs a group identity first.

### C-250 — Numbers stored as text: the measurement, the cache, and the fixture blind spot

<sub>Cut from `CLAUDE.md`, lines 1904–1946 of the 2026-09-05 revision.</sub>

  MEASURED ON QGIS 4.0.3, that is true of WORDS and false of NUMERIC
  STRINGS: a String column running "10" to "120" classifies exactly as
  its integer twin -- five ranges, the same bounds, twelve of twelve
  features symbolised. The rule was true of the example that prompted
  it and wider than its evidence, and it cost a choropleth to anybody
  whose numbers arrived through a CSV join or a GeoJSON: at three
  thousand areas, three thousand and one categories.
  `_field_is_numeric` IS THE ONE OWNER and answers the wider question
  now, so all eight readers move together -- which is what stops the
  row and the assignment disagreeing. A column declared numeric
  answers True as it always did; a column declared text answers True
  where every one of its values parses.
  STRICT, AND THAT IS THE HALF THAT KEEPS IT SAFE. "Mostly numbers" is
  a column with something else in it, and a graduated renderer drops
  those rows in silence -- the very failure the old rule was written
  about, arriving through the door opened to relax it. Both answers
  are asserted in one test, because a reader meeting either alone
  would take it for the whole rule.
  AND THERE IS A SECOND HALF, FOUND BY THE FIRST FULL SUITE AFTER THIS
  WAS BUILT: no two distinct TEXTS may collapse onto one number.
  Python reads `float(" 3")` as 3.0, so a column holding "3", " 3" and
  "3 " -- three values a legend shows as three classes, and which
  `test_awkward_attribute_values_keep_their_meaning` exists to keep
  apart, since "tidying is a silent edit of somebody's data" -- passed
  the parse test and was then drawn as ONE. The ruling was made so a
  quoted CSV column could be classed as numbers; it was never made to
  merge values a reader can tell apart. So the question is not "does
  every value parse" but "does every value parse to a number of its
  OWN", which also refuses "3" beside "3.0" without needing a rule of
  its own.
  NO TARGETED RUN COULD HAVE FOUND IT, and that is the transferable
  part: every fixture written FOR the ruling held clean numbers,
  because that is what the ruling is about. The case that broke it
  lived in a test about hostile data that nobody would have thought to
  run. A green subset is not a green suite, and this is that rule
  arriving from the direction of a NEW FEATURE rather than a
  regression.
  AND IT IS CACHED, keyed by layer, column, fingerprint and data
  version exactly as `_classification_values` is. `_field_is_numeric`
  is asked once per field for the variable lists and once per element
  inside `_assignments`, which every keystroke reaches, so an
  unguarded scan would rebuild the cache-of-one defect of 2026-08-19.

### C-251 — What the doubled alphabet was measured at before it moved

<sub>Cut from `CLAUDE.md`, lines 1961–1977 of the 2026-09-05 revision.</sub>

  MEASURED BEFORE IT MOVED: all four formula families build a unit
  with exactly n DISTINCT ids at 27, 52, 53, 100, 196 and 256, at
  0.01-0.05s each. The catalogue went from 247 entries to 1,168 and
  the sweep that builds every one of them still passes.
  AND `"aa" < "z"`, WHICH IS THE HALF A DOUBLED ALPHABET BREAKS
  QUIETLY. Python compares strings character by character, so the
  twenty-seventh element sorted SECOND -- second in the assignment
  table, in the layers panel, in the design view's labels, in the
  legibility check's pairs, and second again in a resumed panel, where
  table names carry the same fault. Nothing was lost; a user simply
  could not find their twenty-seventh variable.
  `bridge.element_order` is the one owner of that question and every
  site reads it. `tools/probes/element_order_through_a_roundtrip.py`
  prints the three orders -- the dock, the file, and the dock after a
  resume -- because they are three different questions, and the file's
  own listing is right only by the accident of creation order.

### C-252 — The chooser and the panel answering one fact two ways, and the six splitters

<sub>Cut from `CLAUDE.md`, lines 1984–2001 of the 2026-09-05 revision.</sub>

  ONE FACT, TWO PLACES, AND ONLY ONE OF THEM ANSWERED. The chooser
  composed its label as `<group name> — <dataset>`; the panel had the
  counter. So the name now carries the dataset and the chooser
  appends it only where the name does not already have it -- a group
  somebody renamed, or output made before this ruling, for which the
  chooser is the only place the dataset appears.
  THE NAME IS STILL A LABEL AND NEVER AN IDENTITY. The lookup asks
  the layers; renaming stays the user's business and is never undone.
  And the dataset is taken from THE LAYER THIS RUN TILED where the
  caller knows it, falling back to the chooser only where it does
  not, which is the rule the region stamp already follows for the
  same reason.
  ITS COST WAS IN THE SUITE, and worth knowing: six call sites
  recovered a group's name from a chooser label by splitting on the
  separator, which was right until the separator moved inside the
  name. They route through one helper now. When you change how a
  label is composed, grep for whoever DECOMPOSES it.

### C-253 — The two registered tests that collided over a kept scheme

<sub>Cut from `CLAUDE.md`, lines 2005–2014 of the 2026-09-05 revision.</sub>

  IT SETTLED A COLLISION BETWEEN TWO REGISTERED TESTS, which is why it
  is a ruling and not a fix. One required the element to own those
  colours ("a missing file is a reason to stop consulting the file,
  not a reason to repaint somebody's map"); the other, written the day
  before, required the record to stay empty, because colours that
  outrank a template make restoring an edited scheme change nothing.
  Both harms were real and measured. WHEN TWO SETTLED RULES GIVE ONE
  ACT TWO ANSWERS, THE ANSWER IS USUALLY BOTH -- with the thing that
  tells them apart written down.

### C-254 — The four regressions round nine shipped, and the leg that found them

<sub>Cut from `CLAUDE.md`, lines 2028–2036 of the 2026-09-05 revision.</sub>

What found them was the mutation workflow's coverage leg,
  which runs the WHOLE suite: green at `6d6ea2d`, red at `64cb0fa`,
  four named tests, all four reproduced here on the first attempt.
  The rule already written is that a change to a core path is verified
  by the whole suite and that the candidate is where that happens.
  What this adds is the failure mode when the rule is skipped: the
  four survived a hunt round aimed at exactly that code, because a
  hunt asks what MIGHT be broken and the suite asks what IS.

### C-255 — Why a modal refusal is the quietest exit, and harness fault eleven

<sub>Cut from `CLAUDE.md`, lines 2064–2070 of the 2026-09-05 revision.</sub>

  THE MODAL IS THE PART TO REMEMBER: that guard refuses through a
  QMessageBox, which in a headless suite lands in the shim's MODALS
  and never reaches the message bar -- so a run refused there is
  indistinguishable from a run that was never launched. The ledger
  already carried this as harness fault eleven; it recurs because
  the two stores are read by different code. Read both.

### C-256 — Windows running install-and-load alone, and the instruction that ended it

<sub>Cut from `CLAUDE.md`, lines 396–407 of the 2026-09-05 revision.</sub>

  Windows is where most of this plugin's users are, and until
  2026-08-15 it ran nothing but an install-and-load. (Maintainer's
  instruction that day: Windows and Linux should test as much as
  macOS does, within only the limits GitHub imposes that we cannot
  code around; restated that night, once a macOS runner existed, as
  every platform staying as close to the local suite as practical.)
  THE MACOS LEG EARNED ITS PLACE ON ITS FIRST COMPLETE RUN: it is the
  only leg that runs the package a macOS user installs, in a profile
  nobody has seeded, and it found three faults this machine cannot show
  -- all three masked here by a style library the plugin seeded years
  ago. C-5.

### C-257 — The macos job missing from the check's own list, and the sixteen-day false sentence

<sub>Cut from `CLAUDE.md`, lines 422–430 of the 2026-09-05 revision.</sub>

  still running a command this check can SEE. `macos` was missing
  from that last list on the day the job was added, so the newest
  platform was the one that could go quiet without failing anything;
  corrected 2026-08-15 and proved by hushing it in a throwaway copy.
  Nothing there is a hand-kept list, so the two cannot drift apart
  quietly -- a sentence that was FALSE for sixteen days, because
  `EXPECTED_STAGES` in release.py was exactly that. Both widenings, and
  the instruments audit that found the second: C-6.

### C-258 — The eighteen red pushes across six hours, and why every local gate was green

<sub>Cut from `CLAUDE.md`, lines 474–482 of the 2026-09-05 revision.</sub>

  The specific trap here is worth naming, because it will recur: the
  local checks all passed the whole time. `check_standards` and
  `check_no_secrets` are green on a tree whose text-review queue is
  full, because approving prose is the USER'S act and no local gate
  may do it. A gate only a person can satisfy is exactly the one that
  goes unsatisfied for six hours. So the local habit is now ONE
  command, and it reads its own contents out of `ci.yml`:

### C-259 — How release_notes.entry_for collapsed the categorized changelog shape

<sub>Cut from `CLAUDE.md`, lines 702–711 of the 2026-09-05 revision.</sub>

  displays the metadata text as it stands, and by the GitHub release
  page, which renders MARKDOWN -- where single newlines fold into one
  paragraph. The categorized shape settled on 2026-08-13 therefore
  worked in the plugin manager and arrived on the release page as a
  wall of prose, because `release_notes.entry_for` collapsed the
  entry with `" ".join(...)` before GitHub ever saw it. Found and
  fixed 2026-08-14; the entry is now emitted as an opening paragraph
  plus one bullet per category, and `test_the_release_notes_keep_
  their_categories` holds the line.

### C-260 — The guard that walks every version header, and the entry it stands on

<sub>Cut from `CLAUDE.md`, lines 719–730 of the 2026-09-05 revision.</sub>

  ITS OWN TEST COULD NOT SEE IT, and that is the transferable half:
  the test reads the CURRENT version's entry and requires a paragraph
  then bold bullets, which TWO ENTRIES JOINED END TO END satisfy
  exactly. A shape assertion cannot tell one record from two. Where a
  tool cuts one record out of a document holding several, assert the
  CUT -- that the piece stops where the next begins and carries none
  of its neighbour's furniture -- and not merely that the piece is
  shaped like a piece. The guard walks every version header in the
  field now, and the catalogue entry
  `an-entry-stops-where-the-next-version-starts` stands on the
  boundary itself.

### C-261 — The six boundaries icon mode was driven across, and how each was read

<sub>Cut from `CLAUDE.md`, lines 1078–1088 of the 2026-09-05 revision.</sub>

  ICON MODE WAS ON THAT LIST AND IS NOT OPEN, corrected 2026-08-27.
  Ruling 4 of 2026-08-25 puts icon mode in the working state a group
  restores, the restore whitelist carries it, and a hunt drove six
  boundaries -- group switch and return, project save and reopen,
  GeoPackage resume, dataset switch, off-and-re-generate -- reading
  the node property with plain json, the file with bare GDAL and the
  .qgz out of its own zip. All agreed. A binding file that lists a
  settled question as open is read as current and invites somebody to
  implement forgetting, which is why the clause is struck rather than
  left as harmless untidiness.

### C-262 — The 48-design spread behind multi-class selection, and cairo measured against laves

<sub>Cut from `CLAUDE.md`, lines 3483–3500 of the 2026-09-05 revision.</sub>

  MULTI-CLASS SELECTORS: CLICK TO SELECT, A LIST TO CONFIRM, each
  following the other with the blocked-signal discipline the pin
  controls already carry. What decided the shape was how much there is
  to select: across a 48-design spread most designs carry ONE OR TWO
  transitivity classes of each kind, and where there are two the
  chooser's per-class entries plus "every vertex" and "every edge"
  already cover all three subsets, so the feature only bites on the
  eight of 48 with three or more -- `hex-slice 5` at 5 vertex and 7
  edge classes being the richest. The record needs nothing: an edit's
  `classes` is already a STRING selector and the library matches
  `label in selector`.
  CAIRO IS A RENAME, NOT A FAMILY. Measured through `catalog.make_unit`,
  `tiling_type="cairo"` and the catalogue's own `laves 3.3.4.3.4` draw
  the SAME GROUND -- four tiles, ids a-d, identical areas and bounds,
  symmetric difference 0.000 -- so one entry reads `laves 3.3.4.3.4
  (cairo)` and the well-known Archimedean and Laves names come with
  it, through `text_review` like any other prose.

