"""Self-contained browser player for recorded games.

``build_player`` embeds a JSON recording (see
:class:`rdds.core.RecordingObserver`) into the bundled HTML template,
producing a single standalone file: no dependencies, no network, works from
disk or any static host.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

_PLACEHOLDER = "__RECORDING_JSON__"


def build_player(recording: dict[str, Any]) -> str:
    """Return a complete HTML document with ``recording`` embedded."""
    payload = json.dumps(recording, separators=(",", ":"))
    if "</script" in payload.lower():  # defense in depth; never true for our data
        raise ValueError("recording cannot be embedded safely")
    template = files("rdds.web").joinpath("template.html").read_text(encoding="utf-8")
    body = template.replace(_PLACEHOLDER, payload)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    )


def write_player(recording: dict[str, Any], path: str | Path) -> Path:
    """Build the player and write it to ``path``; returns the absolute path."""
    out = Path(path)
    out.write_text(build_player(recording), encoding="utf-8")
    return out.absolute()
