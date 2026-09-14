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

| 항목 | 값 | 출처 |
|---|---|---|
| 출력 부품 | 20개, 440 g (PLA 꽉 찬 기준, 실제 인필은 더 가벼움) | `artifacts/parts.json` |
| 구매품 | 서보 15 × 18 g + 배터리 95 g + 보드 30 g + 카메라 4 g = 399 g | 카탈로그 질량 |
| 모델 총질량 | 838 g (Microduck 780 g) | `artifacts/balance.json` |
| 기립 높이 · 무게중심 | HOME에서 몸통 119 mm, 무게중심 142 mm, 지지영역 여유 10.6 mm | `artifacts/balance.json` |
| 간섭 | 설계 자세 겹침 **0** / 측정 가동 범위 안 충돌 **0** | `artifacts/interference.json` |
| 출력성 | 20개 모두 220×220 침대, 최대 오버행 30 % | `artifacts/printability.json` |
| 공식 가중치 시험 | 15회 모두 10초 직립, 속도·방향 기준 6회 통과(정지·서기). 전진 0.3 m/s 명령에 0.11 m/s | `artifacts/compat_evaluation.json` |

전진 명령 추종 미달은 원본 Microduck 모델에 같은 하네스를 돌려도 나타납니다([Micro Rex 비교](https://github.com/hwkim3330/micro-rex)). X 기구만의 결함으로 해석하지 않습니다.

## 측정된 가동 범위

| 관절 | 측정값 | 관절 | 측정값 |
|---|---|---|---|
| 고관절 요 | -26° … +30° | 목 피치 | -11° … +37° |
| 고관절 롤 | -20° … +17° | 머리 피치 | ±34° |
| 고관절 피치 | -90° … +63° | 머리 요 | ±115° |
| 무릎 | -90° … +63° | 머리 롤 | ±17° |
| 발목 | ±32° | 턱 | 0° … +6° |

좌우가 비대칭인 것은 브래킷이 좌우 대칭이라 회전 방향에 따라 닿는 곳이 다르기 때문입니다. 전체 표는 `engineering/joint_travel.json`.

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
