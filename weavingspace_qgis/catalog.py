"""Catalogue of tiling and weave families.

The TILINGS_BY_N literal is ported verbatim from the mapweaver web app
(https://dosull.github.io/mapweaver/app/, app.py
setup_tilings_dictionary cell); the loop after it adds the two
sanctioned library extras (stripes, grid) that the app does not carry,
and the block after THAT carries every family on to the element counts
the app's hand-written dictionary happened to stop at. When syncing
against a new app release, update the literal only and leave both
extension blocks alone.

Each entry maps a display name to the constructor spec for a
weavingspace TileUnit or WeaveUnit. Keys of TILINGS_BY_N are the number
of distinct tile ids (mappable variables) the unit provides.
"""

TILINGS_BY_N = {
  2: {
    "plain weave a|b": dict(type="weave", weave_type="plain", strands="a|b", n="1"),
    "twill weave a|b": dict(type="weave", weave_type="twill", strands="a|b", n="2"),
    "twill weave a|b-": dict(type="weave", weave_type="twill", strands="a|b-", n="2"),
    "twill weave a|b 3": dict(type="weave", weave_type="twill", strands="a|b", n="3"),
    "twill weave a|b- 3": dict(type="weave", weave_type="twill", strands="a|b-", n="3"),
    "twill weave a|b 4": dict(type="weave", weave_type="twill", strands="a|b", n="4"),
    "twill weave a|b 1,2": dict(type="weave", weave_type="twill", strands="a|b", n="1,2"),
    "twill weave a|b- 1,2": dict(type="weave", weave_type="twill", strands="a|b-", n="1,2"),
    "twill weave a|b 1,2,2,1": dict(type="weave", weave_type="twill", strands="a|b", n="1,2,2,1"),
    "twill weave a|b 2,3": dict(type="weave", weave_type="twill", strands="a|b", n="2,3"),
    "twill weave a|b 2,3,3,2": dict(type="weave", weave_type="twill", strands="a|b", n="2,3,3,2"),
    "archimedean 4.8.8": dict(type="tiling", tiling_type="archi", code="4.8.8"),
    "square-slice 2": dict(type="tiling", tiling_type="square-slice", n=2, offset=0),
    "crosses 2": dict(type="tiling", tiling_type="cross", n=2),
    "star1 44": dict(type="tiling", tiling_type="star1", code="44", point_angle=30),
    "hex-colouring 2": dict(type="tiling", tiling_type="hex-col", n=2),
    "square-colouring 2": dict(type="tiling", tiling_type="square-col", n=2),
    "hex-slice 2": dict(type="tiling", tiling_type="hex-slice", n=2, offset=0),
    "laves 3.3.3.4.4": dict(type="tiling", tiling_type="lave", code="3.3.3.4.4"),
  },
  3: {
    "cube weave a--|b--|c--": dict(type="weave", weave_type="cube", strands="a--|b--|c--"),
    "plain weave ab|c": dict(type="weave", weave_type="plain", strands="ab|c", n="1"),
    "plain weave ab-|c": dict(type="weave", weave_type="plain", strands="ab-|c", n="1"),
    "twill weave ab|c-": dict(type="weave", weave_type="twill", strands="ab|c-", n="2"),
    "basket weave ab|c-": dict(type="weave", weave_type="basket", strands="ab|c-", n="2"),
    "hex-slice 3": dict(type="tiling", tiling_type="hex-slice", n=3, offset=0),
    "hex-colouring 3": dict(type="tiling", tiling_type="hex-col", n=3),
    "crosses 3": dict(type="tiling", tiling_type="cross", n=3),
    "square-colouring 3": dict(type="tiling", tiling_type="square-col", n=3),
    "archimedean 3.6.3.6": dict(type="tiling", tiling_type="archi", code="3.6.3.6"),
    "archimedean 3.12.12": dict(type="tiling", tiling_type="archi", code="3.12.12"),
    "square-slice 3": dict(type="tiling", tiling_type="square-slice", n=3, offset=0),
    "archimedean 3.3.3.4.4": dict(type="tiling", tiling_type="archi", code="3.3.3.4.4"),
    "star1 33": dict(type="tiling", tiling_type="star1", code="33", point_angle=30),
    "star2 66": dict(type="tiling", tiling_type="star2", code="66"),
    "star1 36": dict(type="tiling", tiling_type="star1", code="36", point_angle=30),
    "star1 63": dict(type="tiling", tiling_type="star1", code="63", point_angle=30),
  },
  4: {
    "laves 3.3.4.3.4": dict(type="tiling", tiling_type="laves", code="3.3.4.3.4"),
    "plain weave ab|cd": dict(type="weave", weave_type="plain", strands="ab|cd", n="1"),
    "plain weave ab-|cd": dict(type="weave", weave_type="plain", strands="ab-|cd", n="1"),
    "plain weave ab-|cd-": dict(type="weave", weave_type="plain", strands="ab-|cd-", n="1"),
    "basket weave ab|cd": dict(type="weave", weave_type="basket", strands="ab|cd", n="2"),
    "basket weave ab|cd 3": dict(type="weave", weave_type="basket", strands="ab|cd", n="3"),
    "twill weave ab|cd": dict(type="weave", weave_type="twill", strands="ab|cd", n="2"),
    "twill weave ab|cd 3": dict(type="weave", weave_type="twill", strands="ab|cd", n="3"),
    "twill weave ab|cd 1,2": dict(type="weave", weave_type="twill", strands="ab|cd", n="1,2"),
    "twill weave ab|cd 1,2,2,1": dict(type="weave", weave_type="twill", strands="ab|cd", n="1,2,2,1"),
    "basket weave ab-|cd": dict(type="weave", weave_type="basket", strands="ab-|cd", n="3"),
    "twill weave ab-|cd": dict(type="weave", weave_type="twill", strands="ab-|cd", n="3"),
    "basket weave ab-|cd-": dict(type="weave", weave_type="basket", strands="ab-|cd-", n="3"),
    "twill weave ab-|cd-": dict(type="weave", weave_type="twill", strands="ab-|cd-", n="3"),
    "crosses 4": dict(type="tiling", tiling_type="cross", n=4),
    "square-slice 4": dict(type="tiling", tiling_type="square-slice", n=4, offset=0),
    "square-colouring 4": dict(type="tiling", tiling_type="square-col", n=4),
    "hex-colouring 4": dict(type="tiling", tiling_type="hex-col", n=4),
    "star2 64": dict(type="tiling", tiling_type="star2", code="64"),
    "star2 464": dict(type="tiling", tiling_type="star2", code="464"),
    "star2 844": dict(type="tiling", tiling_type="star2", code="844"),
    "hex-slice 4": dict(type="tiling", tiling_type="hex-slice", n=4, offset=0),
  },
  5: {
    "square-colouring 5": dict(type="tiling", tiling_type="square-col", n=5),
    "crosses 5": dict(type="tiling", tiling_type="crosses", n=5),
    "plain weave abc|de": dict(type="weave", weave_type="plain", strands="abc|de", n="1"),
    "plain weave abc-|de": dict(type="weave", weave_type="plain", strands="abc-|de", n="1"),
    "plain weave abc-|de-": dict(type="weave", weave_type="plain", strands="abc-|de-", n="1"),
    "twill weave abc|de": dict(type="weave", weave_type="twill", strands="abc|de", n="3"),
    "twill weave abc|de-": dict(type="weave", weave_type="twill", strands="abc|de-", n="3"),
    "twill weave abc-|de-": dict(type="weave", weave_type="twill", strands="abc-|de-", n="3"),
    "basket weave abc|de": dict(type="weave", weave_type="basket", strands="abc|de", n="3"),
    "basket weave abc|de-": dict(type="weave", weave_type="basket", strands="abc|de-", n="3"),
    "basket weave abc-|de-": dict(type="weave", weave_type="basket", strands="abc-|de-", n="3"),
    "hex-colouring 5": dict(type="tiling", tiling_type="hex-col", n=5),
    "hex-slice 5": dict(type="tiling", tiling_type="hex-slice", n=5, offset=0),
    "square-slice 5": dict(type="tiling", tiling_type="square-slice", n=5, offset=0),
    "square-dissection 5": dict(type="tiling", tiling_type="square-dissect", n=5, offset=0, offset_angle=0),
  },
  6: {
    "hex-slice 6": dict(type="tiling", tiling_type="hex-slice", n=6, offset=0),
    "square-slice 6": dict(type="tiling", tiling_type="square-slice", n=6, offset=0),
    "square-colouring 6": dict(type="tiling", tiling_type="square-col", n=6),
    "laves 3.3.3.3.6": dict(type="tiling", tiling_type="lave", code="3.3.3.3.6"),
    "laves 3.12.12": dict(type="tiling", tiling_type="lave", code="3.12.12"),
    "cube weave a-b|c-d|e-f": dict(type="weave", weave_type="cube", strands="a-b|c-d|e-f"),
    "plain weave abc|def": dict(type="weave", weave_type="plain", strands="abc|def", n="1"),
    "plain weave abc-|def": dict(type="weave", weave_type="plain", strands="abc-|def", n="1"),
    "plain weave abc-|def-": dict(type="weave", weave_type="plain", strands="abc-|def-", n="1"),
    "basket weave abc|def": dict(type="weave", weave_type="basket", strands="abc|def", n="3"),
    "twill weave abc|def": dict(type="weave", weave_type="twill", strands="abc|def", n="3"),
    "basket weave abc-|def": dict(type="weave", weave_type="basket", strands="abc-|def", n="3"),
    "twill weave abc-|def": dict(type="weave", weave_type="twill", strands="abc-|def", n="3"),
    "basket weave abc-|def-": dict(type="weave", weave_type="basket", strands="abc-|def-", n="4"),
    "twill weave abc-|def-": dict(type="weave", weave_type="twill", strands="abc-|def-", n="4"),
    "archimedean 3.3.4.3.4": dict(type="tiling", tiling_type="archi", code="3.3.4.3.4"),
    "archimedean 3.4.6.4": dict(type="tiling", tiling_type="archi", code="3.4.6.4"),
    "archimedean 4.6.12": dict(type="tiling", tiling_type="archi", code="4.6.12"),
    "crosses 6": dict(type="tiling", tiling_type="cross", n=6),
    "star2 45": dict(type="tiling", tiling_type="star2", code="45"),
    "star2 663": dict(type="tiling", tiling_type="star2", code="663"),
    "star2 466": dict(type="tiling", tiling_type="star2", code="466"),
    "hex-colouring 6": dict(type="tiling", tiling_type="hex-col", n=6),
  },
  7: {
    "hex-colouring 7": dict(type="tiling", tiling_type="hex-col", n=7),
    "crosses 7": dict(type="tiling", tiling_type="cross", n=7),
    "plain weave abcd|efg": dict(type="weave", weave_type="plain", strands="abcd|efg", n="1"),
    "plain weave abcd|efg-": dict(type="weave", weave_type="plain", strands="abcd|efg-", n="1"),
    "plain weave abcd-|efg-": dict(type="weave", weave_type="plain", strands="abcd-|efg-", n="1"),
    "basket weave abcd|efg": dict(type="weave", weave_type="basket", strands="abcd|efg", n="3"),
    "basket weave abcd|efg-": dict(type="weave", weave_type="basket", strands="abcd|efg-", n="4"),
    "basket weave abcd|efg- 2": dict(type="weave", weave_type="basket", strands="abcd|efg-", n="2"),
    "twill weave abcd|efg": dict(type="weave", weave_type="twill", strands="abcd|efg", n="3"),
    "twill weave abcd|efg-": dict(type="weave", weave_type="twill", strands="abcd|efg-", n="4"),
    "twill weave abcd|efg- 2": dict(type="weave", weave_type="twill", strands="abcd|efg-", n="2"),
    "square-colouring 7": dict(type="tiling", tiling_type="square-col", n=7),
    "hex-slice 7": dict(type="tiling", tiling_type="hex-slice", n=7, offset=0),
    "square-slice 7": dict(type="tiling", tiling_type="square-slice", n=7, offset=0),
    "hex-dissection 7": dict(type="tiling", tiling_type="hex-dissect", n=7, offset=0, offset_angle=0),
  },
  8: {
    "square-slice 8": dict(type="tiling", tiling_type="square-slice", n=8, offset=0),
    "plain weave abcd|efgh": dict(type="weave", weave_type="plain", strands="abcd|efgh", n="1"),
    "plain weave abcd-|efgh": dict(type="weave", weave_type="plain", strands="abcd-|efgh", n="1"),
    "plain weave abcd-|efgh-": dict(type="weave", weave_type="plain", strands="abcd-|efgh-", n="1"),
    "basket weave abcd|efgh": dict(type="weave", weave_type="basket", strands="abcd|efgh", n="4"),
    "basket weave abcd|efgh 2": dict(type="weave", weave_type="basket", strands="abcd|efgh", n="2"),
    "twill weave abcd|efgh": dict(type="weave", weave_type="twill", strands="abcd|efgh", n="4"),
    "twill weave abcd|efgh 2": dict(type="weave", weave_type="twill", strands="abcd|efgh", n="2"),
    "square-colouring 8": dict(type="tiling", tiling_type="square-col", n=8),
    "hex-slice 8": dict(type="tiling", tiling_type="hex-slice", n=8, offset=0),
    "hex-colouring 8": dict(type="tiling", tiling_type="hex-col", n=8),
  },
  9: {
    "cube weave abc|def|ghi": dict(type="weave", weave_type="cube", strands="abc|def|ghi"),
    "hex-slice 9": dict(type="tiling", tiling_type="hex-slice", n=9, offset=0),
    "square-colouring 9": dict(type="tiling", tiling_type="square-col", n=9),
    "hex-colouring 9": dict(type="tiling", tiling_type="hex-col", n=9),
    "square-slice 9": dict(type="tiling", tiling_type="square-slice", n=9, offset=0),
    "archimedean 3.3.3.3.6": dict(type="tiling", tiling_type="archi", code="3.3.3.3.6"),
    "plain weave abcde|fghi": dict(type="weave", weave_type="plain", strands="abcde|fghi", n="1"),
    "plain weave abcde-|fghi": dict(type="weave", weave_type="plain", strands="abcde-|fghi", n="1"),
    "plain weave abcde-|fghi-": dict(type="weave", weave_type="plain", strands="abcde-|fghi-", n="1"),
    "hex-dissection 9": dict(type="tiling", tiling_type="hex-dissect", n=9, offset=0, offset_angle=0),
    "square-dissection 9": dict(type="tiling", tiling_type="square-dissect", n=9, offset=0, offset_angle=0),
  },
  10: {
    "hex-colouring 10": dict(type="tiling", tiling_type="hex-col", n=10),
    "hex-slice 10": dict(type="tiling", tiling_type="hex-slice", n=10, offset=0),
    "square-slice 10": dict(type="tiling", tiling_type="square-slice", n=10, offset=0),
    "plain weave abcde|fghij": dict(type="weave", weave_type="plain", strands="abcde|fghij", n="1"),
    "plain weave abcde-|fghij": dict(type="weave", weave_type="plain", strands="abcde-|fghij", n="1"),
    "plain weave abcde-|fghij-": dict(type="weave", weave_type="plain", strands="abcde-|fghij-", n="1"),
  },
  11: {
    "hex-colouring 11": dict(type="tiling", tiling_type="hex-col", n=11),
    "hex-slice 11": dict(type="tiling", tiling_type="hex-slice", n=11, offset=0),
    "square-slice 11": dict(type="tiling", tiling_type="square-slice", n=11, offset=0),
    "chavey E": dict(type="tiling", tiling_type="chavey", code="E"),
    "chavey F": dict(type="tiling", tiling_type="chavey", code="F"),
    "plain weave abcdef|ghijk": dict(type="weave", weave_type="plain", strands="abcdef|ghijk", n="1"),
    "plain weave abcdef|ghijk-": dict(type="weave", weave_type="plain", strands="abcdef|ghijk-", n="1"),
    "plain weave abcdef-|ghijk-": dict(type="weave", weave_type="plain", strands="abcdef-|ghijk-", n="1"),
  },
  12: {
    "hex-slice 12": dict(type="tiling", tiling_type="hex-slice", n=12, offset=0),
    "square-slice 12": dict(type="tiling", tiling_type="square-slice", n=12, offset=0),
    "plain weave abcdef|ghijkl": dict(type="weave", weave_type="plain", strands="abcdef|ghijkl", n="1"),
    "plain weave abcdef-|ghijkl": dict(type="weave", weave_type="plain", strands="abcdef-|ghijkl", n="1"),
    "plain weave abcdef-|ghijkl-": dict(type="weave", weave_type="plain", strands="abcdef-|ghijkl-", n="1"),
  },
  13: {"chavey A": dict(type="tiling", tiling_type="chavey", code="A")},
  14: {"chavey B": dict(type="tiling", tiling_type="chavey", code="B")},
  15: {
    "chavey H": dict(type="tiling", tiling_type="chavey", code="H"),
    "chavey J": dict(type="tiling", tiling_type="chavey", code="J"),
  },
  16: {
    "square-colouring 16": dict(type="tiling", tiling_type="square-col", n=16),
    "hex-colouring 16": dict(type="tiling", tiling_type="hex-col", n=16),
  },
  18: {
    "chavey C": dict(type="tiling", tiling_type="chavey", code="C"),
    "chavey D": dict(type="tiling", tiling_type="chavey", code="D"),
  },
  19: {"chavey G": dict(type="tiling", tiling_type="chavey", code="G")},
  20: {
    "chavey I": dict(type="tiling", tiling_type="chavey", code="I"),
    "chavey K": dict(type="tiling", tiling_type="chavey", code="K"),
  },
}


