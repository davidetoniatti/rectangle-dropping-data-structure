"""The JSON recording must reconstruct the game state exactly."""

from __future__ import annotations

import json

from rdds import RDDS, RecordingObserver, Rect


def test_recording_reconstructs_final_state(tmp_path) -> None:
    rdds = RDDS(30, [Rect(0, 0, 9, 5)])
    recorder = RecordingObserver(rdds)
    for width, height in [(5, 2), (12, 3), (30, 1), (2, 6)]:
        _, x = rdds.query(width)
        rdds.insert(width, height, x)

    path = tmp_path / "game.json"
    recorder.save(path)
    data = json.loads(path.read_text())

    assert data["version"] == 1
    assert data["board_width"] == 30
    assert data["initial_pieces"] == [[0, 0, 9, 5]]
    kinds = {e["t"] for e in data["events"]}
    assert kinds == {"structure", "gap_probe", "height_probe", "query_answered", "piece_dropped"}

    # Replaying only the state-bearing events must yield the live final state.
    skyline = chunks = None
    pieces = [tuple(p) for p in data["initial_pieces"]]
    for e in data["events"]:
        if e["t"] == "structure":
            skyline, chunks = e["skyline"], e["chunks"]
        elif e["t"] == "piece_dropped":
            pieces.append(tuple(e["rect"]))
    assert skyline == [[s.x0, s.x1, s.y] for s in rdds.skyline()]
    assert chunks == [c.start for c in rdds.chunks]
    assert pieces == [(r.x, r.y, r.width, r.height) for r in rdds.placed]
