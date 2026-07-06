#!/usr/bin/env python3
"""Greedy Tetris, played by the data structure.

Random rectangular pieces are queried and dropped where the RDDS says.
With a display, every query probe and drop is animated; with --headless
the game runs silently and saves the final board to a PNG.

    python -m rdds.demo.tetris --width 60 --pieces 30 --speed 0.3
    python -m rdds.demo.tetris --headless --out board.png
"""

from __future__ import annotations

import argparse
import random

from rdds.core import RDDS


def play(rdds: RDDS, n_pieces: int, rng: random.Random) -> None:
    max_w = max(2, int(rdds.board_width) // 3)
    for _ in range(n_pieces):
        width = rng.randint(1, max_w)
        height = rng.randint(1, 5)
        _, x = rdds.query(width)
        rdds.insert(width, height, x)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=40, help="board width")
    parser.add_argument("--pieces", type=int, default=20, help="pieces to drop")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--speed", type=float, default=0.35, help="animation pace (s)")
    parser.add_argument("--no-probes", action="store_true", help="skip probe animations")
    parser.add_argument("--headless", action="store_true", help="no window, save PNG")
    parser.add_argument("--out", default="board.png", help="output PNG (headless)")
    parser.add_argument(
        "--record", metavar="PATH", help="record the game as JSON for the web player"
    )
    parser.add_argument(
        "--web",
        metavar="PATH",
        nargs="?",
        const="player.html",
        help="build a self-contained browser player (default: player.html) and open it",
    )
    parser.add_argument(
        "--no-open", action="store_true", help="with --web: do not open the browser"
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rdds = RDDS(args.width)

    if args.record or args.web:
        from rdds.core import RecordingObserver

        recorder = RecordingObserver(rdds)
        play(rdds, args.pieces, rng)
        if args.record:
            recorder.save(args.record)
            print(f"wrote {args.record} ({len(recorder.events)} events)")
        if args.web:
            from rdds.web import write_player

            out = write_player(recorder.to_dict(), args.web)
            print(f"wrote {out} ({len(recorder.events)} events)")
            if not args.no_open:
                import webbrowser

                webbrowser.open(out.as_uri())
        return

    if args.headless:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from rdds.viz import draw_board

        play(rdds, args.pieces, rng)
        fig, ax = plt.subplots(figsize=(11, 6))
        draw_board(ax, rdds)
        ax.set_title(f"{args.pieces} pieces, greedy", loc="left")
        fig.savefig(args.out, dpi=150, facecolor="white")
        print(f"wrote {args.out} ({rdds.n_segments} skyline segments)")
        return

    from rdds.viz import SkylineAnimator

    animator = SkylineAnimator(rdds, speed=args.speed, show_probes=not args.no_probes)
    play(rdds, args.pieces, rng)
    animator.show()


if __name__ == "__main__":
    main()
