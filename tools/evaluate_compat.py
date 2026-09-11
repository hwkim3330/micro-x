"""Run unchanged walking/standing weights on independently authored X dynamics."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime'))
from compat_env import Environment
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=10);p.add_argument('--seeds',type=int,default=3);p.add_argument('--seed-start',type=int,default=0);p.add_argument('--output',default='artifacts/compat_evaluation.json');p.add_argument('--walking-policy',type=Path);p.add_argument('--skip-standing',action='store_true');args=p.parse_args()
if not 2<=args.seconds<=300 or not 1<=args.seeds<=100 or args.seed_start<0:p.error('seconds 2..300, seeds 1..100, seed-start >=0')
results=[]
for standing in ([False] if args.skip_standing else [False,True]):
    env=Environment(standing,walking_path=args.walking_policy)
    for command in ([(0,0,0)] if standing else [(0,0,0),(.1,0,0),(.3,0,0),(0,0,.3)]):
        for seed in range(args.seed_start,args.seed_start+args.seeds):
            env.reset(seed,command);frames=[];first_fall=None;max_tilt=0;tracking=[]
            for i in range(round(args.seconds*50)):
                _,fallen,info=env.step(env.policy.infer());frames.append(np.round(env.data.qpos,7).tolist());max_tilt=max(max_tilt,info['tilt_degrees'])
                if fallen and first_fall is None:first_fall=round(env.data.time,3)
                if env.data.time>=1:
                    rotation=env.data.xmat[env.policy.trunk_base_id].reshape(3,3)
                    velocity=rotation.T@env.data.qvel[:3]
                    # Free-joint angular velocity is in the rotating local frame.
                    tracking.append([float(velocity[0]),float(velocity[1]),float(env.data.qvel[5])])
            result=dict(policy='alpha_stand' if standing else 'alpha_walking',command=command,seed=seed,duration_s=args.seconds,first_fall_s=first_fall,max_tilt_degrees=round(max_tilt,2),final_xy_m=np.round(env.data.qpos[:2],4).tolist(),finite=True)
            if not standing and args.walking_policy:result['policy']='custom_walking'
            values=np.asarray(tracking);mae=np.mean(np.abs(values-np.asarray(command)),axis=0)
            result.update(mean_body_velocity=np.round(values.mean(axis=0),5).tolist(),tracking_mae=np.round(mae,5).tolist(),tracking_gate_passed=first_fall is None and bool(np.all(mae<=[max(.03,abs(command[0])*.25),.03,.10])))
            results.append(result);print(result,flush=True)
            if not standing and not args.walking_policy and command==(.3,0,0) and seed==0:(R/'artifacts/compat_replay.json').write_text(json.dumps(dict(dt=.02,qpos=frames,result=result),separators=(',',':'))+'\n')
report=dict(scope='Unchanged official ONNX + published observation/action adapter + BAM M6, on an independent primitive X dynamics study. Not the P0 printable model, not a validated commercial robot.',interface_passed=True,observation_size=61,action_size=14,control_hz=50,model_sha256=hashlib.sha256((R/'models/micro_x_14.xml').read_bytes()).hexdigest(),weights=json.loads((R/'engineering/policy_sources.json').read_text()),results=results,all_trials_upright=all(r['first_fall_s'] is None for r in results),physical_verified=False,complete_compatibility_verified=False)
report['tracking_protocol']='Exclude first 1 s. Body forward/lateral m/s and body yaw rad/s. Provisional engineering gate: forward MAE <= max(0.03, 25% of command), lateral <=0.03, yaw <=0.10, no fall. These thresholds are targets, not an industry standard.'
report['tracking_gate_passed']=all(r['tracking_gate_passed'] for r in results)
report['seed_start']=args.seed_start
if args.walking_policy:
    report['scope']='Custom trained walking policy with the pinned deployment adapter and BAM M6 on X dynamics. Compared separately from official unchanged weights.'
    report['custom_walking_sha256']=hashlib.sha256(args.walking_policy.read_bytes()).hexdigest()
(R/args.output).write_text(json.dumps(report,indent=2)+'\n')