# Two families from the underlying library that the web app's
# catalogue does not carry (sanctioned additions, design review
# 2026-08-06): stripes runs the elements as n parallel bands; grid
# arrays squares as nrows x ncols. When grid's n is smaller than
# nrows * ncols the library fills the FIRST n cells and leaves the
# remainder as openings — a regularly punctured grid, not a cycled
# repeat — which is worth having on purpose (the holes read like a
# built-in group inset). make_unit() fills nrows/ncols from
# tightest_grid() unless the dialog's spinners supply them.
for _n in TILINGS_BY_N:
  TILINGS_BY_N[_n][f"stripes {_n}"] = dict(
    type="tiling", tiling_type="stripes", n=_n)
  TILINGS_BY_N[_n][f"grid {_n}"] = dict(
    type="tiling", tiling_type="grid", n=_n)


# ---------------------------------------------------------------------
# Element counts past the web app's dictionary (user instruction,
# 2026-08-10).
#
# The literal above offers 2 to 16, then 18, 19 and 20. Seventeen is
# missing and the range stops at twenty because that is how far
# somebody typed a dictionary out by hand, not because the library
# refuses: measured at every count from 2 to 60, four families build a
# correct unit at EVERY count in between. So the block below carries
# them on, in the same manner as the stripes/grid loop above.
#
# Everything here was measured rather than reasoned about, and it had
# to be. An element count a family does not support is not refused:
# Tileable.__init__ prints the setup function's complaint and
# substitutes a default tileable, so a wrongly offered design would
# reach the user as a plausible unit carrying the wrong number of
# elements -- a map quietly missing variables. Nothing may be offered
# here that has not been built and counted;
# ``test_the_catalogue_offers_only_designs_that_build`` re-measures
# every entry at every count on every run.

