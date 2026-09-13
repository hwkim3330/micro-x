# 14축 정책 호환 검증 (Rev A)

목표는 **독자 설계 상업용 Micro X가 Microduck의 정책 인터페이스(61 관측 → 14 행동, 50 Hz)를 그대로 쓰는 것**입니다. 원본 CAD로 돌아가거나 비상업 하드웨어를 재라이선스하는 것이 아닙니다.

## 세 층

1. **Rev A CAD** (`cad/build.py`): 20개 출력 부품 + 15개 서보·배터리·보드·카메라 외형. 관절 피벗·축은 `engineering/functional_interface.json`(기능 인터페이스 측정값)을 따르고 나머지는 새로 설계.
2. **CAD 기반 동역학 모델** (`cad/compat_model.py` → `models/micro_x_14.xml`): 부품 메시에서 링크별 질량·질량중심·관성을 계산(PLA 꽉 찬 밀도 + 구매품 카탈로그 질량). 접촉은 발바닥 상자, 몸통·머리 타원체, 다리 상자. 이전의 원시 도형 연구 모델은 `models/archive/micro_x_14_primitive_study.xml`로 보존.
3. **고정된 공식 추론 코드 + 가중치** (`runtime/compat_env.py`, `.cache/compat/`): 변경 없는 `alpha_walking.onnx`/`alpha_stand.onnx`와 BAM M6 XL330 모터 모델(kp 200, 7.4 V 재현 조건).

## 제어 계약

`engineering/control_interface.json`: 14 액추에이터 이름·순서, HOME 오프셋, 61 관측(자이로 3, 투영 중력 3, HOME 상대 관절 위치 14, 관절 속도 14, 이전 행동 14, 명령 13), 50 Hz 제어 / 200 Hz 물리. 목표 = HOME + 행동, 스케일 1. 턱은 15번째 수동 관절(정책 외)로 모델에 포함되며 `models/rig.json`이 qpos 배열 순서를 기록합니다.

Rev A에서 기구적으로 제한한 범위: 고관절 롤 HOME ±10° (원본 ±22°), 목 피치 절대 0.15~1.05 rad(HOME +0.35에서 뒤로 -0.2), 머리 롤 ±12°, 머리 요 ±2.0 rad, 턱 0~0.35 rad. 무릎은 모델에서 ±1.0 rad이지만 기울인 발목 서보 때문에 ±0.5 rad 이상에서 허벅지와 닿을 수 있어 학습 시 제한을 권장합니다. 정책이 그 이상을 명령하면 시뮬레이션에서 관절 한계에 걸립니다.

## 시험 프로토콜

`tools/evaluate_compat.py`: 정지, 전진 0.1 / 0.3 m/s, 회전 0.3 rad/s 명령 × 시드, 각 N초. 넘어짐 = 몸통 기울기 45° 초과 또는 높이 65 mm 미만. 1초 워밍업 후 몸체 좌표 속도 MAE. 통과 = 넘어짐 없음, 전진 MAE ≤ max(0.03, 명령의 25 %), 좌우 ≤ 0.03, 요 ≤ 0.10. 학습 체크포인트는 `--walking-policy`로 같은 프로토콜에 넣습니다(Lab의 "평가 실행").

## 현재 결과

- `artifacts/compat_evaluation.json`: CAD 기반 모델에 변경 없는 공식 가중치. 결과 요약은 Lab 14축 학습 탭의 첫 카드와 `README.md`에 있으며, 모델 SHA256이 파일에 묶여 있어 모델을 바꾸면 테스트가 실패합니다.
- `artifacts/compat_training.json`: 같은 액터를 CPU PPO로 짧게 이어 학습·ONNX 재내보내기 (파이프라인 검증).
- 이전 원시 연구 모델의 기록(`compat_heldout_evaluation.json`, `training_500.json`, `trained_500_evaluation.json`, `official_recipe_x_validation.json`)은 아카이브 모델 SHA256에 묶여 보존됩니다.

원본 Microduck 모델에 같은 프로토콜을 돌린 비교값은 [micro-rex](https://github.com/hwkim3330/micro-rex)의 `tools/evaluate_policy.py`가 만듭니다. 두 결과를 나란히 읽어야 "가중치 호환"의 의미가 정해집니다: 원본에서도 이 하네스의 전진 명령 추종은 미달이므로, X의 미달을 X 기구만의 문제로 보지 않습니다.

## 재현

```sh
uv venv --python 3.12 .venv-policy && uv pip install --python .venv-policy/bin/python -r requirements-policy.txt
.venv-policy/bin/python tools/fetch_compat.py
.venv/bin/python cad/build.py && .venv/bin/python cad/compat_model.py
.venv-policy/bin/python tools/evaluate_compat.py --seconds 10 --seeds 3
.venv-policy/bin/python tools/train_compat.py --updates 10 --steps 256
.venv-policy/bin/python runtime/training_service.py   # Lab에서 학습·평가·재생
```

실물 호환(전압 5 V 재보정, 실제 관성, 케이블, 접촉)과 생산 준비는 별도 미해결 과제입니다.
