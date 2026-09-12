# Micro X Lab

[Lab 열기](https://hwkim3330.github.io/micro-x/web/lab.html) · [보행 실험](https://hwkim3330.github.io/micro-x/web/simulator.html)

Lab은 Rev A CAD 위에서 **구조 탐색 → 14축 학습 → 평가 → 재생**이 한 화면에서 이어지도록 만들었습니다. 무거운 계산(MuJoCo·BAM·PyTorch)은 로컬 서버가 하고, 공개 페이지는 저장소에 고정된 기록을 보여 줍니다.

## 탭 구성

| 탭 | 공개 페이지 | 로컬 서버 연결 시 |
|---|---|---|
| 구조 | 레이어별 부품 표시, 치수·질량·STL/STEP | 동일 |
| 14축 학습 | 공식 가중치·이어 학습·500회 학습 기록 카드 | 이름·업데이트·스텝·시드로 **실제 PPO 실행**, 업데이트별 평균 보상·넘어짐 그래프, 체크포인트 목록, **평가 실행**과 결과 표, ONNX 저장 |
| 보행 재생 | 공식 가중치로 계산한 qpos 기록을 실제 CAD 관절에 재생, 관절 각도 표시 | 동일 |
| 1축 실습 | 브라우저 CEM으로 가상 턱 서보 계수 학습, 저장/불러오기 | 동일 |
| 목소리 | 브라우저 TTS와 턱 애니메이션 | 동일 |

## 로컬 서버 실행

```sh
uv venv --python 3.12 .venv-policy
uv pip install --python .venv-policy/bin/python -r requirements-policy.txt
.venv-policy/bin/python tools/fetch_compat.py        # 공식 추론 코드·가중치를 .cache/compat에 내려받고 SHA256 검증
.venv-policy/bin/python runtime/training_service.py  # http://127.0.0.1:5201/web/lab.html
```

BAM 액추에이터 패키지는 Python 3.12를 요구합니다. 서버는 루프백에만 바인딩하고, 다른 출처의 요청·경로 탈출·HEAD·잘못된 설정을 거부합니다.

## API

| 엔드포인트 | 설명 |
|---|---|
| `POST /api/train {name, updates, steps, seed}` | `tools/train_compat.py` 실행. 진행은 `.cache/checkpoints/progress.json` |
| `GET /api/progress` | 업데이트별 평균 보상·넘어짐·손실 |
| `GET /api/checkpoints` | 저장된 ONNX와 학습 요약, 평가 여부 |
| `POST /api/evaluate {checkpoint, seconds, seeds}` | `tools/evaluate_compat.py`를 시드 10부터, 정지·전진 0.1/0.3·회전 0.3 명령으로 실행 |
| `GET /api/evaluation/<name>` | 평가 결과 (`official` 또는 체크포인트 이름) |
| `GET /api/checkpoint?name=<name>` | ONNX 다운로드 |
| `POST /api/sim/start {seed, policy}` / `POST /api/sim/step` | 공식 또는 체크포인트 정책으로 실시간 시뮬레이션. 응답에 전체 `qpos`가 포함되어 브라우저가 실제 CAD 리그를 그 자세로 놓습니다 |

## 평가 기준 (모든 정책에 동일)

1초 워밍업 후 몸체 좌표계의 전진·좌우 속도와 요 각속도를 평균해 명령과의 MAE를 계산합니다. 통과 기준은 넘어짐 없음, 전진 MAE ≤ max(0.03, 명령의 25 %), 좌우 ≤ 0.03 m/s, 요 ≤ 0.10 rad/s입니다. 이 기준은 저장소가 정한 공학적 목표이며 업계 표준이 아닙니다.

## 무엇이 아닌가

- 브라우저 안에서 14축 보행을 학습하지 않습니다. 브라우저 학습은 교육용 1축 예제만입니다.
- 학습한 정책이 실물에서 걷는다는 증거가 아닙니다. 모든 결과는 `models/micro_x_14.xml`(CAD 기반) 시뮬레이션입니다.
- 공식 가중치·코드는 저장소에 재배포하지 않고 로컬 캐시에만 둡니다(`engineering/policy_sources.json`).

## 재현과 테스트

```sh
npm ci
node --test tests/learning.test.mjs
CHROME_PATH=/path/to/chrome node tools/test-web.mjs        # 랜딩 뷰어: 리그·관절·재생·다운로드
CHROME_PATH=/path/to/chrome node tools/test-lab.mjs        # Lab: 레이어·카드·재생·1축 학습
CHROME_PATH=/path/to/chrome node tools/test-simulator.mjs  # 로컬 서버: 실시간 물리·정책 선택
CHROME_PATH=/path/to/chrome node tools/test-compat-web.mjs # 로컬 서버: PPO 실행·평가 표·취소
```

`CHROME_PATH`를 비우면 Puppeteer가 내려받은 Chrome을 사용합니다.
