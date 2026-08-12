# Large plain weaves: a reproducible difference, and a retraction

Written 2026-08-10 for the weavingspace maintainers.
**This supersedes the note sent earlier today.**

## Retraction first

The earlier note suspected commit **c0f109c** of having fixed the
problem. **That was wrong, and nothing about it implicates your
commit.** Please disregard that part.

The mistake was ours and worth stating so you can weigh the rest:
our differential sweep seeds its random draw per run, and the
"confirming" re-run used a different seed from the failing one. Cases
are numbered per run, so what looked like "case 259 now passes" was a
different design entirely. We compared two things that only looked
comparable.

## What is actually established

Re-run on **c0f109c** with a different seed: the same failure, same
family. Across two independent seeds:

- seed 20260810, 5,000 designs: **12 divergences**
- seed 20260808, 1,700 designs: **4 divergences**

Every one of the sixteen is a **plain weave whose strand groups are
six letters long**, i.e. 11 or 12 elements:

    plain weave abcdef-|ghijk-      (11 elements)
    plain weave abcdef|ghijk        (11)
    plain weave abcdef|ghijk-       (11)
    plain weave abcdef-|ghijkl      (12)
    plain weave abcdef-|ghijkl-     (12)
    plain weave abcdef|ghijkl       (12)

at spacings 650 and 800, aspect 0.75, `n = 1`. Nothing else in 6,700
designs diverged: no tiling of any family or element count, no twill,
no basket, and no plain weave with fewer strands. The differences are
large -- 19,000 to 27,000 of about 51,000 sampled interior pixels --
so this is not tolerance or antialiasing.

## What we have ruled out, by measurement

- **The unit itself is identical.** Building the unit through our
  plugin and through a direct `WeaveUnit(...)` call gives the same
  tile count, the same total area and the same element ids, at two
  aspects. Whatever differs happens AFTER the unit exists.
- `n="1"` (string) and `n=1` (int) give identical units.
- Our own UI is not at fault: family selection, every per-element
  variable and every colour ramp choice land as asked at 11 and 12
  elements, and the comparison now asserts that any refused control
  fails loudly rather than silently.
- It is not the vendor bump: it reproduces on 2fb5a87 and c0f109c
  alike.

## Where that leaves it

The difference must arise in the **tiling step or later**. The two
paths reach it differently: our plugin builds a unit and tiles it
over a real region with `Tiling`, while the reference applies
`transform_rotate` / `transform_scale` / `transform_skew` /
`inset_tiles` to the unit and then tiles. If fragment merging for
weaves whose elements connect diagonally depends on how the unit was
reached, that would fit the evidence -- but we have not demonstrated
it, and after today's error we would rather show you the diff than
speculate again.

Our next step is to render one failing design through both paths and
compare the tiled output element by element. We will send what that
shows, whether or not it implicates the library.

## Questions, if any of this rings a bell

1. Is there a known sensitivity in many-strand plain weaves -- six
   letters per group is where it starts for us -- around fragment
   merging or prototile regularisation?
2. Would a reproduction script calling only weavingspace (no QGIS) be
   useful to you? We can almost certainly reduce it to one.

No action needed until we send the element-by-element diff.
