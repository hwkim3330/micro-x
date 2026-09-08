# Provenance and commercial boundaries

This is a newly initialized repository, not a fork of Microduck or the earlier Micro Rex retrofit. `cad/build.py` constructs geometry from explicit dimensions using CadQuery primitives and lofts; it reads no external robot geometry. Body outlines, joint display pivots and part splits originate in this file. The developer previously inspected Microduck sources, so this is not represented as a formal clean-room legal process.

The old Micro Rex geometry stays in its separate repository. Its pinned upstream Microduck RL README states hardware designs are CC BY-SA-NC, without a version in that notice:
https://raw.githubusercontent.com/pollen-robotics/microduck_rl/2b25a48b08f1f17bc38c90bb03144c81fbd9ed07/README.md

No conversion of those rights to a commercial license is attempted. The general NC restriction is described by Creative Commons at https://creativecommons.org/licenses/by-nc-sa/4.0/ ; that page does not determine the unspecified version of the upstream notice.

Original design data including parametric CAD source is reserved for the owner under the root LICENSE. Software utilities and web application logic are MIT. Three.js is MIT and retains its upstream text. Public GitHub access is not an additional manufacturing grant. This is a chosen publication policy, not a legal opinion establishing ownership or freedom to operate. Micro X is a working name; trademark/design/patent searches and supplier rights review remain product launch gates.

## Supplier research, accessed 2026-09-08

- ROBOTIS XL330-M288 official manual: https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/ . Used for candidate comparison only. No CAD copied.
- Waveshare ST3215 family product page: https://www.waveshare.com/product/modules/st3215-servo.htm . Listed family price $16.99–21.99, different voltage variants; not a negotiated quote or a validated actuator selection. Do not assume the same voltage/torque for every variant.
- FEETECH SCS0009 manufacturer PDF links were located but retrieval failed. No dimensional or torque claims from those unread files were used in this CAD.
- Pollen Robotics Robot HAT repository is Apache-2.0, unlike the noncommercial mechanical model: https://github.com/pollen-robotics/elec_RPI_Robot_HAT . Not bundled or integrated here.

None of the supplier names imply partnership, endorsement or manufacturing approval.
