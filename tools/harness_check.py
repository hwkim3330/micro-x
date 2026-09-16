"""Calibrate the instrument before trusting it: what does the ORIGINAL robot do?

Every locomotion claim in this repository is made with the pinned upstream inference code
and the unchanged official weights. Before any of it can be read as a statement about
Micro Cat's geometry, the same harness has to be run on the reference robot's own scene.
This records that command-response curve. If the reference robot does not track its own
commands here, then neither does any model, and velocity tracking is not a usable
instrument for comparing designs - which is exactly what this found.

Needs the micro-rex checkout for the reference scene; pass its path.
"""
import json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime'))
from compat_env import Environment
def sweep(model,label,seconds=10.):
    env=Environment(model_path=Path(model));rows=[]
    for cmd in [(0.05,0,0),(0.1,0,0),(0.2,0,0),(0.3,0,0),(0.6,0,0),(1.0,0,0),(0,0,0.3),(0,0,1.0),(0,0,1.5)]:
        env.reset(seed=0);env.policy.set_vel_cmd(*cmd);fell=None
        for _ in range(int(seconds*50)):
            _,f,_=env.step(env.policy.infer())
            if f and fell is None:fell=float(env.data.time)
        q=env.data.qpos[3:7];yaw=math.atan2(2*(q[0]*q[3]+q[1]*q[2]),1-2*(q[2]**2+q[3]**2))
        rows.append(dict(model=label,command=list(cmd),speed_m_s=round(float(env.data.qpos[0])/seconds,4),
                         yaw_rate_rad_s=round(yaw/seconds,4),fell_s=fell))
        print(rows[-1],flush=True)
    return rows
if __name__=='__main__':
    models=[(a.split('=',1)[0],a.split('=',1)[1]) for a in sys.argv[1:]] or [('micro_cat',str(R/'models/micro_cat_14.xml'))]
    rows=[r for label,path in models for r in sweep(path,label)]
    def ratio(rows,label):
        fwd=[r for r in rows if r['model']==label and r['command'][0]>0]
        turn=[r for r in rows if r['model']==label and r['command'][2]>0]
        return dict(model=label,
            best_forward_tracking=round(max(r['speed_m_s']/r['command'][0] for r in fwd),3),
            best_yaw_tracking=round(max(r['yaw_rate_rad_s']/r['command'][2] for r in turn),3))
    summary=[ratio(rows,label) for label,_ in models]
    (R/'artifacts/harness_check.json').write_text(json.dumps(dict(
        scope=' '.join(l.strip() for l in __doc__.strip().split('\n')[2:8]),
        protocol='10 s per command, seed 0, pinned upstream inference, unchanged official walking weights, BAM M6 XL330 kp 200 / 7.4 V',
        results=rows,best_tracking_ratio=summary,
        conclusion='Velocity tracking in this harness is only usable as a comparison between models if the reference robot tracks its own commands. Read best_tracking_ratio before citing any speed or yaw number.'),indent=1)+'\n')
    print(json.dumps(summary,indent=1))
