# Can a reader tell the elements apart? Findings, method, and what to do

Working notes, deliberately outside the repository. Nothing here has
been acted on; the decisions are open.

## Why this question is the whole product

A tiled multivariate map asks a reader to do something an ordinary
choropleth does not: separate several interleaved element shapes and
read each one's colour as a separate variable. If two elements' fills
are indistinguishable in some part of the map, the reader cannot do
that there — and, worse, cannot tell that they cannot. The map looks
finished. It just silently carries fewer variables than it claims.

So "are the element colours far enough apart" is not a polish
question. It is the cartographic claim of the technique, and it is
measurable.

## What was measured

`tools/perceptual_check.py` (in the repo) takes rendered maps, samples
interior pixels — not edges, which are antialiasing rather than
symbology — clusters them into the fill colours actually present
weighted by how much of the map each covers, and reports the minimum
pairwise CIELAB ΔE between those fills. It does this three times:
normal vision, deuteranopia, protanopia. The dichromacy simulation is
the Viénot, Brettel & Mollon (1999) single-plane LMS method applied to
linear RGB.

It reuses `srgb_to_lab` and the sampling from `tests/visual_tests.py`
rather than copying them, so the two cannot drift apart.

Threshold used: ΔE 10. That is a convention, not a law — roughly "a
reader can tell these apart at a glance without comparing them side by
side". Below about 3, colours are nearly indistinguishable even when
adjacent.

## The findings, on the v0.22.0 gallery

**Eleven of twelve renders have at least one pair of element fills
closer than ΔE 10.** The single pass is
`hex-colouring_7_shared_ramp.png`, at ΔE 21.8 normal / 18.4
deuteranopic / 22.1 protanopic — the shared-ramp design, which is what
the paper argues for. That is a striking result on its own: the
design the article recommends is the one that survives measurement.

Two separate causes, wanting different responses.

### 1. The pale ends collide, under normal vision

Sequential ramps all start at essentially white:

| ramp | first class |
|---|---|
| Reds | #fff5f0 |
| Blues | #f7fbff |
| Greens | #f7fcf5 |
| Purples | #fcfbfd |

Blues' and Purples' lowest classes sit **ΔE 2.0 apart before any
simulation**, dropping to 1.3 under protanopia. The diverging ramps do
the same thing at their midpoints: RdBu, PiYG and PuOr land within
ΔE 1.4 of each other (#f3eeea / #f5f3ef / #f2f0ee).

The consequence is specific and worth stating plainly: **wherever
several variables are jointly low — or jointly middling, for diverging
ramps — the map shows one colour rather than four.** The reader sees a
pale patch and cannot recover which elements are there. In deprivation
data, "jointly low on every index" is not a random subset of the map;
it is a meaningful region, and it is precisely the region that becomes
unreadable.

This has nothing to do with colour vision. It is a consequence of
assigning several sequential ramps that share a white endpoint.

### 2. Cross-element pairs collapse under CVD

Pairs comfortably separated for a normal-vision reader that close up
under simulation:

| pair | ramps | normal | deuter. | protan. |
|---|---|---|---|---|
| #fa694c / #228b45 | Reds 3 / Greens 4 | 100.7 | — | **4.7** |
| #9e9bc9 / #6daed6 | Purples 3 / Blues 3 | 21.2 | 6.3 | **4.8** |
| #cb1b1e / #00441b | Reds 4 / Greens 5 | 100.1 | — | **7.2** |
| #2171b4 / #6a51a3 | Blues 4 / Purples 4 | 29.3 | **6.2** | — |
| #e896c4 / #6bacd0 | PiYG / RdBu | 50.3 | — | **4.3** |
| #f88d52 / #9bcf63 | Spectral / PiYG | 71.0 | **8.5** | — |
| #17becf / #9e9bc9 | tab10 cyan / Purples 3 | 43.7 | **2.7** | — |
| #1f77b4 / #6a51a3 | tab10 blue / Purples 4 | 33.4 | **5.8** | — |
| #228b45 / #8c564b | Greens 4 / tab10 brown | 68.1 | **9.9** | — |
| #cb1b1e / #d64903 | Reds 4 / Oranges 4 | 20.1 | **8.6** | — |

Reds against Greens is the sharpest illustration: ΔE 100.7 for a
normal-vision reader, 4.7 for a protanope. Blues against Purples is
the most widespread, since those two appear together in almost every
default assignment, and it fails under both deficiencies.

The categorical maps are the worst case (tab10 cyan against Purples'
middle class, ΔE 2.7 deuteranopic), and categorical data is exactly
where a reader has no ordering to fall back on: if the colours cannot
be separated, the class cannot be recovered at all.

## Calibration decisions, and why they matter

Two thresholds inside the tool were forced by the data, and both cut
towards reporting MORE failures rather than fewer:

**Near-white filtering had to be tightened to essentially #ffffff.** A
roomier filter dropped Purples' palest class (#fcfbfd) as
"background" — but that is a real element colour, and the one most at
risk of colliding. Excluding it would have hidden the finding.

**Clustering tolerance had to come down to ΔE 1.** At a tolerance of
3, the closest pairs were being merged into a single swatch before
measurement, so the very worst results were silently absorbed.
Anything merged can never be reported as a failing pair.

Both are worth remembering if the numbers are ever re-derived: a
generous filter and a generous clustering tolerance would produce a
much rosier and completely misleading report.

## Options, none taken

**Clip the pale end of sequential ramps when they are assigned to
elements.** Starting each ramp at roughly 15% rather than 0% is
ordinary practice for multivariate work and would fix the
normal-vision half outright, at the cost of a slightly narrower
lightness range per variable. This is the change I would argue for
first: it addresses the cause rather than warning about the symptom.

**Check the assigned SET at assignment time, in the dialog.** The
plugin knows every element's ramp before it renders anything; it could
compute the same minimum ΔE across the assigned ramps and say so while
the user is still choosing, rather than after the map exists. Cheap,
since it works on the ramp definitions rather than on pixels.

**Prefer a shared ramp for many elements.** Already what the article
recommends, and the only gallery case that passes. Could be the
default for element counts above some number.

**Reserve one axis that survives dichromacy.** Blue–yellow contrast
survives both deuteranopia and protanopia; red–green does not. A
default palette set built on that axis would fail less often, though
it constrains the aesthetic considerably.

**Gate the release on the checker.** One line in `release.py`. Would
currently fail, which is the point, but it should not be turned on
until the defaults are changed or the threshold is deliberately set
where the current maps sit.

## Caveats

ΔE 10 is a convention. The dichromacy simulation is a model of an
average dichromat, not a prediction about any individual. Interior
sampling ignores what happens at tile boundaries, where adjacency
effects and simultaneous contrast do real perceptual work that CIELAB
distance does not capture. And a map is read with a legend, at a
particular size, on a particular medium — none of which the number
knows about.

None of that undermines the finding. Two colours at ΔE 2.0 are not
separable under any of those conditions.
