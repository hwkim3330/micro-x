# Micro X product design goal

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
