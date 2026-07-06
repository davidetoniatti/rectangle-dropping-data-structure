"""Skyline construction by plane sweep (paper, Lemma 15).

Every rectangle is first extended so that its bottom lies on the x-axis
(Definition 14); the skyline is the upper envelope of the extended set,
returned as a normalized segment list covering ``[0, board_width]``.
Runs in O(n log n).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from sortedcontainers import SortedList

from .geometry import Number, Rect, Segment


def skyline_of(rects: Iterable[Rect], board_width: Number) -> list[Segment]:
    """Build the skyline of ``rects`` over the board ``[0, board_width]``."""
    if board_width <= 0:
        raise ValueError(f"board_width must be positive, got {board_width}")

    events: defaultdict[Number, tuple[list[Number], list[Number]]] = defaultdict(
        lambda: ([], [])
    )
    for r in rects:
        if r.width <= 0 or r.height <= 0:
            raise ValueError(f"rectangle must have positive size: {r}")
        if r.x < 0 or r.x1 > board_width or r.y < 0:
            raise ValueError(f"rectangle out of board bounds [0, {board_width}]: {r}")
        events[r.x][0].append(r.top)
        events[r.x1][1].append(r.top)

    active: SortedList = SortedList()
    result: list[Segment] = []
    cur_x: Number = 0
    cur_h: Number = 0
    for x in sorted(events):
        adds, removals = events[x]
        for top in adds:
            active.add(top)
        for top in removals:
            active.remove(top)
        h: Number = active[-1] if active else 0
        if h != cur_h:
            if x > cur_x:
                result.append(Segment(cur_x, x, cur_h))
            cur_x, cur_h = x, h
    if cur_x < board_width:
        result.append(Segment(cur_x, board_width, cur_h))
    return result
