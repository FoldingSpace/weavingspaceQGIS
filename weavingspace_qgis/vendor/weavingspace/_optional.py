"""Placeholders for optional plotting dependencies.

The QGIS plugin build of weavingspace does not require matplotlib or
scipy: they are only used by the notebook-oriented plotting helpers.
When absent we substitute a proxy that supports attribute access (so
type annotations such as ``plt.Axes`` still evaluate) but raises
ImportError as soon as anything is actually called.
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
      "matplotlib (and topology splines need scipy); the QGIS plugin "
      "does not use them.")
