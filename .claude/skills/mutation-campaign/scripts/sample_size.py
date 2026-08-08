#!/usr/bin/env python3
"""How many mutants a mutation-score claim actually needs.

    python3 sample_size.py [target]        # target defaults to 0.70

Prints, for a range of sample sizes, how many kills are required to
defend the target with 95% confidence, and -- the part people miss --
how often a suite of a given true quality will actually manage it.

The second question is the important one. A suite that genuinely
catches 85% of mutants fails to certify on a batch of thirty about
two-thirds of the time, because 27/30 is a demanding result even when
the underlying rate is good. Small batches steer well and conclude
badly.

Uses the exact Clopper-Pearson lower limit of the two-sided 95%
interval: the conservative convention, chosen deliberately, since a
one-sided bound reads several points higher on the same data.
"""
import math
import sys


def clopper_pearson_lower(killed, total, alpha=0.025):
  """The lower limit of the two-sided 95% interval, by bisection.

  Args:
    killed: mutants caught.
    total: mutants tried, equivalents already excluded.
    alpha: tail mass below the bound; 0.025 gives the two-sided 95%
      interval's lower limit.

  Returns:
    The largest rate for which this many kills would be unsurprising.
  """
  if total == 0 or killed == 0:
    return 0.0
  low, high = 0.0, 1.0
  for _ in range(200):
    mid = (low + high) / 2
    tail = sum(math.comb(total, i) * mid ** i * (1 - mid) ** (total - i)
               for i in range(killed, total + 1))
    if tail > alpha:
      high = mid
    else:
      low = mid
  return (low + high) / 2


def kills_needed(total, target):
  """Fewest kills out of `total` whose bound clears `target`."""
  for killed in range(total + 1):
    if clopper_pearson_lower(killed, total) > target:
      return killed
  return None


def chance_of_certifying(total, target, true_rate):
  """P(a suite this good produces a certifying result at this n)."""
  needed = kills_needed(total, target)
  if needed is None:
    return 0.0
  return sum(math.comb(total, i) * true_rate ** i
             * (1 - true_rate) ** (total - i)
             for i in range(needed, total + 1))


def main():
  target = float(sys.argv[1]) if len(sys.argv) > 1 else 0.70
  truths = (0.75, 0.80, 0.85, 0.90)
  print(f"to defend a true kill rate of at least {target:.0%}:\n")
  print("     n   kills   observed | chance of getting there if truly")
  print("                          | " + "  ".join(f"{t:>6.0%}" for t in truths))
  for n in (20, 30, 60, 100, 150, 200, 300):
    needed = kills_needed(n, target)
    if needed is None:
      continue
    odds = "  ".join(f"{chance_of_certifying(n, target, t):>6.0%}"
                     for t in truths)
    print(f"  {n:>4}   {needed:>5}   {needed / n:>7.1%} | {odds}")
  print("\nRaising the true rate improves the software; raising n only "
        "sharpens\nthe measurement. No sample size certifies a suite "
        "that is genuinely\nbelow the target -- it just establishes "
        "the shortfall more precisely.")


if __name__ == "__main__":
  main()
