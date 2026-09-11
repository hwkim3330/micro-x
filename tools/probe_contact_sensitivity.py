"""Single-variable X contact experiments; never overwrite the default model."""
from pathlib import Path
import contextlib, hashlib, io, json, sys, xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime'))
from compat_env import Environment

base=(ROOT/'models/micro_x_14.xml').read_bytes()
cache=ROOT/'.cache/contact_probe';cache.mkdir(parents=True,exist_ok=True)
results=[]
for variant in ['baseline','friction_08','sole_width_16mm','sole_length_28mm','no_nonfoot_contact']:
    tree=ET.fromstring(base)
    if variant=='friction_08':tree.find('./default/geom').set('friction','.8 .005 .0001')
    for g in tree.findall('.//geom'):
        if g.get('name','').endswith('_sole'):
            if variant=='sole_width_16mm':g.set('size','.036 .016 .006')
            if variant=='sole_length_28mm':g.set('size','.028 .021 .006')
        elif variant=='no_nonfoot_contact' and g.get('name') not in (None,'floor'):
            g.set('contype','0');g.set('conaffinity','0')
    target=cache/f'{variant}.xml';ET.ElementTree(tree).write(target)
    with contextlib.redirect_stdout(io.StringIO()):env=Environment(model_path=target)
    for command in [(0,0,0),(.1,0,0),(.3,0,0),(0,0,.3),(0,0,-.3)]:
        with contextlib.redirect_stdout(io.StringIO()):env.reset(10,command)
        samples=[];fall=None;contacts={}
        for i in range(500):
            _,fallen,_=env.step(env.policy.infer())
            if fallen and fall is None:fall=float(env.data.time)
            if i>=50:
                velocity=env.data.xmat[env.policy.trunk_base_id].reshape(3,3).T@env.data.qvel[:3]
                samples.append([float(velocity[0]),float(velocity[1]),float(env.data.qvel[5])])
            for c in env.data.contact:
                if c.dist<0:
                    names=tuple(sorted(env.model.geom(int(g)).name for g in c.geom))
                    key=' / '.join(names);contacts[key]=contacts.get(key,0)+1
        values=np.asarray(samples);mae=np.mean(np.abs(values-command),axis=0)
        row=dict(variant=variant,command=command,seed=10,duration_s=10,first_fall_s=fall,mean_body_velocity=values.mean(axis=0).tolist(),mae=mae.tolist(),tracking_passed=fall is None and bool(np.all(mae<=[max(.03,.25*abs(command[0])),.03,.1])),penetrating_contact_samples=contacts)
        results.append(row);print(json.dumps({k:v for k,v in row.items() if k!='penetrating_contact_samples'}),flush=True)
(ROOT/'artifacts/contact_sensitivity.json').write_text(json.dumps(dict(scope='Exploratory single-variable simulation probes, one seed, unchanged ONNX/BAM. Contact removal is diagnostic only, not a proposed physical design. No default model changes or hardware validation.',base_sha256=hashlib.sha256(base).hexdigest(),results=results),indent=2)+'\n')
