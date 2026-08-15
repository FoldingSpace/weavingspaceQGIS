#!/bin/bash
# Run the plugin test suite under the QGIS-bundled Python on macOS.
# Usage: bash tests/run_tests_macos.sh [/Applications/QGIS.app]
set -e
cd "$(dirname "$0")/.."
# The bundle, its interpreter and the PYTHONHOME that interpreter needs
# are all DISCOVERED rather than written down here, by the same script
# the macOS CI job uses. Each of the three has moved between QGIS
# releases -- the paths this script hardcoded until 2026-08-15 are the
# 4.0.3 build's, and the 4.2.0 cask needs different ones -- so a fixed
# path works until somebody upgrades. Sharing the script is what keeps
# the runner and this machine from disagreeing about how to start QGIS's
# Python; see tools/macos_qgis_env.sh for what it proves.
#
# The environment is captured into a variable BEFORE being eval'd, so
# that `set -e` sees the script's own exit status: `eval "$(...)"`
# returns eval's status, and a discovery that refused and printed
# nothing would otherwise leave every variable empty and produce a
# confusing error two lines later instead of the diagnosis the script
# just wrote to stderr.
unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
QGIS_ENV="$(bash tools/macos_qgis_env.sh "$@")"
eval "$QGIS_ENV"
export PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
echo "Using $QGIS_PY"
QT_QPA_PLATFORM=offscreen "$QGIS_PY" -u tests/run_tests.py
