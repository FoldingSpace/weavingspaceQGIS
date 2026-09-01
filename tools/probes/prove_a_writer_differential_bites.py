"""Break the session writer three ways and require the differential to notice.

A differential that has only ever been green is a differential nobody
has watched fail. Each mutation removes one thing
`tools/probes/two_writers_one_file.py` is supposed to see; the probe
must report a difference for each, and must be clean again once the
source is put back.

RUN IT WITH THE QGIS ENVIRONMENT HANDED OVER EXPLICITLY, which is the
fault this script itself was written with:

    env -u PYTHONHOME -u PYTHONPATH \\
      QGIS_PY="$QGIS_PY" WS_PYTHONHOME="$PYTHONHOME" \\
      WS_PROJ_LIB="$PROJ_LIB" WS_QGIS_PREFIX_PATH="$QGIS_PREFIX_PATH" \\
      WS_QGIS_PYTHONHOME="$QGIS_PYTHONHOME" \\
      python3 tools/probes/prove_a_writer_differential_bites.py

An edit script must run under `env -u PYTHONHOME`, which is precisely
the environment a QGIS child cannot start in -- so letting the child
inherit it made every arm INCLUDING THE CONTROL report disagreement,
and three "caught" verdicts meant nothing.

THE RESTORE IS VERIFIED BYTE FOR BYTE and runs in a `finally`, because
this project has already left a deliberate no-op in shipped source
when a ten-minute timeout landed between a run and its restore.
"""

import hashlib
import os
import subprocess
import sys

#: The checkout this runs against, taken from the environment or the
#: working directory rather than written down: a path from one
#: machine is a file written for that machine rather than a reader.
REPO = os.environ.get("WS_REPO", os.getcwd())
TARGET = os.path.join(REPO, "weavingspace_qgis", "bridge.py")
PROBE = "tools/probes/two_writers_one_file.py"

MUTATIONS = [
  ("every field written as text",
   '    kind, subtype = types.get(int(field.type()),\n'
   '                              (ogr.OFTString, ogr.OFSTNone))',
   '    kind, subtype = (ogr.OFTString, ogr.OFSTNone)'),
  ("the geometry never set",
   '      if shape is not None:\n        record.SetGeometry(shape)',
   '      if shape is not None:\n        pass'),
  ("a null written as an unset field",
   '        record.SetFieldNull(index)',
   '        pass'),
]


def digest(path):
  """The sha256 of a file, for proving a restore actually restored.

  Args:
    path: the file to read.

  Returns:
    Its hex digest. Compared before and after, this is the only
    thing that tells a clean run from a collision.
  """
  with open(path, "rb") as handle:
    return hashlib.sha256(handle.read()).hexdigest()


def run_probe():
  """Run the differential and return its verdict and its whole output.

  THE CHILD IS GIVEN THE QGIS ENVIRONMENT EXPLICITLY. This script runs
  under `env -u PYTHONHOME -u PYTHONPATH python3`, which is what an
  edit script must use here -- so its own environment is precisely the
  one a QGIS child cannot start in, and inheriting it made every run
  including the CONTROL report disagreement. A uniform verdict is
  almost always the instrument, and this was.
  """
  env = dict(os.environ)
  for name in ("PYTHONHOME", "PROJ_LIB", "QGIS_PREFIX_PATH",
               "QGIS_PYTHONHOME"):
    value = os.environ.get("WS_" + name)
    if value:
      env[name] = value
  env.update({"WS_REPO": REPO, "PYTHONPATH": REPO,
              "PYTHONUNBUFFERED": "1", "QT_QPA_PLATFORM": "offscreen"})
  done = subprocess.run([env["QGIS_PY"], PROBE], cwd=REPO, env=env,
                        capture_output=True, text=True, timeout=1800)
  text = done.stdout + done.stderr
  agreed = "THE TWO WRITERS AGREE" in text
  disagreed = "THE TWO WRITERS DISAGREE" in text
  if not agreed and not disagreed:
    # NEITHER VERDICT MEANS THE PROBE DID NOT RUN, which reads exactly
    # like a disagreement and is a different fact entirely.
    print("    THE PROBE PRODUCED NO VERDICT AT ALL; its last lines:")
    for line in text.strip().splitlines()[-6:]:
      print(f"      | {line[:140]}")
  return agreed, text


def main():
  """Run the control, then each mutation, and say which could be seen.

  Returns:
    0 where the control passed and every mutation was noticed, 1
    otherwise. The CONTROL is the whole point: a treatment whose
    control also fails has measured nothing, and this script
    reported three good verdicts that way before its child was
    given a QGIS environment.
  """
  original = open(TARGET, encoding="utf-8").read()
  before = digest(TARGET)
  results = []
  try:
    print("CONTROL: the tree as it stands", flush=True)
    agreed, _text = run_probe()
    print(f"  agree={agreed}  (must be True, or the mutations below "
          f"prove nothing)\n", flush=True)
    results.append(("control (unmutated)", agreed, True))

    for label, old, new in MUTATIONS:
      count = original.count(old)
      assert count == 1, (
        f"the anchor for {label!r} matches {count} places, so the "
        f"mutation would apply to nothing or to the wrong thing")
      print(f"MUTATION: {label}", flush=True)
      open(TARGET, "w", encoding="utf-8").write(
        original.replace(old, new, 1))
      agreed, text = run_probe()
      print(f"  agree={agreed}  (must be False)", flush=True)
      for line in text.splitlines():
        if "DIFFERENCE" in line or line.strip().startswith("- "):
          print(f"    {line.strip()[:130]}")
      print(flush=True)
      results.append((label, agreed, False))
  finally:
    open(TARGET, "w", encoding="utf-8").write(original)
    after = digest(TARGET)
    assert after == before, (
      f"RESTORE FAILED: {TARGET} is {after} and was {before}")
    print(f"restored, sha256 unchanged: {after[:16]}", flush=True)

  print()
  print("=" * 70)
  bad = [label for label, agreed, wanted in results if agreed != wanted]
  for label, agreed, wanted in results:
    verdict = "OK  " if agreed == wanted else "DEAD"
    print(f"  {verdict}  {label:<34} agree={agreed} wanted={wanted}")
  print("=" * 70)
  print("THE DIFFERENTIAL BITES" if not bad else
        f"IT CANNOT SEE: {bad} -- so a green run says nothing about these")
  return 1 if bad else 0


sys.exit(main())
