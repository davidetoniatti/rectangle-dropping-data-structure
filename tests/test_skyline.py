"""Skyline construction (Lemma 15) against the grid oracle."""

from __future__ import annotations

import pytest
from hypothesis import given

from conftest import scenes
from rdds import NaiveBoard, Rect, Segment, skyline_of


def test_empty_board_is_one_ground_segment() -> None:
    assert skyline_of([], 10) == [Segment(0, 10, 0)]


def test_single_rectangle() -> None:
    assert skyline_of([Rect(2, 0, 3, 4)], 10) == [
        Segment(0, 2, 0),
        Segment(2, 5, 4),
        Segment(5, 10, 0),
    ]


def test_floating_rectangle_is_bottom_extended() -> None:
    # Definition 14: bottoms are extended to the x-axis first.
    assert skyline_of([Rect(2, 5, 3, 4)], 10) == [
        Segment(0, 2, 0),
        Segment(2, 5, 9),
        Segment(5, 10, 0),
    ]


def test_adjacent_rectangles_with_equal_top_merge() -> None:
    assert skyline_of([Rect(0, 0, 5, 3), Rect(5, 0, 5, 3)], 10) == [Segment(0, 10, 3)]


def test_rejects_out_of_board_rectangles() -> None:
    with pytest.raises(ValueError):
        skyline_of([Rect(8, 0, 5, 1)], 10)
    with pytest.raises(ValueError):
        skyline_of([Rect(0, 0, 0, 1)], 10)


@given(scenes())
def test_skyline_matches_grid_oracle(scene: tuple[int, list[Rect]]) -> None:
    board_width, rects = scene
    assert skyline_of(rects, board_width) == NaiveBoard(board_width, rects).segments()
