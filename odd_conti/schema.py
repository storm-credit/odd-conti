"""
Pydantic schemas for conti / Remotion types.
"""
from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ContiShot(BaseModel):
    """단일 컷 정의 (conti YAML의 shots[])."""
    shot_id: str                   # S01, S02, ...
    section: str                   # intro / verse1 / chorus1 / ...
    time_start: str                # "0:00"
    time_end: str                  # "0:08"
    screen_duration: float          # seconds
    tag: Literal["BG", "FEMALE", "MALE", "FX", "OBJECT"] = "FEMALE"
    tone: str = "cute_base"
    story_beat: str = ""
    mirror_of: Optional[str] = None
    hero_cut: bool = False
    anchor_cut: bool = False
    turnpoint: bool = False
    aspect: str = "9:16"
    motion: str = "static"
    engine_preferred: str = "imagen_4"
    tool: str = ""
    reuse_from: Optional[str] = None

    class Config:
        extra = "allow"  # 다른 필드 허용 (v8 conti의 추가 필드 보존)


class LyricLine(BaseModel):
    """가사 한 줄 — odd-transcription의 LyricLine과 호환."""
    text: str
    en: Optional[str] = None
    emphasis: bool = False
    startFrame: int = 0
    endFrame: int = 0


class RemotionScene(BaseModel):
    """Remotion composition의 한 scene."""
    sceneId: str
    type: Literal["video", "image"]
    path: str
    startFrame: int
    durationFrames: int
    emotion: str = "CALM"
    transition: Literal["cut", "dissolve", "fade"] = "dissolve"
    playbackRate: Optional[float] = None
    colorOverlay: Optional[str] = None


class RemotionProps(BaseModel):
    """Remotion composition의 전체 props (defaultXXMVProps)."""
    trackId: str
    title: str
    audioSrc: str
    scenes: list[RemotionScene]
    lyrics: list[LyricLine] = Field(default_factory=list)
