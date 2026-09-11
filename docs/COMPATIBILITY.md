# Commercial Micro X, compatible control target

The active goal is an independently designed commercial Micro X with the same policy interface as Microduck. It is **not** a return to original Microduck CAD or a relicensing of noncommercial hardware. The earlier “original model first” direction was withdrawn.

## Three separate pieces

1. The existing 14-part printable P0 shell is an appearance/assembly prototype with fixed legs. It is not an integrated 14-axis robot.
2. `cad/compat_model.py` creates a separate, independent 14-axis MuJoCo study using authored primitive shapes and assumed masses. Functional joint axes and pivot locations at HOME were measured from the separate reference model and rounded to 0.1 mm; see `engineering/functional_interface.json` for source attribution. No upstream meshes, component surfaces, mass or inertia tables are imported. It is not manufacturing CAD or a validated physical model of P0.
3. `runtime/compat_env.py` connects that study to pinned, unchanged inference software and walking/standing ONNX weights. Only software and weights are downloaded to the excluded local cache; source hashes and URLs are in `engineering/policy_sources.json`.

The design owner retains commercial use of original X designs. The published policy model card declares Apache-2.0, and the inference software repository has an Apache-2.0 license. Those software terms do not grant a commercial license to upstream hardware. Functional interface names and HOME references are used for interoperability; no claim of trademark/patent clearance or legal clean-room certification is made.

## Control contract

`engineering/control_interface.json` fixes 14 actuator names and order, HOME offsets, 61 observations, 14 actions, a 13-value command vector and 50 Hz control over 200 Hz physics. Observation order is gyro (3), projected gravity (3), HOME-relative joint position (14), joint velocity (14), previous action (14), command (13). Targets are HOME + action, scale 1. The actuator study uses the published XL330 BAM M6 settings: kp 200, 7.4 V, sag gain 0.1 and voltage floor 6 V.

The target hardware arrangement is five axes in each leg (hip yaw/roll/pitch, knee, ankle) and four neck/head axes (neck pitch, head pitch/yaw/roll). The jaw is not one of the 14 policy-controlled axes. This replaces the earlier 13-axis ST3215-oriented planning assumption; that cost study does not demonstrate weight compatibility.

## Actual evaluation, not a compatibility claim

`artifacts/compat_evaluation.json` records untouched walking and standing weights on the independent X study, using 0, 0.1 and 0.3 m/s forward commands and 0.3 rad/s turning, plus standing. Three initial-noise seeds and ten-second trials are used. The current functional-interface study stays upright in all 15 trials. It still has substantial tracking error: the seed-0 0.3 m/s forward trial ends at X=0.7846 m, Y=0.6199 m after ten seconds. Low-command upright behavior does not demonstrate command tracking. The complete report, including first-fall times, is published rather than treating successful ONNX loading as successful walking.

Whole-body geometry, axes, masses, inertias, transmissions and contact behavior still need to converge before “drop-in weights compatible” is justified. Real-hardware compatibility and production readiness remain unverified.

## Training and exporting the same actor

`runtime/trainable_policy.py` loads the official actor and its fixed observation normalization into a differentiable PyTorch network of the same 61→512→256→128→14 ELU architecture. It rejects a different ONNX operator layout. Against 128 seeded input vectors, the initial conversion's maximum absolute discrepancy is approximately 9.1e-7.

`tools/train_compat.py` genuinely updates that actor with PPO rollouts in the independent X MuJoCo/BAM environment, saves a checkpoint and exports a new ONNX. The checkpoint is a fine-tuned X policy, **not the unchanged official weights**. Original policy files are preserved separately. The export is checked against the trained PyTorch actor. `artifacts/compat_training.json` records the executed run, falls, losses, update count and hashes.

The compact training harness is **not identical to the full upstream mjlab training recipe**: rewards, domain randomization, curriculum, parallel simulation and versioned training stack are handled separately by the new `tools/train_official_recipe.py` adapter, whose smoke trial and remaining parity limits are reported in `docs/OFFICIAL_BASELINE.md`. Same actor, input/output contract and motor model are necessary steps, not evidence that all training behavior is the same. Short training runs are pipeline checks and do not prove a better walking policy.

## Run locally

```sh
python3 -m venv --system-site-packages .venv-policy
.venv-policy/bin/python -m pip install -r requirements-policy.txt
.venv-policy/bin/python tools/fetch_compat.py
python3 cad/compat_model.py
.venv-policy/bin/python tools/evaluate_compat.py --seconds 10 --seeds 3
.venv-policy/bin/python tools/train_compat.py --updates 30 --steps 256
.venv-policy/bin/python runtime/training_service.py
# Open http://127.0.0.1:5201/web/lab.html
```

The local workbench starts/cancels real training processes and downloads the generated ONNX. It binds only to loopback, rejects foreign origins, validates bounded integer settings, runs fixed commands without a shell, and exposes no motor endpoint. Public GitHub Pages displays published results and links to these local instructions; it does not pretend to run server-side training.

Before commercial manufacture, finish independently authored actuator housings and load paths, purchased-part fit, measured inertia and thermal/power design, original-recipe training acceptance, unchanged-weight command-tracking acceptance, and physical validation. These are outstanding engineering tasks.

## Longer trials with new initial conditions

`artifacts/compat_heldout_evaluation.json` records 15 trials of 30 seconds each using seeds 10–12, not the initial geometry-search seeds. All remained upright, but only the six stationary trials met the provisional tracking gate. All nine commanded forward/turn trials failed tracking. In seed 10, a 0.1 m/s command produced only about 0.00004 m/s mean forward velocity; a 0.3 m/s command produced about 0.11648 m/s. Upright stability is not accepted as useful walking. The report specifies body-frame velocity MAE, a one-second warmup exclusion and provisional thresholds.

## 500-iteration official-recipe training result

The 256-environment run completed 500 iterations from initialization and exported normalized ONNX. Its 12 held-out 30-second trials stayed upright, but all nine forward/turn-command trials failed tracking; only stationary trials passed. This policy is not accepted as the default. See `artifacts/training_500.json` and `artifacts/trained_500_evaluation.json`. More training alone is not assumed to solve the problem: command curriculum, rest-state reward balance and the authored dynamics must be examined before another run.
