"""Per-chunk gap table and staircase records (Lemma 16) against brute force."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from rdds import Chunk, Segment


@st.composite
def chunk_runs(draw: st.DrawFn) -> Chunk:
    start = draw(st.integers(0, 5))
    n = draw(st.integers(1, 20))
    segments = []
    x = start
    for _ in range(n):
        w = draw(st.integers(1, 6))
        y = draw(st.integers(0, 10))
        segments.append(Segment(x, x + w, y))
        x += w
    return Chunk(tuple(segments))


def brute_widest_gap(chunk: Chunk, h: int) -> int:
    """Widest maximal run of segments with y <= h, clipped to the chunk."""
    best = 0
    run = 0
    for s in chunk.segments:
        if s.y <= h:
            run += s.width
            best = max(best, run)
        else:
            run = 0
    return best


@given(chunk_runs(), st.integers(-1, 11))
def test_gap_table_matches_brute_force(chunk: Chunk, h: int) -> None:
    gap = chunk.widest_gap_at(h)
    expected = brute_widest_gap(chunk, h)
    if gap is None:
        assert expected == 0
        return
    assert gap.width == expected
    # The returned interval must be valid: inside the chunk, at or below h,
    # and bounded by real walls (or the chunk boundary).
    assert chunk.start <= gap.x0 < gap.x1 <= chunk.end
    for s in chunk.segments:
        if s.x1 > gap.x0 and s.x0 < gap.x1:
            assert s.y <= h


@given(chunk_runs(), st.integers(-1, 11))
def test_corridor_records_match_brute_force(chunk: Chunk, h: int) -> None:
    # corridor_start: left wall of the maximal suffix with y <= h.
    walls = [s for s in chunk.segments if s.y > h]
    expected_start = walls[-1].x1 if walls else chunk.start
    expected_end = walls[0].x0 if walls else chunk.end
    assert chunk.corridor_start(h) == expected_start
    assert chunk.corridor_end(h) == expected_end
