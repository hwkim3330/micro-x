"""Shared tipping analysis; see tools/tip_study.py."""
"""Static tipping limit at HOME by quasi-static rocking on a flat floor.

Not a projected-centroid shortcut: the body is rotated to each tilt angle, dropped onto
the floor, and the contact set is recomputed at that angle. That is the only way a raised
heel spur counts - it carries no load standing upright, and becomes the pivot only after
the robot has already pitched back far enough to touch it.

Rigid, frictionless-pivot, quasi-static. No contact compliance, no dynamics, no walking
proof. Extra model paths are compared against the first.
"""
import hashlib,json,math,sys
from pathlib import Path
import mujoco,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import layout as L
def rel(p):
    p=Path(p).resolve()
    return str(p.relative_to(R)) if p.is_relative_to(R) else str(p)
def foot_points_and_com(path):
    m=mujoco.MjModel.from_xml_path(str(path));d=mujoco.MjData(m)
    d.qpos[:7]=[0,0,.125,1,0,0,0]
    for j in range(m.njnt):
        name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,j)
        if name in L.HOME:d.qpos[m.jnt_qposadr[j]]=L.HOME[name]
    mujoco.mj_forward(m,d)
    pts=[]
    for g in range(m.ngeom):
        name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or ''
        if 'foot' not in name or 'collision' not in name:continue
        c=d.geom_xpos[g];M=d.geom_xmat[g].reshape(3,3);s=m.geom_size[g]
        pts+=[c+M@np.array([sx*s[0],sy*s[1],sz*s[2]]) for sx in(-1,1) for sy in(-1,1) for sz in(-1,1)]
    mass=float(m.body_mass.sum());com=(d.xipos*m.body_mass[:,None]).sum(0)/mass
    return np.array(pts),com,mass
def tip_angle(pts,com,u,limit_deg=45.,step_deg=.05):
    """Smallest tilt toward horizontal direction `u` at which the centre of mass passes
    every remaining contact. The body is rotated about the horizontal axis z x u, so the
    +u side goes down, then dropped onto the floor."""
    z=np.array([0,0,1.]);w=np.cross(z,u);Q=pts-com
    qu=Q@u;qw=Q@w;qz=Q@z
    for k in range(int(limit_deg/step_deg)+1):
        th=math.radians(k*step_deg);c,s=math.cos(th),math.sin(th)
        nu=qu*c+qz*s;nz=-qu*s+qz*c
        contact=nu[nz<=nz.min()+1e-5]
        if contact.max()<0:return round(k*step_deg,2)
    return None
def study(path):
    pts,com,mass=foot_points_and_com(path)
    floor=pts[:,2].min()
    out=dict(model=rel(path),mass_g=round(mass*1000,1),com_height_above_sole_mm=round(float(com[2]-floor)*1000,1))
    for label,u in [('fwd',(1,0,0)),('aft',(-1,0,0)),('lat',(0,1,0))]:
        out['tip_'+label+'_deg']=tip_angle(pts,com,np.array(u,float))
    return out
