"""Run unchanged walking/standing weights on independently authored X dynamics."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime'))
from compat_env import Environment
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=10);p.add_argument('--seeds',type=int,default=3);args=p.parse_args()
results=[]
for standing in [False,True]:
    env=Environment(standing)
    for command in ([(0,0,0)] if standing else [(0,0,0),(.1,0,0),(.3,0,0),(0,0,.3)]):
        for seed in range(args.seeds):
            env.reset(seed,command);frames=[];first_fall=None;max_tilt=0
            for i in range(round(args.seconds*50)):
                _,fallen,info=env.step(env.policy.infer());frames.append(np.round(env.data.qpos,7).tolist());max_tilt=max(max_tilt,info['tilt_degrees'])
                if fallen and first_fall is None:first_fall=round(env.data.time,3)
            result=dict(policy='alpha_stand' if standing else 'alpha_walking',command=command,seed=seed,duration_s=args.seconds,first_fall_s=first_fall,max_tilt_degrees=round(max_tilt,2),final_xy_m=np.round(env.data.qpos[:2],4).tolist(),finite=True)
            results.append(result);print(result,flush=True)
            if not standing and command==(.3,0,0) and seed==0:(R/'artifacts/compat_replay.json').write_text(json.dumps(dict(dt=.02,qpos=frames,result=result),separators=(',',':'))+'\n')
report=dict(scope='Unchanged official ONNX + published observation/action adapter + BAM M6, on an independent primitive X dynamics study. Not the P0 printable model, not a validated commercial robot.',interface_passed=True,observation_size=61,action_size=14,control_hz=50,model_sha256=hashlib.sha256((R/'models/micro_x_14.xml').read_bytes()).hexdigest(),weights=json.loads((R/'engineering/policy_sources.json').read_text()),results=results,all_trials_upright=all(r['first_fall_s'] is None for r in results),physical_verified=False,complete_compatibility_verified=False)
(R/'artifacts/compat_evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
