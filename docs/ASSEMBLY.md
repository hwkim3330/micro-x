# P0 assembly and unresolved interfaces

**This is an appearance/fit development model, not a complete powered robot kit.** All dimensions use the independent CAD coordinate system: X forward, Y left, Z up; mm. `models/print/` contains bed-oriented STL. STEP and `models/*.stl` retain the world assembly pose. Use one set, not duplicate print and world files.

## Defined interfaces

- Torso split at Z = 180 mm. Four screw axes: X = -25 and +15 mm, Y = ±22 mm, parallel to Z. Upper Ø3.4 clearance, lower Ø2.6 pilot over Z167–180. M3 plastic thread-forming screw fit and head access must be tested; do not substitute a heat-set insert into the pilot without redesign. Screw lengths depend on the local roof height and available product; measure STEP before procurement.
- Rear leg axes: X = -14 mm, Z = 143 mm, parallel to Y, Ø3.4 clearance. Fixed pose concept; one axis does not provide anti-rotation locking. Final fastener/locking feature is pending.
- Ankle axes: X = 8 mm, Z = 27 mm, parallel to Y, Ø3.4 clearance. Feet have fork lugs. Add washers only after measuring actual print clearance.
- Jaw axes: X = 59 mm, Z = 212 mm, parallel to Y, Ø3.4 clearance. Two side bolts are intended; sufficient bearing engagement, stops and finger access are unverified.
- Eyes: independent sphere/socket pair with 0.2 mm radial adhesive allowance. Adhesive is a prototype method, not validated captive retention for a consumer product.

- Tail seam: transverse M3 axes at (X,Z) = (-100,145) and (-155,133), Ø3.4. Axial tail-to-torso bolts: Y = ±8, Z = 153, parallel to X, Ø3.4 in tail / Ø2.6 torso pilots. Mating face X = -58. Verify print fit and select bolt lengths from the STEP stack.
- Forearm posts: X = 36, Z = 181, parallel to Y, Ø3.4; inner arm faces Y = ±34. Posts are split by the torso service seam, so access and stiffness need a build test.

## Prototype evaluation sequence

1. Review the full assembly STEP and unresolved interfaces before printing a complete set.
2. Print a torso screw and jaw hinge interface coupon; tune dimensional compensation for the actual printer/material.
3. Print upper/lower torso and jaw/skull for access/clearance assessment. Test screw selection and opening sequence without electronics.
4. Check foot/leg alignment in a supported fixture. Do not use the fixed mock-up to infer balance or walking capability.
5. Trial the tail seam and axial mounting bolts, then the forearm posts. Neck/head retention remains unresolved; support those parts in a fixture. None of these interfaces is a production release.
6. Integrate the selected drive cartridges, cable paths and controller only after the product architecture is settled.

## Explicit remaining work

- Neck/head retention assembly and physical verification of the new tail bolt interfaces.
- Forearm motion stops and fastener stack; anti-rotation rear-leg fixing.
- Jaw motion stops, bearing stack and retention; eye insert retention.
- Actuator cradles with verified purchased-part dimensions, horn and load path.
- Continuous assembly clearance sweep including screws/tolerances, slicer settings and support removal access. Reference-pose STEP intersections have been cleared; see artifacts/interference.json.
- Electronics, power distribution, firmware and motion/thermal testing.

No adhesive joint or missing interface should be interpreted as production-ready. This package is P0, with visible design debt rather than a manufacturing release.

## Calibration files and static geometry evidence

`models/coupons/m3_pilot_coupon.stl`: left-to-right X order Ø2.4 / 2.5 / 2.6 / 2.7 / 2.8 mm, blind pilots with 1 mm bottom. `m3_clearance_coupon.stl`: Ø3.1 / 3.2 / 3.3 / 3.4 / 3.5 mm, through holes. These test actual printer and screw combinations; no particular screw supplier fit is implied.

The neck entry clearance tool is the union of its shape translated by ±0.3 mm along each CAD axis. This reserves an axial clearance envelope, not an exact constant normal offset. Foot fork opening is 18.6 mm for an 18 mm leg. Both still need physical tolerance tests.

Exact STEP booleans show no positive-volume overlap among the 15 parts at the reference pose (threshold 0.01 mm³). The jaw is separately sampled every 2° from 0° to 20°. Fasteners, production tolerances, continuous movement, load and minimum pinch gap are outside these checks.
