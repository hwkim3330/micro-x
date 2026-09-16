# MICRO X — Rev C

**소유자 hwkim3330이 제작·판매를 목표로 개발하는 상업용 독자 설계 소형 두발 로봇.** 공룡을 고집하지 않습니다. 넓은 부리와 큰 눈, 크림 몸에 호박색 부리·발, 두꺼운 벽. Microduck의 14축 정책 인터페이스(61 관측 → 14 행동, 50 Hz)를 그대로 쓰되, 기구·외장·서보 배치·전장 자리는 독자 설계입니다. 원본 기구를 그대로 쓰는 비상업 비교 시험기 [Micro Rex](https://github.com/hwkim3330/micro-rex)는 별도 저장소로 보존합니다.

[![Micro X Rev C — 실제 CAD 렌더](artifacts/readme_hero.png)](https://hwkim3330.github.io/micro-x/web/)

[제품 페이지 · 3D 뷰어](https://hwkim3330.github.io/micro-x/web/) · [학습 Lab](https://hwkim3330.github.io/micro-x/web/lab.html) · [보행 실험](https://hwkim3330.github.io/micro-x/web/simulator.html) · [설계](docs/DESIGN.md) · [조립](docs/ASSEMBLY.md) · [목표와 진행 기준](PROJECT_GOAL.md)

**현재 단계: Rev C 구동 설계 · 디지털 검증 완료, 실물 검증 전.** 출력·조립·보행·내구 시험은 아직 없습니다. 판매 가능한 완제품이 아닙니다.

## Rev C까지 바뀐 것

| | Rev A | Rev B → C |
|---|---|---|
| 설계 자세 | HOME(다리 굽은 자세) 측정 → 축이 5° 기울고 브래킷이 사선 | **qpos 0(곧게 선 자세) 측정 → 모든 축이 정렬, 브래킷이 평평하게 출력** |
| 서보 고정 | 관절마다 판 두 장으로 감싸는 클레비스 | **기준 로봇과 같은 방식: 한쪽 링크의 U자 채널 + 혼 판 한 장** |
| 출력물 질량 | 422 g | Rev B 347 g → **Rev C 440 g** (벽 2.4 → 3.0 mm, 20개 부품; 튼튼함을 위해 되돌린 부분) |
| 가동 범위 | 추측한 값을 모델에 기입 | **`tools/travel.py`가 0.05 rad씩 돌려 측정**, 그 값이 곧 MuJoCo 관절 한계 |
| 머리 | 타원체 한 덩이 | 단면 8개 로프트의 둥근 머리, **넓은 호박색 부리**, 렌즈 후드 코, **쉘과 한 몸인 Ø22 버튼 눈**(부품 아님) |
| 출력성 | 미측정 | **`artifacts/printability.json`**: 20개 전부 220×220 침대, 최대 오버행 27 % |

## 숫자

아래 표는 전부 `artifacts/`의 JSON에서 `tools/report.py`가 채웁니다. 손으로 적은 성능 숫자는 없습니다.

<!-- measured:summary -->
| 항목 | 값 | 출처 |
|---|---|---|
| 출력 부품 | 20개, 436.2 g (PLA 꽉 찬 기준, 실제 인필은 더 가벼움) | `artifacts/parts.json` |
| 구매품 | 18개, 399.0 g (카탈로그) | 같은 파일 |
| 모델 총질량 · 무게중심 | 834.3 g, 무게중심 z 141.68 mm, 지지영역 여유 12.71 mm | `artifacts/balance.json` |
| 간섭 | 설계 자세 정적 겹침 0건 / 측정 가동 범위 안 스윕 충돌 0 | `artifacts/interference.json` |
| 출력성 | 20개 모두 220×220 침대, 최악 오버행 30 %, 침대 접촉 0 mm² 4개(skull, right_upper_leg, left_upper_leg, neck_sleeve)는 브림/서포트 필요 | `artifacts/printability.json` |
| 공식 가중치 (무수정) | 15회 중 15회 직립, 추종 게이트 6/15 통과 | `artifacts/compat_evaluation.json` |
<!-- /measured -->

## 측정된 가동 범위

`tools/travel.py`가 관절마다 0.05 rad씩 돌려 정확한 STEP 불리언으로 충돌을 찾은 값이고, 그대로 MuJoCo 관절 한계가 됩니다.

<!-- measured:travel -->
| 관절 | 왼쪽 | 오른쪽 |
|---|---|---|
| 고관절 요 | -28.6° … +29.8° | -29.8° … +28.6° |
| 고관절 롤 | -22.9° … +20.1° | -20.1° … +22.9° |
| 고관절 피치 | -90.0° … +51.6° | -51.6° … +90.0° |
| 무릎 | -90.0° … +63.0° | -63.0° … +90.0° |
| 발목 | -31.5° … +31.5° | -31.5° … +31.5° |
| 목 피치 | -11.5° … +37.2° | (단일) |
| 머리 피치 | -34.4° … +34.4° | (단일) |
| 머리 요 | -114.6° … +43.0° | (단일) |
| 머리 롤 | -5.7° … +8.6° | (단일) |
| 턱 | +0.0° … +5.7° | (단일) |

탐색 상한: 고관절 요 ±30°, 고관절 롤 ±23°, 고관절 피치 ±90°, 무릎 ±90°, 발목 ±90°, 목 피치 ±60°, 머리 피치 ±90°, 머리 요 ±115°, 머리 롤 ±25°, 턱 ±40°. 상한에 도달한 값은 기구가 아니라 탐색 범위가 끝난 것입니다.
<!-- /measured -->

## 정적 기울기 한계

<!-- measured:tip -->
| | Micro X | **Microduck (원본)** | **Micro Cat** |
|---|---|---|---|
| **뒤로 기울기** | 5.5° | 8.5° | 17.7° |
| 앞으로 기울기 | 18.0° | 13.25° | 19.25° |
| 옆으로 기울기 | 24.9° | 23.8° | 25.25° |
| 무게중심 높이 (mm) | 138.0 | 141.1 | 135.7 |
| 질량 (g) | 834.3 | 737.2 | 872.5 |

`tools/tip_study.py`: 기울기마다 몸을 회전시켜 바닥에 내려놓고 접촉점을 다시 계산합니다. 원본은 HOME에서 **발바닥이 평평하지 않아** 뒤꿈치 선으로 서 있고, 무게중심이 그 선보다 21 mm 앞에 있어 발끝이 닿을 때까지 앞으로 넘어갑니다. 표의 값은 그렇게 안정된 자세부터 넘어질 때까지의 각도입니다. 강체·정적이며 접촉 강성·마찰·동역학은 없습니다.
<!-- /measured -->

## 속도·회전 숫자는 믿지 마세요

<!-- measured:harness -->
| 모델 | 전진 명령 추종 (최대) | 회전 명령 추종 (최대) |
|---|---|---|
| microduck_reference | 45 % | 9 % |
| micro_x | 33 % | 1 % |

기준 로봇 자신이 자기 명령을 못 따르므로, **이 하네스의 절대 속도·회전 숫자는 설계 근거로 쓸 수 없습니다.** 같은 하네스 안에서의 모델 간 상대 비교만 의미가 있습니다.
<!-- /measured -->

## 설계 개요

- **관절**: 좌우 고관절 요·롤·피치, 무릎, 발목(10) + 목 피치, 머리 피치·요·롤(4) + 턱(1).
- **피벗·축**: `engineering/functional_layout.json` (기준 로봇을 qpos 0에서 측정한 기능 치수). 서보 몸체 방향만 두 곳에서 바꿨고 이유를 같은 파일에 적었습니다.
- **서보**: XL330급. 인터페이스 치수와 발주 전 확인 항목은 `engineering/actuator_interface.json`. 케이스 홀 패턴은 아직 모델에 없습니다.
- **패키징**: 2S 18650급 배터리는 꼬리 커버 안, 보드(최대 50 × 27 mm)는 고관절 서보 위 데크, 카메라는 주둥이 끝.
- **외장 7개**(몸통·목 커버·머리·아래 부리·꼬리·발 2)만 보이고 나머지는 프레임. 눈은 쉘과 한 몸인 버튼, 손·발톱 없음.
- **배색**: 따뜻한 크림 쉘 + 호박색 부리·발 + 그래파이트 관절. 몸통 아래는 도색으로 한 톤 낮춥니다.
- **튼튼함**: 쉘 벽 3.0 mm, 서보 채널 벽 3.0 mm, 고관절 리브 4 mm + 상하 거싯, 발바닥 4 mm 스킨. 낙하 시험은 아직 없습니다.

## 재생성

```sh
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python cad/build.py            # 20 STEP/STL + GLB 리그 + parts.json
.venv/bin/python cad/compat_model.py     # models/micro_x_14.xml, models/rig.json
.venv/bin/python tools/travel.py         # 관절별 가동 범위 측정 → engineering/joint_travel.json
.venv/bin/python cad/compat_model.py     # 측정값을 관절 한계로 반영
.venv/bin/python tools/interference.py   # 정적 + 가동 범위 안 간섭
.venv/bin/python tools/balance.py && .venv/bin/python tools/printability.py && .venv/bin/python tools/documents.py
.venv/bin/python tools/validate.py && .venv/bin/python -m unittest discover -s tests

uv venv --python 3.12 .venv-policy && uv pip install --python .venv-policy/bin/python -r requirements-policy.txt
.venv-policy/bin/python tools/fetch_compat.py
.venv-policy/bin/python tools/evaluate_compat.py --seconds 10 --seeds 3
.venv-policy/bin/python runtime/training_service.py   # Lab http://127.0.0.1:5201/web/lab.html

npm ci && node --test tests/learning.test.mjs
CHROME_PATH=/path/to/chrome node tools/test-web.mjs && node tools/test-lab.mjs && node tools/test-simulator.mjs && node tools/test-compat-web.mjs
```

## 권리와 판매 방향

원본 기구·CAD 생성 소스·모델·도면은 소유자 권리를 유보합니다(소유자의 상업 이용을 제한하는 비상업 라이선스가 아닙니다). 웹·도구 코드는 MIT, Three.js는 MIT. 공식 추론 코드·가중치(Apache-2.0)는 저장소에 재배포하지 않고 로컬 캐시에만 내려받습니다. 상세: [LICENSE](LICENSE) · [THIRD_PARTY.md](THIRD_PARTY.md) · [PROVENANCE.md](docs/PROVENANCE.md). 제품명·디자인 권리 검토와 공급자 견적은 출시 전 별도 게이트입니다.

### 실제 실행 보드

소형 Radxa Zero 3W 4GB를 첫 실물 검증 후보로 정했습니다. 보행·행동 계산은 로봇 내부, 학습은 PC에서 실행하는 구조입니다. [배선 구상·전체 신경망 CPU 실측·미검증 항목](docs/ONBOARD_COMPUTE.md)을 확인하세요. 실제 보드·전원 검증 전이며 기존 7.4 V BAM 실험은 XL330의 실물 전원 사양이 아닙니다.
