"""Run the pinned Microduck mjlab recipe with X's independently authored model.

Execute with the separately installed microduck_rl virtualenv. No upstream
hardware assets are copied. This is a recipe integration smoke test, not a
claim that a new policy walks well or transfers to physical hardware.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import os
import xml.etree.ElementTree as ET
import mujoco

ROOT = Path(__file__).resolve().parents[1]


def x_spec():
    root = ET.parse(ROOT / 'models/micro_x_14.xml').getroot()
    world = root.find('worldbody')
    world.remove(world.find("geom[@name='floor']"))  # mjlab supplies terrain
    ET.SubElement(root.find('sensor'), 'subtreeangmom', name='root_angmom', body='trunk_base')
    for side in ('left', 'right'):
        body = root.find(f".//body[@name='x_{side}_ankle']")
        sole = body.find(f"geom[@name='{side}_ankle_sole']")
        sole.set('name', f'{side}_foot_collision')
        ET.SubElement(body, 'site', name=f'{side}_foot', pos=sole.get('pos'), size='.002')
    return mujoco.MjSpec.from_string(ET.tostring(root, encoding='unicode'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--iterations', type=int, default=5)
    parser.add_argument('--num-envs', type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 10000 or not 1 <= args.num_envs <= 4096:
        parser.error('iterations 1..10000; num-envs 1..4096')
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
    import mjlab_microduck.tasks  # registers the unchanged upstream recipe
    from mjlab.scripts.train import TrainConfig, run_train
    cfg = TrainConfig.from_task('Mjlab-Velocity-Flat-MicroDuck')
    robot = deepcopy(cfg.env.scene.entities['robot'])
    robot.spec_fn = x_spec
    robot.collisions = ()  # retain X's explicitly authored collision masks
    cfg.env.scene.entities['robot'] = robot
    # Map only the original head-body selection to X's four head links.
    # Reward functions, weights, observation layout, noise, delays and BAM stay.
    for event in cfg.env.events.values():
        asset = event.params.get('asset_cfg')
        if asset is not None and asset.body_names and 'neck' in asset.body_names:
            # Upstream also includes the right hip-yaw link in this event.
            # Preserve that historical selection rather than silently fixing it.
            asset.body_names = ('x_neck_pitch', 'x_head_pitch', 'x_head_yaw', 'x_head_roll', 'x_right_hip_yaw')
    cfg.env.scene.num_envs = args.num_envs
    cfg.agent.max_iterations = args.iterations
    cfg.agent.logger = 'tensorboard'
    cfg.agent.experiment_name = 'micro_x_official_recipe'
    from datetime import datetime
    log = ROOT / '.cache/official_recipe' / datetime.now().strftime('%Y%m%d_%H%M%S')
    log.mkdir(parents=True)
    run_train('Mjlab-Velocity-Flat-MicroDuck', cfg, log)


if __name__ == '__main__':
    main()
