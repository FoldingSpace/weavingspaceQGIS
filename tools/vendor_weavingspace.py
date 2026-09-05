#!/usr/bin/env python3
"""Vendor (or re-vendor) the weavingspace library into the plugin.

Usage:
    python3 tools/vendor_weavingspace.py /path/to/weavingspace/weavingspace

The argument is the *package directory* of an upstream checkout or
release (the folder containing tileable.py, tile_map.py, ...). The
script copies it into weavingspace_qgis/vendor/weavingspace and
re-applies every plugin patch, so upgrading the core library is:

    1. get the new upstream,
    2. run this script,
    3. read its report,
    4. run release.py (tests + visual gallery + zip).

The plugin targets QGIS 4+ (Python 3.12+), so upstream's modern
Python (match statements, dataclass slots, and so on) is vendored
untouched. WHY PATCHES EXIST (each is a numbered PATCH below):
  1. Optional plotting dependencies. QGIS installs lack matplotlib and
     the plugin never plots with it, so its imports are wrapped to fall
     back to a proxy (_optional.MissingModule) that only errors if
     actually *called*. Scipy was in this family until 2026-08-31, when
     upstream dropped its one use; patches 1e and 1f are retired below
     with the measurement that closed them.
  2. Performance (RETIRED -- see below; upstream adopted the same
   optimisation and the patch went with it): _TileGrid buffers the
   region to find its tiling
     rectangle; buffering the *convex hull* instead of the full
     detailed union is equivalent for that purpose (hull ⊇ union, and
     the rectangle only needs to contain the region generously) and
     turns minutes into milliseconds on coastline-heavy data.

FAILURE MODE, BY DESIGN: every patch asserts on an exact anchor string
from upstream. When a new upstream changes that code, the script
REPORTS the patch as needing attention instead of writing a silently
broken vendor — read the report, adapt the patch (the intent is
documented at each one), rerun.

The script needs only the standard library; run it with any Python 3.
"""

import pathlib
import re
import subprocess
import shutil
import sys

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent / "weavingspace_qgis"
VENDOR_DIR = PLUGIN_DIR / "vendor" / "weavingspace"

OK, FAILED = [], []


def report(name, applied, detail=""):
  """Record and announce the outcome of one patch.

  Args:
    name: the patch's label, the same one used in the numbered PATCH
      comments in main(), e.g. "1c tile_map matplotlib". It is what a
      maintainer reads in the summary line and then goes looking for
      in this file.
    applied: True when the vendored file now carries the patch,
      including the case where it was already present; False when the
      upstream anchor no longer matches and a person has to adapt the
      patch by hand.
    detail: optional clause printed after the name, used to say why
      nothing was written ("anchor not found in tileable.py") or that
      there was nothing to do ("already present"). Omitted when the
      patch simply applied.

  Returns:
    Nothing. Appends name to the module-level OK or FAILED list, which
    is what the closing summary counts and what decides the exit
    status; the immediate feedback goes to stdout.
  """
  (OK if applied else FAILED).append(name)
  mark = "applied" if applied else "NEEDS ATTENTION"
  print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def targeted(path, name, old, new):
  """Apply one exact-anchor patch; report instead of raising when the
  anchor no longer exists in the new upstream.

  Args:
    path: the file to rewrite, always one already copied into
      VENDOR_DIR. The upstream checkout is never touched.
    name: the patch's label, passed straight to report().
    old: the upstream text to find, character for character. The
      exactness is the point: a fuzzy match would let a changed
      upstream be patched in a way nobody had read.
    new: the text that replaces it. It doubles as the "already
      patched" marker, so it must be the complete patched form and
      must not appear in unpatched upstream, or a re-vendor would
      either skip a needed patch or apply it twice.

  Returns:
    Nothing. Rewrites path in place when the anchor is present and the
    patch is not, replacing only the FIRST occurrence so that a patch
    written against one site cannot silently spread to a second one
    that happens to match. Any other outcome leaves the file exactly
    as copied. Every path reports, so the patch lands in OK or FAILED
    and never passes unnoticed.
  """
  text = path.read_text()
  if new in text:
    report(name, True, "already present")
    return
  if old not in text:
    report(name, False, f"anchor not found in {path.name}")
    return
  path.write_text(text.replace(old, new, 1))
  report(name, True)


