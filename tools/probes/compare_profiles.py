"""Diff two profiles by CALL COUNT, which is the number that carries.

Seconds are swamped by profiler overhead and by whatever else the
machine is doing; on 2026-08-16 the self-time ratio understated a
threefold regression as 1.2x while the counts carried it exactly. So
this ranks by how many MORE times a function was called, and lists
what is new in the second profile that was absent from the first.

Argv: <before.prof> <after.prof>
"""
import pstats
import sys


def counts(path):
  """{(file, function): primitive call count} from one profile.

  KEYED WITHOUT THE LINE NUMBER, and the first version of this was
  not. Between two revisions of a file that gained six hundred lines
  every function moves, so a line-keyed diff reports each one as new
  in the second profile and gone from the first, at identical counts,
  and buries a real difference under hundreds of false ones. The
  tell was that every "increase" had a matching "disappearance" of
  the same name and the same number.
  """
  stats = pstats.Stats(path)
  out = {}
  for (file, _line, fn), (calls, *_rest) in stats.stats.items():
    short = file.rsplit("/", 1)[-1] if file != "~" else "builtin"
    out[(short, fn)] = out.get((short, fn), 0) + calls
  return out


def name(func):
  """A profile key as one readable string: file then function."""
  return f"{func[0]} {func[1]}"


def main():
  """Print the diff: totals, the biggest growers, what is new or gone."""
  before_path, after_path = sys.argv[1], sys.argv[2]
  before, after = counts(before_path), counts(after_path)
  print(f"before: {before_path}  ({sum(before.values()):,} calls)")
  print(f"after:  {after_path}  ({sum(after.values()):,} calls)")
  print(f"delta:  {sum(after.values()) - sum(before.values()):+,} calls\n")

  grew = []
  for func, n in after.items():
    was = before.get(func, 0)
    if n - was > 0:
      grew.append((n - was, was, n, func))
  grew.sort(reverse=True)

  print("BIGGEST INCREASES IN CALL COUNT")
  print(f"{'delta':>10}  {'before':>10}  {'after':>10}  where")
  for delta, was, now, func in grew[:25]:
    print(f"{delta:>10,}  {was:>10,}  {now:>10,}  {name(func)}")

  fresh = [(n, f) for f, n in after.items() if f not in before and n > 20]
  fresh.sort(reverse=True)
  if fresh:
    print("\nCALLED IN THE SECOND PROFILE AND NOT IN THE FIRST")
    for n, func in fresh[:15]:
      print(f"{n:>10,}  {name(func)}")

  gone = [(n, f) for f, n in before.items() if f not in after and n > 20]
  gone.sort(reverse=True)
  if gone:
    print("\nCALLED IN THE FIRST AND NOT IN THE SECOND "
          "(work that went away)")
    for n, func in gone[:10]:
      print(f"{n:>10,}  {name(func)}")


main()
