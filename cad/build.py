"""Micro X Rev A: actuated 14-axis chibi T-rex. All dimensions in mm, world frame
X forward, Y left, Z up, floor at Z=0, trunk origin 125 mm above the floor.

Original X design. Joint pivots/axes follow engineering/functional_interface.json so the
robot keeps the Microduck policy interface; brackets, shells, servo packaging and
proportions are authored here. Servo interface dimensions are purchased-part data.
NOT a physically validated or production-released robot.
"""
from pathlib import Path
import json, math, sys
import cadquery as cq
import numpy as np
import trimesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
import layout as L
import servo as S
from appearance import paint
R=Path(__file__).resolve().parents[1]
for folder in ['models/step','models/print','artifacts','models/purchased']:(R/folder).mkdir(parents=True,exist_ok=True)
CREAM=[.98,.94,.79,1];CORAL=[.98,.94,.79,1];GRAPHITE=[.16,.18,.19,1];WHITE=[.99,.99,.97,1];MINT=[.62,.82,.72,1];SLATE=[.30,.34,.34,1]
DENSITY=0.00124 # g/mm3 PLA solid-equivalent; slicer mass will be lower
parts=[];purchased=[]

def box(x0,x1,y0,y1,z0,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
def rbox(x0,x1,y0,y1,z0,z1,r):return box(x0,x1,y0,y1,z0,z1).edges().fillet(min(r,(x1-x0)/2-.01,(y1-y0)/2-.01,(z1-z0)/2-.01))
def ellipsoid(c,h):return cq.Workplane('XY').sphere(1).val().transformGeometry(cq.Matrix([[h[0],0,0,c[0]],[0,h[1],0,c[1]],[0,0,h[2],c[2]]]))
def ell(c,h):return cq.Workplane(obj=ellipsoid(c,h))
def cyl(p,axis,r,length):
    plane={'Z':'XY','Y':'XZ','X':'YZ'}[axis];return cq.Workplane(plane,origin=tuple(p)).circle(r).extrude(length)
def mirror(shape):return shape.mirror('XZ')
def keep_solid(shape,name):
    shape=shape.clean();solids=shape.solids().vals()
    if len(solids)!=1:
        # Keep the largest solid if tiny slivers appear, but report it.
        big=max(solids,key=lambda s:s.Volume());small=sum(s.Volume() for s in solids)-big.Volume()
        if small>200:raise ValueError(f'{name}: {len(solids)} solids, {small:.1f} mm3 loose')
        for sl in solids:
            if sl is not big:bb=sl.BoundingBox();print(f'  WARNING {name}: dropped {sl.Volume():.1f} mm3 sliver at x {bb.xmin:.1f}..{bb.xmax:.1f} y {bb.ymin:.1f}..{bb.ymax:.1f} z {bb.zmin:.1f}..{bb.zmax:.1f}')
        shape=cq.Workplane(obj=big)
    if not shape.val().isValid():raise ValueError(name+' invalid solid')
    return shape

def add(name,shape,color,body,print_axis='Z',note='',group='frame'):
    shape=keep_solid(shape,name)
    path=R/'models/step'/f'{name}.step';cq.exporters.export(shape,str(path))
    restored=cq.importers.importStep(str(path))
    if len(restored.solids().vals())!=1 or not restored.val().isValid():raise ValueError(name+' STEP round trip lost valid solid')
    stl=R/'models'/f'{name}.stl';cq.exporters.export(shape,str(stl),tolerance=.05,angularTolerance=.1)
    mesh=trimesh.load_mesh(stl,process=True);mesh.merge_vertices(digits_vertex=6);mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight:
        # Retry with a coarser tessellation before giving up; report which part needed it.
        cq.exporters.export(shape,str(stl),tolerance=.1,angularTolerance=.2);mesh=trimesh.load_mesh(stl,process=True);mesh.merge_vertices(digits_vertex=5);print('  retessellated',name)
    mesh.export(stl)
    if not mesh.is_watertight or mesh.volume<=0:raise ValueError(name+' mesh invalid')
    printable=mesh.copy()
    rot={'Y':math.pi/2,'-Y':-math.pi/2}
    if print_axis in rot:printable.apply_transform(trimesh.transformations.rotation_matrix(rot[print_axis],[1,0,0]))
    if print_axis=='X':printable.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
    if print_axis=='-X':printable.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[0,1,0]))
    if print_axis=='-Z':printable.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
    printable.vertices-=np.r_[printable.bounds.mean(axis=0)[:2],printable.bounds[0,2]];printable.export(R/'models/print'/f'{name}.stl')
    vol=shape.val().Volume()
    parts.append(dict(name=name,shape=shape,mesh=mesh,color=color,body=body,group=group,note=note,printed=True,dimensions_mm=np.round(mesh.extents,2).tolist(),volume_mm3=round(vol,1),mass_g=round(vol*DENSITY,2),step=f'models/step/{name}.step',stl=f'models/print/{name}.stl'))
    print(f'  {name:22s} {vol*DENSITY:7.1f} g')
    return shape

