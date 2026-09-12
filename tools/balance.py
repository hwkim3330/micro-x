"""Whole-model static balance at HOME from the CAD-derived MuJoCo model.

Uses the body masses and inertial positions written by cad/compat_model.py (printed parts at
PLA solid density plus purchased catalogue masses) and the foot collision boxes as the support
polygon. This is a static check of the design's mass layout, not a walking or strength claim.
"""
from pathlib import Path
import hashlib,json
import numpy as np,mujoco
R=Path(__file__).resolve().parents[1]
m=mujoco.MjModel.from_xml_path(str(R/'models/micro_x_14.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d)
mass=float(sum(m.body_mass));com=(d.xipos*m.body_mass[:,None]).sum(0)/mass
points=[]
for side in ['left','right']:
    g=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,f'{side}_foot_collision');c=d.geom_xpos[g];Rm=d.geom_xmat[g].reshape(3,3);s=m.geom_size[g]
    for sx in (-1,1):
        for sy in (-1,1):points.append(tuple((c+Rm@np.array([sx*s[0],sy*s[1],-s[2]]))[:2]*1000))
def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
points=sorted(set(points));lower=[];upper=[]
for seq,hull in [(points,lower),(points[::-1],upper)]:
    for point in seq:
        while len(hull)>1 and cross(hull[-2],hull[-1],point)<=0:hull.pop()
        hull.append(point)
hull=lower[:-1]+upper[:-1];c2=com[:2]*1000
margins=[cross(a,b,c2)/np.linalg.norm(np.subtract(b,a)) for a,b in zip(hull,hull[1:]+hull[:1])]
per_body=[dict(body=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,i),mass_g=round(float(m.body_mass[i])*1000,1),com_mm=np.round(d.xipos[i]*1000,1).tolist()) for i in range(1,m.nbody)]
report=dict(scope='HOME pose, both feet flat; CAD-derived masses (PLA solid density + purchased catalogue masses); fasteners, cables and print infill not modelled.',
    mass_g=round(mass*1000,1),center_of_mass_mm=np.round(com*1000,2).tolist(),support_hull_xy_mm=[list(map(lambda v:round(v,2),p)) for p in hull],minimum_static_margin_mm=round(float(min(margins)),2),
    bodies=per_body,model_sha256=hashlib.sha256((R/'models/micro_x_14.xml').read_bytes()).hexdigest(),physical_verified=False)
(R/'artifacts/balance.json').write_text(json.dumps(report,indent=2)+'\n')
print(f"Model {report['mass_g']} g, COM {report['center_of_mass_mm']} mm, static margin {report['minimum_static_margin_mm']} mm")
