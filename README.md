# MICRO X

독자적인 티렉스 로봇 제품을 개발하는 공개 설계 기록입니다. **현재 P0 외형·조립 설계이며, 완성된 구동 로봇이나 양산 승인품은 아닙니다.**

[제품 개발 페이지](https://hwkim3330.github.io/micro-x/) · [목표와 진행 기준](PROJECT_GOAL.md) · [출처와 권리](docs/PROVENANCE.md)

기존 [Micro Rex 비상업 시제품](https://github.com/hwkim3330/micro-rex)은 별도 보존합니다. 이 저장소의 CAD는 독립적인 치수와 기본 형상으로 새로 생성하며, Microduck 메시·CAD·관절 데이터·학습 정책을 포함하지 않습니다.

## 제공 파일

- `cad/build.py`: 독자적인 매개변수 CAD 생성기 (mm).
- `models/micro_x.step`, `models/micro_x.glb`: 전체 외형 조립체.
- `models/step/`, `models/print/`: 부품별 STEP 및 출력 방향을 정리한 STL.
- `artifacts/drawings.pdf`, `artifacts/bom.csv`: 부품 도면 및 잠정 BOM.
- `artifacts/validation.json`: 닫힌 메시·출력 범위 검사. 물리적 제작 검증과 구분합니다.
- 웹페이지: 실제 모델 회전·분해·부품 선택·턱 자세 시연·파일 다운로드·가정 기반 원가 비교.

## 재생성

```sh
python3 -m pip install -r requirements.txt
python3 cad/build.py
python3 cad/coupons.py
python3 tools/interference.py
python3 tools/jaw_clearance.py
python3 tools/documents.py
python3 cad/quadruped.py
python3 tools/documents.py --variant q4
python3 tools/camera_fit.py
python3 tools/validate.py
python3 -m unittest discover -s tests -v
npm ci
npm test
python3 -m http.server 5191
```

[조립 문서](docs/ASSEMBLY.md)에 체결 좌표와 미해결 연결부를 기록했습니다. 현재 목·머리의 최종 체결 및 꼬리·앞팔의 실물 끼워맞춤, 구동부, 간섭 검증, 실물 시험이 남아 있습니다. 이 상태로 양산 발주하거나 완성 로봇으로 판매할 수 있다는 뜻이 아닙니다.

## 권리와 판매 방향

원본 기구·CAD 생성 소스·모델·도면은 소유자 권리를 유보합니다. 공개 저장소 열람이 추가적인 제조·판매 허락을 뜻하지 않습니다. 웹과 일반 도구 코드는 MIT, Three.js는 원래 MIT 조건을 유지합니다. 상세 범위는 [LICENSE](LICENSE), [THIRD_PARTY.md](THIRD_PARTY.md)를 따릅니다. 제품 이름과 독자 설계의 권리 검토는 상용 출시 전에 별도로 필요합니다.

## B2 두 발형 + Q4 네 발형

두 발 보행을 주 제품 요구사항으로 확정했고, 공용 부품을 이용한 Q4 네 발형을 추가했습니다. 웹에서 두 모델을 전환할 수 있습니다. Q4는 20개 부품 인스턴스의 STEP·GLB·출력 STL을 제공합니다. 현재는 고정 다리의 배치 시제품이며, 실제 보행 구동계는 미완성입니다.

[플랫폼 요구사항과 하중 검토](docs/PLATFORMS.md) · [Q4 CAD](models/q4/micro_x_q4.step) · [검사 기록](artifacts/q4_validation.json)

```sh
python3 cad/quadruped.py
python3 tools/platform_screen.py
```

## 표정과 고정 구조 개선

눈동자·하이라이트는 GLB의 도색 표현이며 추가 소형 부품이 아닙니다. 눈 부품을 안쪽 M3 나사와 일체형 받침판으로 고정하도록 변경했고 앞팔 모서리를 R0.7로 다듬었습니다. 고정력·반복 수명·낙하·수리 시간은 [시험 목표](engineering/acceptance.json)로 관리하며 실물 통과값은 아직 없습니다. [설계 상세](docs/DESIGN_QUALITY.md)

## 카메라와 음성

Camera Module 3 Standard의 제조사 장착 치수에 맞춘 독자 브래킷과 코의 렌즈 포트를 추가했습니다. B2 16개, Q4 20개 출력 부품입니다. 로컬 장치 서비스는 명시적으로 활성화한 촬영·마이크 샘플·합성 울음소리 재생을 지원하며 실제 로봇 검증은 아직 없습니다. [기능 상태·비교·실행 방법](docs/FUNCTIONS.md)
