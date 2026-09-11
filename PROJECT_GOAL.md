# Micro X product design goal

Latest direction: the user requested a return to original Microduck geometry and compatibility with its pretrained weights. That derived model, revised T-rex shell and paired ONNX evaluation are developed in https://github.com/hwkim3330/micro-rex under its upstream noncommercial hardware terms. This independent Micro X repository is preserved, and its page links prominently to the active compatibility work. Selling a Microduck-derived model is not authorized by the software weight license.

Owner: hwkim3330. User requested independent, lower-cost T-rex product design, fabrication models, public GitHub and Pages, with proper licensing.

Deliver a traceable engineering prototype package: original parametric CAD, printable parts, neutral assembly, drawings and BOM, assembly interfaces, cost assumptions and evidence, interactive product/assembly page and automated geometry checks. Preserve the separate Micro Rex noncommercial experiment.

## Acceptance and limits

- No Microduck CAD, STL, body transforms, trained policies or hardware-derived model data in this repository.
- Design source and generated parts are traceable to this repository's independent dimensions.
- Original hardware/design rights are reserved for the owner; publishing source does not silently grant manufacturing rights. Separately identify software/dependency licenses.
- Every printable part must be a valid closed CAD solid and a watertight positive-volume mesh.
- Provide actual assembly interfaces and identify which interfaces have not been physically checked.
- Show honest status of motor selection, electronics, movement control, fit, durability, safety and production tooling. Static CAD is not production approval.
- User confirmed biped walking is required and requested an additional quadruped. B2 is the primary walking product; Q4 is a second platform. Both require real locomotion engineering; fixed packaging models are not walking robots.
- Public website must load its actual geometry and downloads on desktop/mobile.

## Completion ledger

- [x] Independent P0 appearance and printable CAD; actuator interfaces remain open
- [x] P0 interface drawings, provisional BOM and assembly notes; procurement BOM remains open
- [x] Editable cost assumptions and supplier price evidence (not procurement BOM)
- [x] Repository license scope and provenance inventory; commercial IP clearance remains open
- [x] P0 closed meshes, reference-pose intersection checks and web/download verification; production verification remains open
- [x] Public GitHub and Pages; both HTTP 200, initial CI and Pages deployment passed
- [ ] Actuated prototype integration (B2 walking and Q4 quadruped requirements confirmed; drive engineering remains open)
- [ ] Physical build, fit and endurance verification (requires hardware)
- [ ] Production readiness (requires supplier DFM, test results and market-specific review)

## B2 / Q4 expansion

Q4 is retired from the public viewer at the user's request. Files remain as archived design evidence. Active work here is the independent commercial Micro X: shorter friendly face, larger retained eyes, lower body, manufacturable parts, and measured validation. Micro Rex is a separate noncommercial hardware project; its policy compatibility does not apply to X.

- [x] Q4 common-part packaging CAD and model viewer selection
- [ ] B2 13-axis and Q4 15-axis candidate drive configuration validation
- [ ] Motor torque/thermal evidence, bearings, shafts and mechanical drive cartridges
- [ ] Walking controller, calibrated dynamics and physical locomotion validation

## Appearance and durability

User requested a cute and robust product competitive with Microduck. Current eye finish and rear fastening are design improvements; comparative performance remains unproven. Proposed measurable targets are in `engineering/acceptance.json`, with no physical results claimed.

## Camera and audio

- [x] Original camera carrier and nose aperture, manufacturer mounting dimensions attributed
- [x] Opt-in local JPEG capture and ALSA sample/playback paths with software unit tests
- [x] Original synthesized chirp preview and honest public feature comparison
- [ ] Physical camera, audio, sensor, compute and power integration
- [ ] Measured performance comparison against Microduck; superiority not established

## Commercial X redesign and browser lab

- [x] Owner commercial-use scope explicit; third-party design manufacturing rights remain reserved
- [x] Shorter smooth head, larger retained eyes, lower torso, shortened tail and updated printable CAD
- [x] STEP export/reimport validation and updated static/jaw checks
- [x] Printed-geometry-only center of mass report, with excluded hardware stated
- [x] Actual CAD README portrait and X-first product page
- [x] Anatomy layers and part inspection in the X Lab
- [x] Real browser-worker CEM learning for a normalized virtual jaw; held-out evaluation and policy import/export
- [x] Browser speech expression preview and desktop/mobile interaction tests
- [ ] Whole-body dynamics, locomotion training, physical integration and production verification

## Corrected compatibility target

Commercial X remains independent hardware. The original-model restoration was withdrawn. Active target: 14 axes, 61 observations, 14 actions, same pretrained actor and motor model. Independent dynamics and unchanged-weight evaluation plus PPO warm-start/export now run; some walking/standing trials fall. Full upstream training recipe parity, actuator manufacturing CAD and physical compatibility are unfinished. See docs/COMPATIBILITY.md.
