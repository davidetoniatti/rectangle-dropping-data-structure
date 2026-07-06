"""Pure algorithmic core — no rendering dependencies."""

from .chunk import Chunk
from .events import (
    Event,
    GapProbe,
    HeightProbe,
    Observer,
    PieceDropped,
    QueryAnswered,
    StructureChanged,
)
from .geometry import Gap, Number, Rect, Segment, normalize
from .naive import NaiveBoard
from .recording import RecordingObserver
from .skyline import skyline_of
from .structure import RDDS

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
