"""Whether a reader can tell one element's colours from another's.

A tiled multivariate map asks its reader to separate several
interleaved element shapes and read each one's colour as a different
variable. Where two elements' fills are too close, that reading fails
in a way the map does not admit to: it still looks finished, it just
carries fewer variables than it claims.

So this module answers one question about a set of assignments, before
or after the map is drawn: are any two elements' colours closer than a
reader can reliably separate, either in ordinary vision or for the
roughly one man in twelve with a red-green colour deficiency?

It works on the RAMPS the user has chosen rather than on rendered
pixels, which makes it cheap enough to run on every map: a handful of
colours per element, a few dozen distance calculations, no image.
``tools/perceptual_check.py`` does the same arithmetic on finished
renders and is the instrument for auditing a whole gallery; this is
the part that belongs in the plugin.

The plugin does not change anyone's colours on the strength of this.
It says what it found and leaves the cartography to the cartographer.
"""
from __future__ import annotations

# The threshold below which two fills are treated as too close. CIELAB
# Delta-E of 10 is a convention rather than a law: roughly "tellable
# apart at a glance, without holding them side by side". Under about
# 3 two colours are nearly identical even when adjacent. A higher bar
# would flag almost every multi-ramp map and be ignored; a lower one
# would miss pairs that genuinely collapse.
CLASH_THRESHOLD = 10.0

# Human vision, and the two dichromacies worth modelling. Tritanopia
# is left out deliberately: it is far rarer, and the blue-yellow axis
# it affects is the one that survives the other two, so including it
# would mostly add noise to the message.
VISIONS = ("normal", "deuteranopia", "protanopia")

# Hunt-Pointer-Estevez style transform into cone response, as used by
# Vienot, Brettel & Mollon (1999), whose single-plane simplification
# of Brettel et al. (1997) this follows.
RGB_TO_LMS = [[17.8824, 43.5161, 4.11935],
              [3.45565, 27.1554, 3.86714],
              [0.0299566, 0.184309, 1.46709]]

# Substitutions in LMS space. A protanope lacks the L cone and its
# response is reconstructed from M and S; a deuteranope lacks M.
LMS_PROTAN = [[0.0, 2.02344, -2.52581],
              [0.0, 1.0, 0.0],
              [0.0, 0.0, 1.0]]
LMS_DEUTAN = [[1.0, 0.0, 0.0],
              [0.494207, 0.0, 1.24827],
              [0.0, 0.0, 1.0]]


