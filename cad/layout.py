"""Rev B joint and servo layout. Design pose = qpos 0 (straight legs), so every axis is
world-aligned and every bracket prints flat. World: X forward, Y left, Z up, mm.

Pivots, axes and servo placements come from engineering/functional_layout.json (measured
functional dimensions of the reference robot). The part geometry built around them in
cad/build.py is original. Policy HOME offsets stay joint angles and are never baked in here.
"""
from pathlib import Path
import json
import numpy as np
R=Path(__file__).resolve().parents[1]
_F=json.loads((R/'engineering/functional_layout.json').read_text())
ENVELOPES=_F['link_envelopes_mm']
# The trunk body frame sits 120 mm above the floor, like the reference robot, so trunk height
# means the same thing in both models. Everything else is a joint pivot.
TRUNK_ORIGIN=np.array([0.,0.,120.])
ORDER=['left_hip_yaw','left_hip_roll','left_hip_pitch','left_knee','left_ankle','neck_pitch','head_pitch','head_yaw','head_roll','right_hip_yaw','right_hip_roll','right_hip_pitch','right_knee','right_ankle']
HOME=dict(zip(ORDER,[0,-.0873,-.4579,-.0049,.4530,.3491,.3491,0,0,0,.0873,.4579,.0049,-.4530]));HOME['jaw']=0.0
BODIES=['trunk','left_yaw2roll','left_hip','left_upper_leg','left_lower_leg','left_foot','neck','head_base','head_yoke','head','jaw','right_yaw2roll','right_hip','right_upper_leg','right_lower_leg','right_foot']
PARENT={'trunk':None,'left_yaw2roll':'trunk','left_hip':'left_yaw2roll','left_upper_leg':'left_hip','left_lower_leg':'left_upper_leg','left_foot':'left_lower_leg',
        'neck':'trunk','head_base':'neck','head_yoke':'head_base','head':'head_yoke','jaw':'head',
        'right_yaw2roll':'trunk','right_hip':'right_yaw2roll','right_upper_leg':'right_hip','right_lower_leg':'right_upper_leg','right_foot':'right_lower_leg'}
CHILD_OF={'left_hip_yaw':'left_yaw2roll','left_hip_roll':'left_hip','left_hip_pitch':'left_upper_leg','left_knee':'left_lower_leg','left_ankle':'left_foot',
          'right_hip_yaw':'right_yaw2roll','right_hip_roll':'right_hip','right_hip_pitch':'right_upper_leg','right_knee':'right_lower_leg','right_ankle':'right_foot',
          'neck_pitch':'neck','head_pitch':'head_base','head_yaw':'head_yoke','head_roll':'head','jaw':'jaw'}
SERVOS=[]
for name,j in _F['joints'].items():
    child=CHILD_OF[name];parent=PARENT[child];body=j['servo_in']
    # The link that does NOT hold the servo body carries the horn plate at the pivot plane.
    plate_on=parent if body==child else child
    SERVOS.append(dict(name=name,P=np.array(j['pivot'],float),axis=np.array(j['axis'],float),
                       h=np.array(j['h'],float),d=np.array(j['d'],float),
                       parent=parent,child=child,body=body,plate_on=plate_on))
JOINT_OF_BODY={s['child']:s for s in SERVOS}
def get(name):return next(s for s in SERVOS if s['name']==name)
def pivot(name):return get(name)['P']
def axis(name):return get(name)['axis']
def servos_in(body):return [s for s in SERVOS if s['body']==body]
def plates_on(body):return [s for s in SERVOS if s['plate_on']==body]
