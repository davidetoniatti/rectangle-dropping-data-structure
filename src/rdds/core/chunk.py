"""One contiguous piece of the skyline with the Lemma-16 machinery.

A chunk owns an immutable run of skyline segments and precomputes:

* the *gap table* (Lemma 16): for every distinct segment height ``h`` in the
  chunk, the widest interval around a height-``h`` segment where the skyline
  stays at or below ``h`` (clipped to the chunk); entries are prefix-maxed
  over increasing heights so a floor lookup answers "widest rectangle
  droppable at or below ``h`` inside this chunk" in O(log s);
* the *staircase records* (Definition 14): the suffix/prefix maxima of the
  run, used by the cross-chunk corridor scan of Theorem 17.

The paper computes the gap table with an augmented self-balancing BST while
sweeping; since chunks here are immutable between rebuilds we use a
monotonic stack instead — same result, O(s) instead of O(s log s) for the
nearest-strictly-higher-neighbor pass.
"""

from __future__ import annotations

from bisect import bisect_right

from .geometry import Gap, Number, Segment


class Chunk:
    __slots__ = (
        "_gap_entries",
        "_gap_heights",
        "_left_records",
        "_right_records",
        "end",
        "max_y",
        "segments",
        "start",
    )

    def __init__(self, segments: tuple[Segment, ...]) -> None:
        if not segments:
            raise ValueError("a chunk cannot be empty")
        self.segments = segments
        self.start: Number = segments[0].x0
        self.end: Number = segments[-1].x1
        self.max_y: Number = max(s.y for s in segments)
        self._build_gap_table()
        self._build_staircases()

    def __len__(self) -> int:
        return len(self.segments)

    def _build_gap_table(self) -> None:
        segs = self.segments
        n = len(segs)
        # Nearest strictly-higher segment on each side (monotonic stacks).
        left_wall: list[Number] = [self.start] * n
        stack: list[int] = []
        for i, s in enumerate(segs):
            while stack and segs[stack[-1]].y <= s.y:
                stack.pop()
            left_wall[i] = segs[stack[-1]].x1 if stack else self.start
            stack.append(i)
        right_wall: list[Number] = [self.end] * n
        stack.clear()
        for i in range(n - 1, -1, -1):
            while stack and segs[stack[-1]].y <= segs[i].y:
                stack.pop()
            right_wall[i] = segs[stack[-1]].x0 if stack else self.end
            stack.append(i)

        best: dict[Number, Gap] = {}
        for i, s in enumerate(segs):
            gap = Gap(right_wall[i] - left_wall[i], left_wall[i], right_wall[i])
            cur = best.get(s.y)
            if cur is None or gap.width > cur.width:
                best[s.y] = gap

        # Prefix-max over increasing heights (Lemma 16, last step).
        heights = sorted(best)
        entries: list[Gap] = []
        for h in heights:
            gap = best[h]
            if entries and entries[-1].width > gap.width:
                gap = entries[-1]
            entries.append(gap)
        self._gap_heights = heights
        self._gap_entries = entries

    def _build_staircases(self) -> None:
        # Suffix maxima, collected right-to-left: ascending y, descending x.
        right_records: list[tuple[Number, Number]] = []
        top: Number = float("-inf")
        for s in reversed(self.segments):
            if s.y > top:
                right_records.append((s.y, s.x1))
                top = s.y
        self._right_records = right_records
        # Prefix maxima, collected left-to-right: ascending y, ascending x.
        left_records: list[tuple[Number, Number]] = []
        top = float("-inf")
        for s in self.segments:
            if s.y > top:
                left_records.append((s.y, s.x0))
                top = s.y
        self._left_records = left_records

    def widest_gap_at(self, h: Number) -> Gap | None:
        """Widest interval with skyline <= ``h`` around a segment of this chunk.

        Clipped to the chunk extent; ``None`` if every segment is above ``h``.
        """
        i = bisect_right(self._gap_heights, h) - 1
        if i < 0:
            return None
        return self._gap_entries[i]

    def corridor_start(self, h: Number) -> Number:
        """Left wall of the region with skyline <= ``h`` touching the right edge.

        Returns ``self.start`` when the whole chunk is at or below ``h``.
        """
        recs = self._right_records
        i = bisect_right(recs, h, key=lambda t: t[0])
        if i == len(recs):
            return self.start
        return recs[i][1]

    def corridor_end(self, h: Number) -> Number:
        """Right wall of the region with skyline <= ``h`` touching the left edge.

        Returns ``self.end`` when the whole chunk is at or below ``h``.
        """
        recs = self._left_records
        i = bisect_right(recs, h, key=lambda t: t[0])
        if i == len(recs):
            return self.end
        return recs[i][1]
