# Micro X Lab

[Open the lab](https://hwkim3330.github.io/micro-x/web/lab.html). The commercial Micro X design remains independent of the separate Micro Rex hardware experiment.

The lab uses the current 16-part Micro X GLB. Anatomy controls isolate the head, torso, legs, tail or camera carrier, select dimensions and download STEP/STL. The carrier is present; a complete camera or motor assembly is not depicted as integrated hardware.

## Learning that runs in the browser

The learning tab performs cross-entropy-method optimization in a dedicated Web Worker. Each candidate has two log-space proportional/derivative gains. The normalized virtual jaw state is position and velocity; the action is clipped to ±3 normalized units. Integration uses a fixed 1/60-second step, damping 0.12, travel 0–1 mapped to the CAD jaw's 0–20° display range. These are teaching assumptions, not identified motor/inertia parameters.

Each training rollout lasts 240 steps. Training targets are 0.15, 0.45, 0.75 and 0.9 with initial position 1−target. Loss is mean squared tracking error plus 0.0005 times mean squared action. The top fifth of candidates updates a Gaussian search distribution; the best candidate is retained. Evaluation uses separate targets 0.23, 0.63 and 0.92. The displayed RMSE includes the initial transient across the whole rollout.

Default settings: seed 42, 40 generations, 32 candidates. The deterministic reference check reduces held-out angle RMSE from approximately 5.87° to 3.57°. This is a virtual tracking exercise, not locomotion RL, an ONNX neural policy, or physical robustness evidence. It does not establish Microduck weight compatibility.

The page supports start, cancel, live loss history, held-out evaluation, target-angle replay, JSON export and import. Imports are restricted to the versioned virtual-jaw schema, two finite bounded gains, the declared algorithm and matching travel range. Imported performance is recomputed locally rather than trusting uploaded metrics. JSON files are not sent to a server.

## Voice

Text-to-speech uses the browser's speech synthesis service, with an illustrative jaw animation. Voice support and whether synthesis uses an OS/network service depend on the browser. There is no microphone capture, LLM conversation, or precise phoneme synchronization here. Empty input, unavailable speech and playback errors are surfaced. An independently synthesized dinosaur chirp is also available.

## References inspected 2026-09-10

- [Microduck Simulator](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/tree/e81974b932c7ca1819843b7bb3dcd42e2993e98e): package manifest includes browser MuJoCo and ONNX Runtime. Reference for interactive simulation/policy experiences; those engines, robot files and policies are not copied into X Lab.
- [Microduck Anatomy](https://huggingface.co/spaces/mishig/microduck-anatomy/blob/5329ff5db7c6baa5c15def88085f842e0221395e/components/microduck-blueprint.tsx): inspection component provides categories, layers and part exploration. Reference for the independent layer/part interface.
- [Reachy Mini 3D Voice](https://huggingface.co/spaces/pollen-robotics/reachy-mini-3d-voice/blob/bdcac3f73e9b7def1a71ee03d2ca7a858fd0004b/README.md): links voice to a rigged 3D character and uses a server for realtime conversation. Reference for voice expression; X Lab currently uses browser TTS instead of that backend.

Only interaction concepts are referenced. No reference CAD, textures, audio, trajectories, policy weights or application source are distributed in X Lab. Original software is MIT; original X design data retains the owner's commercial rights under the root LICENSE.

## Reproduce

```sh
npm ci
node --test tests/learning.test.mjs
node tools/test-lab.mjs
python3 -m http.server 5191
# Open http://localhost:5191/web/lab.html
```

The desktop/mobile browser checks train a real policy, replay it, download and reimport it, reject a foreign environment, cancel a run, inspect CAD layers and check overflow. Headless tests do not certify audible speech on every operating system.

Before whole-body learning, X still needs an actuated joint architecture, measured purchased-component inertias and transmissions, a validated dynamics/contact model, observation/action definitions, training/evaluation tasks and supported hardware safety limits. The current fixed-leg appearance model is not presented as that finished system.
