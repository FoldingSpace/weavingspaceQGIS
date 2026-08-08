"""Catalogue of tiling and weave families.

The TILINGS_BY_N literal is ported verbatim from the mapweaver web app
(https://dosull.github.io/mapweaver/app/, app.py
setup_tilings_dictionary cell); the loop after it adds the two
sanctioned library extras (stripes, grid) that the app does not carry.
When syncing against a new app release, update the literal only and
leave the loop alone.

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
