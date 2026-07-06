"""The RDDS against the grid oracle: full games, invariants, edge cases."""

from __future__ import annotations

from itertools import pairwise

import pytest
from hypothesis import given
from hypothesis import strategies as st

from conftest import games, scenes
from rdds import RDDS, NaiveBoard, Rect


def check_invariants(r: RDDS) -> None:
    segs = [s for c in r.chunks for s in c.segments]
    assert segs[0].x0 == 0
    assert segs[-1].x1 == r.board_width
    for a, b in pairwise(segs):
        assert a.x1 == b.x0
    for s in segs:
        assert s.x0 < s.x1
    for c in r.chunks:
        assert 1 <= len(c) <= 2 * r._target
    # Candidate heights must cover every current skyline height (Theorem 18).
    assert {s.y for s in segs} <= set(r.heights)


@given(games())
def test_greedy_game_matches_oracle(
    game: tuple[int, list[Rect], list[tuple[int, int, int]]],
) -> None:
    """Play every piece greedily where the RDDS says; the oracle must agree."""
    board_width, rects, pieces = game
    rdds = RDDS(board_width, rects)
    naive = NaiveBoard(board_width, rects)
    assert rdds.skyline() == naive.segments()
    for width, height, _ in pieces:
        h, x = rdds.query(width)
        oracle_h, _ = naive.query(width)
        assert h == oracle_h
        # The suggested drop position must actually achieve that height.
        assert naive.landing(width, x) == h
        assert rdds.insert(width, height, x) == naive.insert(width, height, x)
        assert rdds.skyline() == naive.segments()
        check_invariants(rdds)


@given(games())
def test_arbitrary_drops_match_oracle(
    game: tuple[int, list[Rect], list[tuple[int, int, int]]],
) -> None:
    """Drop pieces at arbitrary positions (the Theorem 17 update operation)."""
    board_width, rects, pieces = game
    rdds = RDDS(board_width, rects)
    naive = NaiveBoard(board_width, rects)
    for width, height, x in pieces:
        assert rdds.landing_height(width, x) == naive.landing(width, x)
        assert rdds.insert(width, height, x) == naive.insert(width, height, x)
        assert rdds.skyline() == naive.segments()
        check_invariants(rdds)


@given(scenes(), st.integers(-1, 20))
def test_widest_gap_matches_oracle(scene: tuple[int, list[Rect]], h: int) -> None:
    board_width, rects = scene
    rdds = RDDS(board_width, rects)
    naive = NaiveBoard(board_width, rects)
    gap = rdds.widest_gap(h)
    oracle = naive.widest_gap(h)
    if gap is None:
        assert oracle is None
        return
    assert oracle is not None
    assert gap.width == oracle.width
    # The interval must be real: within the board and at or below h throughout.
    assert 0 <= gap.x0 < gap.x1 <= board_width
    for s in rdds.skyline():
        if s.x1 > gap.x0 and s.x0 < gap.x1:
            assert s.y <= h


def test_thesis_demo_scene() -> None:
    """The prefilled scene from the original thesis demos, played to the end."""
    rects = [
        Rect(0, 0, 9, 5),
        Rect(5, 5, 2, 7),
        Rect(2, 5, 2, 3),
        Rect(8, 5, 5, 2),
        Rect(19, 0, 5, 10),
        Rect(24, 0, 3, 4),
        Rect(13, 0, 5, 4),
        Rect(13, 4, 3, 5),
        Rect(17, 4, 2, 5),
        Rect(9, 0, 4, 5),
        Rect(0, 5, 2, 2),
        Rect(27, 0, 1, 1),
        Rect(28, 0, 2, 4),
        Rect(30, 0, 4, 2),
        Rect(33, 2, 1, 3),
        Rect(29, 4, 1, 10),
        Rect(9, 7, 2, 3),
        Rect(24, 4, 2, 2),
    ]
    rdds = RDDS(34, rects)
    naive = NaiveBoard(34, rects)
    assert rdds.skyline() == naive.segments()
    for width, height in [(3, 3), (7, 2), (13, 3), (25, 3), (2, 7), (10, 2)]:
        h, x = rdds.query(width)
        assert h == naive.query(width)[0]
        assert rdds.insert(width, height, x) == naive.insert(width, height, x)
        assert rdds.skyline() == naive.segments()
        check_invariants(rdds)


def test_piece_covering_whole_board() -> None:
    rdds = RDDS(20, [Rect(3, 0, 4, 6)])
    assert rdds.insert(20, 2, 0) == 6
    assert rdds.skyline()[0].y == 8
    assert len(rdds.skyline()) == 1


def test_growth_triggers_rebuild() -> None:
    rdds = RDDS(1000)
    n0 = rdds._n0
    for i in range(200):
        rdds.insert(3, 1, (i * 5) % 995)
    assert rdds.n_segments > n0  # grew...
    check_invariants(rdds)
    naive = NaiveBoard(1000)
    for i in range(200):
        naive.insert(3, 1, (i * 5) % 995)
    assert rdds.skyline() == naive.segments()


def test_validation() -> None:
    rdds = RDDS(10)
    with pytest.raises(ValueError):
        rdds.query(0)
    with pytest.raises(ValueError):
        rdds.query(11)
    with pytest.raises(ValueError):
        rdds.insert(4, 1, 7)
    with pytest.raises(ValueError):
        rdds.insert(4, 0, 0)
    with pytest.raises(ValueError):
        rdds.insert(4, 1, -1)


def test_events_are_emitted() -> None:
    from rdds import PieceDropped, QueryAnswered, StructureChanged

    seen: list[object] = []
    rdds = RDDS(30, observer=seen.append)
    assert any(isinstance(e, StructureChanged) for e in seen)
    h, x = rdds.query(5)
    assert any(isinstance(e, QueryAnswered) for e in seen)
    rdds.insert(5, 2, x)
    dropped = [e for e in seen if isinstance(e, PieceDropped)]
    assert len(dropped) == 1
    assert dropped[0].rect == Rect(x, h, 5, 2)
