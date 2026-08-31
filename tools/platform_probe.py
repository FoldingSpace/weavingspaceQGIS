"""The tests whose answers are a property of the PLATFORM, run first.

WHY THIS EXISTS, and it is a cost rather than a principle. The
Windows leg takes about seventy-five minutes, of which the functional
suite is nearly all; the Linux and macOS legs take about an hour. So a
fault that only a second machine can show is reported at the END of
that hour, and the loop to fix it and learn whether the fix worked is
another one. On 2026-08-29 that cost exactly one such round: the
assignment table's columns were taught to grow, the window's ceiling
stopped binding on any platform whose fonts are wider than the
development machine's, and Windows said so seventy-five minutes later
in three tests and two locales, all quoting one number.

RUN THE PLATFORM QUESTIONS FIRST AND THE ANSWER ARRIVES IN MINUTES.
Everything named below is a test whose verdict depends on font
metrics, locale or the window manager -- the things that differ
between machines and that this machine therefore cannot answer for
anybody else. None of them takes more than a few seconds; together
they are a rounding error against the suite, and they fail the job
before the hour is spent rather than after.

IT DOES NOT REPLACE THE SUITE, and nothing here may be removed from
it. This is the same shape as the release gates being ordered
cheapest-first: a fast refusal is worth having precisely because the
expensive measurement still follows.

ONE OWNER FOR THE LIST. It lives here rather than in `ci.yml` because
a list of test names in YAML is a hand-kept list nothing can check --
this project's own recurring fault -- and because `check_standards`
can read a Python module. Adding a test whose answer is a property of
the platform means adding it here, with the reason at the line.
"""

import importlib.util
import os
import sys
import traceback

# WHAT MAKES A TEST BELONG HERE: its verdict is decided by something
# the development machine cannot vary honestly -- the platform's font
# metrics, its locale machinery, or how its window manager assembles a
# dialog. A test that merely LOOKS at the interface does not qualify;
# the question is whether a green run here proves anything about
# anywhere else.
PLATFORM_TESTS = [
  # Font metrics decide every one of these. The columns are sized from
  # what their content needs, so the window's width is a claim about a
  # font, and the ceiling is the one clause of the layout rule that a
  # person cannot work around: a window wider than the display cannot
  # be made narrower by whoever is using it.
  "test_the_ceiling_holds_when_the_columns_want_more_than_it",
  "test_the_window_fits_the_narrowest_screen",
  "test_the_table_copes_with_the_largest_element_count",
  # The ASSEMBLED window against the screen it opens on, which is the
  # one thing no runner here can measure: offscreen reports 1279px
  # where cocoa gives 1334, and `availableGeometry` on a headless
  # platform is not a claim about anybody's desk. The unit test can
  # only ask that the RULE holds -- a size larger than the screen
  # comes back smaller -- so what a person actually meets is measured
  # here. (Added 2026-08-30 with the ceiling itself.)
  "test_the_window_never_grows_past_the_screen",
  # Locale changes the text in every control, so it changes the widths
  # too -- German and Arabic both reported the 2026-08-29 fault, and
  # the right-to-left case exercises the layout a second way.
  "test_the_plugin_in_another_locale",
  # Tooltips and labels are measured against the platform's own font
  # when the rule about their length is checked.
  "test_every_control_explains_itself",
]


def load_suite(root):
  """Import `tests/run_tests.py` without running it.

  Args:
    root: the checkout to load from.

  Returns:
    The loaded module. Imported by path rather than by name because
    the suite is not a package and the working directory on a runner
    is not something to rely on.
  """
  spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(root, "tests", "run_tests.py"))
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


def main():
  """Run every platform-sensitive test and report each one.

  Returns:
    None. Exits 0 when all of them pass and 1 otherwise, naming each
    failure with its traceback -- a remote failure that cannot be
    attributed costs a whole round to reproduce, which is why this
    prints what it FOUND rather than only that something went wrong.
    A name that is no longer in the suite is a FAILURE here and not a
    skip: a probe quietly running four tests where it names five is
    the matches-nothing-reports-nothing fault this project keeps
    meeting.
  """
  root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  sys.path.insert(0, root)
  os.chdir(root)
  suite = load_suite(root)

  from qgis.core import QgsApplication, QgsProject
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()
  suite._no_modal_dialogs()

  failed = 0
  print(f"platform probe: {len(PLATFORM_TESTS)} test(s) whose answer "
        f"belongs to this machine rather than to the one they were "
        f"written on")
  for name in PLATFORM_TESTS:
    QgsProject.instance().clear()
    suite.BAR_MESSAGES.clear()
    fn = getattr(suite, name, None)
    if fn is None:
      print(f"MISSING  {name}  -- named here and not in the suite")
      failed += 1
      continue
    try:
      fn()
      print(f"PASS  {name}")
    except Exception:
      failed += 1
      print(f"FAIL  {name}")
      traceback.print_exc()
      sys.stdout.flush()

  print(f"\nplatform probe: {len(PLATFORM_TESTS) - failed} passed, "
        f"{failed} failed")
  if failed:
    print("The full suite has NOT run. These are the questions whose "
          "answers differ between machines, and this machine has just "
          "answered one of them differently from the one the code was "
          "written on.")
  # `os._exit`, as the suite itself does: a buffered verdict never
  # reaches a pipe, and a run that printed nothing looks exactly like
  # a run that passed.
  sys.stdout.flush()
  os._exit(1 if failed else 0)


main()