def buy(name,shape,color,body,mass_g,note,kind):
    shape=keep_solid(shape,name)
    stl=R/'models/purchased'/f'{name}.stl';cq.exporters.export(shape,str(stl),tolerance=.08,angularTolerance=.15)
    mesh=trimesh.load_mesh(stl,process=True);mesh.export(stl)
    purchased.append(dict(name=name,shape=shape,mesh=mesh,color=color,body=body,kind=kind,mass_g=mass_g,note=note,printed=False,dimensions_mm=np.round(mesh.extents,2).tolist(),stl=f'models/purchased/{name}.stl'))

# ---------------------------------------------------------------- servos (purchased)
# Servo bodies live in the child link for hip pitch, knee and head yaw (horn bolted to the parent plate);
# everywhere else the body sits in the parent link and the child carries horn/idler plates.
IN_CHILD={'left_hip_pitch','right_hip_pitch','left_knee','right_knee','head_yaw'}
for s in L.SERVOS:
    buy('servo_'+s['name'],S.envelope(s['P'],s['h'],s['d']),GRAPHITE,s['parent'] if s['name'] not in IN_CHILD else s['child'],S.MASS_G,'XL330-class smart servo envelope; verify drawing before ordering',
        'actuator')

def horn(s,**kw):return S.horn_plate(s['P'],s['h'],s['d'],**kw)
def idler(s,**kw):return S.idler_plate(s['P'],s['h'],s['d'],**kw)
def pocket(s,**kw):return S.pocket(s['P'],s['h'],s['d'],**kw)

# ---------------------------------------------------------------- leg frame helpers
def leg_frame(side):
    a=math.radians(-5 if side=='left' else 5);Rm=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    O=L.pivot(f'{side}_hip_roll')
    def to_world(shape):
        plane=cq.Plane(origin=tuple(O),xDir=(1,0,0),normal=tuple(Rm[:,2]));return cq.Workplane(obj=shape.val().moved(cq.Location(plane)))
    def local(p):return Rm.T@(np.asarray(p)-O)
    return to_world,local