# The ceiling on every family alike, and it is OURS rather than the
# library's. Two limits sit here and only the tighter one is enforced.
#
# Upstream's limit is 52: it names elements from
# ``string.ascii_letters``, so above 52 the id list runs out while the
# geometry does not, pandas aligns the two, and the unit comes back
# with 52 elements covering part of the prototile -- asked for 60
# stripes, upstream 0.0.7.61 returns 52, silently and without
# complaint (measured 2026-08-10).
#
# OUR limit is 26, the lowercase alphabet, and it is the one that
# applies. Element 27 is ``A``, sharing a name with element 1's ``a``
# everywhere that does not distinguish case -- and these ids do not
# stay inside Python. They become GeoPackage table names, they reach
# filesystems that are case-insensitive by default on both macOS and
# Windows, and they are matched against saved layer properties when a
# project is reopened. A pair of elements whose ids differ only in
# case is a collision waiting for the first user who exports a map,
# and the failure would arrive as one element's styling landing on
# another's layer rather than as anything that looks like a bug.
# Twenty-six variables on one map is already far past what anybody
# can read, so the cap costs nothing real.
#
# LIFTING IT IS NOT A SMALL CHANGE, and it is worth setting out why
# at length, because the two obvious routes past 26 are blocked by two
# DIFFERENT things and the reasoning gets garbled when they are run
# together.
#
# ROUTE ONE: use the capitals as well, giving a..z then A..Z, 52 ids.
# Blocked by CASE FOLDING, and measured rather than argued. An
# element's tiles are written to a GeoPackage table named for its id,
# and GeoPackage folds case: writing `tiles_a` and then `tiles_A` into
# one file leaves a SINGLE table holding the second element's data,
# and both writes report success (2026-08-14). The same fold waits on
# any other case-insensitive path -- a filesystem, a style name, a
# layer name -- so this route does not just need care, it needs
# abandoning.
#
# ROUTE TWO: double the letters, giving a..z then aa, ab.. zz, 702
# ids. NOT blocked by the GeoPackage at all: `tiles_aa` and `tiles_ab`
# are distinct however case is folded, which is the whole appeal.
# Blocked instead by the WEAVE STRING FORMAT. A weave is specified as
# a string with one character per element -- "abcdef-|ghijk-" -- which
# users type, this catalogue stores verbatim, and the library reads
# character by character. Upstream's own code makes that concrete:
# the strand count comes from `len(ID)` and the ids from
# `list(IDs[i])`, so "ab" ALREADY MEANS two strands, a then b. A
# two-character id is not unsupported there so much as already spoken
# for, and widening it changes what every stored design means.
#
# WHAT UPSTREAM CHANGED, 2026-08-18, and what it does not settle.
# weavingspace 0.0.7.89 supplies tile ids from
# `TILE_IDS = [a..z, aa, ab.. zz]`, used ONLY in `_tiling_geometries`;
# `weave_unit.py` never touches it, deliberately. So for TILINGS both
# blockers are now off: upstream provides the ids and doubled
# lowercase survives the GeoPackage. For WEAVES route two is still
# shut, for the reason above, which is upstream's format to change
# rather than ours.
#
# SO THE CEILING COULD MOVE FOR TILINGS ALONE, and this is a decision
# rather than a discovery. It stays at 26 for both because a limit
# that differs by family is one more thing a user and a maintainer
# each have to hold in mind, nobody has asked for a twenty-seventh
# element, and the work is not the number: it is auditing everything
# that assumes an id is one character, in this plugin and in whatever
# a user has already saved. Twenty-six stands until somebody wants
# more enough to pay for that. (Reasoning rewritten 2026-08-18, after
# the earlier version compressed the two routes into one sentence and
# left the impression that case folding was what stopped doubling.)
MAX_ELEMENTS = 26

