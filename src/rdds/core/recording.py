"""Record the event stream as JSON for offline replay (e.g. the web player).

Events that reference structure state (``StructureChanged``) are recorded as
full snapshots — skyline segments and chunk boundaries — so a replayer can
reconstruct any moment of the game without running the data structure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import (
    Event,
    GapProbe,
    HeightProbe,
    PieceDropped,
    QueryAnswered,
    StructureChanged,
)
from .structure import RDDS


class RecordingObserver:
    """Observer that serializes events (with structure snapshots) for replay."""

    def __init__(self, rdds: RDDS) -> None:
        self.rdds = rdds
        self.initial_pieces = [[r.x, r.y, r.width, r.height] for r in rdds.placed]
        self.events: list[dict[str, Any]] = []
        rdds.observer = self
        # The "init" StructureChanged fired inside RDDS.__init__, before we
        # attached — record the starting structure ourselves.
        self._snapshot("init")

    def _snapshot(self, reason: str) -> None:
        self.events.append(
            {
                "t": "structure",
                "reason": reason,
                "skyline": [[s.x0, s.x1, s.y] for s in self.rdds.skyline()],
                "chunks": [c.start for c in self.rdds.chunks],
            }
        )

    def __call__(self, event: Event) -> None:
        if isinstance(event, GapProbe):
            self.events.append(
                {
                    "t": "gap_probe",
                    "source": event.source,
                    "h": event.h,
                    "gap": list(event.gap),
                    "chunk": event.chunk_index,
                }
            )
        elif isinstance(event, HeightProbe):
            self.events.append(
                {
                    "t": "height_probe",
                    "h": event.h,
                    "gap": list(event.gap) if event.gap is not None else None,
                }
            )
        elif isinstance(event, QueryAnswered):
            self.events.append(
                {"t": "query_answered", "width": event.width, "h": event.h, "x": event.x}
            )
        elif isinstance(event, PieceDropped):
            r = event.rect
            self.events.append({"t": "piece_dropped", "rect": [r.x, r.y, r.width, r.height]})
        elif isinstance(event, StructureChanged):
            self._snapshot(event.reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "board_width": self.rdds.board_width,
            "initial_pieces": self.initial_pieces,
            "events": self.events,
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), separators=(",", ":")))
