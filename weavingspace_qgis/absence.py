"""The kinds of value a graduated renderer cannot place, named once.

A choropleth draws a number by putting it in a class. Three sorts of
cell have no class to go in -- nothing was recorded, the value is
below any finite value, or above any finite value -- so the tiles
carrying them leave the element's own layer for its paired one, which
is categorized on ``ABSENCE_FIELD`` to keep the three apart.

WHY THIS IS ITS OWN MODULE, which is the only surprising thing here.
These constants were part of bridge.py, and bridge.py cannot be
imported without QGIS. perception.py must know which fills are
placeholders -- every element wears the SAME placeholder colour, so
comparing them against each other reports a clash in every design that
has one -- and perception.py is deliberately importable without QGIS,
being arithmetic about human vision and tested as such. A copy of the
fills kept in perception.py would answer that need and would go stale
the day a fourth kind is added, silently, since a copy that has
stopped matching still excludes something. So the definition lives
here, where both can read it and neither owns it, and this module
imports nothing at all. bridge.py re-exports every name below, so
``bridge.NO_DATA_FILL`` and the rest still resolve for its callers.
"""
from __future__ import annotations

# light grey used wherever an element has no variable or a feature has
# no value
NO_DATA_FILL = "#dddddd"

# The key standing for the catch-all category in a per-value colour
# override map. A real field value could in principle be the string
# "no data", so this is deliberately something no attribute value can
# collide with rather than a readable word.
NO_DATA_KEY = "\x00no-data"

# THE THREE WAYS A VALUE CAN BE UNPLACEABLE, and they are not one
# thing. A graduated renderer draws none of them, so all three leave
# the element's own layer for its paired one -- but a reader is owed
# the difference between "nobody recorded a value here" and "this area
# is off the top of the scale", which on a choropleth is the
# difference between missing and extreme. (Maintainer's instruction,
# 2026-08-16.)
#
# WHY THREE AND NOT FOUR, which is the measurement that settled it. A
# stored NaN is a fourth state QGIS itself holds apart from NULL --
# but writing one to a GeoPackage stores NULL (measured 2026-08-16
# through QgsVectorFileWriter and read back with sqlite3), so the
# category would be empty for anyone whose data came from a file,
# and a legend swatch no tile can ever wear is the defect this
# project fixes elsewhere. The maintainer's ruling was to support
# what a GeoPackage supports and collapse NaN into No data, which
# `isna()` already does for free. The infinities need no such care:
# the same measurement showed SQLite stores them as REAL and hands
# them straight back, and they arrive here as ordinary values whose
# only peculiarity is that `isna()` is False -- which is exactly why
# they used to fall through the split AND the class breaks and be
# drawn as nothing at all.
POS_INF_KEY = "\x00+inf"
NEG_INF_KEY = "\x00-inf"

# The column the paired layer carries so its renderer can tell the
# kinds apart. Named once here because the renderer categorizes on it
# and should not have to know which variable produced the layer.
ABSENCE_FIELD = "ws_absence"

# key -> (value stored in ABSENCE_FIELD, legend label, default fill).
# The labels say what happened rather than naming a floating-point
# state. The infinities are deliberately NOT the no-data grey: they
# mean off-the-scale rather than absent, and one colour for both would
# break one-colour-one-meaning inside the feature meant to uphold it.
ABSENCE_KINDS = (
  # "no data" and NOT "no value": this label is the one this plugin
  # has always shown, in the legend and in the colour editor, and
  # renaming it would be an unreviewed change to shipped text for
  # no gain. The two infinities are new and get new words.
  (NO_DATA_KEY, "no-value", "no data", NO_DATA_FILL),
  (NEG_INF_KEY, "neg-infinity", "below any value", "#8c9fc7"),
  (POS_INF_KEY, "pos-infinity", "above any value", "#c78c8c"),
)

# Every DEFAULT placeholder fill, lowercased, as a set for testing
# membership. Derived from ABSENCE_KINDS rather than written out, so a
# fourth kind is covered by whoever adds it and by nobody else.
#
# DEFAULT is the whole of it, and the narrowness is the point. These
# colours mean the same thing on every element, which is why
# perception.clashes drops them: two elements both drawing "no value"
# grey tell a reader the same true thing, and reporting them as
# confusable was measured to score every categorical pair at Delta-E
# 0.00. A colour a user has HAND-PICKED for one of these kinds is a
# choice like any other and is compared like any other.
ABSENCE_FILLS = frozenset(fill.lower() for _k, _v, _l, fill in ABSENCE_KINDS)

# key -> the value stored in ABSENCE_FIELD, and back again. Two dicts
# rather than repeated indexing into the tuples above, so a reader
# never has to remember which position means what.
ABSENCE_VALUE = {key: stored for key, stored, _label, _fill in ABSENCE_KINDS}
ABSENCE_BY_VALUE = {stored: key for key, stored, _l, _f in ABSENCE_KINDS}
