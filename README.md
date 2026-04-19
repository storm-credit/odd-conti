# odd-conti

**Storyboard (conti) YAML → Remotion props generator for ODD Engine tracks.**

트랙별 콘티 YAML, 가사 aligned JSON, 클립 폴더를 읽어서 Remotion composition에
그대로 넘길 수 있는 props JSON을 생성한다.

## 핵심 기능

- **자동 폴더 구조 감지** — 레거시(분산형) / 신규(통합형) 둘 다 지원
- **실제 클립 길이 측정** — ffprobe로 mp4 duration 측정 → playbackRate 자동 계산
- **가사 자동 병합** — `odd-transcription`이 생성한 aligned JSON 그대로 사용
- **변형(variant) 시스템** — sub / veo / adult 등 같은 트랙의 다른 버전 지원
- **Remotion 직접 호환** — camelCase JSON 그대로 `defaultProps`로 사용 가능

## 설치

```bash
pip install git+https://github.com/storm-credit/odd-conti.git
```

**시스템 의존성**: `ffmpeg` (playbackRate 자동 계산용, optional)

## 사용법

### CLI

```bash
odd-conti --track KR-01 --variant sub --out remotion/src/tracks/KR-01-sub.json
```

### Python API

```python
from pathlib import Path
from odd_conti import Track

track = Track.load("KR-01", Path("outputs"))
props = track.to_remotion_props(
    variant="sub",
    audio_url_base="http://localhost:8899/outputs",
)

# JSON 파일로 저장
import json
Path("remotion/src/tracks/KR-01-sub.json").write_text(
    props.model_dump_json(indent=2, exclude_none=True)
)
```

### Remotion에서 사용

```typescript
// Root.tsx
import kr01 from "./tracks/KR-01-sub.json";

<Composition
  id="KR-01-Sub"
  component={OddFullMV}
  durationInFrames={6396}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={kr01}
/>
```

## 폴더 구조 지원

### 레거시 (KR-01 스타일)

```
outputs/
  conti/KR-01_conti_v8.yaml
  conti/KR-01_lyrics_aligned.json
  songs/KR-01/저승DM.mp3
  stills/KR-01-adult/*.png
  videos/KR-01_sub/*.mp4
```

### 신규 (통합형, KR-02+)

```
outputs/KR-02/
  track.yaml
  song.mp3
  conti.yaml
  lyrics/{source,aligned}.json
  characters/{variant}/
  stills/{variant}/
  clips/{variant}/
  renders/
```

**자동 감지**: `outputs/{track}/conti.yaml`이 있으면 신규, 없으면 레거시.

## 같이 쓰면 좋은 모듈

- [`odd-transcription`](https://github.com/storm-credit/odd-transcription) — Whisper + LCS 가사 정렬

## 라이선스

MIT
