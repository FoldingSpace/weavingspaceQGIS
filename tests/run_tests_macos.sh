#!/bin/bash
# Run the plugin test suite under the QGIS-bundled Python on macOS.
# Usage: bash tests/run_tests_macos.sh [/Applications/QGIS.app]
set -e
APP="${1:-$(ls -d /Applications/QGIS*.app 2>/dev/null | head -1)}"
if [ -z "$APP" ]; then
  echo "No QGIS app found in /Applications — pass its path as an argument."
  exit 1
fi
QP="$APP/Contents"
PY="$(ls "$QP"/MacOS/python3.* 2>/dev/null | head -1)"
if [ -z "$PY" ]; then
  echo "No bundled python3 found in $QP/MacOS"
  exit 1
fi
echo "Using $PY"
cd "$(dirname "$0")/.."
QT_QPA_PLATFORM=offscreen \
PYTHONHOME="$QP/Frameworks" \
PROJ_LIB="$QP/Resources/qgis/proj" \
QGIS_PREFIX_PATH="$QP/MacOS" \
"$PY" -u tests/run_tests.py
