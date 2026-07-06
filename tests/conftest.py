"""Shared Hypothesis strategies: random boards, scenes and piece sequences."""

from __future__ import annotations

import os

from hypothesis import settings
from hypothesis import strategies as st

from rdds import Rect

settings.register_profile("default", max_examples=200, deadline=None)
settings.register_profile("heavy", max_examples=2000, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


@st.composite
def scenes(draw: st.DrawFn) -> tuple[int, list[Rect]]:
    """A board width and a list of rectangles lying inside it."""
    board_width = draw(st.integers(2, 48))
    n = draw(st.integers(0, 12))
    rects = []
    for _ in range(n):
        w = draw(st.integers(1, board_width))
        x = draw(st.integers(0, board_width - w))
        y = draw(st.integers(0, 8))
        h = draw(st.integers(1, 8))
        rects.append(Rect(x, y, w, h))
    return board_width, rects


@st.composite
def games(draw: st.DrawFn) -> tuple[int, list[Rect], list[tuple[int, int, int]]]:
    """A scene plus a sequence of pieces (width, height, drop x) to play."""
    board_width, rects = draw(scenes())
    n_pieces = draw(st.integers(1, 25))
    pieces = []
    for _ in range(n_pieces):
        w = draw(st.integers(1, board_width))
        h = draw(st.integers(1, 6))
        x = draw(st.integers(0, board_width - w))
        pieces.append((w, h, x))
    return board_width, rects, pieces