def build_leg(side):
    s=1 if side=='left' else -1
    W,loc=leg_frame(side)
    hy,hr,hp,kn,an=[L.get(f'{side}_{n}') for n in ['hip_yaw','hip_roll','hip_pitch','knee','ankle']]
    def lb(x0,x1,y0,y1,z0,z1,r=None):
        # leg-local box; y is mirrored for the right leg so the same numbers describe both sides
        if s<0:y0,y1=-y1,-y0
        return W(rbox(x0,x1,y0,y1,z0,z1,r) if r else box(x0,x1,y0,y1,z0,z1))
    # --- yaw-to-roll bracket: bolted under the hip yaw horn, cradles the hip roll servo (world frame)
    yb=horn(hy,width=26,length=30)
    yb=yb.union(box(-6,21,s*5.5 if s>0 else -29.5,s*29.5 if s>0 else -5.5,84,117.5)).cut(pocket(hr))
    yb=yb.cut(box(-8,23,s*7.1 if s>0 else -27.9,s*27.9 if s>0 else -7.1,84,116.5)) # open below the servo, side walls remain
    yb=yb.cut(pocket(hy,clearance=.6))
    add(f'{side}_yaw2roll',yb,SLATE,f'{side}_yaw2roll','-Z','Hip yaw horn plate with hip roll servo cradle; servo drops in from below and is retained by the hip bracket horn/idler bolts. M2 case screws to be confirmed.')
    # --- hip bracket (leg frame): narrow roll clevis (stays clear of the centreline at roll HOME ±15°),
    #     pitch clevis plates and a top tie above the pitch servo cap
    hb=lb(0,3,-8,8.5,-29.5,14).union(lb(0,3,8,25,-14,14)).union(lb(-30.5,3,22,25,-13,13)).union(lb(-33,-30,-8,8.5,-29.5,7)).union(lb(-33,3,-8,8.5,-29.5,-26))
    hb=hb.union(lb(-30.5,-6.5,55,58,-13,13)).union(lb(-30.5,-6.5,22,58,19.5,22.5)).union(lb(-30.5,-6.5,22,25,13,22.5)).union(lb(-30.5,-6.5,55,58,13,22.5))
    hb=hb.union(horn(hr,width=16,length=26)).union(idler(hr,width=16,length=17)).union(horn(hp,width=24,length=26)).union(idler(hp,width=24,length=26))
    hb=hb.cut(pocket(hr,clearance=.6)).cut(pocket(hp,clearance=.6))
    add(f'{side}_hip',hb,SLATE,f'{side}_hip','X','Hip bracket: roll horn/idler plates with an under-bar, pitch horn/idler plates and a tie above the pitch servo cap. Pitch servo body lives in the thigh.')
    # --- thigh: cup around the hip pitch servo (front/rear walls, bottom, short-end cap), knee clevis plates, tie over the knee servo
    th=lb(-31.9,-5.1,27,53,-28.2,10,6).cut(lb(-28.9,-8.1,26,54,-24.9,11))
    th=th.union(lb(-31.9,-5.1,27,53,-28.2,-24.9)).union(lb(-31.9,-5.1,27,53,8,12.5)) # bottom and short-end cap
    th=th.union(lb(-52.9,-28.9,18,21,-48.5,-17)).union(lb(-52.9,-28.9,51,54,-48.5,-17)).union(lb(-52.9,-28.9,18,54,-20,-17))
    th=th.union(horn(kn,width=24,length=26)).union(idler(kn,width=24,length=26))
    th=th.cut(pocket(hp,clearance=.5)).cut(pocket(kn,clearance=.6))
    add(f'{side}_thigh',th,CREAM,f'{side}_thigh','Y' if s>0 else '-Y','Thigh: houses the hip pitch servo, carries the knee horn and idler plates with a tie above the knee servo.')
    # --- shin: inboard spine plate, knee servo rear/bottom walls, upright ankle servo cradle (front wall, bottom, cap)
    sh=lb(-54.3,-9.5,21.5,49,-86,-30,7).cut(lb(-52.1,-11.7,23.7,50,-84,-28)) # rounded shin shell: front/back/inboard walls + bottom, open outboard side and top
    sh=sh.union(lb(-54.3,-51.3,21.5,49,-60.4,-30)).union(lb(-54.3,-33,21.5,49,-63,-60.4)).union(lb(-35,-9.5,21.5,49,-86,-83.8)) # knee servo rear wall, bridge, floor
    sh=sh.union(S.cradle(an['P'],an['h'],an['d'],['y+','y-','cap'],wall=2.5)) # cradle follows the leaning ankle servo; open at the top
    sh=sh.cut(lb(-60,0,20,50,-95,-74)) # keep the shell above the foot's swing
    sh=sh.cut(lb(-33,0,20,50,-46,-20)) # front of the shell steps down so it clears the hip-pitch servo when the knee bends
    sh=sh.cut(pocket(kn,clearance=.5)).cut(pocket(an,clearance=.5))
    add(f'{side}_shin',sh,CREAM,f'{side}_shin','Y' if s>0 else '-Y','Shin: spine plate with knee servo bay above an upright ankle servo cradle; both servos retained by the neighbouring clevis plates.')
    # --- foot: ankle horn/idler plates on a wide rounded hollow sole with a toe bumper
    sole=rbox(-38,44,s*26 if s>0 else -74,s*74 if s>0 else -26,0,11,9)
    sole=sole.union(rbox(24,52,s*30 if s>0 else -70,s*70 if s>0 else -30,0,15,7))
    sole=sole.cut(rbox(-34,40,s*30 if s>0 else -70,s*70 if s>0 else -30,-5,8.5,6)) # hollow underside, 2.5 mm skin; TPU pad fills it
    ft=sole.union(horn(an,width=22,length=24,thickness=3)).union(idler(an,width=22,length=24,thickness=3))
    for y0,y1 in [(24.5,28.5),(57.5,61.5)]:ft=ft.union(box(-8,8,s*y0 if s>0 else -y1,s*y1 if s>0 else -y0,8,21)) # posts join the plates to the sole
    ft=ft.union(rbox(-15,15,s*22 if s>0 else -64,s*64 if s>0 else -22,8,25,5).cut(box(-13.5,13.5,s*24.5 if s>0 else -61.5,s*61.5 if s>0 else -24.5,7,40))) # low boot cuff around the ankle plates
    ft=ft.cut(pocket(an,clearance=.5))
    add(f'{side}_foot',ft,CREAM,f'{side}_foot','Z','Foot: ankle horn/idler plates on a wide rounded sole with a toe bumper; replaceable TPU sole pad is a follow-up.',group='shell')

