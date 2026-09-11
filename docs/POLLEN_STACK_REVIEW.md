# Pollen Robotics 조사와 Micro X 적용 판단

조사일: 2026-09-11. **MuJoCo는 전체 제품의 한 구성요소입니다.** X는 보행 학습, 실행 제어, 인식·표현, 제품 운영을 구분해 검증합니다. 아래의 공식 설명과 X에서 직접 확인한 결과를 혼동하지 않습니다.

| 계층 | 공식 구성·자료 | X의 현재 상태와 판단 |
|---|---|---|
| 학습 | mjlab / MuJoCo Warp, PPO, BAM XL330, 지연·전압·마찰·관측 오차 랜덤화, 별도 backlash 변형 | 공식 고정 버전에서 GPU 실행 확인. 같은 recipe에 X 모델을 연결했으며 장기 학습 평가 진행. 간단한 CPU PPO는 보조 실습으로 유지 |
| 정책 실행 | 정규화가 포함된 ONNX, 61개 관측·14개 행동, 50Hz, 보행·기립·기술 전환 | 보행·기립 연결 확인. 모든 기술·전환·복구 호환을 검증한 것은 아님 |
| 웹 실험 | 브라우저 WASM 물리 + ONNX 추론 | 공식 웹 직접 조작 확인. X는 별도 로컬 MuJoCo/BAM 서버에 실제 조작 화면을 연결; 공개 Pages는 정지 미리 보기 |
| 로봇 운영 | robotd 중심 제어, 별도 미디어·센서·설정·업데이트 서비스 | X의 로컬 실험 서버는 이 전체 운영 시스템을 대체하지 않음. 실물 버스·보호·복구·업데이트는 추가 구현/시험 대상 |
| 통합 시뮬레이션 | 실제 daemon + 가상 모터·센서, 컨테이너·통신 장애 시험 | 공식 문서를 확인했으며 X에서 이 경로를 실행한 것으로 표시하지 않음 |
| 시각 | 단안 영상의 물체 검출, ONNX 및 RKNN 변환 | 카메라 하나 유지. X 인식 성능·전력·열 예산과 데이터 수집 필요 |
| 표현·음성 | 감정 동작 키프레임 + 소리, Reachy Mini의 GStreamer / WebRTC 미디어 구조 | 동작·표현과 보행의 연동을 참고. 브라우저 TTS를 실물 음성 시스템 완성으로 보지 않음 |

학습/실행 구성의 근거는 [공식 RL 저장소](https://github.com/pollen-robotics/microduck_rl), [정책 저장소](https://huggingface.co/pollen-robotics/microduck-policies)입니다. 현재 X 실행은 RL commit `2b25a48b08f1f17bc38c90bb03144c81fbd9ed07`에 고정했습니다. 기본 학습과 backlash 변형은 별도이므로 현재 X 시험에 기어 유격 모델까지 적용됐다고 주장하지 않습니다.

[공식 운영 설계](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/design/architecture.md)는 일부 설계 목표를 포함합니다. [통합 시뮬레이션 문서](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/design/simulation.md)는 실제 제어 프로그램을 가상 장치와 연결하는 구현을 설명합니다. 물리 엔진만 통과하면 제어 제품도 통과한다고 추론할 수 없습니다.

[공식 감정 데이터](https://huggingface.co/datasets/pollen-robotics/microduck-emotions)는 머리·몸통·소리·정책 전환을 함께 다룹니다. 머리 이동이 실물 보행에 영향을 주었다는 경험도 기록돼 있으므로, X 외형 질량을 바꾸고 감정 동작만 복사하는 접근은 피합니다. [Reachy Mini 미디어 설명](https://huggingface.co/blog/pollen-robotics/reachy-mini-media-stack)은 영상·양방향 음성·로컬/원격 SDK 구조의 참고입니다. Reachy Mini 기능을 Microduck이나 X의 기능으로 간주하지 않습니다.

## 상업용 적용 판단

원본 하드웨어와 소프트웨어·정책의 권리는 별개입니다. 원본 3D 하드웨어는 상업용 X 파일에 포함하지 않으며, 기능 치수 측정은 별도로 출처를 표시합니다. 이는 법적 권리 전체에 대한 승인 판정이 아닙니다.

[Microduck 검출기 카드](https://huggingface.co/pollen-robotics/microduck-duck-detector)는 Apache-2.0을 표시하지만 YOLO11n 기반이라고도 명시합니다. [Ultralytics 공식 안내](https://www.ultralytics.com/license)는 자사 모델·코드에 별도 AGPL/Enterprise 조건을 설명합니다. 상위 모델과 학습 경로의 권리가 해소됐다는 증거 없이 카드의 태그 하나만으로 상업용 X에 포함하지 않습니다. 이 검출기는 현재 조사 대상이며 X에 통합하거나 배포하지 않았습니다.

## 다음 합격 기준

1. 새로운 초기 조건에서 정지·전진·회전의 속도 오차와 넘어짐을 함께 평가.
2. 장기 학습 정책을 공식 실행용 정규화 포함 ONNX로 내보내 동일 시험 재실행.
3. 제품 제어 루프·정책 전환·센서 중단·복구를 통합 환경에서 검증.
4. 단일 카메라의 인식·지연·전력과 기구 시야, 목 질량·배선 검증.
5. 팔·돌출 발톱 없는 독자 기구를 실제 부품과 조립해 내구성 확인.

현재 기록: [공식 기준 시험](OFFICIAL_BASELINE.md), [X 제어 호환 범위](COMPATIBILITY.md). 제품 우위나 양산 가능 여부는 이 조사만으로 입증되지 않습니다.
