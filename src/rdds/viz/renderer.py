"""Matplotlib animation layer, driven entirely by core events.

The core knows nothing about drawing: :class:`SkylineAnimator` registers
itself as the RDDS observer and reacts to events — query probes become
transient arrows, drops become falling rectangles, structure changes
trigger a redraw of the skyline and chunk boundaries. Click the figure to
pause/resume.
"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

from rdds.core import (
    RDDS,
    Event,
    GapProbe,
    HeightProbe,
    PieceDropped,
    QueryAnswered,
    Rect,
    StructureChanged,
)

INK = "#3d3d3a"
GRID = "#c9c9c4"
CHUNK = "#1baf7a"
PROBE_CHUNK = "#2a78d6"
PROBE_CORRIDOR = "#eb6834"
ANSWER = "#008300"
PIECES = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]


def draw_board(ax: Any, rdds: RDDS) -> None:
    """Static rendering: walls, placed rectangles, skyline."""
    ax.set_xlim(-1, rdds.board_width + 1)
    top = max((s.y for s in rdds.skyline()), default=0)
    ax.set_ylim(0, max(top * 1.3, 10))
    ax.axvline(0, color=INK, linewidth=2)
    ax.axvline(rdds.board_width, color=INK, linewidth=2)
    ax.axhline(0, color=INK, linewidth=2)
    for i, r in enumerate(rdds.placed):
        ax.add_patch(
            plt.Rectangle(
                (r.x, r.y), r.width, r.height,
                facecolor=PIECES[i % len(PIECES)], edgecolor="white", linewidth=1, alpha=0.85,
            )
        )
    xs, ys = zip(*rdds.skyline_vertices(), strict=True)
    ax.plot(xs, ys, color=INK, linewidth=2)


class SkylineAnimator:
    """Observer that animates RDDS events on a matplotlib figure."""

    def __init__(self, rdds: RDDS, speed: float = 0.4, show_probes: bool = True):
        self.rdds = rdds
        self.speed = speed
        self.show_probes = show_probes
        self.paused = False
        self._skyline_artists: list[Any] = []
        self._chunk_artists: list[Any] = []
        self._piece_count = 0

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(11, 6))
        self.fig.canvas.mpl_connect("button_press_event", self._toggle_pause)
        self.ax.set_title("Rectangle Dropping Data Structure", loc="left", color=INK)
        self.ax.set_xlim(-1, rdds.board_width + 1)
        self.ax.axvline(0, color=INK, linewidth=2)
        self.ax.axvline(rdds.board_width, color=INK, linewidth=2)
        self.ax.axhline(0, color=INK, linewidth=2)
        for r in rdds.placed:
            self._draw_piece(r)
        self._redraw_structure()
        rdds.observer = self

    # ------------------------------------------------------------- plumbing

    def _toggle_pause(self, _event: Any) -> None:
        self.paused = not self.paused

    def _pause(self, dt: float) -> None:
        if dt > 0:
            plt.pause(dt)
        while self.paused:
            plt.pause(0.1)

    def _flash(self, artists: list[Any], dt: float) -> None:
        """Show transient artists for ``dt`` seconds, then remove them."""
        self._pause(dt)
        for a in artists:
            a.remove()

    def _draw_piece(self, rect: Rect) -> None:
        color = PIECES[self._piece_count % len(PIECES)]
        self._piece_count += 1
        self.ax.add_patch(
            plt.Rectangle(
                (rect.x, rect.y), rect.width, rect.height,
                facecolor=color, edgecolor="white", linewidth=1, alpha=0.85,
            )
        )

    def _redraw_structure(self) -> None:
        for a in self._skyline_artists + self._chunk_artists:
            a.remove()
        top = max(s.y for s in self.rdds.skyline())
        self.ax.set_ylim(0, max(top * 1.3, 10))
        xs, ys = zip(*self.rdds.skyline_vertices(), strict=True)
        self._skyline_artists = self.ax.plot(xs, ys, color=INK, linewidth=2)
        self._chunk_artists = [
            self.ax.axvline(c.start, color=CHUNK, linewidth=1, linestyle=":", alpha=0.7)
            for c in self.rdds.chunks[1:]
        ]

    # --------------------------------------------------------------- events

    def __call__(self, event: Event) -> None:
        if isinstance(event, GapProbe) and self.show_probes:
            color = PROBE_CHUNK if event.source == "chunk" else PROBE_CORRIDOR
            gap = event.gap
            arrow = self.ax.annotate(
                "", xy=(gap.x0, event.h), xytext=(gap.x1, event.h),
                arrowprops={"arrowstyle": "<->", "color": color},
            )
            label = self.ax.annotate(
                f"{gap.width}", xy=((gap.x0 + gap.x1) / 2, event.h),
                textcoords="offset points", xytext=(0, 4),
                fontsize=8, color=color, ha="center",
            )
            self._flash([arrow, label], self.speed * 0.25)
        elif isinstance(event, HeightProbe):
            line = self.ax.axhline(event.h, color=GRID, linestyle="--", linewidth=1)
            self._flash([line], self.speed * 0.5)
        elif isinstance(event, QueryAnswered):
            marker = self.ax.annotate(
                "", xy=(event.x, event.h), xytext=(event.x + event.width, event.h),
                arrowprops={"arrowstyle": "<->", "color": ANSWER, "linewidth": 2},
            )
            self._flash([marker], self.speed)
        elif isinstance(event, PieceDropped):
            rect = event.rect
            y_start = self.ax.get_ylim()[1]
            patch = self.ax.add_patch(
                plt.Rectangle(
                    (rect.x, y_start), rect.width, rect.height,
                    facecolor=PIECES[self._piece_count % len(PIECES)],
                    edgecolor="white", linewidth=1, alpha=0.85,
                )
            )
            steps = 8
            for i in range(1, steps + 1):
                patch.set_y(y_start + (rect.y - y_start) * i / steps)
                self._pause(self.speed / steps)
            patch.remove()
            self._draw_piece(rect)
        elif isinstance(event, StructureChanged):
            self._redraw_structure()
            self._pause(self.speed * 0.5)

    def show(self) -> None:
        """Block until the figure is closed."""
        plt.ioff()
        plt.show()
