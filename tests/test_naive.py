"""Sanity checks for the grid oracle itself, on hand-verified boards."""

from __future__ import annotations

from rdds import Gap, NaiveBoard, Rect, Segment


def test_flat_board() -> None:
    board = NaiveBoard(10)
    assert board.query(4) == (0, 0)
    assert board.widest_gap(0) == Gap(10, 0, 10)
    assert board.landing(3, 4) == 0


def test_single_tower() -> None:
    board = NaiveBoard(10, [Rect(4, 0, 2, 5)])
    assert board.segments() == [Segment(0, 4, 0), Segment(4, 6, 5), Segment(6, 10, 0)]
    assert board.query(4) == (0, 0)  # fits left of the tower
    assert board.query(5) == (5, 0)  # must rest on top
    assert board.widest_gap(4) == Gap(4, 0, 4)
    assert board.widest_gap(5) == Gap(10, 0, 10)


def test_insert_stacks() -> None:
    board = NaiveBoard(8)
    assert board.insert(3, 2, 2) == 0
    assert board.insert(3, 2, 2) == 2
    assert board.insert(8, 1, 0) == 4
    assert board.segments() == [Segment(0, 8, 5)]


def test_widest_gap_below_everything() -> None:
    board = NaiveBoard(6, [Rect(0, 0, 6, 3)])
    assert board.widest_gap(2) is None
    assert board.widest_gap(3) == Gap(6, 0, 6)
