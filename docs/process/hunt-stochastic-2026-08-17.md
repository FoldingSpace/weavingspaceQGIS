# Stochastic hunt, 2026-08-17: what it saw before it was stopped

Kept because the hunt record says a reproduction worth rerunning
belongs here rather than in a temporary directory. NONE OF THIS IS
CONFIRMED: no claim below has been reproduced by an independent
route, which is this project's bar for calling something a defect.
The ordering is the one the record prescribes -- by how many
INDEPENDENT SEEDS produced the same shape, which last time put both
real findings on top and every fixture fault below.

171 sessions across the batches, 30 steps each.

## Invariant fire counts, so no axis reads as decorative

- `PAINTED` checked 23,240 times
- `RENDERKIND` checked 10,990 times
- `RAMPMATCH` checked 9,038 times
- `HASLAYER` checked 5,153 times
- `NOEXC` checked 4,823 times
- `GROUPCOUNT` checked 3,745 times
- `RECORDS` checked 3,745 times

## Break shapes, most independent seeds first

- **7 seed(s)** — RENDERKIND/table says Graduated layer carries QgsCategorizedSymbolRenderer
  seeds: [102, 106, 109, 133, 135, 138, 142]
- **3 seed(s)** — DRIVER/famspin raised
  seeds: [1, 4, 5]
- **3 seed(s)** — HASLAYER/a table element has no layer
  seeds: [222, 235, 252]
- **2 seed(s)** — RENDERKIND/table says Graduated layer carries QgsSingleSymbolRenderer
  seeds: [100, 114]
- **2 seed(s)** — HASLAYER/an element of the design has no layer
  seeds: [153, 156]

## What to do with this

The top shape -- a row saying Graduated over a layer carrying a
categorized renderer -- is the table lying about the map, which is
this software's characteristic failure and the shape of the defect
found on 2026-08-13. Seven seeds is well above the noise floor the
record describes, so it is the one to reproduce first. The driver
faults (`DRIVER/...`) are the hunt's own and are listed only so
nobody re-finds them.
