"""Everything the plugin has said, kept where it can be said early.

The Messages tab shows this. It lives in its own module, rather than on
the dialog, for one reason: THE PLUGIN SPEAKS BEFORE THE DIALOG EXISTS.
The dependency consent dialogue, the failure to provision, and the
failure to import the library are all raised from `plugin.py` on the
way to opening the window, and two of them mean the window never opens
at all. A record that began at the dialog's construction would be
missing exactly the messages a person most needs to look back at, which
is the silence the tab was asked for to end.

WHY A MODULE RATHER THAN THE DIALOG'S OWN LIST. `plugin.py` imports
`dialog.py` lazily and deliberately -- the dialog pulls in the vendored
library and the scientific stack -- so recording into the dialog's
module would drag all of that into QGIS start-up to hold four strings.
This module imports nothing but the standard library.

THE CLOCK IS THE WALL CLOCK, deliberately, against this project's rule
that durations are monotonic. That rule is about MEASURING; a timestamp
here is one a person compares with their own memory of what they were
doing, which is the case the rule names as wall clock's own.
"""

import time

# Newest last. Read by the dialog, which shows it newest first.
SAID = []

# Anything session-scoped wants a bound. An afternoon of live update
# speaks thousands of times, and nobody reads past the newest few
# hundred, so the oldest fall off the end rather than accumulating
# where nobody would think to look for a leak.
CEILING = 500


def record(kind, text, answer=""):
  """Keep one thing the plugin said.

  Args:
    kind: "notice" for the message bar, "warning" or "problem" for a
      modal that only informs, "question" for one that asks.
    text: exactly the words the user met, not a paraphrase. Runs of
      whitespace are collapsed so a sentence wrapped across source
      lines reads as one line in the tab.
    answer: what the user said back, for a question; "" otherwise.

  Returns:
    The entry, as a dict, so a caller that wants to assert on what it
    recorded need not go looking for it.
  """
  entry = {
    "at": time.strftime("%H:%M:%S"),
    "kind": kind,
    "text": " ".join(str(text).split()),
    "answer": answer,
  }
  SAID.append(entry)
  if len(SAID) > CEILING:
    del SAID[:len(SAID) - CEILING]
  return entry


def clear():
  """Empty the log at the user's asking.

  Returns:
    None. The list is emptied IN PLACE rather than rebound, because
    the dialog holds a reference to it -- rebinding here would leave
    the tab reading a list nothing writes to any more, which is the
    watched-attribute-that-is-a-view trap this project has already
    paid for once.
  """
  del SAID[:]