# Families whose construction is a formula in n, so they hold at every
# count up to the ceiling: stripes cuts the unit into n parallel bands,
# grid arrays n cells over the tightest near-square array, and the two
# slice families cut a hexagon or a square into n radial pieces.
# Measured at 2..60: exactly n distinct ids for every n up to 52.
GENERAL_TILINGS = {
  "stripes": lambda n: dict(type="tiling", tiling_type="stripes", n=n),
  "grid": lambda n: dict(type="tiling", tiling_type="grid", n=n),
  "hex-slice": lambda n: dict(
    type="tiling", tiling_type="hex-slice", n=n, offset=0),
  "square-slice": lambda n: dict(
    type="tiling", tiling_type="square-slice", n=n, offset=0),
}

# The two colouring families are NOT formulas: each count is a
# hand-built arrangement of hexagons or squares in the library's own
# match statement, so what they support is a list rather than a range.
# Measured at 2..60; every other count prints "n-colouring of hexes is
# not supported" and falls back to a default unit. Both lists reach
# past 20, which is how a count with no other interesting design (25
# for squares) comes to have one. Hexagons' 37 does NOT: the
# extension loop stops at MAX_ELEMENTS, which is 26, so 37 is
# recorded as a measured fact about the library and reaches no menu
# until that ceiling moves. (Corrected 2026-08-12: this said 37 was
# offered too, which was true under the higher ceiling it was written
# against.)
HEX_COLOURING_COUNTS = tuple(range(2, 17)) + (19, 37)
SQUARE_COLOURING_COUNTS = tuple(range(2, 10)) + (16, 25)

