"""Bounded local MuJoCo simulation; never controls a physical device."""
import math
import secrets
import threading


class Simulation:
    def __init__(self):
        self.lock = threading.Lock()
        self.env = None
        self.session = None
        self.fallen = False
        self.policy_name = 'official'

    def snapshot(self, geometry=False):
        import mujoco
        m, d = self.env.model, self.env.data
        out = dict(session=self.session, time=float(d.time), fallen=self.fallen,
                   model_sha256=self.env.model_sha256, policy=self.policy_name, qpos=d.qpos.tolist(),
                   position=d.qpos[:3].tolist(),
                   quaternion_wxyz=d.qpos[3:7].tolist(),
                   transforms=[dict(position=d.geom_xpos[i].tolist(), rotation=d.geom_xmat[i].tolist()) for i in range(m.ngeom)])
        if geometry:
            out['geometries'] = [dict(name=mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i),
                                     type=int(m.geom_type[i]), size=m.geom_size[i].tolist(),
                                     rgba=m.geom_rgba[i].tolist()) for i in range(m.ngeom)]
        return out

    def start(self, settings):
        import re
        from pathlib import Path
        if set(settings) - {'seed', 'policy'} or type(settings.get('seed')) is not int or not 0 <= settings['seed'] <= 2**32-1:
            raise ValueError('seed must be an unsigned integer')
        policy = settings.get('policy', 'official')
        if policy != 'official' and not re.fullmatch(r'[A-Za-z0-9_-]{1,40}\.onnx', policy):
            raise ValueError('policy must be official or a checkpoint file name')
        with self.lock:
            if self.env is None or policy != self.policy_name:
                from compat_env import Environment, R
                path = None if policy == 'official' else R / '.cache/checkpoints' / policy
                if path is not None and not path.is_file():
                    raise ValueError('Unknown checkpoint')
                self.env = Environment(walking_path=path)
                self.policy_name = policy
            self.env.reset(settings['seed'])
            self.session = secrets.token_hex(16)
            self.fallen = False
            return self.snapshot(geometry=True)

    def step(self, settings):
        if set(settings) != {'session', 'command', 'steps'}:
            raise ValueError('Invalid simulation fields')
        cmd = settings['command']
        if not isinstance(cmd, list) or len(cmd) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in cmd):
            raise ValueError('Invalid command')
        if any(abs(v) > limit for v, limit in zip(cmd, (.3, .1, .5))):
            raise ValueError('Command outside study bounds')
        if type(settings['steps']) is not int or not 1 <= settings['steps'] <= 10:
            raise ValueError('steps must be 1..10')
        with self.lock:
            if self.env is None or settings['session'] != self.session:
                raise RuntimeError('Reset this simulation session first')
            self.env.policy.set_vel_cmd(*cmd)
            if not self.fallen:
                for _ in range(settings['steps']):
                    _, self.fallen, _ = self.env.step(self.env.policy.infer())
                    if self.fallen:
                        break
            return self.snapshot()


simulation = Simulation()
