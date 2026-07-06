"""The browser player build: template packaging and the --web demo flag."""

from __future__ import annotations

import subprocess
import sys

from rdds import RDDS, RecordingObserver
from rdds.web import build_player


def test_build_player_embeds_recording() -> None:
    rdds = RDDS(20)
    recorder = RecordingObserver(rdds)
    _, x = rdds.query(4)
    rdds.insert(4, 2, x)
    html = build_player(recorder.to_dict())
    assert html.startswith("<!doctype html>")
    assert '"board_width":20' in html
    assert "__RECORDING_JSON__" not in html
    assert '"t":"piece_dropped"' in html


def test_demo_web_flag(tmp_path) -> None:
    out = tmp_path / "player.html"
    result = subprocess.run(
        [
            sys.executable, "-m", "rdds.demo.tetris",
            "--web", str(out), "--no-open", "--width", "30", "--pieces", "5",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists() and out.stat().st_size > 10_000
