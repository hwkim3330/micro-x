> Rev A(2026-09-13)에서 P0 외형 설계가 폐기되었습니다. 현재 설계 원칙과 검증 상태는 [DESIGN_REVA.md](DESIGN_REVA.md)를 보세요. 아래는 P0 기록입니다.

# Cute appearance and measurable durability

The user requested a cute, robust product that can compete with Microduck. We treat that as a design and verification objective, not an achieved comparative claim.

## Implemented in the current CAD

- Large eyes now have dark pupils and two highlights in the GLB paint mask. These marks are a paint/multicolor finish specification, not extra detachable CAD components. STL remains geometry-only; no paint adhesion or wear resistance is implied.
- Adhesive-only eye spheres are replaced by caps with an integral Ø10 mm rear boss, Ø2.6 mm by 7 mm pilot and a 2 mm integrated skull support plate with Ø3.4 mm clearance. Intended fastening is an M3 plastic thread-forming screw fitted from inside the skull. Candidate M3×8 length with a 1 mm washer gives approximately 5 mm engagement; verify actual chosen screw head, thread, torque and clearance before ordering. Thread-forming fit is material/process specific and has not been validated.
- Forearms, their torso posts and decorative toe projections are removed. Continuous rounded soles retain the existing ankle interface. This reduces parts and exposed projections; strength and drop performance still require physical tests.
- Q4 shares the same new eye/head geometry, avoiding two independent cosmetic/retention designs.

## What must be measured

`engineering/acceptance.json` records proposed test targets with **null results**. Eye retention, loaded joint endurance, drop behavior, drive-module replacement time and actual walking tests remain open. No physical robustness conclusion follows from watertight STL or lack of static CAD overlap.

Cost reduction must preserve load capacity and service life. Current load screening rejects the cheaper B2 candidate under the stated assumptions; see `docs/PLATFORMS.md`. The next drive design needs verified motor data, supported shafts/bearings, cable strain relief and a locking/retention strategy.

Both eye print STLs place the rear boss on the bed; support is still needed under the cap rim. Q4 shared parts reuse the exact B2 print STL bytes, preserving the same print setup rather than silently rotating a common part differently.
