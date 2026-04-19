"""
Track — 트랙 단위 고수준 API.

YAML 콘티 + 가사 정렬 JSON + 클립 폴더 → Remotion props 자동 생성.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .layout import LayoutResolver
from .schema import ContiShot, LyricLine, RemotionScene, RemotionProps


# 컷별 감정 태그 맵핑 (section/tone → Remotion emotion)
_EMOTION_MAP = {
    "intro": "REVEAL",
    "verse1": "TENSION",
    "pre_chorus1": "URGENCY",
    "chorus1": "PEAK",
    "verse2": "CALM",
    "pre_chorus2": "WONDER",
    "bridge": "HOLD",
    "final_chorus": "PEAK",
    "outro": "CALM",
}


@dataclass
class Track:
    """트랙 전체 데이터 + Remotion props 생성기."""

    track_id: str
    title: str
    fps: int
    conti: dict                      # raw conti YAML
    shots: list[ContiShot]
    lyrics: list[LyricLine]
    layout: LayoutResolver

    # ── loading ────────────────────────────────────────────────

    @classmethod
    def load(cls, track_id: str, root: Path | str, fps: int = 30) -> "Track":
        """트랙 ID로 전체 데이터 로드."""
        root = Path(root)
        layout = LayoutResolver.detect(track_id, root)

        conti_path = layout.conti_yaml()
        if not conti_path.exists():
            raise FileNotFoundError(f"conti not found: {conti_path}")
        conti = yaml.safe_load(conti_path.read_text(encoding="utf-8"))

        shots = [ContiShot(**s) for s in conti.get("shots", [])]
        title = conti.get("title", track_id)

        # lyrics (없어도 OK)
        lyrics: list[LyricLine] = []
        aligned = layout.lyrics_aligned()
        if aligned.exists():
            raw = json.loads(aligned.read_text(encoding="utf-8"))
            lyrics = [LyricLine(**l) for l in raw]

        return cls(
            track_id=track_id,
            title=title,
            fps=fps,
            conti=conti,
            shots=shots,
            lyrics=lyrics,
            layout=layout,
        )

    # ── Remotion props generation ──────────────────────────────

    def to_remotion_props(
        self,
        variant: str = "sub",
        audio_url_base: str = "http://localhost:8899/outputs",
        clip_ext: str = ".mp4",
        still_ext: str = ".png",
        playback_rates: Optional[dict[str, float]] = None,
        transitions: Optional[dict[str, str]] = None,
        clip_url_prefix: Optional[str] = None,
    ) -> RemotionProps:
        """
        콘티 + 가사 + 클립 폴더를 기반으로 Remotion props 생성.

        Args:
            variant: 클립 variant (sub, veo, adult 등)
            audio_url_base: Remotion이 오디오를 가져올 베이스 URL
            clip_ext: 클립 확장자
            still_ext: 이미지 확장자
            playback_rates: shot_id → playbackRate 덮어쓰기 (None이면 실제 클립 길이로 자동 계산)
            transitions: shot_id → transition 덮어쓰기 ("cut" or "dissolve")
            clip_url_prefix: 클립/스틸 URL 프리픽스 (없으면 audio_url_base 기반 추정)
        """
        # URL prefix 구성
        if clip_url_prefix is None:
            if self.layout.layout == "unified":
                clip_url_prefix = f"{audio_url_base}/{self.track_id}/clips/{variant}"
                still_url_prefix = f"{audio_url_base}/{self.track_id}/stills/{variant}"
            else:
                clip_url_prefix = f"{audio_url_base}/videos/{self.track_id}_{variant}"
                still_url_prefix = f"{audio_url_base}/stills/{self.track_id}-{variant}"
        else:
            still_url_prefix = clip_url_prefix

        # 오디오 URL
        audio_path = self.layout.audio()
        if audio_path is None:
            raise FileNotFoundError(f"audio not found for {self.track_id}")
        if self.layout.layout == "unified":
            audio_src = f"{audio_url_base}/{self.track_id}/{audio_path.name}"
        else:
            audio_src = f"{audio_url_base}/songs/{self.track_id}/{audio_path.name}"

        # 실제 클립 길이 측정 (playbackRate 자동 계산용)
        clip_dir = self.layout.clips_dir(variant)
        clip_durations: dict[str, float] = {}
        if clip_dir.exists():
            clip_durations = _probe_clip_durations(clip_dir)

        # 씬 빌드
        scenes: list[RemotionScene] = []
        running_frame = 0
        playback_rates = playback_rates or {}
        transitions = transitions or {}

        for shot in self.shots:
            dur_frames = int(round(shot.screen_duration * self.fps))
            emotion = _EMOTION_MAP.get(shot.section, "CALM")

            # 파일 이름 (소문자 sXX.mp4 or 대문자 SXX.png)
            clip_lower = f"{shot.shot_id.lower()}{clip_ext}"
            still_upper = f"{shot.shot_id.upper()}{still_ext}"

            # BG 정적 샷 → image 타입
            if shot.tag == "BG" and shot.motion in ("static", "static_or_gentle_push"):
                scene_type = "image"
                path = f"{still_url_prefix}/{still_upper}"
                pb_rate = None
            else:
                scene_type = "video"
                path = f"{clip_url_prefix}/{clip_lower}"
                # playbackRate 자동 계산
                if shot.shot_id in playback_rates:
                    pb_rate = playback_rates[shot.shot_id]
                elif shot.shot_id.lower() in clip_durations:
                    actual_dur = clip_durations[shot.shot_id.lower()]
                    if actual_dur > 0 and abs(actual_dur - shot.screen_duration) > 0.5:
                        pb_rate = round(actual_dur / shot.screen_duration, 2)
                        # 클립이 더 길면 트림 (pb=1.0) — 너무 빠른 재생 방지
                        if pb_rate > 1.05:
                            pb_rate = None  # let it trim
                    else:
                        pb_rate = None
                else:
                    pb_rate = None

            transition = transitions.get(shot.shot_id, "cut" if shot.turnpoint else "dissolve")

            scenes.append(RemotionScene(
                sceneId=shot.shot_id,
                type=scene_type,
                path=path,
                startFrame=running_frame,
                durationFrames=dur_frames,
                emotion=emotion,
                transition=transition,
                playbackRate=pb_rate,
            ))
            running_frame += dur_frames

        return RemotionProps(
            trackId=self.track_id,
            title=self.title,
            audioSrc=audio_src,
            scenes=scenes,
            lyrics=self.lyrics,
        )


def _probe_clip_durations(clip_dir: Path) -> dict[str, float]:
    """ffprobe로 폴더 내 mp4 파일의 duration 측정.

    ffprobe 없으면 빈 dict 반환 (자동 계산 비활성화).
    """
    import subprocess
    durations: dict[str, float] = {}
    for f in clip_dir.glob("*.mp4"):
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(f)],
                capture_output=True, text=True, timeout=10,
            )
            if out.returncode == 0 and out.stdout.strip():
                durations[f.stem] = float(out.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            return {}  # ffprobe 없거나 실패 — 자동 계산 비활성화
    return durations