# Families deliberately NOT extended, so nobody re-measures them:
# chavey is a set of eleven hand-built tilings chosen by letter (A to
# K, carrying 11, 13, 14, 15, 18, 19 or 20 elements), and crosses,
# hex-dissection and square-dissection support only a short list of
# counts each (2-7, {3,4,7,9} and {3,5,9} respectively), all of which
# the literal above already offers where they exist.

for _n in range(2, MAX_ELEMENTS + 1):
  # setdefault throughout: a count the web app already covers keeps the
  # app's own entries untouched, and this block only fills the gaps
  _families = TILINGS_BY_N.setdefault(_n, {})
  for _family, _spec_for in GENERAL_TILINGS.items():
    _families.setdefault(f"{_family} {_n}", _spec_for(_n))
  if _n in HEX_COLOURING_COUNTS:
    _families.setdefault(f"hex-colouring {_n}", dict(
      type="tiling", tiling_type="hex-col", n=_n))
  if _n in SQUARE_COLOURING_COUNTS:
    _families.setdefault(f"square-colouring {_n}", dict(
      type="tiling", tiling_type="square-col", n=_n))

# the chooser lists counts in order, and a dict that gained 17 after 20
# would otherwise offer them in the order they were added
TILINGS_BY_N = {_n: TILINGS_BY_N[_n] for _n in sorted(TILINGS_BY_N)}


