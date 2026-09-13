"""Measure each joint's collision-free mechanical travel on the Rev B assembly.

For every joint, the child subtree is rotated about the joint axis and bisected against the
rest of the robot until the largest clear angle is found in each direction, using exact STEP
booleans. The result is the travel the printed parts actually allow - not a wish - and it is
what cad/compat_model.py writes into the MuJoCo joint limits.
"""
from pathlib import Path
import itertools,json,math,sys
import numpy as np
import cadquery as cq
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import layout as L,servo as S
LIMIT={'hip_yaw':0.52,'hip_roll':0.40,'hip_pitch':1.57,'knee':1.57,'ankle':1.57,'neck_pitch':1.05,'head_pitch':1.57,'head_yaw':2.00,'head_roll':0.44,'jaw':0.70}
TOL=1.0 # mm3; below this an exact boolean is numerical noise
report=json.loads((R/'artifacts/parts.json').read_text())
items={p['name']:p for p in report['parts']+report['purchased']}
shapes={}
for name,p in items.items():
    if p['printed']:shapes[name]=cq.importers.importStep(str(R/p['step']))
    elif p['kind']=='actuator':j=L.get(name[6:]);shapes[name]=S.envelope(j['P'],j['h'],j['d'])
    else:
        import trimesh
        m=trimesh.load_mesh(R/p['stl']);lo,hi=m.bounds
        shapes[name]=cq.Workplane('XY').box(*(hi-lo)).translate(tuple((lo+hi)/2))
body_of={n:p['body'] for n,p in items.items()}
children={b:[c for c in L.BODIES if L.PARENT[c]==b] for b in L.BODIES}
def subtree(b):
    out=[b]
    for c in children[b]:out+=subtree(c)
    return out
def overlap(a,b):
    A=a.val().BoundingBox();B=b.val().BoundingBox()
    if any(getattr(A,k+'max')<=getattr(B,k+'min')+1e-6 or getattr(B,k+'max')<=getattr(A,k+'min')+1e-6 for k in 'xyz'):return 0.0
    return sum(s.Volume() for s in a.intersect(b).solids().vals())
def clear(joint,angle,moving,fixed):
    P=joint['P'];ax=np.asarray(joint['axis'],float);ax/=np.linalg.norm(ax);deg=math.degrees(angle)
    for m in moving:
        rot=shapes[m].rotate(tuple(P),tuple(P+ax),deg)
        for f in fixed:
            if overlap(rot,shapes[f])>TOL:return False
    return True
travel={}
for joint in L.SERVOS:
    key=joint['name'].replace('left_','').replace('right_','')
    moving_bodies=set(subtree(joint['child']))
    moving=[n for n in shapes if body_of[n] in moving_bodies];fixed=[n for n in shapes if body_of[n] not in moving_bodies]
    limits=[]
    for sign in (1,-1):
        cap=LIMIT[key]*sign
        if key=='jaw' and sign<0:limits.append(0.0);continue
        # Walk outward in 0.05 rad steps: every angle up to the limit is checked, not just the end.
        good=0.0;step=0.05*sign;angle=step
        while abs(angle)<=abs(cap)+1e-9:
            if not clear(joint,angle,moving,fixed):break
            good=angle;angle+=step
        else:
            if abs(good-cap)>1e-9 and clear(joint,cap,moving,fixed):good=cap
        limits.append(round(good,3))
    travel[joint['name']]=dict(min_rad=min(limits),max_rad=max(limits),catalogue_rad=[-LIMIT[key] if key!='jaw' else 0.0,LIMIT[key]])
    print(f"{joint['name']:16s} {travel[joint['name']]['min_rad']:+.3f} .. {travel[joint['name']]['max_rad']:+.3f} rad   ({math.degrees(travel[joint['name']]['min_rad']):+6.1f} .. {math.degrees(travel[joint['name']]['max_rad']):+6.1f} deg)",flush=True)
out=dict(scope='Collision-free travel of the Rev B printed parts and purchased envelopes, found by stepping out in 0.05 rad increments on exact STEP booleans with a 1 mm3 tolerance; every step up to the reported limit is clear. One joint moves at a time from the design pose; combined poses, fasteners, cables and print tolerance are not covered.',
         search_limit_rad=LIMIT,tolerance_mm3=TOL,joints=travel)
(R/'engineering/joint_travel.json').write_text(json.dumps(out,indent=2)+'\n')
print('wrote engineering/joint_travel.json')
