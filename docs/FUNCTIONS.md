# 카메라·음성·감각 기능

현재는 **카메라 장착 구조 + 로컬 장치 서비스 초안**입니다. 카메라, 마이크, 스피커가 실물 로봇에 모두 장착되어 작동한다는 뜻은 아닙니다. Microduck보다 높은 성능은 제품 목표이며 입증된 결과가 아닙니다.

| 기능 | Micro X 현재 구현 | 다음 검증 |
|---|---|---|
| 카메라 | Camera Module 3 Standard용 독자 브래킷, 코 Ø18 mm 포트, 명시적으로 활성화하는 JPEG 촬영 코드 | 실물 체결·케이블·초점·주변부 가림·지연 |
| 음성 입력 | ALSA 2초 모노 녹음 경로, 별도 활성화 필요 | 마이크 선정·기구 장착·모터 소음·에코 제거 |
| 소리 | 자체 합성한 짧은 울음소리, ALSA 재생 경로 | 스피커·앰프·음향 공간·음량 |
| 대화·비전 | 미구현 | 인식 모델, 연산 장치, 지연과 전력 측정 |
| IMU·거리·발 접촉 | 요구사항 기록, 부품 미선정 | 회로·배선·보정·제어 주기 |
| 보행 | B2/Q4 고정 다리 외형, 구동 요구안 | 모터·전원·관절·제어·실물 보행 |

## 비교 기준

[Microduck 런타임 소스](https://github.com/pollen-robotics/microduck/tree/bc41fb5c9a9b39894669c1e022e375cf83800382)는 게임패드 보행, 일어나기 등의 동작과 `mediad` WebRTC 영상, 소리 기능, `tofd` 거리 센서 서비스를 제공하거나 문서화합니다. 서비스 존재가 모든 판매 기기의 센서 탑재를 의미하지는 않습니다. Micro X에는 아직 WebRTC 영상, 보행 제어, 통합 음성 대화가 없습니다. 현재 완성도에서는 이 기능들을 따라잡는 작업이 먼저 필요합니다.

차별화 목표는 귀여운 표정과 자체 울음소리, 자동초점 카메라, 수리하기 쉬운 공용 구조, 모터 소음 속에서의 음성 입력입니다. 비교 실험과 원가 견적 없이 성능 우위나 더 낮은 판매 가격을 주장하지 않습니다.

## 카메라 기구

[제조사 기구 도면](https://datasheets.raspberrypi.com/camera/camera-module-3-standard-mechanical-drawing.pdf)의 PCB 및 구멍 치수만 사용해 브래킷을 직접 설계했습니다. 제조사 CAD나 그림은 재배포하지 않습니다. [카메라 사양](https://www.raspberrypi.com/documentation/accessories/camera.html): Standard 모델, 11.9 MP, 자동초점, 수평 66° / 수직 41°.

- PCB 25 × 23.862 × 1.12 mm; 장착 홀 Ø2.2 mm.
- 로봇 좌표에서 PCB 뒷면 X144, 아래 Z209.6; 홀 Y±10.5, Z211.6/224.1.
- 네 M2 체결 위치와 두 M3 측면 체결 위치를 가진 `camera_carrier`; M2×10 및 M3×10은 잠정안입니다. 나사 머리·너트·와셔·PCB 부품 간섭, 조립 순서와 체결 토크는 실물 확인이 필요합니다.
- 광축 Z224, 코의 개구 Ø18 mm. 가정한 동공 위치 X152.1 및 여유를 적용한 [개구 계산](../artifacts/camera_fit.json)에서 반지름 여유 약 0.63 mm입니다. 실제 비네팅이나 전체 전자부품 간섭의 검증 결과는 아닙니다.
- FPC 홈을 두었지만 케이블 굽힘과 몸통까지의 배선은 미완성입니다. Pi Zero 계열에는 맞는 15→22핀 카메라 케이블이 필요합니다.

[Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)는 촬영 서비스 초기 시험용 후보입니다. 전체 비전·대화·보행을 동시에 처리할 최종 보드로 선정하지 않았습니다. 배터리, 보호 회로, 모터 전원, 로직 전원과 발열 설계도 남아 있습니다.

## 로컬 장치 서비스 실행

Raspberry Pi OS에서 카메라를 연결하고 제조사 [rpicam 사용 안내](https://www.raspberrypi.com/documentation/computers/camera_software.html)에 따라 `rpicam-still --list-cameras`를 먼저 확인합니다. 음성 경로는 ALSA의 `aplay`, `arecord`와 운영자가 설정한 기본 장치를 사용합니다. 공개 Pages는 로컬 장치에 자동 연결하지 않습니다.

```sh
# 장치 목록만 조회: 사진 촬영/마이크 녹음/소리 재생 없음
python3 runtime/device_service.py --probe
# 단위 시험: 명령 대역만 사용, 실제 장치 검증 아님
python3 -m unittest discover -s tests -v
```

활성화는 운영자가 장치에서 수행합니다. 다음 명령은 24자 이상 임의 토큰 파일을 만들며 화면에 토큰을 출력하지 않습니다. 세 활성화 옵션은 각각 생략할 수 있습니다.

```sh
python3 -c 'import os,secrets; f=os.open("device.token",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(f,secrets.token_hex(32).encode()); os.close(f)'
python3 runtime/device_service.py --token-file device.token --enable-camera --enable-audio --enable-microphone
```

서비스는 `127.0.0.1:8765`에만 바인딩합니다. `GET /health`, `GET /camera/status`는 열거 결과입니다. `POST /camera/snapshot`, `/audio/chirp`, `/audio/sample`에는 `Authorization: Bearer <토큰>`이 필요합니다. 녹음은 요청당 2초이며 자동 시작하지 않습니다. 다른 컴퓨터에 공개하는 서버 용도는 아닙니다.

장치 없음/비활성화/명령 실패는 오류를 반환하며 합성 사진이나 녹음으로 대체하지 않습니다. 음원 재생 명령의 성공도 실제 스피커에서 소리가 났다는 검증은 아닙니다. `artifacts/device_probe.json`은 개발 호스트의 열거 기록이며 로봇 탑재 부품 목록이 아닙니다.

## 귀여움과 권리

눈동자와 하이라이트는 도색 표현, 울음소리는 `runtime/sound.py`에서 직접 합성한 예시입니다. 제조사나 다른 로봇의 음원을 추출하지 않았습니다. 소프트웨어와 자체 합성 WAV는 MIT, 원본 CAD는 루트 LICENSE 범위를 따릅니다.