for side in ['left','right']:
    print(side,'leg');build_leg(side)

# ---------------------------------------------------------------- trunk: chassis, shell, chest panel, tail battery cover
print('trunk')
egg_c=(2,0,133);egg_h=(56,42,44)
np_=L.get('neck_pitch');lhy=L.get('left_hip_yaw');rhy=L.get('right_hip_yaw')
chassis=cq.Workplane('XY',origin=(2,0,150)).ellipse(40,25).extrude(3) # elliptical top plate fits the egg interior at Z 150
for s,hy in [(1,lhy),(-1,rhy)]:
    hanger=box(-19,15.5,5.4 if s>0 else -29.2,29.2 if s>0 else -5.4,121,150.5).cut(box(-18.9,16,7.1 if s>0 else -27.9,27.9 if s>0 else -7.1,121,150))
    chassis=chassis.union(hanger).cut(pocket(hy,clearance=.6))
neckbox=box(16.4,39,-18,10.5,130,170).cut(box(15.6,36.4,-15.4,11.5,132.5,170)) # no rear wall: the hip yaw servos sit just behind
chassis=chassis.union(neckbox).cut(pocket(np_,clearance=.6))
tray=box(-96,-30,-21.1,21.1,118,120).union(box(-96,-30,-21.1,-19.5,120,140)).union(box(-96,-30,19.5,21.1,120,140)).union(box(-33,-30,-21.1,21.1,120,140))
tray=tray.cut(box(-92,-40,-12,12,117,121)) # tray floor window
chassis=chassis.union(box(-33,-30,-16,16,139,151)) # tray-to-plate web on the tray's rear wall, behind the battery
chassis=chassis.union(box(36.4,40,-19,19,106,151)).cut(box(30,41,-20,20,151.5,170)) # chest board mount wall
for y in [-15,15]:
    for z in [110,154]:chassis=chassis.cut(cyl((36,y,z),'X',1.3,6))
chassis=chassis.cut(box(13,39,11,20,138,175)) # clearance for the neck horn plate
chassis=chassis.union(tray) # the tray runs out the back into the tail cover
for x,reach in [(-22,29.0),(25,28.0)]: # shell bosses stop inside the skin; M3 from outside through the shell flank
    for sgn in (1,-1):
        boss=box(x-2,x+2,min(sgn*20,sgn*reach),max(sgn*20,sgn*reach),136,151)
        chassis=chassis.union(boss).cut(cyl((x,35,140),'Y',1.3,15) if sgn>0 else cyl((x,-20,140),'Y',1.3,15))
