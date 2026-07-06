"""Headless smoke test for the demo and the static renderer."""

from __future__ import annotations

import subprocess
import sys


def test_headless_demo_runs(tmp_path) -> None:
    out = tmp_path / "board.png"
    result = subprocess.run(
        [
            sys.executable, "-m", "rdds.demo.tetris",
            "--headless", "--width", "30", "--pieces", "8", "--out", str(out),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists() and out.stat().st_size > 0
