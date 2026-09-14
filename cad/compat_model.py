"""Micro X Rev B 14-axis MuJoCo model, generated from the Rev A/B CAD.

Bodies, pivots and axes follow cad/layout.py (design pose = qpos 0, so no joint `ref`
offsets are needed and the policy HOME angles are ordinary joint targets). Masses and
inertias come from the printed-part meshes at PLA solid density plus purchased envelopes
with catalogue masses. Names the pinned inference adapter needs are kept: body
trunk_base, freejoint trunk_base_freejoint, site imu, the 14 joint/actuator names.
"""
from pathlib import Path
import json,sys,xml.etree.ElementTree as E
import numpy as np,trimesh,mujoco
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import layout as L
DENSITY=1240.0
# Joint limits are the measured collision-free travel of the printed parts (tools/travel.py),
# not a wish list: the model can only command what the mechanism can actually do.
TRAVEL=json.loads((R/'engineering/joint_travel.json').read_text())['joints']
def vector(v):return ' '.join(f'{x:.9g}' for x in np.asarray(v,float))
def add(p,tag,**kw):return E.SubElement(p,tag,{k:str(v) for k,v in kw.items()})
def inertia_of(meshes):
    total=sum(m for m,_ in meshes);com=sum(m*me.center_mass for m,me in meshes)/total;I=np.zeros((3,3))
    for m,me in meshes:
        props=me.mass_properties;ratio=m/props['mass'] if props['mass']>0 else 0;d=me.center_mass-com
        I+=props['inertia']*ratio+m*(np.eye(3)*np.dot(d,d)-np.outer(d,d))
    return total,com,I
