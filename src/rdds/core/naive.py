"""Brute-force reference implementation on an integer grid.

This is the correctness oracle for the whole project: a board of unit
columns where every operation is a plain scan. O(board_width) per
operation, obviously correct — the property tests check the RDDS against
it on thousands of random games.

Integer coordinates only (the RDDS itself works with arbitrary numbers).
"""

from __future__ import annotations

from collections.abc import Iterable

from .geometry import Gap, Rect, Segment


class NaiveBoard:
    """Grid-based reference for greedy rectangle dropping."""

    def __init__(self, board_width: int, rects: Iterable[Rect] = ()) -> None:
        if board_width <= 0:
            raise ValueError(f"board_width must be positive, got {board_width}")
        self.board_width = board_width
        self.columns: list[int] = [0] * board_width
        for r in rects:
            for i in range(int(r.x), int(r.x1)):
                self.columns[i] = max(self.columns[i], int(r.top))

    def landing(self, width: int, x: int) -> int:
        """Height at which a piece of ``width`` dropped at ``x`` comes to rest."""
        return max(self.columns[x : x + width])

    def insert(self, width: int, height: int, x: int) -> int:
        """Drop a piece; returns the landing height."""
        rest = self.landing(width, x)
        self.columns[x : x + width] = [rest + height] * width
        return rest

    def query(self, width: int) -> tuple[int, int]:
        """Lowest landing height for a piece of ``width`` and its leftmost x."""
        best_h = self.landing(width, 0)
        best_x = 0
        for x in range(1, self.board_width - width + 1):
            h = self.landing(width, x)
            if h < best_h:
                best_h, best_x = h, x
        return best_h, best_x

    def widest_gap(self, h: int) -> Gap | None:
        """Widest maximal interval where the skyline is at or below ``h``."""
        best: Gap | None = None
        x = 0
        while x < self.board_width:
            if self.columns[x] <= h:
                start = x
                while x < self.board_width and self.columns[x] <= h:
                    x += 1
                if best is None or x - start > best.width:
                    best = Gap(x - start, start, x)
            else:
                x += 1
        return best

    def segments(self) -> list[Segment]:
        """The current skyline as a normalized segment list."""
        out: list[Segment] = []
        start = 0
        for i in range(1, self.board_width + 1):
            if i == self.board_width or self.columns[i] != self.columns[start]:
                out.append(Segment(start, i, self.columns[start]))
                start = i
        return out
