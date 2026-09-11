# Third-party software

- Three.js 0.180.0, MIT, bundled under web/vendor/three/. Upstream license retained as LICENSE. Source: https://github.com/mrdoob/three/tree/r180
- CadQuery 2.8.0 (Apache-2.0), Open CASCADE via cadquery-ocp, trimesh 4.11.1 (MIT), NumPy (BSD), ReportLab (BSD): build-time dependencies, not bundled in the website. Their licenses are not automatically assigned to original generated designs.
- Puppeteer 25.10.0 (Apache-2.0): test-time dependency.

No upstream Microduck mesh, CAD or hardware XML is included. Functional joint measurements are attributed in engineering/functional_interface.json. Pinned Apache-2.0 inference software and policy weights are fetched into the excluded local cache by tools/fetch_compat.py; engineering/policy_sources.json records hashes and license sources. The official mjlab training environment is installed separately under its own licenses. These software licenses do not relicense upstream hardware.

Camera mounting dimensions reference the Raspberry Pi Camera Module 3 Standard manufacturer drawing (linked in docs/FUNCTIONS.md). No manufacturer drawing or CAD is bundled. rpicam-apps and ALSA utilities are external system dependencies, not distributed here. The original synthesized chirp and runtime source are MIT under the root LICENSE scope.