chassis=chassis.cut(cyl((-55,40,129),'Y',1.3,80)) # tail cover screws through both tray walls
add('chassis',chassis,SLATE,'trunk','-Z','Internal chassis: hip yaw hangers, neck servo bay, battery tray (NP-F550 class), chest board wall and four M3 shell bosses.')
egg=ell(egg_c,egg_h).cut(ell(egg_c,tuple(h-2.4 for h in egg_h)))
egg=egg.cut(box(-40,36,-200,200,-10,133)).cut(box(-200,200,-200,200,-10,113)) # open underneath over the hips; the belly and rump run lower for a full egg
egg=egg.cut(box(-21,40,-23,23,140,200)) # neck slot: the sleeve passes through and pitches; also clears the neck servo bay
egg=egg.cut(box(-120,-30,-23,23,100,142)) # battery / tail opening (runs out the bottom so no sliver is left under it)
for z in range(122,152,6):egg=egg.cut(box(40,70,-9,9,z,z+2.5)) # speaker grille on the chest
for x in [-22,25]:egg=egg.cut(cyl((x,60,140),'Y',1.7,120)) # four M3 through the flanks into the chassis bosses
add('torso_shell',egg,MINT,'trunk','-Z','One-piece egg shell, open below the hips, with neck and tail-battery openings and a chest grille. Four M3 through the flanks into chassis bosses; remove it to reach the board.',group='shell')
tail_o=ell((-70,0,130),(58,33,24));tail_i=ell((-70,0,130),(55.8,30.8,21.8))
tail=tail_o.cut(tail_i).cut(box(-50,60,-100,100,0,300)) # cap open toward the torso
for sgn in [1,-1]:
    tab=box(-56,-50,21.3 if sgn>0 else -30.2,30.2 if sgn>0 else -21.3,122,138) # reaches into the cover wall
    tail=tail.union(tab)
tail=tail.cut(cyl((-55,40,129),'Y',1.7,80))
add('tail_cover',tail,CREAM,'trunk','-X','Tail = battery cover: slides over the tray and holds an NP-F550 class pack; two M3 screws into the tray.',group='shell')
buy('battery_np_f550',rbox(-104,-33,-19.2,19.2,120,140.5,2),GRAPHITE,'trunk',100,'NP-F550 class 7.4 V 2600 mAh removable pack; dimensions 70.8 x 38.4 x 20.5 mm nominal','battery')
buy('compute_board',box(40,41.6,-18,18,108,149),[.1,.35,.25,1],'trunk',30,'Vertical carrier for a compute module (50 x 36 usable outline); PCB placeholder behind the chest grille','electronics')

