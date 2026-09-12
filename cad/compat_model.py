"""Micro X 14-axis MuJoCo model generated from the Rev A CAD.

Bodies, joint pivots and axes follow cad/layout.py (functional interface). Masses and
inertias come from the actual printed-part meshes (PLA solid-equivalent density) and the
purchased envelopes with catalogue masses. Collision uses the foot soles, trunk shell,
head shell and leg boxes. Names required by the pinned inference adapter are kept:
body trunk_base, freejoint trunk_base_freejoint, site imu, 14 joint/actuator names.
"""
from pathlib import Path
import json,sys,xml.etree.ElementTree as E
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import layout as L
DENSITY=1240.0 # kg/m3
def vector(v):return ' '.join(f'{x:.9g}' for x in np.asarray(v,float))
def add(p,tag,**kw):return E.SubElement(p,tag,{k:str(v) for k,v in kw.items()})
def inertia_of(meshes):
    """Combine (mass, mesh) pairs about the common frame using parallel axis theorem."""
    total=sum(m for m,_ in meshes);com=sum(m*me.center_mass for m,me in meshes)/total;I=np.zeros((3,3))
    for m,me in meshes:
        props=me.mass_properties;ratio=m/props['mass'] if props['mass']>0 else 0;d=me.center_mass-com
        I+=props['inertia']*ratio+m*(np.eye(3)*np.dot(d,d)-np.outer(d,d))
    return total,com,I
