#!/bin/bash
# Find a macOS QGIS bundle and print the environment its Python needs.
#
# WHY THIS EXISTS. A QGIS .app carries its own Python, and that
# interpreter cannot start unaided. The Homebrew cask's
# `Contents/MacOS/python3.12` was built on somebody else's machine and
# has that machine's paths baked into it: on 2026-08-15 a macOS CI run
# printed a `sys.base_prefix` pointing into the QGIS project's own
# build tree -- a vcpkg directory under a home folder that exists on
# nobody else's computer -- and then died with `ModuleNotFoundError: No
# module named 'encodings'` before running a line of Python, because
# the standard library was not where it was told. PYTHONHOME repairs
# that, and
# it points at a directory inside the bundle whose location has moved
# between QGIS releases -- Contents/Frameworks on the 4.0.3 build this
# project develops against, somewhere else on the next one.
#
# So it is DISCOVERED and then PROVED, rather than written down. A
# hardcoded path is what cost the CI job two rounds already, and a
# probe that returns without exercising the thing is worse than one
# that errors (docs/TESTING.md): every candidate here is judged by
# actually starting the interpreter with it.
#
# INPUTS
#   $1  optional path to a QGIS .app bundle. Omitted, the newest-named
#       /Applications/QGIS*.app is taken.
#
# OUTPUT, on stdout, one KEY=value per line and nothing else, so that a
# caller can `eval` it or append it straight to $GITHUB_ENV:
#   QGIS_APP           the bundle that was chosen
#   QGIS_PY            the interpreter inside it that actually starts
#   PYTHONHOME         omitted when the interpreter starts without one
#   PROJ_LIB           omitted when the bundle has no proj directory
#   QGIS_PREFIX_PATH   omitted when Contents/MacOS is absent
# Diagnostics -- what was tried, what was found, what was rejected --
# go to stderr, so they are readable in a log without contaminating the
# values.
#
# EXIT
#   0  a working interpreter was found and printed
#   1  no bundle, no interpreter, or none that could be started; the
#      message says which, with a listing rather than a bare refusal,
#      because a failure read from a runner fifty minutes later has to
#      diagnose itself.

set -e

say() { echo "$@" >&2; }

APP="${1:-$(ls -d /Applications/QGIS*.app 2>/dev/null | sort | tail -1)}"
if [ -z "$APP" ] || [ ! -d "$APP" ]; then
  say "no QGIS application bundle under /Applications:"
  ls -la /Applications >&2 2>/dev/null | head -40
  exit 1
fi
say "bundle: $APP"

# The interpreter has lived in three places across QGIS releases, so
# all three are tried before falling back to a search: QGIS 4.0.3 and
# 4.2.0 both use Contents/MacOS/python3.12, older layouts used a bin/
# beside it, and some builds keep a whole Python framework.
PYS=""
for p in "$APP"/Contents/MacOS/bin/python3* \
         "$APP"/Contents/MacOS/python3* \
         "$APP"/Contents/Frameworks/Python.framework/Versions/*/bin/python3; do
  [ -x "$p" ] && PYS="$PYS $p"
done
if [ -z "$PYS" ]; then
  PYS=$(find "$APP/Contents" -maxdepth 5 -name 'python3*' -type f -perm -u+x 2>/dev/null | head -3)
fi
if [ -z "$PYS" ]; then
  say "no bundled python3 anywhere under $APP/Contents:"
  find "$APP/Contents" -maxdepth 3 -type d >&2 2>/dev/null | head -40
  exit 1
fi

# A PYTHONHOME is a directory holding lib/python3.X/encodings. The
# empty string is tried FIRST and deliberately: an interpreter that
# starts unaided should not be handed an environment variable it does
# not need, since a wrong PYTHONHOME is its own class of failure.
HOMES=""
for d in "$APP/Contents/Frameworks" "$APP/Contents/Resources" \
         "$APP/Contents/MacOS" "$APP/Contents"; do
  if ls -d "$d"/lib/python3.*/encodings >/dev/null 2>&1; then
    HOMES="$HOMES $d"
  fi
done
if [ -z "$HOMES" ]; then
  # Nothing in the four usual places, so look for the stdlib itself
  # and walk back up to the prefix it belongs to.
  for e in $(find "$APP/Contents" -type d -name encodings -path '*/lib/python3*' 2>/dev/null | head -3); do
    HOMES="$HOMES $(dirname "$(dirname "$(dirname "$e")")")"
  done
fi

PROJ="$APP/Contents/Resources/qgis/proj"
# GDAL's own data directory, which nothing here set until 2026-08-15.
# The macOS runs printed "Cannot find tms_NZTM2000.json (GDAL_DATA is
# not defined)" on every GeoPackage test -- harmless in the cases the
# suite covers, since they passed, but it is the same shape as the
# prefix fault below: a variable nobody set, hidden by everything
# happening to work anyway. The file it names is in the bundle. A
# warning that is always there is a warning nobody reads, and it would
# hide the one that mattered.
GDAL_DIR="$APP/Contents/Resources/qgis/gdal"

