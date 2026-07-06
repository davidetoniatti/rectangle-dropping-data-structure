"""Smoke test for the event-driven animator on the Agg backend (no display)."""

from __future__ import annotations

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")


def test_animator_handles_a_full_game() -> None:
    from rdds import RDDS, Rect
    from rdds.viz import SkylineAnimator

    rdds = RDDS(30, [Rect(0, 0, 9, 5), Rect(12, 0, 4, 8)])
    animator = SkylineAnimator(rdds, speed=0)  # speed 0: no pauses, all code paths
    assert rdds.observer is animator
    for width, height in [(5, 2), (12, 3), (30, 1), (2, 6)]:
        h, x = rdds.query(width)
        assert rdds.insert(width, height, x) == h
    # Every placed rectangle got a persistent patch; skyline artists exist.
    assert len(animator.ax.patches) == len(rdds.placed)
    assert animator._skyline_artists
