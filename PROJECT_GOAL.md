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
- Final locomotion configuration is awaiting product decision; develop common appearance/assembly first. Do not silently label a fixed mock-up a walking robot.
- Public website must load its actual geometry and downloads on desktop/mobile.

## Completion ledger

- [x] Independent P0 appearance and printable CAD; actuator interfaces remain open
- [x] P0 interface drawings, provisional BOM and assembly notes; procurement BOM remains open
- [x] Editable cost assumptions and supplier price evidence (not procurement BOM)
- [x] Repository license scope and provenance inventory; commercial IP clearance remains open
- [x] P0 closed meshes, reference-pose intersection checks and web/download verification; production verification remains open
- [x] Public GitHub and Pages; both HTTP 200, initial CI and Pages deployment passed
- [ ] Actuated prototype integration (depends on locomotion/product selection)
- [ ] Physical build, fit and endurance verification (requires hardware)
- [ ] Production readiness (requires supplier DFM, test results and market-specific review)
