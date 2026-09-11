# Microfly에서 참고할 구조

참고: [lvwerra/microfly](https://huggingface.co/spaces/lvwerra/microfly),
revision `89ba5406bb456a53b4fb6a14215216dd35a01d10`.
[README](https://huggingface.co/spaces/lvwerra/microfly/blob/89ba5406bb456a53b4fb6a14215216dd35a01d10/README.md),
[검증 기록](https://huggingface.co/spaces/lvwerra/microfly/blob/89ba5406bb456a53b4fb6a14215216dd35a01d10/VALIDATION.md),
[출처 명세](https://huggingface.co/spaces/lvwerra/microfly/blob/89ba5406bb456a53b4fb6a14215216dd35a01d10/provenance.json)를 읽고 판단했습니다. 비행체가 아니라 초파리 연결망을 Microduck의 상위 행동 제어에 연결한 브라우저 실험입니다.

## 확인한 구조

가상 감각 입력 → 단순화한 신경 활동 계산 → 전진·회전 명령 → 공식 보행 ONNX → MuJoCo 물리 계산 순서입니다. 신경 연결망의 가중치는 이 앱에서 학습하지 않습니다. 공식 정책이 균형과 걸음을 담당합니다. 신경 출력을 직접 14개 모터 목표에 연결하는 별도 경로에는 학습된 균형 제어가 없으며, 작성자의 시험에서도 넘어짐이 기록됐습니다. 이것을 생물학적으로 검증된 뇌나 학습된 자율 탐색으로 설명하지 않습니다.

X에 참고할 것은 **행동을 고르는 기능과 균형을 잡는 기능의 분리**, 실제 물리 상태에 연결된 화면, 중지·리셋·입력 차단을 확인할 수 있는 실험 방식입니다. 이것은 설계 판단이며 Microfly를 X에 포팅했다는 뜻이 아닙니다.

## X 적용 순서

먼저 전진·회전 명령을 추종하는 보행 정책을 확보합니다. 그 위에 카메라 인식으로 관심 대상을 선택하고 속도·회전 명령을 만드는 행동 계층을 붙입니다. 거리·방향 측정과 명령 변환은 별도 시험하고, 센서가 오래되거나 목표가 사라지면 정지 명령으로 돌아가게 합니다. 단안 카메라만으로 거리 정확도가 확보된다고 가정하지 않습니다.

뇌 시각화나 원본 로봇 외형을 제품에 복사하는 것은 현재 범위가 아닙니다. Microfly의 앱 라이선스와 포함된 로봇·뇌 조직 메시·원본 데이터의 조건은 각각 확인해야 하며, 앱 표기만으로 X의 상업용 재배포 권리를 판단하지 않습니다. 현재 X에는 Microfly의 자산·연결망·코드를 포함하지 않았습니다.