def build():
    report=json.loads((R/'artifacts/parts.json').read_text())
    pivots={b:(L.JOINT_OF_BODY[b]['P'] if b in L.JOINT_OF_BODY else L.TRUNK) for b in L.BODIES}
    per_body={b:[] for b in L.BODIES};extents={}
    for p in report['parts']+report['purchased']:
        mesh=trimesh.load_mesh(R/(('models/'+p['name']+'.stl') if p['printed'] else p['stl']));mesh.vertices=(mesh.vertices-pivots[p['body']])*.001
        mass=(mesh.volume*DENSITY if p['printed'] else p['mass_g']*.001)
        if not p['printed']:
            lo,hi=mesh.bounds;mesh=trimesh.creation.box(hi-lo);mesh.apply_translation((lo+hi)/2)
        per_body[p['body']].append((mass,mesh));extents.setdefault(p['body'],[]).append(mesh.bounds)
    r=E.Element('mujoco',model='Micro_X_RevA_14');add(r,'compiler',angle='radian',autolimits='true');add(r,'option',timestep='.005',gravity='0 0 -9.81',iterations=80)
    default=add(r,'default');add(default,'joint',damping='.02',armature='.00001',frictionloss='.005');add(default,'geom',friction='1 .005 .0001',condim='3')
    w=add(r,'worldbody');add(w,'geom',name='floor',type='plane',size='3 3 .01',rgba='.85 .85 .8 1')
    xml_bodies={};qpos_order=[]
    def body_xml(b):
        parent=L.PARENT[b]
        if parent is None:
            el=add(w,'body',name='trunk_base',pos=vector(L.TRUNK*.001));add(el,'freejoint',name='trunk_base_freejoint');add(el,'site',name='imu',size='.003',pos='-0.02 0 -0.01')
        else:
            j=L.JOINT_OF_BODY[b];el=add(xml_bodies[parent],'body',name='x_'+b,pos=vector((pivots[b]-pivots[parent])*.001))
            rng={'hip_yaw':'-0.45 0.55','hip_roll':'-0.26 0.09','hip_pitch':'-1.3 1.3','knee':'-1.0 1.0','ankle':'-0.9 0.9','neck_pitch':'0.15 1.05','head_pitch':'-1.2 1.2','head_yaw':'-2.0 2.0','head_roll':'-0.21 0.21','jaw':'0 0.35'}[j['name'].replace('left_','').replace('right_','')]
            if b=='right_yaw2roll':rng='-0.55 0.45'
            if b=='right_hip':rng='-0.09 0.26'
            extra={'stiffness':'.05'} if j['name']=='jaw' else {}
            add(el,'joint',name=j['name'],axis=vector(j['axis']),range=rng,ref=L.HOME.get(j['name'],0),**extra);qpos_order.append(j['name'])
        mass,com,I=inertia_of(per_body[b])
        add(el,'inertial',pos=vector(com),mass=f'{mass:.6g}',fullinertia=vector([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
        xml_bodies[b]=el
        for c in [c for c in L.BODIES if L.PARENT[c]==b]:body_xml(c)
    body_xml('trunk')
    # Collision geometry: soles carry ground contact; shells and leg boxes for self/ground collision awareness.
    def box_geom(b,name,lo,hi,rgba='.8 .3 .1 .25',**kw):
        lo=np.asarray(lo);hi=np.asarray(hi);add(xml_bodies[b],'geom',name=name,type='box',pos=vector((lo+hi)/2),size=vector((hi-lo)/2),mass='0',rgba=rgba,group='3',**kw)
    for side in ['left','right']:
        p=pivots[f'{side}_foot'];sgn=1 if side=='left' else -1
        box_geom(f'{side}_foot',f'{side}_foot_collision',(np.array([-38,min(sgn*26,sgn*74),0])-p)*.001,(np.array([44,max(sgn*26,sgn*74),11])-p)*.001)
        add(xml_bodies[f'{side}_foot'],'site',name=f'{side}_foot',pos=vector((np.array([4,sgn*50,0])-p)*.001),size='.003')
        for b in [f'{side}_thigh',f'{side}_shin']:
            lo=np.min([e[0] for e in extents[b]],axis=0);hi=np.max([e[1] for e in extents[b]],axis=0);box_geom(b,b+'_collision',lo,hi,contype='2',conaffinity='2')
    lo=np.min([e[0] for e in extents['trunk']],axis=0);hi=np.max([e[1] for e in extents['trunk']],axis=0)
    add(xml_bodies['trunk'],'geom',name='trunk_shell_collision',type='ellipsoid',pos=vector((np.array([2,0,132])-L.TRUNK)*.001),size='.054 .037 .044',mass='0',rgba='.8 .3 .1 .25',group='3',contype='1',conaffinity='1')
    add(xml_bodies['head'],'geom',name='head_shell_collision',type='ellipsoid',pos=vector((np.array([-4,0,238])-pivots['head'])*.001),size='.05 .038 .036',mass='0',rgba='.8 .3 .1 .25',group='3',contype='1',conaffinity='1')
    contacts=add(r,'contact')
    for a,b in [('trunk_base','x_head'),('x_left_thigh','x_right_thigh'),('x_left_shin','x_right_shin')]:add(contacts,'exclude',body1=a,body2=b)
    act=add(r,'actuator')
    for name in L.ORDER:add(act,'position',name=name,joint=name,kp='5',ctrlrange='-2.4 2.4',forcerange='-.5 .5')
    sensors=add(r,'sensor');add(sensors,'gyro',name='imu_ang_vel',site='imu');add(sensors,'accelerometer',name='imu_accel',site='imu');add(sensors,'subtreeangmom',name='root_angmom',body='trunk_base')
    E.indent(r);E.ElementTree(r).write(R/'models/micro_x_14.xml',encoding='unicode')
    total=sum(inertia_of(per_body[b])[0] for b in L.BODIES)
    (R/'engineering/control_interface.json').write_text(json.dumps(dict(joint_names=L.ORDER,home_rad=[L.HOME[n] for n in L.ORDER],observation_size=61,action_size=14,command_size=13,control_hz=50,physics_hz=200,action_scale=1,actuator_target='XL330 / BAM M6; assumed kp 200, 7.4 V',geometry='Rev A CAD-derived bodies: printed-part meshes at PLA solid density plus purchased envelopes with catalogue masses',functional_dimensions='engineering/functional_interface.json',model_mass_kg=round(total,4),physical_verified=False),indent=2)+'\n')
    rig=dict(units='m',root='trunk',root_position_m=(L.TRUNK*.001).tolist(),qpos_layout=dict(free=7,joints=qpos_order),
        bodies=[dict(name=b,parent=L.PARENT[b],pivot_m=np.round(pivots[b]*.001,6).tolist(),joint=(L.JOINT_OF_BODY[b]['name'] if b in L.JOINT_OF_BODY else None),axis=(np.round(np.asarray(L.JOINT_OF_BODY[b]['axis'],float)/np.linalg.norm(L.JOINT_OF_BODY[b]['axis']),6).tolist() if b in L.JOINT_OF_BODY else None),home_rad=L.HOME.get(L.JOINT_OF_BODY[b]['name'],0) if b in L.JOINT_OF_BODY else None,mass_kg=round(inertia_of(per_body[b])[0],5)) for b in L.BODIES],
        policy_joints=L.ORDER,mass_kg=round(total,4))
    (R/'models/rig.json').write_text(json.dumps(rig,indent=1)+'\n')
    print(f'Built CAD-derived 14-axis model, total mass {total*1000:.0f} g; qpos joints {qpos_order}')
if __name__=='__main__':build()