OPTIONAL_PY = '''"""Placeholders for optional plotting dependencies.

The QGIS plugin build of weavingspace does not require matplotlib: it
is used only by the notebook-oriented plotting helpers. When absent we
substitute a proxy that supports attribute access (so type annotations
such as ``plt.Axes`` still evaluate) but raises ImportError as soon as
anything is actually called.

Scipy was named here too until 2026-08-31. Upstream's only use of it
was one interpolating spline in ``Topology.zigzag_between_points``,
which their commit 2dbea80 replaced by sampling ``np.sin`` directly, so
the vendored library no longer imports scipy anywhere. The proxy stays
general rather than being renamed for matplotlib, since the next
optional dependency will want the same treatment.
"""

from __future__ import annotations


class MissingModule:
  """Stand-in for an uninstalled optional module."""

  def __init__(self, name: str) -> None:
    self._missing_name = name

  def __getattr__(self, attr: str) -> "MissingModule":
    if attr.startswith("__") and attr.endswith("__"):
      raise AttributeError(attr)
    return MissingModule(f"{self._missing_name}.{attr}")

  def __call__(self, *args, **kwargs):
    raise ImportError(
      f"'{self._missing_name}' requires an optional dependency that is "
      "not installed in this Python environment. Plotting helpers need "
      "matplotlib; the QGIS plugin does not use them.")
'''

# an optional import wrapped in a fallback to the proxy above
OPTIONAL_TEMPLATE = """try:
{imports}
except ImportError:
  from weavingspace._optional import MissingModule
{fallbacks}"""


def wrap_optional(path, name, import_lines, fallback_lines):
  """PATCH 1 for one file: wrap the given import statement(s).

  Args:
    path: the vendored module whose plotting imports must become
      optional.
    name: the patch's label for the report, e.g. "1e topology scipy".
    import_lines: upstream's import statement(s) exactly as written,
      unindented and in upstream's own order. They are joined with
      newlines to form the anchor, so they must be CONSECUTIVE lines
      upstream; a blank line or a reordering between them makes the
      patch report as needing attention, which is the intended
      failure.
    fallback_lines: the assignments to run when the import raises
      ImportError, one per name the import would have bound, each
      binding a MissingModule proxy (see OPTIONAL_PY). Every name the
      module later uses must appear here, or the fallback path fails
      with NameError at import time instead of the proxy's much more
      informative ImportError at call time.

  Returns:
    Nothing. Builds the try/except form and hands it to targeted(), so
    the file is rewritten in place and the outcome recorded in OK or
    FAILED.
  """
  anchor = "\n".join(import_lines)
  replacement = OPTIONAL_TEMPLATE.format(
    imports="\n".join("  " + ln for ln in import_lines),
    fallbacks="\n".join("  " + ln for ln in fallback_lines))
  targeted(path, name, anchor, replacement)


