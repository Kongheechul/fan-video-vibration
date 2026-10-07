# Fan Video Vibration

스마트폰·카메라 영상에서 지정된 부위의 변위와 진동 주파수 후보를 추출하는 연구용 파이프라인입니다. 현재 버전은 **진동 측정 단계**입니다. 이상 부위·고장 원인의 자동 판정이나 자동 ROI 인식은 구현하지 않았습니다.

**Shi-Tomasi → Lucas–Kanade Optical Flow → 배경 기반 카메라 보정 → 부위별 변위 → 주파수 분석**

원본 실험 영상과 개인 촬영 이미지는 포함하지 않았습니다. 설치 후 합성 데모로 바로 실행해 볼 수 있습니다.

## 설치 및 실행

Python 3.10 이상을 사용합니다. Windows PowerShell, macOS, Linux에서 실행할 수 있습니다.

```bash
git clone https://github.com/Kongheechul/fan-video-vibration.git
cd fan-video-vibration
python -m venv .venv
```

가상환경 활성화:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
python -m pip install -e .
python -m fanvib demo --out results/demo
```

데모는 120 fps 촬영 시간축·30 fps 재생·23.4 Hz 물체 진동·카메라 흔들림을 합성합니다. 합성 데이터는 설치와 수치 동작을 확인하는 예제이며 실제 고장 검출 성능을 증명하지 않습니다.

`results/demo/analysis/`의 결과:

| 파일 | 내용 |
|---|---|
| `analysis.json` | FPS·추적점수·부위별 후보 peak·보정 품질·판정 한계 |
| `signals.npz` | 프레임별 x/y 변위: raw / affine / translation, 단위 pixel |
| `roi.png` | 사람이 지정한 측정 영역 |
| `spectra.png` | Welch PSD 및 보정 방식별 Hann periodogram |

## 자신의 영상 분석

먼저 디코딩된 영상의 방향과 크기를 확인합니다. MOV 회전 메타데이터 처리는 OpenCV/플랫폼에 따라 달라질 수 있으므로 **저장된 첫 프레임을 기준**으로 ROI를 지정합니다.

```bash
python -m fanvib inspect data/my_video.mov --frame results/first_frame.png
python -m fanvib analyze data/my_video.mov --config examples/phone_240fps_2025.json --out results/my_video
```

예제 ROI는 기존 실험 구도에만 맞습니다. 자신의 영상에 맞게 설정 JSON의 좌표·영역을 수정해야 합니다. 기본적으로 원본 해상도로 분석하므로 긴 고해상도 영상은 시간과 메모리를 많이 사용합니다. GPU는 필요하지 않습니다.

### FPS와 슬로모션

`capture_fps`를 **명시적으로 입력**해야 합니다. 파일의 `playback_fps`를 촬영 FPS라고 자동으로 가정하지 않습니다.

- 일반 30 fps 원본: 촬영 간격이 실제 1/30초일 때 `capture_fps: 30`.
- Canon 고속 촬영: 해당 설정·프레임 보존을 확인했을 때 `capture_fps: 179.82017982017982`.
- 240 fps 슬로모션: 내보낸 프레임이 연속 촬영 프레임을 그대로 보존했을 때 `capture_fps: 240`.

240 fps 영상이 30 fps로 재생되더라도 물리 주파수 계산은 240 fps 시간축을 사용합니다. 하지만 내보내기 과정에서 프레임 삭제·복제·부분 속도 변경이 있으면 단순한 FPS 교체는 유효하지 않습니다. 현재 도구는 그 여부를 자동 검증하지 않습니다. JSON에 `frame_preservation_verified: false`를 기록합니다. 프레임 수 / 촬영 FPS로 예상되는 실제 길이도 반환합니다.

```bash
python -m fanvib analyze data/my_video.mov --config examples/phone_240fps_2025.json --capture-fps 240 --out results/my_video
```

Nyquist = 촬영 FPS / 2입니다. 프레임 간격이 올바르더라도 노출·모션블러 때문에 고주파 움직임이 약해질 수 있습니다. Peak가 Nyquist보다 낮다는 사실만으로 원래 주파수가 확정되지는 않습니다.

### ROI 설정

`frame_size`는 디코딩된 `[width, height]`이며 실제 크기와 다르면 오류를 반환합니다. ROI 좌표는 같은 프레임의 pixel 단위입니다. `background`에는 움직이지 않는 텍스처가 있는 영역을, `target`에는 측정할 본체를 지정합니다. 날개 회전 자체를 본체 진동으로 측정하지 않도록 영역을 구분합니다.

```json
{
  "capture_fps": 240,
  "frame_size": [1080, 1920],
  "nperseg": 512,
  "ransac_threshold_px": 1,
  "rois": [
    {"id": "head", "role": "target", "shape": "rectangle", "bounds": [300, 400, 200, 200]},
    {"id": "joint", "role": "target", "shape": "rectangle", "bounds": [400, 650, 100, 100]},
    {"id": "background", "role": "background", "shape": "rectangle", "bounds": [700, 300, 200, 900]}
  ],
  "relative_pairs": [["head", "joint"]]
}
```

위 좌표는 형식 예시입니다. 자신의 영상에 그대로 적용하지 마세요. 지원하는 shape:

- `rectangle`: `bounds: [x, y, width, height]`
- `polygon`: `points: [[x, y], ...]`
- `annulus`: `center`, `radii: [rx, ry]`, `inner`, `outer`, 선택적 `half: upper/lower`

예제 설정:

| 파일 | 대응 구도 / 시간축 가정 |
|---|---|
| `canon_179fps.json` | 기존 Canon 정지·강풍, 1920×1080 |
| `canon_weak_179fps.json` | 구도가 변경된 Canon 정지·약풍 |
| `phone_240fps_2023.json` | 스마트폰 정지, upright 1080×1920 |
| `phone_240fps_2024.json` | 스마트폰 앞면 강풍 |
| `phone_240fps_2025.json` | 스마트폰 옆면 강풍 |

## 현재 처리와 한계

1. ROI별 Shi-Tomasi 최대 150점 검출.
2. 인접 프레임 LK(21×21, pyramid level 3), forward/backward 오차 0.7 pixel 이내.
3. 전체 영상에서 살아남은 점만 사용. 긴 영상에서는 점이 많이 소실될 수 있습니다.
4. 정적 배경의 RANSAC affinePartial2D로 카메라 이동·회전·스케일 보정. 비교용 이동 보정과 raw도 함께 반환합니다.
5. 부위별 점의 좌표별 중앙값, 지정한 부위 사이의 상대 변위.
6. 선형 detrend 후 Welch PSD 및 Hann periodogram. x/y PSD를 합산합니다. 출력 후보 peak는 기본적으로 Welch 기준이며 full-periodogram 곡선은 그래프로 확인합니다.

배경은 최소 6개, 측정 ROI는 최소 3개 생존 특징점이 필요합니다. 배경 보정 실패 시 가짜 정상 결과를 만들지 않고 오류를 반환합니다. 한 ROI의 특징점이 부족하면 그 부위만 `insufficient_features`로 표시합니다.

**손촬영에서는 깊이가 다른 배경과 물체의 시차 때문에 보정이 오히려 잡음을 키울 수 있습니다.** raw / affine / translation 결과와 정지 영상·구간별 일관성을 함께 확인해야 합니다. 배경 fitting residual은 고장 신뢰도 확률이 아닙니다. 안정적인 관측 peak와 이상 원인 부위는 서로 다른 정보입니다.

`diagnosis`의 `vibration_confirmed`, `abnormal_region`, `fault_source`는 항상 `null`입니다. 이는 고장 없음(False)을 뜻하지 않습니다. 자동 판정이 구현·검증되지 않았다는 뜻입니다. 정상 체결과 유격 상태를 같은 풍량·구도·카메라 고정 조건에서 비교해야 유격 판별을 검증할 수 있습니다.

기존 실험에서는 시간축 가정하에 강풍 약 23.4 Hz, 약풍 약 16.3 Hz를 관찰했습니다. 이 값은 모든 선풍기에 적용되는 고정 목표가 아니고, 공개 코드는 그 주파수를 강제로 찾거나 고장으로 분류하지 않습니다. 실제 영상이 포함되지 않아 이 저장소만으로 해당 실험을 재현하는 것은 불가능합니다.

## Python 함수 / API 연동

```python
import json
from fanvib import analyze_video

with open("examples/phone_240fps_2025.json", encoding="utf-8") as f:
    config = json.load(f)
result = analyze_video("data/my_video.mov", config, "results/my_video")
print(result["regions"])
```

반환 dict는 JSON 직렬화 가능합니다. HTTP 서버는 포함하지 않습니다. 서버에 붙일 때 파일 업로드와 ROI 입력, 비동기 작업 처리, 업로드 크기 제한과 작업별 출력 경로를 따로 설계하세요. 현재 구현은 로컬 연구 실행을 위한 것입니다.

## 검증

```bash
python -m unittest discover -s tests -v
```

합성 카메라 흔들림 아래의 알려진 23.4 Hz, capture/playback 분리, 출력 파일, ROI·설정 오류를 검증합니다. GitHub Actions는 Python 3.10/3.12에서 같은 테스트를 실행합니다. 베어링·유격·불균형 분류의 정확도를 검증하는 테스트는 아닙니다.
