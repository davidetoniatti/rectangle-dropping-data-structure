"""The Rectangle Dropping Data Structure (paper, Theorems 17 and 18).

The skyline is kept in O((n / log n)^(1/2)) chunks of at most
2 (n log n)^(1/2) segments each. Queries combine per-chunk gap tables
(Lemma 16) with a sliding scan over cross-chunk *corridors* — maximal
regions at or below the query height bounded by walls in two different
chunks (the p1/p2 staircase step in the proof of Theorem 17).

Costs, matching Theorem 18: ``widest_gap`` O(n^(1/2) log^(1/2) n),
``query`` and ``insert`` O(n^(1/2) log^(3/2) n), construction O(n log n).
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Iterable
from math import ceil, log2, sqrt
from typing import Any

from sortedcontainers import SortedSet

from .chunk import Chunk
from .events import (
    Event,
    GapProbe,
    HeightProbe,
    Observer,
    PieceDropped,
    QueryAnswered,
    StructureChanged,
)
from .geometry import Gap, Number, Rect, Segment, normalize
from .skyline import skyline_of


class RDDS:
    """Maintains the skyline of dropped rectangles between walls at 0 and board_width."""

    def __init__(
        self,
        board_width: Number,
        rects: Iterable[Rect] = (),
        observer: Observer | None = None,
    ) -> None:
        self.board_width = board_width
        self.observer = observer
        self.placed: list[Rect] = list(rects)
        self._rebuild(skyline_of(self.placed, board_width))
        self._emit(StructureChanged("init"))

    # ------------------------------------------------------------------ build

    def _emit(self, event: Event) -> None:
        if self.observer is not None:
            self.observer(event)

    def _rebuild(self, segments: list[Segment]) -> None:
        """Cut a fresh segment list into chunks of the ideal size (Theorem 17)."""
        n = len(segments)
        self._n0 = n
        self._target = max(2, ceil(sqrt(n * log2(max(n, 2)))))
        step = self._target
        self.chunks: list[Chunk] = [
            Chunk(tuple(segments[i : i + step])) for i in range(0, n, step)
        ]
        self._starts: list[Number] = [c.start for c in self.chunks]
        self.heights: Any = SortedSet(s.y for s in segments)

    @property
    def n_segments(self) -> int:
        return sum(len(c) for c in self.chunks)

    def skyline(self) -> list[Segment]:
        """The current skyline as a normalized segment list."""
        return normalize([s for c in self.chunks for s in c.segments])

    def skyline_vertices(self) -> list[tuple[Number, Number]]:
        """The skyline as a step polyline (the paper's vertex view)."""
        out: list[tuple[Number, Number]] = []
        for s in self.skyline():
            out.append((s.x0, s.y))
            out.append((s.x1, s.y))
        return out

    # ----------------------------------------------------------------- queries

    def widest_gap(self, h: Number) -> Gap | None:
        """Widest rectangle droppable at or below height ``h`` (Theorem 17 query).

        Returns ``None`` when the whole skyline lies strictly above ``h``.
        """
        best: Gap | None = None
        for i, chunk in enumerate(self.chunks):
            gap = chunk.widest_gap_at(h)
            if gap is not None:
                self._emit(GapProbe("chunk", h, gap, i))
                if best is None or gap.width > best.width:
                    best = gap
        # Corridors between consecutive blocking chunks (and the board walls).
        cur_start: Number = 0
        for chunk in self.chunks:
            if chunk.max_y > h:
                end = chunk.corridor_end(h)
                if end > cur_start:
                    gap = Gap(end - cur_start, cur_start, end)
                    self._emit(GapProbe("corridor", h, gap))
                    if best is None or gap.width > best.width:
                        best = gap
                cur_start = chunk.corridor_start(h)
        if self.board_width > cur_start:
            gap = Gap(self.board_width - cur_start, cur_start, self.board_width)
            self._emit(GapProbe("corridor", h, gap))
            if best is None or gap.width > best.width:
                best = gap
        return best

    def query(self, width: Number) -> tuple[Number, Number]:
        """Lowest height where a piece of ``width`` can rest, and a drop x (Theorem 18).

        Binary search over the candidate heights; dropping the piece at the
        returned x makes it land exactly at the returned height.
        """
        if width <= 0 or width > self.board_width:
            raise ValueError(f"width must be in (0, {self.board_width}], got {width}")
        lo, hi = 0, len(self.heights) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            h = self.heights[mid]
            gap = self.widest_gap(h)
            self._emit(HeightProbe(h, gap))
            if gap is not None and gap.width >= width:
                hi = mid
            else:
                lo = mid + 1
        h = self.heights[lo]
        gap = self.widest_gap(h)
        if gap is None or gap.width < width:
            raise RuntimeError("candidate-height invariant violated")  # pragma: no cover
        self._emit(QueryAnswered(width, h, gap.x0))
        return h, gap.x0

    def landing_height(self, width: Number, x: Number) -> Number:
        """Height at which a piece of ``width`` dropped at ``x`` comes to rest."""
        self._check_piece(width, x)
        x0, x1 = x, x + width
        p1 = bisect_right(self._starts, x0) - 1
        p2 = bisect_left(self._starts, x1) - 1
        if p1 == p2:
            return max(
                s.y for s in self.chunks[p1].segments if s.x1 > x0 and s.x0 < x1
            )
        best: Number = max(s.y for s in self.chunks[p1].segments if s.x1 > x0)
        for i in range(p1 + 1, p2):
            best = max(best, self.chunks[i].max_y)
        return max(best, max(s.y for s in self.chunks[p2].segments if s.x0 < x1))

    # ----------------------------------------------------------------- updates

    def insert(self, width: Number, height: Number, x: Number) -> Number:
        """Drop a ``width`` x ``height`` piece at ``x``; returns the landing height."""
        self._check_piece(width, x)
        if height <= 0:
            raise ValueError(f"height must be positive, got {height}")
        rest = self.landing_height(width, x)
        top = rest + height
        self.placed.append(Rect(x, rest, width, height))
        self._emit(PieceDropped(self.placed[-1]))

        x0, x1 = x, x + width
        p1 = bisect_right(self._starts, x0) - 1
        p2 = bisect_left(self._starts, x1) - 1
        left_run: list[Segment] = []
        for s in self.chunks[p1].segments:
            if s.x1 <= x0:
                left_run.append(s)
            elif s.x0 < x0:
                left_run.append(Segment(s.x0, x0, s.y))
        left_run.append(Segment(x0, x1, top))
        right_run: list[Segment] = []
        for s in self.chunks[p2].segments:
            if s.x0 >= x1:
                right_run.append(s)
            elif s.x1 > x1:
                right_run.append(Segment(x1, s.x1, s.y))
        self._replace(p1, p2, [left_run, right_run])
        self.heights.add(top)

        n = self.n_segments
        if n > 2 * self._n0 or 2 * n < self._n0:
            self._rebuild(self.skyline())
            self._emit(StructureChanged("rebuild"))
        else:
            self._emit(StructureChanged("insert"))
        return rest

    def _replace(self, p1: int, p2: int, runs: list[list[Segment]]) -> None:
        """Replace chunks p1..p2 with ``runs``, restoring the size bounds of Thm 17."""
        merged: list[list[Segment]] = []
        for run in runs:
            if not run:
                continue
            if merged and len(merged[-1]) + len(run) < self._target:
                merged[-1].extend(run)
            else:
                merged.append(run)
        # Still undersized: absorb a neighbouring chunk (Theorem 17 merge rule).
        if p1 > 0 and len(merged[0]) + len(self.chunks[p1 - 1]) < self._target:
            merged[0][:0] = self.chunks[p1 - 1].segments
            p1 -= 1
        if p2 < len(self.chunks) - 1 and len(merged[-1]) + len(self.chunks[p2 + 1]) < self._target:
            merged[-1].extend(self.chunks[p2 + 1].segments)
            p2 += 1
        # Oversized: divide in approximate halves (Theorem 17 split rule).
        final: list[list[Segment]] = []
        for run in merged:
            while len(run) > 2 * self._target:
                half = len(run) // 2
                final.append(run[:half])
                run = run[half:]
            final.append(run)
        self.chunks[p1 : p2 + 1] = [Chunk(tuple(run)) for run in final]
        self._starts = [c.start for c in self.chunks]

    def _check_piece(self, width: Number, x: Number) -> None:
        if width <= 0:
            raise ValueError(f"width must be positive, got {width}")
        if x < 0 or x + width > self.board_width:
            raise ValueError(
                f"piece [{x}, {x + width}] outside board [0, {self.board_width}]"
            )
