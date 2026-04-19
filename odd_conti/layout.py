"""
레거시(분산형) ↔ 신규(통합형) 폴더 구조 자동 감지 + 경로 해석.

레거시 구조 (KR-01):
    outputs/conti/{track}_conti_v8.yaml
    outputs/conti/{track}_lyrics_aligned.json
    outputs/songs/{track}/*.mp3
    outputs/characters/{track}/female/
    outputs/stills/{track}-{variant}/*.png
    outputs/videos/{track}_{variant}/*.mp4
    outputs/videos/{track}/*.mp4                  (최종 렌더)

신규 구조 (KR-02+):
    outputs/{track}/
      track.yaml
      song.mp3
      conti.yaml
      lyrics/{source,aligned}.json
      characters/{variant}/
      stills/{variant}/
      clips/{variant}/
      renders/
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LayoutResolver:
    """트랙의 폴더 구조 감지 + 경로 계산."""

    track_id: str
    root: Path               # oddengine/outputs
    layout: str              # "legacy" or "unified"

    @classmethod
    def detect(cls, track_id: str, root: Path) -> "LayoutResolver":
        """자동 감지: 신규 구조 우선, 없으면 레거시."""
        unified_dir = root / track_id
        if unified_dir.is_dir() and (unified_dir / "conti.yaml").exists():
            return cls(track_id=track_id, root=root, layout="unified")
        return cls(track_id=track_id, root=root, layout="legacy")

    # ── paths ──────────────────────────────────────────────────

    def conti_yaml(self) -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "conti.yaml"
        # legacy — 가장 높은 버전 번호 자동 선택
        conti_dir = self.root / "conti"
        candidates = sorted(conti_dir.glob(f"{self.track_id}_conti_v*.yaml"))
        if candidates:
            return candidates[-1]
        return conti_dir / f"{self.track_id}_conti.yaml"

    def lyrics_source(self) -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "lyrics" / "source.json"
        return self.root / "conti" / f"{self.track_id}_lyrics_source.json"

    def lyrics_aligned(self) -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "lyrics" / "aligned.json"
        return self.root / "conti" / f"{self.track_id}_lyrics_aligned.json"

    def audio(self) -> Optional[Path]:
        if self.layout == "unified":
            for pat in ("song.mp3", "song.wav", "song.m4a"):
                p = self.root / self.track_id / pat
                if p.exists():
                    return p
            return None
        # legacy — outputs/songs/{track}/*.mp3
        song_dir = self.root / "songs" / self.track_id
        if song_dir.is_dir():
            for pat in ("*.mp3", "*.wav", "*.m4a"):
                for f in song_dir.glob(pat):
                    return f
        return None

    def characters_dir(self, variant: str = "base") -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "characters" / variant
        # legacy: female / female-adult 매핑
        legacy_map = {"base": "female", "adult": "female-adult"}
        sub = legacy_map.get(variant, variant)
        return self.root / "characters" / self.track_id / sub

    def stills_dir(self, variant: str = "base") -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "stills" / variant
        # legacy: {track}-{variant} or {track}
        legacy = self.root / "stills" / f"{self.track_id}-{variant}"
        if legacy.is_dir():
            return legacy
        return self.root / "stills" / self.track_id

    def clips_dir(self, variant: str = "sub") -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "clips" / variant
        # legacy: {track}_{variant}
        return self.root / "videos" / f"{self.track_id}_{variant}"

    def renders_dir(self) -> Path:
        if self.layout == "unified":
            return self.root / self.track_id / "renders"
        return self.root / "videos" / self.track_id

    def prompts_dir(self, variant: str = "sub") -> Path:
        """프롬프트 영구 저장소 (신규 규칙)."""
        if self.layout == "unified":
            return self.root / self.track_id / "clips" / variant
        # legacy: 별도 prompts/ 폴더 사용 권장
        return self.root / "prompts" / self.track_id
