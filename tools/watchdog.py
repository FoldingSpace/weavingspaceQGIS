#!/usr/bin/env python3
"""Run a command and notice when it STOPS WORKING, not merely when it
has taken too long.

    python3 tools/watchdog.py --stall 45 --timeout 3600 -- <command...>

Why this exists. This project's long-running jobs (the test suite, the
mutation audit, a release) fail in one characteristic way: a modal
dialog, a lock, or an event loop with nothing left to fire, and the
process sits there indefinitely. A wall-clock timeout catches that
eventually and tells you nothing about where. Twice here it cost more
than half an hour before anyone looked, and once the diagnosis needed
a separate investigation afterwards.

The signal that distinguishes "slow" from "stuck" is CPU TIME. A busy
process accumulates it; a blocked one does not, no matter how long it
waits. So this polls the child's CPU usage and its output, and when
NEITHER has advanced for `--stall` seconds it declares a stall — in
tens of seconds rather than tens of minutes.

What it does at that moment matters as much as the detection. It
sends SIGUSR1 first: any Python process that called
``faulthandler.register(signal.SIGUSR1)`` — as tests/run_tests.py
does — responds by dumping every thread's stack to stderr. So the
report names the line the process is stuck on. Only then does it
terminate the child, escalating to SIGKILL if the polite request is
itself ignored.

Exit codes: the child's own on success, 124 on a hard timeout, 125 on
a stall. Both failure codes are distinct from any test failure, so a
caller can tell "the tests failed" from "the run never finished".
"""

import argparse
import os
import signal
import subprocess
import sys
import time


def cpu_seconds(pid):
  """Total CPU time a process and its children have used.

  Args:
    pid: the process to inspect.

  Returns:
    Seconds as a float, or None when the process is gone. Read from
    ``ps`` rather than a library so this needs nothing installed;
    the child's own children count too, because our runners spawn
    QGIS subprocesses that do the actual work.
  """
  try:
    out = subprocess.run(
      ["ps", "-o", "time=", "-p", str(pid)],
      capture_output=True, text=True, timeout=10).stdout.strip()
  except Exception:
    return None
  if not out:
    return None
  total = 0.0
  for part in out.split():
    bits = [float(b) for b in part.replace("-", ":").split(":")]
    for value in bits:
      total = total * 60 + value
  return total


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--stall", type=float, default=45,
                      help="seconds of no CPU and no output before a "
                           "run is called stalled (default 45)")
  parser.add_argument("--timeout", type=float, default=3600,
                      help="hard limit regardless of progress")
  parser.add_argument("--log", default=None,
                      help="file to tee the child's output into")
  parser.add_argument("--quiet", action="store_true",
                      help="do not echo the child's output")
  parser.add_argument("command", nargs=argparse.REMAINDER)
  args = parser.parse_args()
  command = [a for a in args.command if a != "--"]
  if not command:
    sys.exit("watchdog: no command given")

  log = open(args.log, "w", encoding="utf-8") if args.log else None
  child = subprocess.Popen(command, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True,
                           bufsize=1)
  started = time.time()
  last_progress = time.time()
  last_cpu = 0.0
  last_line = ""
  import threading

  lines = []

  def pump():
    """Read the child's output on its own thread, so a silent child
    never blocks the poller."""
    for line in child.stdout:
      lines.append((time.time(), line))
      if log:
        log.write(line)
        log.flush()
      if not args.quiet:
        sys.stdout.write(line)
        sys.stdout.flush()

  reader = threading.Thread(target=pump, daemon=True)
  reader.start()

  verdict = None
  while True:
    if child.poll() is not None:
      break
    now = time.time()
    if now - started > args.timeout:
      verdict = ("timeout", f"hard limit of {args.timeout:.0f}s reached")
      break
    cpu = cpu_seconds(child.pid) or last_cpu
    produced = len(lines)
    moved = (cpu - last_cpu > 0.5) or (produced and
                                       lines[-1][0] > last_progress)
    if moved:
      last_progress = now
      last_cpu = cpu
      if lines:
        last_line = lines[-1][1].strip()
    elif now - last_progress > args.stall:
      verdict = ("stall",
                 f"no CPU and no output for {args.stall:.0f}s "
                 f"(used {cpu:.1f}s CPU in "
                 f"{now - started:.0f}s wall clock)")
      break
    time.sleep(2)

  if verdict is None:
    code = child.wait()
    if log:
      log.close()
    sys.exit(code)

  kind, why = verdict
  print(f"\n=== watchdog: {kind.upper()} — {why}", file=sys.stderr)
  if last_line:
    print(f"=== last output: {last_line}", file=sys.stderr)
  # ask for a stack dump before killing: any process that registered
  # faulthandler on SIGUSR1 will say exactly where it is stuck
  try:
    os.kill(child.pid, signal.SIGUSR1)
    time.sleep(3)
  except Exception:
    pass
  for line in lines[-25:]:
    sys.stderr.write(line[1])
  try:
    child.terminate()
    time.sleep(3)
    if child.poll() is None:
      child.kill()
  except Exception:
    pass
  if log:
    log.close()
  sys.exit(124 if kind == "timeout" else 125)


if __name__ == "__main__":
  main()
