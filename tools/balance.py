"""Uniform-density printed geometry only; no electronics or dynamic balance claim."""
from pathlib import Path
import hashlib, json
import numpy as np
import trimesh
R=Path(__file__).resolve().parents[1]
parts=json.loads((R/'artifacts/parts.json').read_text())
meshes={p['name']:trimesh.load_mesh(R/'models'/f"{p['name']}.stl") for p in parts}
mass=sum(m.volume*.00124 for m in meshes.values())
com=sum(m.volume*.00124*m.center_mass for m in meshes.values())/mass
points=[]
for name in ['foot_left','foot_right']:
    m=meshes[name];points.extend(map(tuple,m.vertices[m.vertices[:,2]<m.bounds[0,2]+.05,:2]))
def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
points=sorted(set(points));lower=[];upper=[]
for seq,hull in [(points,lower),(points[::-1],upper)]:
    for point in seq:
        while len(hull)>1 and cross(hull[-2],hull[-1],point)<=0:hull.pop()
        hull.append(point)
hull=lower[:-1]+upper[:-1]
margins=[cross(a,b,com[:2])/np.linalg.norm(np.subtract(b,a)) for a,b in zip(hull,hull[1:]+hull[:1])]
report=dict(scope='Uniform PLA-equivalent printed shells in fixed reference pose. Both feet assumed flat; contact points within 0.05 mm of foot minimum Z. Excludes fasteners, electronics, battery, motors and deformation. Not whole-robot balance or strength validation.',mass_g=round(mass,2),center_of_mass_mm=np.round(com,3).tolist(),support_hull_xy_mm=hull,minimum_static_margin_mm=round(min(margins),3),physical_verified=False,stl_sha256={n:hashlib.sha256((R/'models'/f'{n}.stl').read_bytes()).hexdigest() for n in meshes})
(R/'artifacts/balance.json').write_text(json.dumps(report,indent=2)+'\n')
print('Printed geometry only:',report['mass_g'],'g, COM',report['center_of_mass_mm'],'mm; static margin',report['minimum_static_margin_mm'],'mm')
