"""Original X primitives around measured functional joint dimensions.
No upstream surfaces, component geometry, mass or inertia tables are imported.
Joint measurements have separate provenance. Not production actuator CAD.
"""
from pathlib import Path
import json,xml.etree.ElementTree as E
import numpy as np
R=Path(__file__).resolve().parents[1]
NAMES=['left_hip_yaw','left_hip_roll','left_hip_pitch','left_knee','left_ankle','neck_pitch','head_pitch','head_yaw','head_roll','right_hip_yaw','right_hip_roll','right_hip_pitch','right_knee','right_ankle']
HOME=[0,-.0873,-.4579,-.0049,.4530,.3491,.3491,0,0,0,.0873,.4579,.0049,-.4530]
def vector(v):return ' '.join(f'{x:.9g}' for x in v)
def add(p,tag,**kw):return E.SubElement(p,tag,{k:str(v) for k,v in kw.items()})
def build():
    records={j['name']:j for j in json.loads((R/'engineering/functional_interface.json').read_text())['joints']}
    r=E.Element('mujoco',model='Micro_X_14_functional_interface_study');add(r,'compiler',angle='radian',autolimits='true');add(r,'option',timestep='.005',gravity='0 0 -9.81',iterations=80)
    default=add(r,'default');add(default,'joint',damping='.02',armature='.00001');add(default,'geom',friction='1 .005 .0001',condim='3')
    w=add(r,'worldbody');add(w,'geom',name='floor',type='plane',size='3 3 .01',rgba='.85 .85 .8 1')
    trunk=add(w,'body',name='trunk_base',pos='0 0 .125');add(trunk,'freejoint',name='trunk_base_freejoint');add(trunk,'site',name='imu',size='.003')
    add(trunk,'geom',name='x_torso',type='ellipsoid',size='.036 .035 .025',mass='.17',rgba='.92 .89 .78 1')
    chains=[NAMES[:5],NAMES[5:9],NAMES[9:]];contacts=add(r,'contact')
    for chain in chains:
        parent=trunk;previous=np.zeros(3);body_names=[]
        for index,name in enumerate(chain):
            rec=records[name];pivot=np.array(rec['pivot_at_home_m']);axis=np.array(rec['axis_at_home']);axis/=np.linalg.norm(axis)
            b=add(parent,'body',name='x_'+name,pos=vector(pivot-previous));body_names.append('x_'+name)
            add(b,'joint',name=name,axis=vector(axis),range='-2.4 2.4',ref=HOME[NAMES.index(name)])
            terminal=index==len(chain)-1
            if terminal and name.endswith('ankle'):
                z=-.125-pivot[2]+.006
                add(b,'geom',name=name+'_sole',type='box',size='.036 .021 .006',pos=vector([.008,0,z]),mass='.035',rgba='.86 .56 .16 1')
                add(b,'geom',name=name+'_bracket',type='capsule',size='.009',fromto=vector([0,0,0,.008,0,z+.006]),mass='.025',rgba='.19 .22 .2 1')
            elif terminal:
                add(b,'geom',name='x_head_shell',type='ellipsoid',size='.046 .036 .025',pos='.036 0 .006',mass='.13',rgba='.92 .89 .78 1')
                for sign in [-1,1]:add(b,'geom',name=f'x_eye_{sign}',type='sphere',size='.01',pos=vector([.058,sign*.031,.015]),mass='.003',rgba='.06 .07 .06 1',contype='0',conaffinity='0')
            else:
                next_pivot=np.array(records[chain[index+1]]['pivot_at_home_m']);delta=next_pivot-pivot
                rotor_only=index<2 if len(chain)==5 else index>0
                add(b,'geom',name=name+'_link',type='capsule',size='.009' if rotor_only else '.01',fromto=vector([0,0,0,*delta]),mass='.018' if rotor_only else '.04',rgba='.19 .22 .2 1',contype='0' if rotor_only else '1',conaffinity='0' if rotor_only else '1')
            parent=b;previous=pivot
        if len(chain)==4:
            # Hollow head admits its neck/gimbal stack; solid proxy doesn't.
            for name in body_names[:-1]:add(contacts,'exclude',body1=name,body2=body_names[-1])
    a=add(r,'actuator')
    for name in NAMES:add(a,'position',name=name,joint=name,kp='5',ctrlrange='-2.4 2.4',forcerange='-.5 .5')
    sensors=add(r,'sensor');add(sensors,'gyro',name='imu_ang_vel',site='imu');add(sensors,'accelerometer',name='imu_accel',site='imu')
    E.indent(r);E.ElementTree(r).write(R/'models/micro_x_14.xml',encoding='unicode')
    (R/'engineering/control_interface.json').write_text(json.dumps(dict(joint_names=NAMES,home_rad=HOME,observation_size=61,action_size=14,command_size=13,control_hz=50,physics_hz=200,action_scale=1,actuator_target='XL330 / BAM M6; assumed kp 200, 7.4 V',geometry='authored X primitive mechanics around measured functional joint dimensions; not P0 shell or finished actuator CAD',functional_dimensions='engineering/functional_interface.json',physical_verified=False),indent=2)+'\n')
    print('Built original X geometry around 14-axis functional interface')
if __name__=='__main__':build()
