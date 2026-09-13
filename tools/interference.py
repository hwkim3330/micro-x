"""Exact BREP interference checks for the actuated Micro X.

1. Static: every printed part and purchased envelope at HOME, pairwise, positive-volume overlap.
2. Motion sweep: rotate each joint's subtree through sampled angles and re-check the pairs
   whose relative pose changes. This is a sampled clearance check, not a continuous sweep,
   and it excludes fasteners, cables and print tolerance.
"""
from pathlib import Path
import itertools,json,math,sys,hashlib
import numpy as np
import cadquery as cq
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import layout as L
report=json.loads((R/'artifacts/parts.json').read_text())
items={p['name']:p for p in report['parts']+report['purchased']}
shapes={}
for name,p in items.items():
    if p['printed']:shapes[name]=cq.importers.importStep(str(R/p['step']))
    elif p['kind']=='actuator':
        import servo;j=L.get(name[6:]);shapes[name]=servo.envelope(j['P'],j['h'],j['d']) # exact envelope incl. horn/idler discs
    else:
        import trimesh
        m=trimesh.load_mesh(R/p['stl']);lo,hi=m.bounds
        shapes[name]=cq.Workplane('XY').box(*(hi-lo)).translate(tuple((lo+hi)/2)) # boxes for battery/board/camera
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
def rotated(shape,joint,angle):
    P=joint['P'];ax=np.asarray(joint['axis'],float);ax/=np.linalg.norm(ax)
    return shape.rotate(tuple(P),tuple(P+ax),math.degrees(angle))
names=list(shapes);static=[];tested=0
for a,b in itertools.combinations(names,2):
    v=overlap(shapes[a],shapes[b]);tested+=1
    if v>1.0:static.append(dict(parts=[a,b],overlap_mm3=round(v,3))) # 1 mm3 threshold: exact-boolean noise below that
print('static pairs',tested,'overlaps',len(static))
for s in static:print('  STATIC',s)
# Sampled joint sweeps: each joint moved alone from HOME, others at HOME.
# Angles are relative to the HOME pose in which the CAD is built; they are the intended mechanical envelopes, not the policy's full range.
# Sampled inside the measured travel of each joint (engineering/joint_travel.json), which is
# where the mechanism is allowed to go. tools/travel.py is what finds those limits.
_t=json.loads((R/'engineering/joint_travel.json').read_text())['joints']
sweeps={}
for _n,_v in _t.items(): # keyed by the full joint name: left and right limits are not the same
    _lo,_hi=_v['min_rad'],_v['max_rad']
    sweeps[_n]=sorted({round(x,4) for x in [_lo,_lo/2,_hi/2,_hi] if abs(x)>1e-6})
motion=[]
for joint in L.SERVOS:
    key=joint['name']
    moving=set(subtree(joint['child']));fixed=[n for n in names if body_of[n] not in moving];mov=[n for n in names if body_of[n] in moving]
    worst=0;hits=[]
    for angle in sweeps[key]:
        rot={n:rotated(shapes[n],joint,angle) for n in mov}
        for m in mov:
            for f in fixed:
                v=overlap(rot[m],shapes[f])
                if v>1.0:hits.append(dict(angle_rad=angle,parts=[m,f],overlap_mm3=round(v,3)));worst=max(worst,v)
    motion.append(dict(joint=joint['name'],angles_rad=sweeps[key],collisions=hits))
    print(f"  {joint['name']:16s} {len(hits)} collision samples" + (f" worst {worst:.1f} mm3" if hits else ''))
out=dict(scope='Exact STEP intersections at HOME plus single-joint sampled sweeps; purchased items as bounding boxes. Not a continuous sweep, tolerance, cable or fastener check.',
    static_pairs=tested,static_overlaps=static,assembly_cleared=not static,motion=motion,motion_cleared=all(not m['collisions'] for m in motion),
    step_sha256={p['name']:hashlib.sha256((R/p['step']).read_bytes()).hexdigest() for p in report['parts']})
(R/'artifacts/interference.json').write_text(json.dumps(out,indent=2)+'\n')
print('assembly_cleared',out['assembly_cleared'],'motion_cleared',out['motion_cleared'])