def _to_lab(rgb):
  """CIELAB for one sRGB colour, D65.

  Args:
    rgb: (r, g, b) on 0..255.

  Returns:
    (L, a, b). Lab is used rather than raw RGB distance because a
    fixed step in RGB means wildly different things to an eye
    depending on where in the cube it happens, and this project has
    already been misled once by an unweighted colour comparison.
  """
  r, g, b = (float(v) / 255.0 for v in rgb)

  def linear(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

  r, g, b = linear(r), linear(g), linear(b)
  x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
  y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
  z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

  def f(t):
    return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

  fx, fy, fz = f(x), f(y), f(z)
  return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _as_dichromat(rgb, vision):
  """The same colour, as a dichromat receives it.

  Args:
    rgb: (r, g, b) on 0..255.
    vision: one of VISIONS. "normal" returns the colour unchanged, so
      callers can loop without a special case.

  Returns:
    (r, g, b) on 0..255, clipped into gamut: the projection can land
    outside the sRGB cube, and a negative primary is not something any
    screen can show.

  Implemented without numpy on purpose. bridge.py may run before the
  dependency provisioner has finished, and a colour check is not worth
  an import that might not be there; three-by-three arithmetic is
  cheap to write out.
  """
  if vision == "normal":
    return tuple(float(v) for v in rgb)
  substitution = LMS_PROTAN if vision == "protanopia" else LMS_DEUTAN

  def linear(c):
    c = c / 255.0
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

  vector = [linear(float(v)) for v in rgb]
  lms = [sum(RGB_TO_LMS[i][j] * vector[j] for j in range(3))
         for i in range(3)]
  lms = [sum(substitution[i][j] * lms[j] for j in range(3))
         for i in range(3)]
  inverse = _inverse_3x3(RGB_TO_LMS)
  back = [sum(inverse[i][j] * lms[j] for j in range(3)) for i in range(3)]

  def encode(c):
    c = min(max(c, 0.0), 1.0)
    return (1.055 * c ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c

  return tuple(encode(c) * 255.0 for c in back)


def _inverse_3x3(m):
  """The inverse of a 3x3 matrix, by cofactors.

  Computed rather than transcribed: the published inverse of the cone
  matrix is quoted to six figures in several places, and a digit slip
  in it would show up as a small, plausible, wrong distance rather
  than as an obvious failure.
  """
  a, b, c = m[0]
  d, e, f = m[1]
  g, h, i = m[2]
  det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
  return [[(e * i - f * h) / det, (c * h - b * i) / det,
           (b * f - c * e) / det],
          [(f * g - d * i) / det, (a * i - c * g) / det,
           (c * d - a * f) / det],
          [(d * h - e * g) / det, (b * g - a * h) / det,
           (a * e - b * d) / det]]


def distance(first, second, vision="normal"):
  """CIELAB distance between two sRGB colours under one vision.

  Args:
    first, second: (r, g, b) on 0..255.
    vision: one of VISIONS.

  Returns:
    Delta-E (CIE76). Around 2 the colours are all but identical; 10 is
    where this project treats them as tellable apart at a glance.
  """
  one = _to_lab(_as_dichromat(first, vision))
  two = _to_lab(_as_dichromat(second, vision))
  return sum((a - b) ** 2 for a, b in zip(one, two)) ** 0.5


# The placeholder fills, from the one module that defines them.
#
# There used to be a COPY of the no-data grey here, because bridge.py
# defines it and importing bridge pulls in QGIS, which this module
# deliberately does without. A copy answers the need and goes stale:
# the day a second placeholder colour arrived the copy still matched
# the grey perfectly and excluded the new colours not at all, which is
# the failure a copy always has -- it stops being complete without
# ever stopping being correct. absence.py imports nothing, so it can
# be read from here as easily as from bridge, and there is no second
# copy to drift. `NO_DATA_FILL` is re-exported because callers and
# tests name it.
from .absence import (  # noqa: E402, F401 (constant, and a re-export)
  ABSENCE_FILLS,
  NO_DATA_FILL,
)


def _hex_of(colour):
  """One fill as a lowercase "#rrggbb" string.

  Args:
    colour: an (r, g, b) triple on 0..255, as the renderers hand
      them over.

  Returns:
    The hex form, for comparing against named constants. Written out
    rather than using QColor so this module stays free of Qt: it is
    arithmetic about human vision, and is tested as such.
  """
  r, g, b = (int(round(v)) for v in colour[:3])
  return f"#{r:02x}{g:02x}{b:02x}"


def clashes(element_colours, shared=None, threshold=CLASH_THRESHOLD):
  """Pairs of ELEMENTS whose colours a reader may not separate.

  Args:
    element_colours: {tile_id: [(r, g, b), ...]} -- the fills each
      element will actually use, which for a graduated element are its
      class colours and for a single-colour element is one colour.
    shared: {tile_id: ramp identity} -- optional. Two elements given
      the SAME ramp are meant to share colours, and are skipped.
    threshold: Delta-E below which a pair is reported.

  Returns:
    A list of (tile_id_a, tile_id_b, vision, distance), worst first,
    with at most one entry per pair of elements: the closest pair of
    colours between them, under whichever vision separates them least.
    Comparisons WITHIN an element are ignored -- neighbouring classes
    of one ramp are meant to be close, that is what a ramp is.

  The distinction matters: a reader confusing two classes of the same
  variable misreads a value, which the legend can rescue. A reader
  confusing two ELEMENTS attributes a value to the wrong variable
  entirely, and nothing on the map corrects that.
  """
  found = []
  shared = shared or {}
  # A PLACEHOLDER FILL IS THE SAME COLOUR IN EVERY ELEMENT by
  # construction, so it can never distinguish one element from
  # another: comparing it against itself scored every categorical
  # pair at Delta-E 0.00 and made this warning useless for
  # categorical designs whatever ramps were chosen (measured
  # 2026-08-09). It is not a colour anyone picked, it is the absence
  # of one, and a reader meeting two grey tiles learns the same true
  # thing from both -- that no value was mapped there. Dropped from
  # the comparison entirely (user decision, 2026-08-09); an element
  # left with NOTHING else keeps it, so a design of two unmapped
  # elements is still described rather than silently skipped.
  #
  # ALL of them, not only the grey: the paired layer gained two more
  # placeholder colours on 2026-08-16, one per infinity, and they have
  # exactly the property the grey has -- every element carrying an
  # infinity wears the same one, so every such pair would be reported
  # as confusable. ABSENCE_FILLS is derived from the kinds themselves,
  # so a fourth kind is excluded by the person who adds it.
  #
  # What is NOT excluded is a colour a user hand-picked for one of
  # these kinds. That is a choice like any other, it is off these
  # defaults by construction (it is why somebody opens the editor),
  # and two elements landing on the same picked colour is a real
  # clash a reader would meet.
  compared = {}
  for tile_id, colours in element_colours.items():
    kept = [c for c in colours if _hex_of(c) not in ABSENCE_FILLS]
    compared[tile_id] = kept or list(colours)
  element_colours = compared
  ids = sorted(element_colours)
  for index, first in enumerate(ids):
    for second in ids[index + 1:]:
      # Elements deliberately given the same ramp are not a problem:
      # a shared-ramp design distinguishes its elements by SHAPE and
      # is the arrangement this technique's authors recommend for
      # many variables. Warning there would be both wrong and
      # self-contradictory, since the remedy suggested below IS a
      # shared ramp. The failure worth reporting is two DIFFERENT
      # ramps that happen to land on indistinguishable colours.
      if first in shared and shared[first] == shared.get(second):
        continue
      worst = None
      # LAB ONCE PER COLOUR, not once per COMPARISON. `distance`
      # converts both of its arguments every call, so the obvious
      # nested loop did 2*k*k conversions where 2*k will do -- and a
      # conversion is about 12 microseconds, which is the whole cost.
      #
      # Measured before this change, per element pair: k=250 took
      # 2.25s, k=500 9.11s, k=1000 37.05s, exactly four times per
      # doubling. Four categorized elements of 401 classes froze QGIS
      # for 36.75s of which 35.70s was here, on the GUI thread, with
      # the event loop dead -- a heartbeat fired 9 times instead of
      # ~700. The tiling those colours belonged to took 1.05s.
      #
      # Nothing about WHAT is compared changes: the same pairs, the
      # same distances, the same worst-case picked. Only the repeated
      # arithmetic goes.
      for vision in VISIONS:
        firsts = [_to_lab(_as_dichromat(c, vision))
                  for c in element_colours[first]]
        seconds = [_to_lab(_as_dichromat(c, vision))
                   for c in element_colours[second]]
        for one in firsts:
          for two in seconds:
            apart = sum((a - b) ** 2 for a, b in zip(one, two)) ** 0.5
            if apart < threshold and (worst is None or apart < worst[3]):
              worst = (first, second, vision, apart)
      if worst is not None:
        found.append(worst)
  return sorted(found, key=lambda entry: entry[3])


def clash_message(found):
  """One sentence about element colours a reader may not separate.

  Args:
    found: what ``clashes`` returned.

  Returns:
    A sentence for the message bar, or None when every pair is far
    enough apart.

  It names the worst pair and how many others there are, rather than
  listing everything: a message bar is not a report, and the reader
  needs to know THAT the map has this problem and where to start, not
  the whole table. Wording avoids implying the plugin will fix it,
  because it will not: which ramps to use is the cartographer's call.
  """
  if not found:
    return None
  first, second, vision, apart = found[0]
  where = {"normal": "for any reader",
           "deuteranopia": "for a reader with deuteranopia",
           "protanopia": "for a reader with protanopia"}[vision]
  others = ""
  if len(found) > 1:
    others = f" ({len(found) - 1} other pair(s) are close too)"
  return (f"Elements '{first}' and '{second}' use colours that are "
          f"hard to tell apart {where}{others}. Readers may not be "
          f"able to say which variable a tile belongs to. A shared "
          f"ramp, or ramps that differ in lightness as well as hue, "
          f"separates them more reliably.")
