"""Rectangle Dropping Data Structure.

Reference implementation of the data structure from Section 4 of
J. Dallant and J. Iacono, "How fast can we play Tetris greedily with
rectangular pieces?" (arXiv:2202.10771).
"""

from .core import (
    RDDS,
    Chunk,
    Event,
    Gap,
    GapProbe,
    HeightProbe,
    NaiveBoard,
    Number,
    Observer,
    PieceDropped,
    QueryAnswered,
    RecordingObserver,
    Rect,
    Segment,
    StructureChanged,
    normalize,
    skyline_of,
)

__version__ = "1.0.0"

__all__ = [
    "RDDS",
    "Chunk",
    "Event",
    "Gap",
    "GapProbe",
    "HeightProbe",
    "NaiveBoard",
    "Number",
    "Observer",
    "PieceDropped",
    "QueryAnswered",
    "RecordingObserver",
    "Rect",
    "Segment",
    "StructureChanged",
    "normalize",
    "skyline_of",
]
