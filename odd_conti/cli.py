"""
CLI: `odd-conti` — 트랙 콘티 → Remotion props JSON 생성.

사용법:
    odd-conti --track KR-01 --variant sub --out remotion/src/tracks/KR-01-sub.json
    odd-conti --track KR-02 --variant base --root outputs --fps 30
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .track import Track


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="odd-conti", description="Generate Remotion props from conti YAML.")
    p.add_argument("--track", required=True, help="track id (e.g. KR-01)")
    p.add_argument("--variant", default="sub", help="clip variant (default: sub)")
    p.add_argument("--stills-variant", default=None, help="stills variant (default: same as --variant)")
    p.add_argument("--root", default="outputs", help="outputs root (default: outputs)")
    p.add_argument("--clip-url-prefix", default=None, help="override clip URL prefix")
    p.add_argument("--still-url-prefix", default=None, help="override still URL prefix")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--out", required=True, help="output JSON path")
    p.add_argument(
        "--audio-url-base",
        default="http://localhost:8899/outputs",
        help="Remotion audio URL base (default: http://localhost:8899/outputs)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    track = Track.load(args.track, args.root, fps=args.fps)
    print(f"[loaded] {args.track} — {len(track.shots)} shots, {len(track.lyrics)} lyrics, layout={track.layout.layout}")

    props = track.to_remotion_props(
        variant=args.variant,
        stills_variant=args.stills_variant,
        audio_url_base=args.audio_url_base,
        clip_url_prefix=args.clip_url_prefix,
        still_url_prefix=args.still_url_prefix,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Remotion은 camelCase JSON을 직접 소비
    out.write_text(
        props.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )
    print(f"[output] {out}")
    print(f"[preview] {props.scenes[0].sceneId} → {props.scenes[-1].sceneId}, total {props.scenes[-1].startFrame + props.scenes[-1].durationFrames}f")

    return 0


if __name__ == "__main__":
    sys.exit(main())
