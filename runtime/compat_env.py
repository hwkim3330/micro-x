"""X's independent dynamics model connected to unchanged pinned policy software."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json
import mujoco,numpy as np
R=Path(__file__).resolve().parents[1]
def upstream():
    for name,record in json.loads((R/'engineering/policy_sources.json').read_text()).items():
        if hashlib.sha256((R/'.cache/compat'/name).read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Stale policy dependency: '+name)
    spec=importlib.util.spec_from_file_location('pinned_policy_runtime',R/'.cache/compat/infer_policy.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
class Environment:
    def __init__(self,standing=False,model_path=None,walking_path=None):
        self.model_path=Path(model_path or R/'models/micro_x_14.xml')
        self.model_sha256=hashlib.sha256(self.model_path.read_bytes()).hexdigest()
        self.up=upstream()
        with contextlib.redirect_stdout(io.StringIO()):
            motor=self.up.load_bam_model(200,7.4,None)
            self.model,self.data,self.motor,_=self.up.load_mujoco_with_bam(str(model_path or R/'models/micro_x_14.xml'),motor,.005,.1,6)
            self.policy=self.up.PolicyInference(self.model,self.data,walking_onnx_path=None if standing else str(walking_path or R/'.cache/compat/alpha_walking.onnx'),standing_onnx_path=str(R/'.cache/compat/alpha_stand.onnx') if standing else None,bam_ctrl=self.motor,new_cmd_obs=True,use_projected_gravity=True)
        names=[mujoco.mj_id2name(self.model,mujoco.mjtObj.mjOBJ_JOINT,int(j)) for j in self.model.actuator_trnid[:,0]]
        assert names==json.loads((R/'engineering/control_interface.json').read_text())['joint_names']
    def reset(self,seed=0,command=(0,0,0)):
        mujoco.mj_resetData(self.model,self.data);self.data.qpos[:7]=[0,0,.125,1,0,0,0]
        self.data.qpos[self.policy.joint_qpos_indices]=self.policy.default_pose+np.random.default_rng(seed).normal(0,.003,14)
        self.policy.last_action[:]=0;self.policy.set_vel_cmd(*command);self.motor.reset(self.data.qpos);self.policy.set_position_targets(self.policy.default_pose);mujoco.mj_forward(self.model,self.data)
        return self.observation()
    def observation(self):
        value=self.policy.get_observations();assert value.shape==(61,) and np.isfinite(value).all();return value
    def step(self,action):
        action=np.asarray(action,dtype=np.float32);assert action.shape==(14,) and np.isfinite(action).all()
        self.policy.last_action=action.copy();self.policy.apply_action(action)
        for _ in range(4):self.motor.update();mujoco.mj_step(self.model,self.data)
        mujoco.mj_forward(self.model,self.data)
        tilt=float(np.arccos(np.clip(self.data.xmat[self.policy.trunk_base_id].reshape(3,3)[2,2],-1,1)))
        height=float(self.data.xpos[self.policy.trunk_base_id,2]);fallen=tilt>np.pi/4 or height<.065
        return self.observation(),fallen,dict(tilt_degrees=float(np.degrees(tilt)),height_m=height)