def record_upstream_version(upstream):
  """Write down which upstream release this vendor copy came from.

  Args:
    upstream: the weavingspace PACKAGE directory that was copied.

  Returns:
    The version string recorded, or "unknown" when the upstream tree
    carries no pyproject.toml to read it from.

  Why a file rather than prose: the vendored version is claimed in
  README.md, MAINTAINING.md and CLAUDE.md, and prose does not update
  itself. With a stamp on disk the release-time content audit can
  check those claims against something that was written by the tool
  that actually did the copying.
  """
  version = "unknown"
  commit = ""
  project = upstream.parent / "pyproject.toml"
  if project.exists():
    for line in project.read_text(encoding="utf-8").splitlines():
      match = re.match(r"""\s*version\s*=\s*["']([^"']+)["']""", line)
      if match:
        version = match.group(1)
        break
  try:
    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            cwd=upstream.parent, capture_output=True,
                            text=True, check=True)
    commit = result.stdout.strip()
  except (subprocess.CalledProcessError, FileNotFoundError, OSError):
    pass
  # A MISSING COMMIT IS SAID OUT LOUD rather than quietly dropped.
  # The stamp carries the commit precisely BECAUSE upstream does not
  # always bump the version when the code moves, so a stamp reduced to
  # its version half has lost the part that was the reason for having
  # it -- and it looks exactly like a stamp that never had one. Met on
  # 2026-08-30, vendoring from a `git archive` extraction with no
  # repository in it, which turned "0.0.7.89 (bf1bbbf)" into
  # "0.0.7.89" with nothing said.
  if not commit:
    print("  WARNING: no git repository above the upstream package, so "
          "the stamp records the VERSION ONLY.\n"
          "  Upstream does not always bump the version when the code "
          "changes, which is why the commit is recorded at all.\n"
          "  Vendor from a checkout rather than an export, or write "
          "the commit into VENDOR-VERSION.txt by hand.")
  stamp = version if not commit else f"{version} ({commit})"
  (VENDOR_DIR.parent / "VENDOR-VERSION.txt").write_text(
    f"{stamp}\n", encoding="utf-8")
  print(f"recorded upstream version: {stamp}")
  return version


