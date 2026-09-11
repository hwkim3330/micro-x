# Official baseline before Micro X transfer

The official simulator and training source are installed separately from this
commercial design repository. Original hardware assets are not shipped as X.

## Executed official browser trial

Source: <https://huggingface.co/spaces/pollen-robotics/microduck-simulator>,
revision `023172c8a7d629b5258d90364c13bafe013abbfa`.
Local Vite server, Chrome and SwiftShader ran real MuJoCo WASM physics and ONNX.
Keyboard forward input advanced 10.04 simulation seconds and displaced the
robot 1.0291 m forward. Actor observations had 61 entries and no page errors
were recorded. This was a single trial, without continuous fall monitoring.
Approximately 4 FPS / 4 Hz appeared in the HUD: real-time performance is not
accepted on this headless rendering setup. This is not a prerecorded replay.
See [raw measurements](../artifacts/official_browser_validation.json).

## Executed official training trial

The unmodified `microduck_rl` revision
`2b25a48b08f1f17bc38c90bb03144c81fbd9ed07` was installed with `uv sync --frozen`
and its lockfile. On the local RTX 3090:

```sh
uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 64 --agent.max-iterations 5 --agent.logger tensorboard
```

All five iterations completed. Checkpoints and normalized ONNX export were
generated; ONNX accepted `[1,61]` and returned finite `[1,14]` values. Actor
weights changed between saved checkpoints. This verifies the training pipeline,
not learned gait quality. The pretrained browser policy and this newly trained
five-iteration policy are different. TensorBoard logs stayed local.
See [version and artifact hashes](../artifacts/official_training_validation.json).

## Applying the recipe to X

`tools/train_official_recipe.py` loads the official registered walking recipe
in that separate virtual environment, replacing the robot spec with X's
primitive dynamics study. It preserves reward definitions, observation/noise
settings, curricula, BAM and PPO. Adaptations are explicit: X collision masks,
foot contact/site names, an angular-momentum sensor, and head COM body selectors
(including the right hip-yaw body retained by the upstream recipe).

```sh
/path/to/microduck_rl/.venv/bin/python tools/train_official_recipe.py --iterations 5 --num-envs 64
```

The first X run exposed a missing `root_angmom` sensor required by the official
reward. The adapter now supplies that actual MuJoCo sensor; the reward was not
removed to bypass the error. X trials are integration checks, not full training
parity, unchanged-weight tracking acceptance or physical compatibility. The
P0 printable shell is still separate from this actuated dynamics study.

The corrected X run completed all five iterations in 64 environments, changed
actor weights and exported a finite `[1,61]` → `[1,14]` ONNX policy.
[X model, adapter and output hashes](../artifacts/official_recipe_x_validation.json)
bind this result to the executed model. The browser workbench's compact CPU PPO
remains a separate harness; the official GPU recipe currently runs via the CLI.
