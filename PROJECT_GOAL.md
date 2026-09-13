# Micro X product design goal

Owner: hwkim3330. Commercial, independently designed T-rex companion robot that keeps the Microduck 14-axis policy interface. The noncommercial Micro Rex repository stays separate as the unchanged-Microduck reference rig.

## Direction as of 2026-09-13 (Rev B)

User direction, in order: the P0 appearance was rejected; make X as cute as the original Microduck; drop parts that can break off (eyes, hands, claws); this is for sale, so do it properly and make it easy to print. Rev B therefore:

- measures the reference robot's joint layout at qpos 0 (straight legs) instead of the HOME pose, so every axis is world-aligned and every bracket prints flat;
- holds each servo the way the reference does - body in a U-channel on one link, a single horn plate on the next - giving 20 printed parts at 347 g;
- has no eye, hand or claw parts: the nose camera is the eye and the eyes are painted;
- measures each joint's collision-free travel by exact-boolean bisection and uses those numbers as the MuJoCo joint limits, instead of declaring a range and hoping;
- reports printability (bed fit, overhang fraction, bed contact) per part;
- generates the 14-axis MuJoCo model from the CAD meshes and re-runs the unchanged official weights on it;
- ships a Lab where the same evaluation protocol covers the official weights and locally trained checkpoints, and replays recorded gaits on the real CAD rig.

## Acceptance and limits

- No Microduck CAD, STL, body transforms, trained policies or hardware-derived model data in this repository. Functional joint pivots/axes are attributed measurements.
- Every printable part is a valid closed CAD solid and a watertight mesh; the HOME assembly has no exact-STEP overlaps; single-joint sampled sweeps are recorded with any remaining collision samples listed.
- Servo interface dimensions are purchased-part data; case hole pattern, cable exits and voltage rail must be confirmed before ordering.
- Static CAD, simulation upright-ness and ONNX loading are not walking acceptance. Acceptance needs measured velocity/yaw tracking, fall rates and reproducible training, then physical trials.
- Cost model uses retail servo pricing and stated assumptions; it is not a quote.

## Completion ledger

- [x] Rev B actuated CAD: 20 printed parts, 15 servo envelopes, battery/board/camera placements, STEP/STL/GLB, drawings and BOM
- [x] Chibi appearance per user request; README portrait rendered from the actual CAD
- [x] Static interference clear in the design pose; per-joint sweeps clear inside the measured travel; travel and printability published as artefacts
- [x] CAD-derived 14-axis dynamics model with the pinned adapter; unchanged official weights evaluated on it
- [x] Lab: anatomy, 14-axis studio (train / evaluate / compare / download), gait replay on the CAD rig, 1-axis teaching example, voice
- [x] Local simulator drives the CAD rig from MuJoCo qpos with official or trained policies
- [ ] Servo case retention and cable routing after the drawing is confirmed
- [ ] IMU, microphone, speaker, power board placement; compute carrier design
- [ ] Printed coupons, one leg, full assembly; physical fit, endurance, drop, thermal tests
- [ ] Walking acceptance (measured tracking, fall rate) in simulation, then on hardware
- [ ] Supplier quotes, DFM, market/rights review before any sale

## Historical

P0 appearance-only shells and the Q4 quadruped packaging study are archived (`models/q4/`, `models/archive/p0_parts.json`, git history). The primitive 14-axis study model is kept at `models/archive/micro_x_14_primitive_study.xml` so its recorded evaluations stay verifiable.
