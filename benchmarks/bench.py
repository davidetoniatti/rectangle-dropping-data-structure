#!/usr/bin/env python3
"""Empirical verification of the paper's bounds (Theorem 18).

Plays greedy Tetris at growing board sizes and measures the time per
operation for the RDDS against the obvious linear-scan approach, then
plots both on a log-log chart with the theoretical O(n^(1/2) log^(3/2) n)
guide. Run from the repo root:

    python benchmarks/bench.py --out docs/benchmark.png --csv docs/benchmark.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import time
from collections import deque
from pathlib import Path

from rdds import RDDS, NaiveBoard, Rect


def naive_query(board: NaiveBoard, width: int) -> tuple[int, int]:
    """O(W) greedy query for the grid board: sliding-window maximum + argmin."""
    cols = board.columns
    window: deque[int] = deque()  # indices, decreasing column height
    best_h, best_x = -1, 0
    for i, h in enumerate(cols):
        while window and cols[window[-1]] <= h:
            window.pop()
        window.append(i)
        if window[0] <= i - width:
            window.popleft()
        if i >= width - 1:
            top = cols[window[0]]
            if best_h < 0 or top < best_h:
                best_h, best_x = top, i - width + 1
    return best_h, best_x


def make_scene(n_rects: int, board_width: int, rng: random.Random) -> list[Rect]:
    rects = []
    for _ in range(n_rects):
        w = rng.randint(1, 8)
        x = rng.randint(0, board_width - w)
        rects.append(Rect(x, 0, w, rng.randint(1, 20)))
    return rects


def bench_size(n_rects: int, ops: int, seed: int) -> dict[str, float]:
    board_width = 4 * n_rects
    rng = random.Random(seed)
    scene = make_scene(n_rects, board_width, rng)
    # Measured pieces stay at the scene's scale so the skyline keeps ~n segments
    # throughout the measurement (a handful of huge pieces would flatten it).
    pieces = [(rng.randint(1, 8), rng.randint(1, 10)) for _ in range(ops)]

    t0 = time.perf_counter()
    rdds = RDDS(board_width, list(scene))
    construction_s = time.perf_counter() - t0
    n_segments = rdds.n_segments

    rdds_query = rdds_insert = 0.0
    for w, hp in pieces:
        t0 = time.perf_counter()
        _, x = rdds.query(w)
        rdds_query += time.perf_counter() - t0
        t0 = time.perf_counter()
        rdds.insert(w, hp, x)
        rdds_insert += time.perf_counter() - t0

    naive = NaiveBoard(board_width, scene)
    naive_q = naive_i = 0.0
    for w, hp in pieces:
        t0 = time.perf_counter()
        _, x = naive_query(naive, w)
        naive_q += time.perf_counter() - t0
        t0 = time.perf_counter()
        naive.insert(w, hp, x)
        naive_i += time.perf_counter() - t0

    ms = 1000.0 / ops
    return {
        "n_segments": float(n_segments),
        "construction_s": construction_s,
        "rdds_query_ms": rdds_query * ms,
        "rdds_insert_ms": rdds_insert * ms,
        "naive_query_ms": naive_q * ms,
        "naive_insert_ms": naive_i * ms,
    }


def plot(rows: list[dict[str, float]], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ns = np.array([r["n_segments"] for r in rows])
    series = [  # categorical palette, fixed slot order
        ("rdds_query_ms", "RDDS query", "#2a78d6"),
        ("rdds_insert_ms", "RDDS insert", "#1baf7a"),
        ("naive_query_ms", "naive query", "#eda100"),
        ("naive_insert_ms", "naive insert", "#008300"),
    ]

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=150)
    for key, label, color in series:
        ys = np.array([r[key] for r in rows])
        ax.loglog(ns, ys, color=color, linewidth=2, marker="o", markersize=5, label=label)
        ax.annotate(
            label,
            (ns[-1], ys[-1]),
            textcoords="offset points",
            xytext=(8, -3),
            fontsize=9,
            color="#3d3d3a",
        )

    # Theoretical guide, anchored to the last RDDS insert measurement.
    guide = np.sqrt(ns * np.log2(ns)) * np.log2(ns)
    anchor = rows[-1]["rdds_insert_ms"] / guide[-1]
    ax.loglog(
        ns,
        guide * anchor,
        color="#8a8a86",
        linewidth=1.5,
        linestyle="--",
        label=r"$c \cdot \sqrt{n \log n}\,\log n$  (Thm 18)",
    )

    slopes = {}
    for key, label, _ in series[:2]:
        slopes[label] = float(
            np.polyfit(np.log10(ns), np.log10([r[key] for r in rows]), 1)[0]
        )
    print("fitted log-log slopes:", {k: round(v, 3) for k, v in slopes.items()})

    ax.set_xlabel("skyline segments  $n$")
    ax.set_ylabel("time per operation (ms)")
    ax.set_title(
        "Greedy Tetris: RDDS vs. linear scan",
        loc="left",
        fontsize=12,
        fontweight="bold",
    )
    ax.grid(True, which="major", color="#e8e8e4", linewidth=0.6)
    ax.grid(True, which="minor", color="#f2f2ef", linewidth=0.4)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.margins(x=0.12)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor="white")
    print(f"wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes", default="256,512,1024,2048,4096,8192,16384", help="prefill sizes"
    )
    parser.add_argument("--ops", type=int, default=100, help="measured ops per size")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("docs/benchmark.png"))
    parser.add_argument("--csv", type=Path, default=Path("docs/benchmark.csv"))
    args = parser.parse_args()

    rows = []
    for n in (int(s) for s in args.sizes.split(",")):
        row = bench_size(n, args.ops, args.seed)
        rows.append(row)
        print(
            f"n={int(row['n_segments']):>6}  "
            f"rdds query {row['rdds_query_ms']:8.3f} ms  "
            f"insert {row['rdds_insert_ms']:8.3f} ms  |  "
            f"naive query {row['naive_query_ms']:8.3f} ms  "
            f"insert {row['naive_insert_ms']:8.3f} ms"
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.csv}")

    plot(rows, args.out)


if __name__ == "__main__":
    main()
