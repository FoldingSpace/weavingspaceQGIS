"""Ask Windows why release.py's cpu accounting reads zero.

WHY THIS EXISTS, and why it is allowed to be temporary. `release.py`
measures a stage's cpu across its whole process tree so a busy stage
is never mistaken for a hung one. That reading is `ps` on Unix and, as
of 2026-08-15, PowerShell's CIM interface on Windows -- and the
Windows path RUNS and reports 0.0 seconds for a tree whose grandchild
is deliberately burning cpu. The suite says so and cannot say why.

Diagnosing it through the functional suite costs about fifty minutes
per guess, because the Windows job installs QGIS and runs four hundred
tests before reaching the two that fail. This probe asks only the
failing question: it needs no QGIS, no plugin and no geopandas, so it
answers in the time a runner takes to boot.

It prints EVERYTHING it can see rather than asserting, because the
point is to find out what is true, and an assertion would stop at the
first surprise. Delete it, and the workflow that runs it, once the
cause is known and fixed -- the properties themselves are asserted by
tests/run_tests.py on the platforms a release is cut on.

Usage:
    python tools/win_process_probe.py

Output: a block per question, each headed by what it is asking, so a
CI log can be read top to bottom without knowing this file.
"""
import os
import subprocess
import sys
import time


def heading(text):
  """Print a section header so the CI log reads as an argument.

  Args:
    text: what this section asks, in a few words.

  Returns:
    None.
  """
  print(f"\n=== {text}\n{'-' * 60}")


def run(command, label):
  """Run a command and print everything about how it went.

  Args:
    command: argv list to run.
    label: what this call is being asked, for the log.

  Returns:
    The CompletedProcess, or None when it could not be started at all
    -- which is itself an answer and is printed rather than raised.
  """
  print(f"[{label}] {command!r}")
  try:
    done = subprocess.run(command, capture_output=True, text=True,
                          timeout=60)
  except (subprocess.SubprocessError, OSError) as exc:
    print(f"[{label}] could not start: {type(exc).__name__}: {exc}")
    return None
  print(f"[{label}] returncode={done.returncode} "
        f"stdout={len(done.stdout)} chars stderr={len(done.stderr)} chars")
  if done.stderr.strip():
    print(f"[{label}] stderr, first 400 chars:\n{done.stderr[:400]}")
  return done


POWERSHELL = (
  "Get-CimInstance Win32_Process | ForEach-Object { "
  "'{0} {1} {2}' -f $_.ProcessId, $_.ParentProcessId, "
  "($_.KernelModeTime + $_.UserModeTime) }")


def main():
  """Ask the questions, in the order that narrows the cause.

  Returns:
    0 always. This probe reports; it does not judge.
  """
  heading("what platform is this")
  print(f"os.name={os.name} sys.platform={sys.platform}")
  print(f"python={sys.version.split()[0]} pid={os.getpid()}")

  heading("does the interpreter we use for the tree exist")
  for shell in ("powershell", "pwsh"):
    run([shell, "-NoProfile", "-NonInteractive", "-Command",
         "$PSVersionTable.PSVersion.ToString()"], f"{shell} version")

  heading("what does the process listing actually return")
  done = run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
              POWERSHELL], "process table")
  if done is not None and done.stdout:
    lines = done.stdout.splitlines()
    print(f"[process table] {len(lines)} lines; first 5 verbatim:")
    for line in lines[:5]:
      print(f"    {line!r}")
    # The parser release.py uses, applied here so a mismatch between
    # what PowerShell prints and what the parser expects is visible
    # rather than inferred.
    parsed, unparsed = 0, []
    for line in lines:
      parts = line.split()
      if len(parts) < 3:
        if line.strip():
          unparsed.append(line)
        continue
      try:
        int(parts[0]), int(parts[1]), int(parts[2])
        parsed += 1
      except ValueError:
        unparsed.append(line)
    print(f"[process table] parsed {parsed} rows, "
          f"{len(unparsed)} unparsable")
    for line in unparsed[:5]:
      print(f"    unparsable: {line!r}")

  heading("can release.py be imported and asked directly")
  root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  sys.path.insert(0, root)
  release = None
  try:
    import release as release_module
    release = release_module
    print("release.py imported")
  except Exception as exc:
    print(f"release.py would not import: {type(exc).__name__}: {exc}")

  heading("does a busy tree report any cpu")
  # A child that starts a GRANDCHILD which burns cpu, which is the
  # shape release.py must measure and the shape the suite says reads
  # zero here.
  program = (
    "import subprocess, sys, time\n"
    "g = subprocess.Popen([sys.executable, '-c',\n"
    "  'import time\\nend=time.time()+25\\n"
    "while time.time()<end: pass'])\n"
    "time.sleep(25)\n")
  child = subprocess.Popen([sys.executable, "-c", program])
  try:
    time.sleep(6)               # let the grandchild accrue something
    print(f"child pid={child.pid}")
    if release is not None and hasattr(release, "_process_table"):
      table = release._process_table()
      if table is None:
        print("_process_table() returned None")
      else:
        children, times = table
        print(f"_process_table(): {len(times)} processes, "
              f"{len(children)} parents")
        print(f"our pid in table: {os.getpid() in times}")
        print(f"child pid in table: {child.pid in times}")
        print(f"child's children: {children.get(child.pid)}")
        for pid in [os.getpid(), child.pid] + list(
            children.get(child.pid) or []):
          print(f"    pid {pid}: cpu={times.get(pid)!r} "
                f"kids={children.get(pid)}")
    if release is not None and hasattr(release, "tree_cpu_seconds"):
      print(f"tree_cpu_seconds(child) = "
            f"{release.tree_cpu_seconds(child.pid)!r}")
      print(f"tree_cpu_seconds(self)  = "
            f"{release.tree_cpu_seconds(os.getpid())!r}")
  finally:
    child.kill()
    child.wait()

  heading("done")
  return 0


if __name__ == "__main__":
  sys.exit(main())
