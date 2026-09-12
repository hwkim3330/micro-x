"""Actuated Micro X joint layout. World frame: X forward, Y left, Z up, mm, floor Z=0.

Pivot points and axes of the 14 policy joints come from engineering/functional_interface.json
(trunk origin 125 mm above the floor). Horn direction h and body long direction d are
original X packaging decisions. The jaw is a 15th, non-policy axis.
"""
from pathlib import Path
import json
import numpy as np
R=Path(__file__).resolve().parents[1]
TRUNK=np.array([0.0,0.0,125.0])
_rec={j['name']:j for j in json.loads((R/'engineering/functional_interface.json').read_text())['joints']}
def pivot(name):return TRUNK+np.array(_rec[name]['pivot_at_home_m'])*1000
def axis(name):return np.array(_rec[name]['axis_at_home'],dtype=float)
HOME=dict(zip(['left_hip_yaw','left_hip_roll','left_hip_pitch','left_knee','left_ankle','neck_pitch','head_pitch','head_yaw','head_roll','right_hip_yaw','right_hip_roll','right_hip_pitch','right_knee','right_ankle'],[0,-.0873,-.4579,-.0049,.4530,.3491,.3491,0,0,0,.0873,.4579,.0049,-.4530]))
def leg(side):
    s=1 if side=='left' else -1;p=lambda n:pivot(f'{side}_{n}');a=lambda n:axis(f'{side}_{n}')
    # Leg pitch axes are tilted 5 degrees about X at HOME; long directions follow that tilt.
    down=np.array([0,0,-1.0]);tilt=a('hip_pitch');down_t=np.cross(tilt,np.array([1.0,0,0]));down_t=-down_t/np.linalg.norm(down_t)
    if down_t[2]>0:down_t=-down_t
    return [
        dict(name=f'{side}_hip_yaw',P=p('hip_yaw'),axis=a('hip_yaw'),h=[0,0,-1],d=[-1,0,0],parent='trunk',child=f'{side}_yaw2roll'),
        dict(name=f'{side}_hip_roll',P=p('hip_roll'),axis=a('hip_roll'),h=[1,0,0],d=[0,0,-1],parent=f'{side}_yaw2roll',child=f'{side}_hip'),
        dict(name=f'{side}_hip_pitch',P=p('hip_pitch'),axis=a('hip_pitch'),h=-s*tilt*np.sign(tilt[1]),d=down_t,parent=f'{side}_hip',child=f'{side}_thigh'),
        dict(name=f'{side}_knee',P=p('knee'),axis=a('knee'),h=-s*tilt*np.sign(tilt[1]),d=down_t,parent=f'{side}_thigh',child=f'{side}_shin'),
        dict(name=f'{side}_ankle',P=p('ankle'),axis=a('ankle'),h=s*tilt*np.sign(tilt[1]),d=-down_t*np.cos(np.radians(15))+np.array([np.sin(np.radians(15)),0,0]),parent=f'{side}_shin',child=f'{side}_foot'), # leans 15 deg forward to clear the knee servo
    ]
NECK=[
    dict(name='neck_pitch',P=pivot('neck_pitch'),axis=axis('neck_pitch'),h=[0,1,0],d=[0,0,-1],parent='trunk',child='neck'),
    dict(name='head_pitch',P=pivot('head_pitch'),axis=axis('head_pitch'),h=[0,1,0],d=[0,0,-1],parent='neck',child='head_base'),
    dict(name='head_yaw',P=pivot('head_yaw'),axis=axis('head_yaw'),h=[0,0,-1],d=[0,1,0],parent='head_base',child='head_yoke'),
    dict(name='head_roll',P=pivot('head_roll'),axis=axis('head_roll'),h=[1,0,0],d=[0,1,0],parent='head_yoke',child='head'),
]
JAW=dict(name='jaw',P=np.array([37.0,14.0,226.0]),axis=np.array([0,1.0,0]),h=[0,1,0],d=[0,0,1],parent='head',child='jaw')
SERVOS=leg('left')+NECK+leg('right')+[JAW]
ORDER=['left_hip_yaw','left_hip_roll','left_hip_pitch','left_knee','left_ankle','neck_pitch','head_pitch','head_yaw','head_roll','right_hip_yaw','right_hip_roll','right_hip_pitch','right_knee','right_ankle']
BODIES=['trunk','left_yaw2roll','left_hip','left_thigh','left_shin','left_foot','neck','head_base','head_yoke','head','jaw','right_yaw2roll','right_hip','right_thigh','right_shin','right_foot']
PARENT={'trunk':None,'left_yaw2roll':'trunk','left_hip':'left_yaw2roll','left_thigh':'left_hip','left_shin':'left_thigh','left_foot':'left_shin','neck':'trunk','head_base':'neck','head_yoke':'head_base','head':'head_yoke','jaw':'head','right_yaw2roll':'trunk','right_hip':'right_yaw2roll','right_thigh':'right_hip','right_shin':'right_thigh','right_foot':'right_shin'}
JOINT_OF_BODY={s['child']:s for s in SERVOS}
def get(name):return next(s for s in SERVOS if s['name']==name)
