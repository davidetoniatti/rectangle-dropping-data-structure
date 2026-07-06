# Paper → code map

How each definition, lemma and theorem of Section 4 of Dallant & Iacono,
*"How fast can we play Tetris greedily with rectangular pieces?"*
([arXiv:2202.10771](https://arxiv.org/abs/2202.10771)) maps onto this
implementation, including the few places where the code deviates (same
asymptotics, simpler mechanics).

## Definition 14 — skyline, left/right staircases

> *The skyline of S is the union of the top, left and right boundaries of the
> region obtained by extending the bottom of every rectangle to the x-axis.
> The left (right) staircase consists of the parts of the skyline visible from
> (−∞, 0) (respectively (+∞, 0)).*

| Paper | Code |
|---|---|
| skyline | `list[Segment]` — maximal horizontal segments covering `[0, board_width]` (`rdds/core/geometry.py`) |
| vertex view | `RDDS.skyline_vertices()` reproduces the paper's step-polyline view |
| left/right staircase | per-chunk prefix/suffix maxima records, `Chunk._left_records` / `Chunk._right_records` (`rdds/core/chunk.py`) |

**Deviation:** the paper (and the original thesis code) works with vertex
lists; this implementation uses segments. The two are equivalent (each segment
is a pair of vertices), but segments make the insert splice mechanical.
Staircases are stored per chunk, not globally — Theorem 17 only ever queries a
staircase *of a chunk*.

## Lemma 15 — skyline construction in O(n log n)

> *Given a set of n independent axis-aligned rectangles, one can construct its
> skyline, left and right staircase in O(n log n) time.*

`skyline_of()` in `rdds/core/skyline.py`: a plane sweep over the 2n
rectangle-boundary events with a sorted multiset of active tops. Grouped
processing of coincident event x-coordinates yields a normalized (merged)
segment list directly.

## Lemma 16 — widest droppable rectangle at or below height h

> *Given the skyline of a set of n rectangles, we can construct a data
> structure in O(n log n) with which, given some height h, we can return the
> width and position of the widest rectangle which can be dropped at or below
> height h in O(log n) time.*

`Chunk._build_gap_table()` in `rdds/core/chunk.py`:

1. For every segment, the widest interval around it where the skyline stays at
   or below its height — the paper computes the nearest strictly-higher
   neighbor on each side with an augmented self-balancing BST during the
   sweep; since chunks here are immutable between rebuilds, a **monotonic
   stack** gives the same walls in O(s) instead of O(s log s).
2. Per distinct height, keep the widest such interval ("widest rectangle
   touching a vertex at height h").
3. Prefix-max over increasing heights ("widest at height h′ for all h′ ≤ h").
4. `Chunk.widest_gap_at(h)` does the floor lookup with `bisect` over the
   sorted height array (the paper's BST — again equivalent because the table
   is immutable).

## Theorem 17 — the chunked structure

> *Chunks of at most 2(n log n)^(1/2) vertices, any two consecutive chunks
> summing to at least (n log n)^(1/2); updates in O(n^(1/2) log^(3/2) n),
> queries in O(n^(1/2) log^(1/2) n).*

All in `rdds/core/structure.py`:

| Paper mechanism | Code |
|---|---|
| chunk list L | `RDDS.chunks`, boundaries in `RDDS._starts` |
| per-chunk Lemma 16 structure, staircases, max height | `Chunk` |
| query: max over per-chunk answers | first loop of `RDDS.widest_gap()` |
| query: p1/p2 sliding-window over cross-chunk rectangles | second loop of `RDDS.widest_gap()` — for each *blocking* chunk (max height > h) it closes the corridor opened by the previous blocker, using `corridor_end`/`corridor_start` (binary search in the staircase records, exactly the paper's "binary searching through the right staircase of p1 and the left staircase of p2") |
| vertical lines at x = 0 and x = w added to the skyline | the corridor scan starts at 0 and closes at `board_width` — the board walls play the role of the paper's added segments |
| update: find covered chunks, landing height via staircases/max | `RDDS.landing_height()` — partial chunks are scanned in O(s) rather than binary-searched in O(log s); s = Θ((n log n)^(1/2)) keeps the update bound unchanged |
| update: rebuild p1 including R, p2 excluding covered parts | the splice in `RDDS.insert()` (trim + new top segment) |
| split > 2(n log n)^(1/2) in approximate halves; merge consecutive < (n log n)^(1/2) | `RDDS._replace()` |

**Deviation:** the paper fixes the chunk-size parameter for a given n; as
inserts change n, this implementation keeps the target from the last full
rebuild and re-cuts the whole skyline (O(n log n)) whenever the segment count
drifts by a factor 2 — amortized O(log n) per insert, absorbed by the
O(n^(1/2) log^(3/2) n) update bound.

## Theorem 18 — the full RDDS

> *Keep track of all the O(n) possible heights a rectangle could be dropped
> at; binary search through them for the lowest height which will accommodate
> a rectangle of that width. O(n log n) construction, queries and updates in
> O(n^(1/2) log^(3/2) n).*

`RDDS.heights` is a `SortedSet` holding every skyline height ever observed
(reset to the exact current set at each full rebuild); `RDDS.query()` performs
the binary search, calling `widest_gap()` per step. The set is a *superset* of
the current skyline heights — stale entries are harmless because the
gap-width-at-height function is a step function that only changes at real
skyline heights, and monotone in h, so the minimal feasible candidate equals
the minimal feasible real height.

## Empirical check

`benchmarks/bench.py` fits the measured log-log slope of the per-operation
time; `docs/benchmark.png` shows the RDDS insert tracking the
c·√(n log n)·log n guide (slope ≈ 0.52 at n up to ~17k) against the exactly
linear naive scan.