def main():
  """Replace the vendored library from an upstream tree, then patch it.

  The upstream package directory comes from the single command-line
  argument. VENDOR_DIR is deleted and copied afresh, which is exactly
  why a hand edit to a vendored file cannot survive and why every
  plugin change to upstream code lives here as a patch instead.
  _optional.py (the proxy the patches fall back to) is written after
  the copy, since it is ours rather than upstream's, and the version
  stamp is recorded before any patching so that even an aborted run
  leaves a truthful record of what was copied.

  Returns:
    Nothing; the process exits instead. Exit 2 with the usage text
    when the argument is missing, exit 1 with a message when the
    directory carries no tileable.py (the cheapest test that this is
    the PACKAGE directory and not the repository root above it),
    exit 1 when any patch needs attention, and exit 0 only when every
    patch applied. Non-zero is what stops release.py from building a
    zip around a vendor tree whose report nobody has read.
  """
  if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(2)
  upstream = pathlib.Path(sys.argv[1]).resolve()
  if not (upstream / "tileable.py").exists():
    sys.exit(f"{upstream} does not look like the weavingspace package "
             "directory (no tileable.py)")

  print(f"Vendoring {upstream}\n     into {VENDOR_DIR}")
  if VENDOR_DIR.exists():
    shutil.rmtree(VENDOR_DIR)
  shutil.copytree(upstream, VENDOR_DIR,
                  ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
  (VENDOR_DIR / "_optional.py").write_text(OPTIONAL_PY)
  record_upstream_version(upstream)
  print("copied; applying patches:")

  # ---- PATCH 1: optional matplotlib / scipy -----------------------------
  wrap_optional(VENDOR_DIR / "tileable.py", "1a tileable matplotlib",
                ["from matplotlib import pyplot as plt"],
                ['plt = MissingModule("matplotlib.pyplot")'])
  wrap_optional(VENDOR_DIR / "symmetry.py", "1b symmetry matplotlib",
                ["from matplotlib import pyplot as plt"],
                ['plt = MissingModule("matplotlib.pyplot")'])
  wrap_optional(VENDOR_DIR / "tile_map.py", "1c tile_map matplotlib",
                ["import matplotlib.colors",
                 "import matplotlib.pyplot as plt"],
                ['matplotlib = MissingModule("matplotlib")',
                 'plt = MissingModule("matplotlib.pyplot")'])
  wrap_optional(VENDOR_DIR / "topology.py", "1d topology matplotlib",
                ["import matplotlib.pyplot as plt"],
                ['plt = MissingModule("matplotlib.pyplot")'])
  # PATCHES 1e (wrap `from scipy import interpolate`) and 1f (replace
  # the ONE call that needed it) were RETIRED on 2026-08-31, at the
  # re-vendor to upstream 6190917, BECAUSE UPSTREAM MERGED THE CHANGE
  # ITSELF -- commit 2dbea80, "dropping scipy spline dependency from
  # Topology.zigzag_between_points", which had been on their
  # `experimental` branch and is now on `main`.
  #
  # 1f's own comment said this was the moment to delete it: it was a
  # patch rather than a wait precisely because that branch's first
  # commit says it holds "code changes that QGIS plugin can ignore
  # until they are merged". The tool did what it is built to do -- both
  # anchors stopped matching and it NAMED them rather than writing a
  # broken vendor.
  #
  # MEASURED AT THE RE-VENDOR rather than assumed: the vendored tree
  # now contains no reference to scipy at all (the only `interpolate`
  # names left are shapely's `line_interpolate_point` and
  # `LineString.interpolate`), and `zigzag_between_points` samples
  # `np.sin` at (n + smoothness) * 2 + 1 points, which is character for
  # character what patch 1f used to write. So there is nothing left to
  # wrap and nothing left to replace.
  #
  # WHAT REMAINS OF PATCH 1 IS MATPLOTLIB ALONE, which is why 1a-1d
  # stand above and _optional.py stays: QGIS ships no matplotlib and
  # upstream's plotting helpers import it at module level.

  # ---- PATCH 3: the join lookup vectorises -------------------------
  # `tile_map.py` builds the tile-to-region lookup with
  #
  #     overlaps.groupby("joinUID")[area_name].agg(pd.Series.idxmax)
  #
  # and passing the FUNCTION defeats pandas' cython path: it falls back
  # to `_aggregate_series_pure_python` and walks every group in Python.
  # The string form uses the fast path and returns the same answer.
  #
  # MEASURED 2026-08-31 on the packaged Auckland data, laves 3.3.4.3.4:
  #
  #     spacing   tiles     groups    callable    method    ratio
  #        400    13,460     4,230     0.069s     0.002s      41x
  #        250    32,436    10,526     0.173s     0.001s     141x
  #        150    86,768    28,619     0.476s     0.003s     182x
  #        100   191,184    63,684     1.076s     0.006s     191x
  #
  # The slow form scales with the number of groups and the fast one is
  # flat, so this bites hardest on exactly the maps that already take
  # longest -- at spacing 100 it was 2.16s of `get_tiled_map`'s 3.92s.
  #
  # IT IS BEHAVIOUR-PRESERVING, INCLUDING TIES, and that was staged
  # rather than hoped for: real areas rarely tie to the last bit, so a
  # run over real data says nothing about it. On a frame built with
  # exact ties, the callable, the method and the string all return the
  # FIRST occurrence of the maximum, index for index.
  #
  # WORTH SENDING UPSTREAM, and recorded in ROADMAP.md as the second
  # conversation to have; carried here meanwhile because a patch
  # re-applies itself at every re-vendor and NAMES itself if the line
  # moves, which is what this family is for.
  targeted(VENDOR_DIR / "tile_map.py", "3 join lookup without a python loop",
           """        lookup = overlaps \\
          .iloc[overlaps.groupby("joinUID")[area_name] \\
          .agg(pd.Series.idxmax)][["joinUID", id_var]]""",
           """        lookup = overlaps \\
          .iloc[overlaps.groupby("joinUID")[area_name] \\
          .agg("idxmax")][["joinUID", id_var]]""")


  # PATCH 4 (four edits, one idea): the grid disc only has to reach the
  # ground the REGION occupies.
  #
  # `_TileGrid` lays its placements over a disc so a tiling can be
  # rotated about its centre and still cover the region -- upstream's
  # own docstring says so, and eight of its example call sites really
  # do pass a rotation. The radius was centre-to-CORNER of the region's
  # oriented bounding rectangle. Rotation about a point PRESERVES
  # DISTANCE FROM THAT POINT, so the radius that keeps the promise in
  # full is the furthest the buffered region itself reaches; a region
  # touches its rectangle's edges by construction and its corners only
  # by coincidence.
  #
  # MEASURED 2026-09-04 on the packaged Auckland data, 8 designs x 2
  # spacings x 4 rotations = 64 comparisons: placements fall to 77.3%
  # on average (best 66.7%), the worker goes 1.152s -> 0.929s at
  # spacing 250, and the overlay falls with it, 0.451s -> 0.366s,
  # because fewer tiles reach it. NOT ONE TILE OF ANY MAP DIFFERS, at
  # any rotation.
  #
  # THE FIRST ATTEMPT WAS NOT EXACT AND THE PROBE SAID SO, which is why
  # this is four edits rather than one. `_get_grid` phases its meshgrid
  # from `extent_in_grid_space.bounds`, so shrinking that polygon
  # SHIFTS EVERY TILE by a sub-cell offset: `crosses 4` at spacing 500
  # drew 2,772 tiles both ways and 2,622 of them differed, every one
  # still touching the region. Nothing was lost; the whole pattern
  # moved, which is a different map rather than a cheaper one. So the
  # original extent still PHASES the lattice and the smaller one
  # decides only which cells are WANTED -- two jobs that had been one
  # polygon.
  #
  # WORTH SENDING UPSTREAM: it costs no API change and helps upstream's
  # own rotating examples. Written up in
  # docs/process/upstream-note-the-grid-disc-is-larger-than-it-needs.md
  # and proved by tools/probes/the_smaller_disc_tiles_the_same_map.py.
  targeted(VENDOR_DIR / "tile_map.py", "4a keep the buffered region",
           '    hull = shapely.convex_hull(geom.GeometryCollection(region_to_tile.values))\n    return hull.buffer(diagonal).minimum_rotated_rectangle\n    # ---AI-suggested-code-ends---',
           "    hull = shapely.convex_hull(geom.GeometryCollection(region_to_tile.values))\n    # ---AI-suggested-code-ends---\n    # PLUGIN PATCH 4a: keep the buffered hull. It is the ground a tiling\n    # actually has to cover; the rectangle round it supplies the grid's\n    # orientation and centre, and its CORNERS are ground nothing\n    # occupies. Patch 4b measures the wanted radius from this.\n    self.buffered_region = hull.buffer(diagonal)\n    return self.buffered_region.minimum_rotated_rectangle")

  targeted(VENDOR_DIR / "tile_map.py", "4b a second, smaller extent",
           '  def _set_extent_in_grid_space(self) -> None:\n    """Set extent of the grid in grid generation space."""\n    corner = geom.Point(self.oriented_rect_to_tile.exterior.coords[0])\n    radius = self.centre.distance(corner)\n    self.extent_in_grid_space = \\\n      affine.affine_transform(self.centre.buffer(radius), self.to_grid_space)',
           '  def _set_extent_in_grid_space(self) -> None:\n    """Set extent of the grid in grid generation space.\n\n    PLUGIN PATCH 4b adds a SECOND, smaller extent beside the first, and\n    the reason the first one stays is the whole of why this patch has\n    the shape it does.\n\n    THE DISC EXISTS so a tiling can be rotated about its centre and\n    still cover the region, and rotation about a point preserves\n    distance from that point -- so the radius that keeps that promise\n    in full is the furthest the buffered REGION reaches, not the\n    furthest its bounding rectangle\'s CORNER does. A region touches its\n    rectangle\'s edges by construction and its corners only by\n    coincidence, which is ground no rotation can ever need.\n\n    BUT THE EXTENT ALSO SETS THE LATTICE\'S PHASE. `_get_grid` takes its\n    meshgrid origin from `extent_in_grid_space.bounds`, so shrinking\n    that polygon SHIFTS EVERY TILE by a sub-cell offset. Measured\n    2026-09-04 on `crosses 4` at spacing 500: both radii drew 2,772\n    tiles and 2,622 of them differed, every one still touching the\n    region -- nothing lost, the whole pattern moved. That is a\n    different map rather than a cheaper one, and this project calls\n    that a cartographic ruling rather than an optimisation.\n\n    So the original extent is kept UNTOUCHED to phase the lattice, and\n    the smaller one decides only which cells are WANTED. The two jobs\n    were one polygon and are now two.\n    """\n    corner = geom.Point(self.oriented_rect_to_tile.exterior.coords[0])\n    radius = self.centre.distance(corner)\n    self.extent_in_grid_space = \\\n      affine.affine_transform(self.centre.buffer(radius), self.to_grid_space)\n    coords = shapely.get_coordinates(self.buffered_region)\n    wanted = float(np.max(np.hypot(coords[:, 0] - self.centre.x,\n                                   coords[:, 1] - self.centre.y)))\n    self.wanted_extent_in_grid_space = \\\n      affine.affine_transform(self.centre.buffer(wanted), self.to_grid_space)')

  targeted(VENDOR_DIR / "tile_map.py", "4c filter on the smaller extent",
           '    return (gpd.GeoSeries(\n      [p for p in pts if p.within(self.extent_in_grid_space)])\n        .affine_transform(self.to_map_space))',
           '    # PLUGIN PATCH 4c: the meshgrid above is phased by the ORIGINAL\n    # extent, so every retained cell sits exactly where it always did;\n    # the smaller extent decides only which of them are wanted. Keeping\n    # the two apart is what makes this a saving rather than a shift.\n    return (gpd.GeoSeries(\n      [p for p in pts if p.within(self.wanted_extent_in_grid_space)])\n        .affine_transform(self.to_map_space))')

  targeted(VENDOR_DIR / "tile_map.py", "4d declare the two new members",
           '  extent_in_grid_space:geom.Polygon\n  """geometry of the circular extent of the tiling transformed into grid\n  generation space."""',
           '  buffered_region:geom.Polygon\n  """the region\'s convex hull buffered by the tile unit\'s diagonal, in map\n  space: the ground a tiling must cover at any rotation (plugin patch 4)."""\n  wanted_extent_in_grid_space:geom.Polygon\n  """the smaller disc that decides which grid cells are wanted, in grid\n  space. The bigger one below still phases the lattice (plugin patch 4)."""\n  extent_in_grid_space:geom.Polygon\n  """geometry of the circular extent of the tiling transformed into grid\n  generation space."""')


  # PATCH 5: let a caller say which rotations it will ask for.
  #
  # Patch 4 keeps the disc's promise to serve ANY rotation on a smaller
  # radius. A caller that knows it will never rotate can do better
  # still: the wanted ground is then the region's own SHAPE rather than
  # a disc round it. `rotations=None` is the default and is exactly
  # today's behaviour, so nothing changes for a caller that does not
  # know; naming them unions the region buffered and turned by each
  # declared angle, because a tiling rotated by r puts the tile placed
  # at p at rot(p).
  #
  # MEASURED 2026-09-04 on the packaged Auckland data: 63.8% of the
  # placements patch 4 already reduced, so about half the original, and
  # the worker at spacing 250 goes 0.929s -> 0.796s on top of patch 4
  # (1.152s before either). Twelve comparisons at rotation 0, none
  # differing.
  #
  # IT IS A PROMISE THE CALLER CAN BREAK, and the probe drives that
  # deliberately rather than showing only the happy arm: a tiling told
  # (0,) and then asked for 45 or 90 degrees comes back SHORT at the
  # edges, in 12 of 12 cases at spacing 250. A small design at a coarse
  # spacing does NOT show it -- `basket weave ab|cd` at 500 came back
  # identical -- which is why the control sweeps rather than asserting
  # on one case.
  #
  # THIS PLUGIN CAN SAY (0,) HONESTLY because its Rotate modifier calls
  # `unit.transform_rotate`, turning the prototile and re-deriving the
  # translation vectors, so the whole lattice turns BEFORE the grid is
  # laid. Upstream's own argument turns a finished tiling about the
  # grid centre instead -- the same picture at a different point in the
  # pipeline.
  #
  # Offered upstream in
  # docs/process/upstream-note-the-grid-disc-is-larger-than-it-needs.md
  # and proved by tools/probes/the_rotation_hint_keeps_the_map.py.
  targeted(VENDOR_DIR / "tile_map.py", "5a the grid takes the hint",
           '  def __init__(\n      self,\n      tile_unit:Tileable,\n      to_tile:gpd.GeoSeries,\n      at_centroids:bool = False) -> None:\n    self.tile_unit = tile_unit\n    self.oriented_rect_to_tile = self._get_rect_to_tile(to_tile)\n    self.to_map_space, self.to_grid_space = self._get_transforms()\n    self._set_centre_in_map_space()\n    self._set_extent_in_grid_space()\n    if at_centroids:\n      self.points = to_tile.representative_point()\n    else:\n      self.points = self._get_grid()\n    self.points.crs = self.tile_unit.crs',
           '  def __init__(\n      self,\n      tile_unit:Tileable,\n      to_tile:gpd.GeoSeries,\n      at_centroids:bool = False,\n      rotations:tuple[float,...]|None = None) -> None:\n    # PLUGIN PATCH 5a: `rotations` is the caller saying which rotations\n    # it will ever ask `get_tiled_map` for. None means "any", which is\n    # today\'s behaviour and the default, so nothing changes for a\n    # caller that does not know.\n    self.rotations = rotations\n    self.tile_unit = tile_unit\n    self.oriented_rect_to_tile = self._get_rect_to_tile(to_tile)\n    self.to_map_space, self.to_grid_space = self._get_transforms()\n    self._set_centre_in_map_space()\n    self._set_extent_in_grid_space()\n    if at_centroids:\n      self.points = to_tile.representative_point()\n    else:\n      self.points = self._get_grid()\n    self.points.crs = self.tile_unit.crs')

  targeted(VENDOR_DIR / "tile_map.py", "5b the wanted ground is a shape, not a disc",
           '    coords = shapely.get_coordinates(self.buffered_region)\n    wanted = float(np.max(np.hypot(coords[:, 0] - self.centre.x,\n                                   coords[:, 1] - self.centre.y)))\n    self.wanted_extent_in_grid_space = \\\n      affine.affine_transform(self.centre.buffer(wanted), self.to_grid_space)',
           "    if self.rotations is None:\n      coords = shapely.get_coordinates(self.buffered_region)\n      wanted = float(np.max(np.hypot(coords[:, 0] - self.centre.x,\n                                     coords[:, 1] - self.centre.y)))\n      wanted_in_map_space = self.centre.buffer(wanted)\n    else:\n      # PLUGIN PATCH 5b: the caller has said which rotations it will\n      # ask for, so the wanted ground is no longer a disc. A tiling\n      # rotated by r about the centre puts the tile placed at p at\n      # rot(p), so the placements worth laying are those whose IMAGE\n      # lands on the region -- p in rot^-1(buffered region), unioned\n      # over the rotations declared. With rotations=(0,) that is the\n      # region's own shape, which is why this is the larger of the two\n      # reductions.\n      wanted_in_map_space = shapely.union_all([\n        affine.rotate(self.buffered_region, -r, origin = self.centre)\n        for r in self.rotations])\n    self.wanted_extent_in_grid_space = \\\n      affine.affine_transform(wanted_in_map_space, self.to_grid_space)")

  targeted(VENDOR_DIR / "tile_map.py", "5c Tiling takes and forwards the hint",
           '      tileable:Tileable,\n      region:gpd.GeoDataFrame,\n      as_icons:bool = False,\n    ) -> None:\n    """Construct a tiling by polygons extending beyond supplied region.\n\n    The tiling is extended sufficiently to allow for its application at any\n    rotation.\n\n    Args:\n      tileable (Tileable): the TileUnit or WeaveUnit to use.\n      region (gpd.GeoDataFrame): the region to be tiled.\n      as_icons (bool, optional): if True prototiles will only be placed at the\n        region\'s zone centroids, one per zone. Defaults to False.\n\n    """\n    self.tileable = tileable\n    self.rotation = 0\n    self.region = region\n    self.region.sindex # this probably speeds up overlay  # noqa: B018\n    self.region_union = self.region.geometry.union_all()\n    self.grid = _TileGrid(\n      self.tileable,\n      self.region.geometry if as_icons else gpd.GeoSeries([self.region_union]),\n      as_icons)',
           '      tileable:Tileable,\n      region:gpd.GeoDataFrame,\n      as_icons:bool = False,\n      rotations:tuple[float,...]|None = None,\n    ) -> None:\n    """Construct a tiling by polygons extending beyond supplied region.\n\n    The tiling is extended sufficiently to allow for its application at any\n    rotation.\n\n    Args:\n      tileable (Tileable): the TileUnit or WeaveUnit to use.\n      region (gpd.GeoDataFrame): the region to be tiled.\n      as_icons (bool, optional): if True prototiles will only be placed at the\n        region\'s zone centroids, one per zone. Defaults to False.\n      rotations (tuple[float,...], optional): PLUGIN PATCH 5. The\n        rotations this tiling will ever be asked for. Defaults to None,\n        meaning any -- which is the behaviour above and costs a grid\n        laid over every radius the region reaches. Naming them lets the\n        grid ask the region\'s own SHAPE instead of a disc, which on the\n        packaged Auckland data at spacing 250 is 2,791 placements of\n        8,109 rather than 6,402. Pass it only if it is true: a tiling\n        asked for a rotation it was not told about will be short of\n        tiles at the edges.\n\n    """\n    self.tileable = tileable\n    self.rotation = 0\n    self.region = region\n    self.region.sindex # this probably speeds up overlay  # noqa: B018\n    self.region_union = self.region.geometry.union_all()\n    self.grid = _TileGrid(\n      self.tileable,\n      self.region.geometry if as_icons else gpd.GeoSeries([self.region_union]),\n      as_icons,\n      rotations)')

  targeted(VENDOR_DIR / "tile_map.py", "5d declare the hint as a slot",
           '  buffered_region:geom.Polygon\n  """the region\'s convex hull buffered by the tile unit\'s diagonal, in map\n  space: the ground a tiling must cover at any rotation (plugin patch 4)."""\n  wanted_extent_in_grid_space:geom.Polygon\n  """the smaller disc that decides which grid cells are wanted, in grid\n  space. The bigger one below still phases the lattice (plugin patch 4)."""',
           '  rotations:tuple[float,...]|None\n  """the rotations this grid will be asked for, or None for any. Naming\n  them lets the grid ask the region\'s own shape rather than a disc\n  (plugin patch 5)."""\n  buffered_region:geom.Polygon\n  """the region\'s convex hull buffered by the tile unit\'s diagonal, in map\n  space: the ground a tiling must cover at any rotation (plugin patch 4)."""\n  wanted_extent_in_grid_space:geom.Polygon\n  """the smaller disc that decides which grid cells are wanted, in grid\n  space. The bigger one below still phases the lattice (plugin patch 4)."""')

  # PATCH 2 (hull buffer in _get_rect_to_tile) was RETIRED on
  # 2026-08-07: upstream adopted the same optimisation itself
  # (commit 8235837), in its own variant — per-geometry convex hulls,
  # a coverage union, then a hull of that. It was verified to tile
  # identically to the patch it replaces (349 tiles, same per-element
  # counts, same total area on the Auckland dataset) and is faster
  # again, so carrying our own version would be pure divergence.
  # Only the optional-imports family remains.


  # PATCH 2 (vectorised tile materialisation) was RETIRED on
  # 2026-08-07, the day after it was offered: upstream took it
  # (commit d4741e6, "optimisation of construction of
  # Tiling.make_tiling() using shapely.transform and numpy"), in a
  # tidier form than ours -- a _to_grid_points helper rather than a
  # closure inside make_tiling. Upstream also took the companion
  # change to the membership test (an STRtree over the region's own
  # polygons instead of testing every tile against region_union),
  # which we had offered but never vendored. Nothing to carry.
  #
  # Two notes kept for whoever revisits this:
  #  * upstream calls shapely.transform with include_z=False
  #    unconditionally, so a 3D tileable would lose its z. Ours
  #    handled that; weavingspace units are 2D, so it costs nothing
  #    today, but it is the one behavioural difference between the
  #    two versions.
  #  * the module still binds the name `shapely` only through
  #    `import shapely.ops`. That is a real Python rule (importing a
  #    submodule binds the package), not an accident, but it is the
  #    sort of thing an import tidy-up could break.

  print(f"\n{len(OK)} patches applied, {len(FAILED)} need attention"
        + (": " + ", ".join(FAILED) if FAILED else ""))
  print("Next: run release.py (tests, visual gallery, zip).")
  sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
  main()