# Two passes, because the two questions are not the same. A
# combination that imports qgis.core is what every later step needs; a
# combination that merely starts the interpreter is worth reporting as
# a fallback, since the failure it then produces names a missing module
# rather than dying in the C runtime with nothing to read.
CHOSEN_PY=""
CHOSEN_HOME=""
for want in qgis stdlib; do
  for py in $PYS; do
    for home in "" $HOMES; do
      if [ "$want" = qgis ]; then
        probe='import qgis.core, sys; print(sys.prefix)'
      else
        probe='import encodings, sys; print(sys.prefix)'
      fi
      if out=$(PYTHONHOME="$home" \
               QT_QPA_PLATFORM=offscreen "$py" -c "$probe" 2>/dev/null); then
        say "starts ($want): $py  PYTHONHOME='${home:-unset}'  sys.prefix=$out"
        CHOSEN_PY="$py"
        CHOSEN_HOME="$home"
        break 3
      fi
      say "rejected ($want): $py  PYTHONHOME='${home:-unset}'"
    done
  done
done

if [ -z "$CHOSEN_PY" ]; then
  say "no interpreter in $APP could be started, with or without a PYTHONHOME."
  say "interpreters tried:$PYS"
  say "PYTHONHOME candidates tried:${HOMES:- none found}"
  say "what the bundle actually contains:"
  find "$APP/Contents" -maxdepth 3 -type d >&2 2>/dev/null | head -40
  exit 1
fi

# QGIS_PREFIX_PATH is what QGIS derives pkgDataPath from, and
# pkgDataPath is where it looks for the style database that every
# stock colour ramp lives in. Get it wrong and QGIS starts perfectly
# well, imports, tiles, renders -- and has NO RAMPS AT ALL.
#
# Measured 2026-08-15, and this project had it wrong for months:
# `$APP/Contents/MacOS` (what tests/run_tests_macos.sh used to say)
# yields a doubled pkgDataPath of `.../Contents/MacOS/Contents/
# Resources/qgis`, which does not exist, and a fresh profile then
# reports ZERO ramps. `$APP` itself yields the real directory and 35
# ramps -- ColorBrewer's, viridis absent, exactly the inventory the
# colour decision of that day describes. It never showed on the
# development machine because that profile has carried 63 ramps since
# the plugin seeded it years ago, which is the same way the
# colourspace gate passed for months on one machine's style library.
#
# So the prefix is chosen by ASKING QGIS, against a THROWAWAY PROFILE.
# The throwaway part is the whole trick: asked with a seeded profile,
# every candidate answers "ramps present" and the measurement proves
# nothing at all.
PREFIX=""
for cand in "$APP" "$APP/Contents/MacOS" "$APP/Contents"; do
  [ -d "$cand" ] || continue
  tmp_profile=$(mktemp -d)
  count=$(PYTHONHOME="$CHOSEN_HOME" QGIS_PREFIX_PATH="$cand" \
          QGIS_CUSTOM_CONFIG_PATH="$tmp_profile" QT_QPA_PLATFORM=offscreen \
          "$CHOSEN_PY" -c 'from qgis.core import QgsApplication, QgsStyle
app = QgsApplication([], False)
app.initQgis()
print(len(QgsStyle.defaultStyle().colorRampNames()))' 2>/dev/null | tail -1)
  rm -rf "$tmp_profile"
  say "prefix $cand: ${count:-no answer} ramp(s) on a fresh profile"
  case "$count" in
    ''|*[!0-9]*) continue ;;
    0) continue ;;
    *) PREFIX="$cand"; break ;;
  esac
done
if [ -z "$PREFIX" ]; then
  # Not fatal: QGIS runs without its stock ramps, and a suite that
  # then fails on a missing ramp name says so plainly. Falling over
  # here would hide that behind a refusal to start at all.
  say "WARNING: no QGIS_PREFIX_PATH gave this QGIS any colour ramps."
  say "Anything asking for a stock ramp by name will get None. The"
  say "usual cause is a bundle layout this script has not met; the"
  say "candidates tried were $APP, $APP/Contents/MacOS, $APP/Contents."
fi


echo "QGIS_APP=$APP"
echo "QGIS_PY=$CHOSEN_PY"
[ -n "$CHOSEN_HOME" ] && echo "PYTHONHOME=$CHOSEN_HOME"
[ -d "$PROJ" ] && echo "PROJ_LIB=$PROJ"
[ -d "$GDAL_DIR" ] && echo "GDAL_DATA=$GDAL_DIR"
[ -d "$PREFIX" ] && echo "QGIS_PREFIX_PATH=$PREFIX"
exit 0