def tightest_grid(n: int):
  """(nrows, ncols) of the smallest near-square array holding n
  squares: rows from rounding sqrt(n), columns from ceiling division.
  Exact when n has a near-square factorisation (4 -> 2x2, 6 -> 2x3,
  12 -> 3x4); otherwise the array gains empty cells (5 -> 2x3 with
  one opening per unit)."""
  import math
  rows = max(1, round(math.sqrt(n)))
  return rows, math.ceil(n / rows)


def get_over_under(pattern: str):
  """Parse a comma-separated over-under pattern, ported verbatim from
  the web app's helper: invalid characters fall back to (2, 2), and an
  odd-length list is trimmed to even length as WeaveUnit expects."""
  if any(c not in "0123456789," for c in pattern):
    return (2, 2)
  try:
    numbers = [int(s) for s in pattern.split(",")]
  except ValueError:
    return (2, 2)
  length = 2 * len(numbers) // 2
  if length == 0:
    return (2, 2)
  return tuple(numbers[:length])


def make_unit(spec: dict, spacing: float, crs, offset=None, offset_angle=None,
              point_angle=None, aspect=0.75, over_under=None,
              nrows=None, ncols=None):
  """Construct a TileUnit or WeaveUnit from a catalogue entry.

  Mirrors mapweaver's get_base_tile_unit(): the catalogue says WHICH
  family and its baked-in defaults, the arguments here say what the
  user has since changed.

  Args:
    spec: one value from TILINGS_BY_N, e.g.
      ``dict(type="tiling", tiling_type="hex-slice", n=4, offset=0)``.
    spacing: the pattern's grain in map units — unit size for
      tilings, strand-to-strand distance for weaves.
    crs: an EPSG code or authority string; weavingspace attaches it
      to the geometry it builds.
    offset, offset_angle, point_angle: family-specific options from
      the Design tab. Each is forwarded ONLY when the spec declares
      it, because passing None to a family that lacks the argument
      would override weavingspace's own dataclass default.
    aspect: strand width as a fraction of spacing (weaves only).
    over_under: the passing pattern as typed ("2", "1,2", "1,2,2,1");
      parsed by get_over_under, which falls back to (2, 2) on
      nonsense rather than raising at the user.
    nrows, ncols: the grid family's array shape. Left None, the
      tightest near-square fit for the element count is used.

  Returns:
    A Tileable (TileUnit or WeaveUnit) with no modifiers applied yet;
    the dialog adds rotation, scale, skew and insets afterwards.
  """
  from weavingspace import TileUnit, WeaveUnit
  if spec["type"] == "tiling":
    kwargs = dict(tiling_type=spec["tiling_type"], spacing=spacing, crs=crs)
    if "n" in spec:
      kwargs["n"] = spec["n"]
    if "code" in spec:
      kwargs["code"] = spec["code"]
    if spec["tiling_type"] == "grid":
      # grid is the one family needing two extra constructor values;
      # the dialog's rows/cols spinners pass them, and everything
      # else (tests, previews without a dialog) gets the tightest fit
      kwargs["nrows"], kwargs["ncols"] = (
        (nrows, ncols) if nrows and ncols else tightest_grid(spec["n"]))
    if "offset" in spec:
      kwargs["offset"] = spec["offset"] if offset is None else offset
    if "offset_angle" in spec:
      kwargs["offset_angle"] = (spec["offset_angle"] if offset_angle is None
                                else offset_angle)
    if "point_angle" in spec:
      kwargs["point_angle"] = (spec["point_angle"] if point_angle is None
                               else point_angle)
    return TileUnit(**kwargs)
  n = 1
  if spec["weave_type"] in ("twill", "basket"):
    n = get_over_under(over_under if over_under is not None
                       else str(spec.get("n", "2")))
  return WeaveUnit(weave_type=spec["weave_type"], spacing=spacing,
                   strands=spec["strands"], n=n, aspect=aspect, crs=crs)