# ---------------------------------------------------------------- neck stack
print('neck')
hp_=L.get('head_pitch');hyw=L.get('head_yaw');hro=L.get('head_roll');jaw=L.get('jaw')
neck=horn(np_,width=20,length=30)
neck=neck.union(box(-4.1,21.9,-18,10.5,176,214.5).cut(box(-1.5,19.3,-15.4,12,179.4,215)))
neck=neck.union(box(13,21.9,10,17.5,170,180)).cut(pocket(hp_,clearance=.6))
add('neck_link',neck,GRAPHITE,'neck','Y','Neck: neck-pitch horn plate rising into the head-pitch servo bay.')
sleeve=rbox(-11,28,-21.5,21.5,172,213,9).cut(rbox(-8.6,25.6,-19.1,19.1,170,215,7)) # neck sleeve: hides both neck servos, rides inside the torso's neck slot
sleeve=sleeve.cut(box(-12,30,10,25,170,182)) # notch for the neck horn plate
for sgn in (1,-1):sleeve=sleeve.cut(box(-12,30,min(sgn*19,sgn*25),max(sgn*19,sgn*25),170,177)) # trim the side walls at the bottom for the pitch swing
add('neck_sleeve',sleeve,MINT,'neck','Z','Neck sleeve: rounded tube around the neck link and head-pitch servo; rotates with the neck inside the torso slot.',group='shell')
hbase=horn(hp_,width=24,length=26).union(box(8,14.5,11,17.5,216,223.1)).union(horn(hyw,width=20,length=26))
add('head_base',hbase,SLATE,'head_base','Z','Head base: head-pitch horn plate and the fixed head-yaw horn plate; the only part that stays still while the head yaws.')
yoke=box(-4.1,19,-12.5,25,224.2,255).cut(box(-1.5,20,-9.9,26,226.2,253)).cut(pocket(hyw,clearance=.5)) # open toward +X and +Y
yoke=yoke.union(box(-36,-12.5,-12.4,26.5,223.5,250).cut(box(-36.1,-12.4,-10,25,227.6,247.6))).cut(pocket(hro,clearance=.6)).cut(box(-37,-28,22,27,223,229)) # roll servo box; rear-outer corner chamfered away from the skull
yoke=yoke.union(box(-12.1,-3.6,12.8,26.5,224,250)).union(box(-14,-12.1,24.9,26.5,224,250)).union(box(-12.1,-3.6,-15,-12.8,224,250)).union(box(-14,-12.1,-15,-10.5,224,250)).union(box(-4.1,-3.6,-15,-9.9,224,250)) # rails join the yaw and roll boxes beside the head roll plate's sweep
add('head_yoke',yoke,SLATE,'head_yoke','Z','Yoke: carries the head-yaw servo body (horn down onto the base) and the head-roll servo.')
frame=horn(hro,width=20,length=24).union(idler(hro,width=20,length=24)).union(box(-9,-6,-10,10,226,264)).union(box(-42,-39,-10,10,226,258)).union(box(-42,-6,-10,10,255,258)).union(box(-9,20.5,-10,10,261,264)).union(box(19.4,24.6,-10,10,246,261.5))
frame=frame.union(box(24.4,26.6,-18,16,224,253)).union(box(24.4,49.5,-18,-15.9,224,245)).cut(pocket(jaw,clearance=.5)) # jaw bay: rear wall and -Y wall (no top: the muzzle ceiling is low)
frame=frame.union(box(47.5,49.5,-16,13.5,222,246)) # camera wall doubles as the bay's front wall
for y in [-10.5,10.5]:
    for z in [229.75,242.25]:frame=frame.cut(cyl((47,y,z),'X',1.1,6))
frame=frame.cut(cyl((47,0,236),'X',6,6))
for x in [-30,15]:frame=frame.cut(cyl((x,0,254),'Z',1.3,12))
add('head_frame',frame,SLATE,'head','Z','Head frame: head-roll clevis, top rail, jaw servo bay and the camera carrier wall (Camera Module 3 hole pattern). Skull screws to the rail.')

# ---------------------------------------------------------------- head shells
print('head')
head_c=(-8,0,241);head_h=(50,41,37);muz_c=(38,0,234);muz_h=(28,34,27)
outer=ell(head_c,head_h).union(ell(muz_c,muz_h));inner=ell(head_c,tuple(h-2.2 for h in head_h)).union(ell(muz_c,tuple(h-2.2 for h in muz_h)))
skull=outer.cut(inner)
skull=skull.cut(box(-200,30,-200,200,0,214)) # open below for the neck stack
skull=skull.cut(box(28,200,-200,200,0,222)) # mouth opening; the jaw closes it
skull=skull.cut(cyl((8.9,0,214),'Z',26,10))
skull=skull.union(cyl((58,0,236),'X',10,10).intersect(ell(muz_c,tuple(h+3 for h in muz_h)))).cut(cyl((49,0,236),'X',6.5,30)) # camera ring boss: the single camera is the eye
for sgn in [1,-1]:skull=skull.cut(cyl((62,sgn*11,228),'X',1.8,10)) # nostrils
for x in [-30,15]:skull=skull.union(cyl((x,0,264.5),'Z',4,12).intersect(ell(head_c,tuple(h-.6 for h in head_h)))).cut(cyl((x,0,263),'Z',1.7,14)) # bosses sit on the head frame rail
for y in [20,-17]:skull=skull.cut(cyl((37,y,226),'Y',9,8)) # beak arm slots
add('skull',skull,MINT,'head','Z','Skull: one-piece hollow head with muzzle, camera ring and nostrils; no separate eye parts. Two M3 screws down into the head frame rail.',group='shell')
def loft(sections):
    wires=[cq.Workplane('YZ',origin=(x,0,z)).ellipse(w,h).val() for x,z,w,h in sections]
    return cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=False))