def build():
    report=json.loads((R/'artifacts/parts.json').read_text())
    pivots={b:(L.JOINT_OF_BODY[b]['P'] if b in L.JOINT_OF_BODY else L.TRUNK_ORIGIN) for b in L.BODIES}
    per_body={b:[] for b in L.BODIES};extents={}
    for p in report['parts']+report['purchased']:
        mesh=trimesh.load_mesh(R/(('models/'+p['name']+'.stl') if p['printed'] else p['stl']));mesh.vertices=(mesh.vertices-pivots[p['body']])*.001
        mass=(mesh.volume*DENSITY if p['printed'] else p['mass_g']*.001)
        if not p['printed']:
            lo,hi=mesh.bounds;mesh=trimesh.creation.box(hi-lo);mesh.apply_translation((lo+hi)/2)
        per_body[p['body']].append((mass,mesh));extents.setdefault(p['body'],[]).append(mesh.bounds)
    r=E.Element('mujoco',model='Micro_X_RevC_14');add(r,'compiler',angle='radian',autolimits='true');add(r,'option',timestep='.005',gravity='0 0 -9.81',iterations=80)
    default=add(r,'default');add(default,'joint',damping='.02',armature='.00001',frictionloss='.005');add(default,'geom',friction='1 .005 .0001',condim='3')
    w=add(r,'worldbody');add(w,'geom',name='floor',type='plane',size='3 3 .01',rgba='.85 .85 .8 1')
    xml={};qpos_order=[]
    def body_xml(b):
        parent=L.PARENT[b]
        if parent is None:
            el=add(w,'body',name='trunk_base',pos=vector(L.TRUNK_ORIGIN*.001));add(el,'freejoint',name='trunk_base_freejoint');add(el,'site',name='imu',size='.003',pos='-0.01 0 0.135')
        else:
            j=L.JOINT_OF_BODY[b];el=add(xml[parent],'body',name='x_'+b,pos=vector((pivots[b]-pivots[parent])*.001))
            lo,hi=TRAVEL[j['name']]['min_rad'],TRAVEL[j['name']]['max_rad']
            extra={'stiffness':'.05'} if j['name']=='jaw' else {}
            add(el,'joint',name=j['name'],axis=vector(j['axis']),range=f'{lo} {hi}',**extra);qpos_order.append(j['name'])
        mass,com,I=inertia_of(per_body[b])
        add(el,'inertial',pos=vector(com),mass=f'{mass:.6g}',fullinertia=vector([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
        xml[b]=el
        for c in [c for c in L.BODIES if L.PARENT[c]==b]:body_xml(c)
    body_xml('trunk')
    def box_geom(b,name,lo,hi,**kw):
        lo=np.asarray(lo);hi=np.asarray(hi);add(xml[b],'geom',name=name,type='box',pos=vector((lo+hi)/2),size=vector((hi-lo)/2),mass='0',rgba='.8 .3 .1 .25',group='3',**kw)
    for side in ['left','right']:
        g=1 if side=='left' else -1;p=pivots[f'{side}_foot']
        box_geom(f'{side}_foot',f'{side}_foot_collision',(np.array([-52,min(g*29,g*71),13.5])-p)*.001,(np.array([2,max(g*29,g*71),24])-p)*.001)
        add(xml[f'{side}_foot'],'site',name=f'{side}_foot',pos=vector((np.array([-25,g*50,13.5])-p)*.001),size='.003')
        for b in [f'{side}_upper_leg',f'{side}_lower_leg']:
            lo=np.min([e[0] for e in extents[b]],axis=0);hi=np.max([e[1] for e in extents[b]],axis=0);box_geom(b,b+'_collision',lo,hi,contype='2',conaffinity='2')
    add(xml['trunk'],'geom',name='trunk_shell_collision',type='ellipsoid',pos=vector((np.array([-6,0,142])-L.TRUNK_ORIGIN)*.001),size='.044 .0376 .024',mass='0',rgba='.8 .3 .1 .25',group='3',contype='1',conaffinity='1')
    add(xml['head'],'geom',name='head_shell_collision',type='ellipsoid',pos=vector((np.array([10,0,247])-pivots['head'])*.001),size='.062 .055 .033',mass='0',rgba='.8 .3 .1 .25',group='3',contype='1',conaffinity='1')
    contacts=add(r,'contact')
    for a,b in [('trunk_base','x_head'),('x_left_upper_leg','x_right_upper_leg'),('x_left_lower_leg','x_right_lower_leg')]:add(contacts,'exclude',body1=a,body2=b)
    act=add(r,'actuator')
    for name in L.ORDER:add(act,'position',name=name,joint=name,kp='5',ctrlrange='-2.4 2.4',forcerange='-.5 .5')
    sensors=add(r,'sensor');add(sensors,'gyro',name='imu_ang_vel',site='imu');add(sensors,'accelerometer',name='imu_accel',site='imu');add(sensors,'subtreeangmom',name='root_angmom',body='trunk_base')
    E.indent(r);E.ElementTree(r).write(R/'models/micro_x_14.xml',encoding='unicode')
    # Standing height at HOME: the absolute trunk height that puts the lowest foot corner on the floor.
    m=mujoco.MjModel.from_xml_path(str(R/'models/micro_x_14.xml'));d=mujoco.MjData(m)
    for i,name in enumerate(qpos_order):
        d.qpos[7+i]=L.HOME[name]
    mujoco.mj_forward(m,d)
    low=min(d.geom_xpos[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,f'{s}_foot_collision')][2]-m.geom_size[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,f'{s}_foot_collision')][2] for s in ['left','right'])
    # A free joint's qpos[:3] is the absolute body position, so this is a height, not an offset.
    home_z=round(float(L.TRUNK_ORIGIN[2]*.001-low+.001),5)
    total=sum(inertia_of(per_body[b])[0] for b in L.BODIES)
    (R/'engineering/control_interface.json').write_text(json.dumps(dict(joint_names=L.ORDER,home_rad=[L.HOME[n] for n in L.ORDER],observation_size=61,action_size=14,command_size=13,control_hz=50,physics_hz=200,action_scale=1,
        actuator_target='XL330 / BAM M6; assumed kp 200, 7.4 V',geometry='Rev B CAD-derived bodies in the design pose: printed-part meshes at PLA solid density plus purchased envelopes with catalogue masses',
        functional_dimensions='engineering/functional_layout.json',joint_ranges_rad={n:[TRAVEL[n]['min_rad'],TRAVEL[n]['max_rad']] for n in L.ORDER},joint_ranges_source='engineering/joint_travel.json (measured)',
        model_mass_kg=round(total,4),home_trunk_z_m=home_z,physical_verified=False),indent=2)+'\n')
    rig=dict(units='m',root='trunk',root_position_m=list(np.round(L.TRUNK_ORIGIN*.001+np.array([0,0,home_z]),6)),qpos_layout=dict(free=7,joints=qpos_order),
        bodies=[dict(name=b,parent=L.PARENT[b],pivot_m=np.round(pivots[b]*.001,6).tolist(),joint=(L.JOINT_OF_BODY[b]['name'] if b in L.JOINT_OF_BODY else None),
                     axis=(np.round(np.asarray(L.JOINT_OF_BODY[b]['axis'],float)/np.linalg.norm(L.JOINT_OF_BODY[b]['axis']),6).tolist() if b in L.JOINT_OF_BODY else None),
                     home_rad=(L.HOME[L.JOINT_OF_BODY[b]['name']] if b in L.JOINT_OF_BODY else None),mass_kg=round(inertia_of(per_body[b])[0],5)) for b in L.BODIES],
        policy_joints=L.ORDER,mass_kg=round(total,4))
    (R/'models/rig.json').write_text(json.dumps(rig,indent=1)+'\n')
    print(f'Built Rev C 14-axis model, mass {total*1000:.0f} g, HOME trunk height {home_z*1000:.1f} mm')
if __name__=='__main__':build()
