"""Events emitted by the core so renderers can animate without coupling.

The data structure knows nothing about drawing: it optionally calls a
single ``Observer`` callable with immutable event objects. The matplotlib
animator in :mod:`rdds.viz` is one such observer; tests can use another.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .geometry import Gap, Number, Rect


@dataclass(frozen=True, slots=True)
class GapProbe:
    """One candidate examined by ``widest_gap``: a chunk table hit or a corridor."""

    source: str  # "chunk" | "corridor"
    h: Number
    gap: Gap
    chunk_index: int | None = None


@dataclass(frozen=True, slots=True)
class HeightProbe:
    """One step of the binary search over candidate heights (Theorem 18)."""

    h: Number
    gap: Gap | None


@dataclass(frozen=True, slots=True)
class QueryAnswered:
    width: Number
    h: Number
    x: Number


@dataclass(frozen=True, slots=True)
class PieceDropped:
    rect: Rect


@dataclass(frozen=True, slots=True)
class StructureChanged:
    reason: str  # "init" | "insert" | "rebuild"


Event = GapProbe | HeightProbe | QueryAnswered | PieceDropped | StructureChanged
Observer = Callable[[Event], None]
