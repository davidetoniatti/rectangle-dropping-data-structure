"""Basic geometric types shared by the whole package.

The skyline (paper, Definition 14) is represented as an ordered list of
horizontal :class:`Segment` objects covering the board ``[0, board_width]``.
This replaces the vertex-pair representation used in early versions: a
segment list cannot express degenerate polylines, which removes a whole
class of splicing bugs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

Number = int | float


@dataclass(frozen=True, slots=True)
class Segment:
    """A horizontal piece of the skyline: height ``y`` over ``[x0, x1)``."""

    x0: Number
    x1: Number
    y: Number

    @property
    def width(self) -> Number:
        return self.x1 - self.x0


@dataclass(frozen=True, slots=True)
class Rect:
    """An axis-aligned rectangle ``[x, x + width] x [y, y + height]``."""

    x: Number
    y: Number
    width: Number
    height: Number

    @property
    def x1(self) -> Number:
        return self.x + self.width

    @property
    def top(self) -> Number:
        return self.y + self.height


class Gap(NamedTuple):
    """The widest rectangle droppable at or below some height (Lemma 16)."""

    width: Number
    x0: Number
    x1: Number


def normalize(segments: list[Segment]) -> list[Segment]:
    """Merge consecutive segments of equal height and drop empty ones."""
    out: list[Segment] = []
    for seg in segments:
        if seg.x1 <= seg.x0:
            continue
        if out and out[-1].y == seg.y and out[-1].x1 == seg.x0:
            out[-1] = Segment(out[-1].x0, seg.x1, seg.y)
        else:
            out.append(seg)
    return out
