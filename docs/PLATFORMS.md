> 기록 문서. B2/Q4 13/15축 계획은 Rev A의 14+1축 구동 설계로 대체되었습니다. [DESIGN_REVA.md](DESIGN_REVA.md) 참고.

# Micro X B2 and Q4 product platforms

User confirmed that the primary product must walk on two legs and requested an additional four-legged model. Locomotion is required, not an optional animation. P0 geometry is a packaging study, not that finished locomotion mechanism.

| Item | B2 primary biped | Q4 additional quadruped |
|---|---|---|
| Candidate leg axes | 5 per leg: hip roll/pitch, knee pitch, ankle pitch/roll | 3 per leg: hip roll/pitch, knee pitch |
| Common head axes | yaw, pitch, jaw | yaw, pitch, jaw |
| Candidate total | 13 actuators | 15 actuators |
| Target mass, assumption | 1.5 kg | 1.8 kg |
| Loaded support legs for initial screen | 1 | 2 |
| First locomotion requirement | Controlled straight-line steps, then turning | Crawl with three-foot support, then dynamic gait if verified |

B2 initially omits hip yaw; turning capability must be demonstrated, not inferred from axis count. Q4's torque screen uses two support legs as a demanding load-sharing case, not proof that a trot is viable. The tail and small cosmetic arms remain passive in the axis budget.

## Shared design and assembly files

`models/q4/micro_x_q4.step` and `.glb` are the new four-legged assembly. It contains 20 part instances using 14 existing original designs plus two new side rails. The front/rear leg-and-foot designs are repeated, rather than independently remodeled. Across B2 and Q4 there are 18 unique printable designs at this stage; this does not imply a measured cost saving.

Q4 leg instances use X offsets +64 mm (front) and -46 mm (rear) from the common leg geometry, and Y offsets +6 mm left / -6 mm right. Hip axes therefore have X = +50 / -60 mm and Z = 143 mm. Rail centers are Y = ±47.2 mm; thickness 5.4 mm. Rails have M3 clearance axes at X = -60 / -14 / +50, Z143. A 0.5 mm nominal gap separates rail and existing torso boss, and a 0.1 mm gap separates rail and leg. These are nominal CAD dimensions, not confirmed printer fits.

The two rails are packaging supports. Anti-rotation, fastener retention, bearing spacing, flexural strength and motor reaction paths are not complete. The common solid leg must be replaced with actual articulated links and motor cartridges before either model walks.

## Load and cost screening

Run `python3 tools/platform_screen.py` to generate `artifacts/platform_screen.json`. The simple calculation is `mass × gravity / supporting legs × horizontal moment arm × load multiplier`.

Under the stated assumptions, B2 requires 1.103 N·m and Q4 0.794 N·m. A hypothetical 30% of the candidate's 30 kg·cm stall value is 0.883 N·m: B2 **fails this assumed screen**, and Q4 has only 1.11× margin. The 30% factor is an assumption, not measured continuous performance. Neither result approves the motor. Link self-weight, acceleration, impacts, thermal conditions and real geometry must be included in the next model.

The family-price comparison for 13 or 15 axes is not a final BOM. The head may use smaller servos and the legs may require stronger ones. Sharing a module is worthwhile only if the same load, speed and supply requirements are met.

## Next engineering gates

1. Freeze load cases, physical link lengths, speed, payload and service life targets. Keep assumptions editable until measured.
2. Obtain dimensioned manufacturer drawings and continuous-duty evidence, or measure samples. Choose bearings and shaft supports before committing outer-shell tooling.
3. Design a pitch/knee cartridge and separate B2 ankle unit. Check actual motor, horn, screws, connectors and cable sweeps in the assembly.
4. Build calibrated articulated simulation and controllers; report falls, motor saturation and thermal limitations rather than just rendering motion.
5. Bench-test a loaded single leg, then a restrained platform, then untethered locomotion. Record physical evidence before calling it a walking product.
6. Freeze EVT/DVT/PVT and supplier DFM gates before production procurement. Market compliance and intended user age remain to be determined.
