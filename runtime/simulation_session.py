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

    def snapshot(self, geometry=False):
        import mujoco
        m, d = self.env.model, self.env.data
        out = dict(session=self.session, time=float(d.time), fallen=self.fallen,
                   model_sha256=self.env.model_sha256,
                   position=d.qpos[:3].tolist(),
                   quaternion_wxyz=d.qpos[3:7].tolist(),
                   transforms=[dict(position=d.geom_xpos[i].tolist(), rotation=d.geom_xmat[i].tolist()) for i in range(m.ngeom)])
        if geometry:
            out['geometries'] = [dict(name=mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i),
                                     type=int(m.geom_type[i]), size=m.geom_size[i].tolist(),
                                     rgba=m.geom_rgba[i].tolist()) for i in range(m.ngeom)]
        return out

    def start(self, settings):
        if set(settings) != {'seed'} or type(settings['seed']) is not int or not 0 <= settings['seed'] <= 2**32-1:
            raise ValueError('seed must be an unsigned integer')
        with self.lock:
            if self.env is None:
                from compat_env import Environment
                self.env = Environment()
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