# Solid lower beak: elliptical loft from the jaw pivot forward, following the muzzle footprint (tessellates cleanly, unlike a plane-cut ellipsoid).
beak=loft([(34+31*t,221,29.5*math.sqrt(max(1e-3,1-((34+31*t-44)/21)**2)),14*math.sqrt(max(1e-3,1-((34+31*t-44)/21)**2))) for t in [0,.2,.4,.6,.8,.97]])
beak=beak.cut(box(-100,100,-100,100,219,400)).cut(box(-100,48,-18,16,214.5,400)) # lower the top under the jaw servo so its pocket never touches the loft
beak=beak.union(box(33.5,41.5,14,17,212,234)).union(box(33.5,41.5,-22,-19,212,230)) # arms start 3.5 mm behind the pivot so a 20-degree opening clears the servo # arms: left on the horn, right 1.5 mm outside the idler clearance
beak=beak.union(horn(jaw,width=18,length=20,thickness=3)) # the servo body lives in the head frame; the plate sits outside the horn disc
beak=beak.cut(cyl((37,-18.5,226),'Y',1.3,6)).cut(cyl((8.9,0,200),'Z',24,16)) # right pin; keep clear of the neck stack when yawing
add('jaw_beak',beak,CREAM,'jaw','-Z','Lower beak: solid rounded scoop with a left arm bolted to the jaw servo horn and a right pin pivot; rear trimmed to clear the neck stack when the head yaws.',group='shell')
buy('camera_module_3',box(49.5,50.6,-12.5,12.5,224,248),GRAPHITE,'head',4,'Raspberry Pi Camera Module 3 Standard class, 25 x 24 mm board','camera')

# ---------------------------------------------------------------- assembly, GLB rig, report
print('assembly')
assembly=cq.Assembly(name='Micro_X_RevA')
for p in parts+purchased:assembly.add(p['shape'],name=p['name'],color=cq.Color(*p['color']))
assembly.export(str(R/'models/micro_x.step'))
scene=trimesh.Scene()
pivots={b:(L.JOINT_OF_BODY[b]['P'] if b in L.JOINT_OF_BODY else L.TRUNK) for b in L.BODIES}
for b in L.BODIES:
    parent=L.PARENT[b];Pb=pivots[b];Pp=pivots[parent] if parent else np.zeros(3)
    T=np.eye(4);T[:3,3]=(Pb-Pp)*.001
    scene.graph.update(frame_to=b,frame_from=parent or 'world',matrix=T)
for p in parts+purchased:
    mesh=trimesh.graph.smooth_shade(p['mesh'],angle=math.radians(35));mesh=paint(mesh,p['name'],p['color'])
    mesh.vertices=(mesh.vertices-pivots[p['body']])*.001
    scene.add_geometry(mesh,node_name='mesh_'+p['name'],geom_name=p['name'],parent_node_name=p['body'])
scene.export(R/'models/micro_x.glb',include_normals=True)
report=dict(revision='RevA actuated chibi',parts=[{k:v for k,v in p.items() if k not in ['shape','mesh']} for p in parts],purchased=[{k:v for k,v in p.items() if k not in ['shape','mesh']} for p in purchased],
    bodies=[dict(name=b,parent=L.PARENT[b],pivot_mm=np.round(pivots[b],3).tolist(),joint=(L.JOINT_OF_BODY[b]['name'] if b in L.JOINT_OF_BODY else None),axis=(np.round(L.JOINT_OF_BODY[b]['axis'],6).tolist() if b in L.JOINT_OF_BODY else None)) for b in L.BODIES],
    printed_mass_g=round(sum(p['mass_g'] for p in parts),1),purchased_mass_g=round(sum(p['mass_g'] for p in purchased),1))
(R/'artifacts/parts.json').write_text(json.dumps(report,indent=2)+'\n')
print('Built',len(parts),'printed parts',report['printed_mass_g'],'g +',len(purchased),'purchased items',report['purchased_mass_g'],'g')
