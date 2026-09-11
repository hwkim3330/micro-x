# MICRO X

**현재 목표: Microduck 제어·가중치·학습 인터페이스와 호환되는 상업용 독자 기구.** 원본 CAD로 복귀하는 방향은 취소했습니다. [14축 호환 개발과 실제 실패 포함 시험 기록](docs/COMPATIBILITY.md)

![Micro X — actual CAD, mint and cream T-rex](artifacts/readme_hero.png)

**소유자 hwkim3330가 제작·판매할 상업용 독자 설계 티렉스입니다.** 비상업 조건의 Micro Rex와 별도 프로젝트입니다. **현재 P0 외형·조립 설계이며, 완성된 구동 로봇이나 양산 승인품은 아닙니다.**

[제품 개발 페이지](https://hwkim3330.github.io/micro-x/) · **[14축 가중치·학습 Lab](https://hwkim3330.github.io/micro-x/web/lab.html#compatibility)** · [목표와 진행 기준](PROJECT_GOAL.md) · [출처와 권리](docs/PROVENANCE.md)

기존 [Micro Rex 비상업 시제품](https://github.com/hwkim3330/micro-rex)은 별도 보존합니다. 이 저장소의 CAD는 독립적인 치수와 기본 형상으로 새로 생성하며, Microduck 원본 메시·CAD·하드웨어 XML을 포함하지 않습니다. 별도 14관절 연구에는 출처를 명시한 기능적 관절 치수와 축 측정값을 사용하며, 학습 소프트웨어와 가중치는 별도 라이선스로 로컬에 내려받습니다.

## 제공 파일

- `cad/build.py`: 독자적인 매개변수 CAD 생성기 (mm).
- `models/micro_x.step`, `models/micro_x.glb`: 전체 외형 조립체.
- `models/step/`, `models/print/`: 부품별 STEP 및 출력 방향을 정리한 STL.
- `artifacts/drawings.pdf`, `artifacts/bom.csv`: 부품 도면 및 잠정 BOM.
- `artifacts/validation.json`: 닫힌 메시·출력 범위 검사. 물리적 제작 검증과 구분합니다.
- 웹페이지: 실제 모델 회전·분해·부품 선택·턱 자세 시연·파일 다운로드·가정 기반 원가 비교.

## 이번 X 디자인

주둥이를 22 mm 줄이고 머리·꼬리를 곡면으로 다듬었습니다. 상체 위치를 24 mm 낮추고 다리 길이를 맞췄으며, 큰 크림색 눈과 민트·크림 배색을 적용했습니다. README 이미지는 이 저장소의 실제 14개 CAD 부품을 렌더링한 것입니다.

STEP를 내보낸 뒤 다시 읽어 유효한 입체인지 검사합니다. 기본 자세 부품 간 겹침과 0–20° 턱의 2° 간격 검사에서 겹침이 없습니다. 출력 형상만 계산한 무게중심의 정적 지지영역 여유는 약 32.15 mm입니다. 배터리·모터·나사·변형을 제외한 값이며 전체 로봇의 안정성이나 내구성 검증은 아닙니다. [계산 기록](artifacts/balance.json)

## 직접 학습하는 웹

Lab에서 구조 레이어를 살펴보고 가상 턱 정책을 브라우저에서 직접 학습·평가·실행·저장·불러오기 할 수 있습니다. 음성 합성과 턱 표현도 제공합니다. Hugging Face의 Simulator·Anatomy·3D Voice를 인터랙션 참고로 삼아 독자 구현했습니다.

현재 학습 범위는 정규화된 **가상 턱 1축 제어**입니다. 별도 14축 동역학 연구에서는 공식 가중치 실행과 같은 신경망의 PPO 학습·ONNX 내보내기를 구현했습니다. 보행 호환 및 원본 전체 학습 설정의 동일성은 아직 미달입니다. [학습 환경, 참고 링크, 테스트 방법](docs/LAB.md)

[실제 보행 조작 화면](https://hwkim3330.github.io/micro-x/web/simulator.html)에서는 로컬 서버의 MuJoCo·BAM·공식 ONNX로 움직임을 계산합니다. 공개 페이지는 정지 미리 보기이며, 제품 외장과 별도인 14관절 동역학 모델을 표시합니다. [Pollen 전체 구성 조사와 적용 판단](docs/POLLEN_STACK_REVIEW.md)

## 재생성

```sh
python3 -m pip install -r requirements.txt
python3 cad/build.py
python3 cad/coupons.py
python3 tools/interference.py
python3 tools/jaw_clearance.py
python3 tools/documents.py
python3 tools/camera_fit.py
python3 tools/balance.py
python3 tools/validate.py
python3 -m unittest discover -s tests -v
npm ci
npm test
node --test tests/learning.test.mjs
node tools/test-lab.mjs
node tools/portrait.mjs
python3 -m http.server 5191
```

[조립 문서](docs/ASSEMBLY.md)에 체결 좌표와 미해결 연결부를 기록했습니다. 현재 목·머리의 최종 체결 및 꼬리의 실물 끼워맞춤, 구동부, 간섭 검증, 실물 시험이 남아 있습니다. 이 상태로 양산 발주하거나 완성 로봇으로 판매할 수 있다는 뜻이 아닙니다.

## 권리와 판매 방향

원본 기구·CAD 생성 소스·모델·도면은 소유자 권리를 유보합니다. **소유자의 원본 설계 상업 이용·제작·판매를 금지하는 비상업 라이선스가 아닙니다.** 공개 저장소 열람이 제3자에게 추가적인 제조·판매 허락을 뜻하지는 않습니다. 웹과 일반 도구 코드는 MIT, Three.js는 원래 MIT 조건을 유지합니다. 상세 범위는 [LICENSE](LICENSE), [THIRD_PARTY.md](THIRD_PARTY.md)를 따릅니다. 제품 이름과 독자 설계의 권리 검토는 상용 출시 전에 별도로 필요합니다.

## 두 발 티렉스에 집중

사용자 요청에 따라 Q4는 공개 모델 선택에서 내렸습니다. 기존 CAD는 설계 기록으로 보존하며, 예전 Q4 웹 링크는 B2로 연결됩니다. 현재 이 저장소에서는 **상업용 Micro X의 독자 설계와 제품화**에 집중합니다. Micro Rex의 관절·가중치 호환 시험 결과를 X의 성능으로 주장하지 않습니다. 저가형 Nano Rex는 후속 단계입니다.

[플랫폼 요구사항과 하중 검토](docs/PLATFORMS.md) · [Q4 CAD](models/q4/micro_x_q4.step) · [검사 기록](artifacts/q4_validation.json)

```sh
python3 tools/platform_screen.py
```

## 표정과 고정 구조 개선

눈동자·하이라이트는 GLB의 도색 표현이며 추가 소형 부품이 아닙니다. 눈 부품을 안쪽 M3 나사와 일체형 받침판으로 고정하도록 변경했고 팔·팔 고정부·돌출 발톱을 제거하고 둥근 발바닥으로 정리했습니다. 고정력·반복 수명·낙하·수리 시간은 [시험 목표](engineering/acceptance.json)로 관리하며 실물 통과값은 아직 없습니다. [설계 상세](docs/DESIGN_QUALITY.md)

## 카메라와 음성

기본형은 **중앙 카메라 1개 + 표정용 눈 2개**입니다. 눈은 카메라가 아닙니다. 카메라 2개는 깊이 인식이 필요한 별도 스테레오 버전으로 보류하며, 현재 구현된 기능으로 표시하지 않습니다. [버전 기준과 검증 조건](engineering/camera_variants.json)

Camera Module 3 Standard의 제조사 장착 치수에 맞춘 독자 브래킷과 코의 렌즈 포트를 추가했습니다. 현재 B2는 14개 출력 부품입니다. 로컬 장치 서비스는 명시적으로 활성화한 촬영·마이크 샘플·합성 울음소리 재생을 지원하며 실제 로봇 검증은 아직 없습니다. [기능 상태·비교·실행 방법](docs/FUNCTIONS.md)

### 실제 실행 보드

개발용 Pi 5 4GB → 제품 검토용 CM5 4GB를 우선 후보로 정했습니다. 보행·행동 계산은 로봇 내부, 학습은 PC에서 실행하는 구조입니다. [배선 구상·전체 신경망 CPU 실측·미검증 항목](docs/ONBOARD_COMPUTE.md)을 확인하세요. 실제 보드·전원 검증 전이며 기존 7.4 V BAM 실험은 XL330의 실물 전원 사양이 아닙니다.
