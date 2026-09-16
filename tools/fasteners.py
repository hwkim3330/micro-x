"""Count the fastener features that are actually in the CAD, so the BOM stops guessing.

Every hole in the printed parts is a cylindrical face in the STEP solid. Group them by
radius and length and you get the real schedule: how many M2 horn bolts, how many M3 into
printed bosses, and where. The previous BOM carried hand-typed counts like "15 x 8" that
nothing checked.

A radius here is the modelled hole, not a thread spec. Pilot sizes for thread-forming
screws into printed plastic still need a coupon test - see docs/ASSEMBLY.md.
"""
import json,math,sys
from pathlib import Path
import numpy as np,trimesh
import cadquery as cq
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import layout as L,servo as S
# modelled radius -> what it is for. Radii come from cad/servo.py and cad/build.py.
KIND={1.1:'M2 clearance, servo horn / idler bolt pattern',
      1.15:'M2.5 or M3 pilot in a printed boss (thread-forming screw)',
      1.3:'M3 pilot in a printed boss (thread-forming screw)',
      1.6:'servo horn hub clearance (not a fastener)',
      1.7:'M3 clearance through a shell',
      4.5:'printed boss outside diameter (not a fastener)',
      5.6:'clearance bore for the skull post (not a fastener)',
      6.5:'camera lens bore (not a fastener)',
      9.0:'nose lens hood (not a fastener)'}
def cylinders(shape):
    out={}
    for f in shape.faces().vals():
        try:
            s=f._geomAdaptor()
            if f.geomType()!='CYLINDER':continue
            r=round(s.Cylinder().Radius(),2)
        except Exception:continue
        out[r]=out.get(r,0)+1
    return out
def bolt_access(mesh,servo,driver_mm=8.0):
    """Is every bolt path through this plate actually open?

    Counting holes is not enough: a hole can exist and still be blocked further along by a
    rib unioned on top. Walk each of the four bolt axes from just in front of the horn to
    driver_mm behind the plate and check that no sample lands inside the part."""
    x,y,z=S.frame(np.asarray(servo['h'],float),np.asarray(servo['d'],float))
    P=np.asarray(servo['P'],float);blocked=[]
    for k in range(4):
        a=k*math.pi/2;off=y*(S.HOLE_R*math.cos(a))+z*(S.HOLE_R*math.sin(a))
        t=np.linspace(0.2,S.PLATE+driver_mm,40)
        pts=P+off+np.outer(t,x)
        inside=mesh.contains(pts)
        if inside.any():blocked.append(dict(bolt=k,first_blocked_mm=round(float(t[inside][0]),2)))
    return blocked
if __name__=='__main__':
    parts=json.loads((R/'artifacts/parts.json').read_text())['parts']
    per_part={};totals={}
    for p in parts:
        counts=cylinders(cq.importers.importStep(str(R/p['step'])))
        per_part[p['name']]=counts
        for r,n in counts.items():totals[r]=totals.get(r,0)+n
    rows=[]
    for r in sorted(totals):
        kind=KIND.get(r,'unclassified - check cad/ before ordering')
        rows.append(dict(radius_mm=r,diameter_mm=round(2*r,2),faces=totals[r],fastener=('not a fastener' not in kind),note=kind))
        print(f"D {2*r:5.2f} mm  x{totals[r]:4d}   {kind}")
    access=[]
    by_name={p['name']:p for p in parts}
    for srv in L.SERVOS:
        owners=[p for p in parts if p['body']==srv['plate_on']]
        for p in owners:
            mesh=trimesh.load_mesh(R/'models'/f"{p['name']}.stl")
            bb=mesh.bounds
            if not (bb[0]-6<=np.asarray(srv['P'],float)).all() or not (np.asarray(srv['P'],float)<=bb[1]+6).all():continue
            blocked=bolt_access(mesh,srv)
            carrier=per_part.get(p['name'],{}).get(1.1,0)>=4
            kind='defect: the plate cannot be bolted' if (blocked and carrier) else (
                  'assembly order: fit this part after the joint is bolted' if blocked else 'clear')
            access.append(dict(joint=srv['name'],part=p['name'],carries_the_plate=carrier,
                               blocked_bolts=len(blocked),meaning=kind,detail=blocked))
            if blocked:print(f"  {srv['name']:16s} in {p['name']:18s} {len(blocked)} of 4 blocked - {kind}")
    defects=[a for a in access if a['carries_the_plate'] and a['blocked_bolts']]
    print('bolt paths blocked in the part that carries the plate:',len(defects))
    out=dict(scope=' '.join(l.strip() for l in __doc__.strip().split('\n')),
        method='cylindrical faces counted in each printed part STEP solid; a through hole is normally two faces',
        note='Counts are cylindrical FACES, not holes: a hole split by a boolean shows up more than once. Use them as a schedule to check against, not as a purchase quantity without reading the part.',
        by_radius=rows,by_part=per_part,bolt_access=access,
        bolt_path_defects=len(defects),thread_spec_verified=False)
    (R/'artifacts/fasteners.json').write_text(json.dumps(out,indent=1)+'\n')
