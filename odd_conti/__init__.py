"""
odd-conti — Storyboard YAML loader + Remotion props generator.

공용 API:
    Track.load(track_id, root)              — 트랙 로드 (legacy + new 구조 자동 감지)
    Track.to_remotion_props(variant, ...)   — Remotion composition props 생성
    ContiShot                                 — 단일 컷 타입
    LyricLine                                 — 가사 한 줄 타입
"""
from .track import Track
from .schema import ContiShot, LyricLine, RemotionScene, RemotionProps
from .layout import LayoutResolver

__all__ = [
    "Track",
    "ContiShot",
    "LyricLine",
    "RemotionScene",
    "RemotionProps",
    "LayoutResolver",
]

__version__ = "0.1.0"
