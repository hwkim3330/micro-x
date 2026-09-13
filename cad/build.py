"""Micro X Rev B: actuated chibi T-rex, built in the straight-leg design pose.

World frame: X forward, Y left, Z up, mm. Joint pivots, axes and servo placements come
from engineering/functional_layout.json (measured functional dimensions); every part
around them is original. Each servo is held by a U-channel in one link and drives a
single horn plate on the next, the way the reference robot does it - no clevis
sandwiches - so every part is a thin prismatic shell that prints flat without support.
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
MINT=[.62,.82,.72,1];CREAM=[.98,.94,.79,1];GRAPHITE=[.22,.25,.26,1];DARK=[.12,.14,.15,1]
DENSITY=0.00124 # g/mm3 PLA solid-equivalent; slicer mass with infill is lower
WALL=2.4
parts=[];purchased=[]

def box(x0,x1,y0,y1,z0,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
def rbox(x0,x1,y0,y1,z0,z1,r):return box(x0,x1,y0,y1,z0,z1).edges().fillet(min(r,(x1-x0)/2-.01,(y1-y0)/2-.01,(z1-z0)/2-.01))
def vbox(x0,x1,y0,y1,z0,z1,r):return box(x0,x1,y0,y1,z0,z1).edges('|Z').fillet(min(r,(x1-x0)/2-.01,(y1-y0)/2-.01)) # flat top and bottom: prints on its face
def ell(c,h):return cq.Workplane(obj=cq.Workplane('XY').sphere(1).val().transformGeometry(cq.Matrix([[h[0],0,0,c[0]],[0,h[1],0,c[1]],[0,0,h[2],c[2]]])))
def cyl(p,axis,r,length):return cq.Workplane({'Z':'XY','Y':'XZ','X':'YZ'}[axis],origin=tuple(p)).circle(r).extrude(length)
def keep_solid(shape,name):
    shape=shape.clean();solids=shape.solids().vals()
    if len(solids)!=1:
        big=max(solids,key=lambda s:s.Volume());small=sum(s.Volume() for s in solids)-big.Volume()
        if small>200:raise ValueError(f'{name}: {len(solids)} solids, {small:.1f} mm3 loose')
        for sl in solids:
            if sl is not big:bb=sl.BoundingBox();print(f'  WARNING {name}: dropped {sl.Volume():.1f} mm3 sliver at x {bb.xmin:.1f}..{bb.xmax:.1f} y {bb.ymin:.1f}..{bb.ymax:.1f} z {bb.zmin:.1f}..{bb.zmax:.1f}')
        shape=cq.Workplane(obj=big)
    if not shape.val().isValid():raise ValueError(name+' invalid solid')
    return shape
ROT={'Z':None,'-Z':(math.pi,[1,0,0]),'Y':(math.pi/2,[1,0,0]),'-Y':(-math.pi/2,[1,0,0]),'X':(math.pi/2,[0,1,0]),'-X':(-math.pi/2,[0,1,0])}
def add(name,shape,color,body,print_axis='Z',note='',group='frame'):
    shape=keep_solid(shape,name)
    path=R/'models/step'/f'{name}.step';cq.exporters.export(shape,str(path))
    restored=cq.importers.importStep(str(path))
    if len(restored.solids().vals())!=1 or not restored.val().isValid():raise ValueError(name+' STEP round trip lost valid solid')
    stl=R/'models'/f'{name}.stl';cq.exporters.export(shape,str(stl),tolerance=.05,angularTolerance=.1)
    mesh=trimesh.load_mesh(stl,process=True);mesh.merge_vertices(digits_vertex=6);mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight:
        cq.exporters.export(shape,str(stl),tolerance=.1,angularTolerance=.2);mesh=trimesh.load_mesh(stl,process=True);mesh.merge_vertices(digits_vertex=5);print('  retessellated',name)
    mesh.export(stl)
    if not mesh.is_watertight or mesh.volume<=0:raise ValueError(name+' mesh invalid')
    printable=mesh.copy()
    if ROT[print_axis]:printable.apply_transform(trimesh.transformations.rotation_matrix(*ROT[print_axis]))
    printable.vertices-=np.r_[printable.bounds.mean(axis=0)[:2],printable.bounds[0,2]];printable.export(R/'models/print'/f'{name}.stl')
    vol=shape.val().Volume()
    parts.append(dict(name=name,shape=shape,mesh=mesh,color=color,body=body,group=group,note=note,printed=True,print_axis=print_axis,
        dimensions_mm=np.round(mesh.extents,2).tolist(),volume_mm3=round(vol,1),mass_g=round(vol*DENSITY,2),step=f'models/step/{name}.step',stl=f'models/print/{name}.stl'))
    print(f'  {name:22s} {vol*DENSITY:7.1f} g')
    return shape
def buy(name,shape,color,body,mass_g,note,kind):
    shape=keep_solid(shape,name)
    stl=R/'models/purchased'/f'{name}.stl';cq.exporters.export(shape,str(stl),tolerance=.08,angularTolerance=.15)
    mesh=trimesh.load_mesh(stl,process=True);mesh.export(stl)
    purchased.append(dict(name=name,shape=shape,mesh=mesh,color=color,body=body,kind=kind,mass_g=mass_g,note=note,printed=False,
        dimensions_mm=np.round(mesh.extents,2).tolist(),stl=f'models/purchased/{name}.stl'))

for s in L.SERVOS:
    buy('servo_'+s['name'],S.envelope(s['P'],s['h'],s['d']),DARK,s['body'],S.MASS_G,'XL330-class smart servo envelope; confirm the case hole pattern before ordering','actuator')
def horn(name,**kw):s=L.get(name);return S.horn_plate(s['P'],s['h'],s['d'],**kw)
def chan(name,**kw):s=L.get(name);return S.channel(s['P'],s['h'],s['d'],**kw)
def pock(name,**kw):s=L.get(name);return S.pocket(s['P'],s['h'],s['d'],**kw)

# ---------------------------------------------------------------- legs
def build_leg(side):
    g=1 if side=='left' else -1
    def sb(x0,x1,y0,y1,z0,z1,r=None):
        a,b=(g*y0,g*y1) if g>0 else (g*y1,g*y0)
        return rbox(x0,x1,a,b,z0,z1,r) if r else box(x0,x1,a,b,z0,z1)
    n=lambda j:f'{side}_{j}'
    # Hip yaw horn plate over a U-channel that holds the hip roll servo. Prints on the plate face.
    yr=horn(n('hip_yaw'),width=26,length=30).union(chan(n('hip_roll'),faces=('y+','y-','far','back')))
    yr=yr.union(sb(-9.4,-7,4.7,30.3,75.2,114.8)) # close the idler side into one shell
    add(n('yaw2roll'),yr,GRAPHITE,n('yaw2roll'),'-Z','Hip yaw horn plate on a U-channel around the hip roll servo. Print on the plate face; every wall is vertical.')
    # Hip bracket: roll horn plate, pitch horn plate, one corner rib. Two thin plates, no enclosure.
    hp=horn(n('hip_roll'),width=26,length=30).union(sb(22.5,25.5,4.5,41.5,89.5,115.5))
    hp=hp.union(horn(n('hip_pitch'),width=26,length=22)).union(sb(-7,25.5,39.5,42.5,89.5,115.5))
    hp=hp.cut(box(-60,60,-60,60,114.5,200)) # stay under the chassis floor through the full roll sweep
    add(n('hip'),hp,GRAPHITE,n('hip'),'-Y' if g>0 else 'Y','Hip corner bracket: roll horn plate and pitch horn plate joined by one rib. Print on the pitch plate face.')
    # Upper leg: open-sided shell holding the hip pitch and knee servos side by side.
    ul=sb(-44.3,16,42.9,74.8,68.5,115).cut(sb(-42.2,13.9,42.5,72.4,70.6,112.9))
    ul=ul.cut(sb(-60,60,40,80,0,71.5)) # open bottom so the shin can fold up
    add(n('upper_leg'),ul,MINT,n('upper_leg'),'Y' if g>0 else '-Y','Thigh shell around the hip pitch and knee servos, open on the inboard face. Print on the outboard face; the cavity opens upward, no support.',group='shell')
    # Lower leg: knee horn plate over an inboard plate and a channel around the ankle servo.
    ll=horn(n('knee'),width=22,length=26).union(chan(n('ankle'),faces=('y+','y-','back')).cut(sb(-60,60,46,90,0,300)))
    ll=ll.union(sb(-42.8,-20.8,32.2,38.5,63.4,69))
    ll=ll.cut(sb(-60,60,0,100,0,31)) # leave the sole room to tilt
    add(n('lower_leg'),ll,MINT,n('lower_leg'),'Y' if g>0 else '-Y','Shin: knee horn plate stepping down into a channel around the ankle servo. Print on the inboard face.',group='shell')
    # Foot: ankle horn plate on a rounded hollow sole with a gusset.
    sole=vbox(-52,2,g*29 if g>0 else -71,g*71 if g>0 else -29,13.5,24,8)
    ft=horn(n('ankle'),width=20,length=26).union(sole)
    ft=ft.cut(vbox(-47,-3,g*33.5 if g>0 else -66.5,g*66.5 if g>0 else -33.5,10,21.5,5)) # hollow underside for a TPU pad
    ft=ft.union(sb(-41.8,-21.8,64.5,67.5,22,40)) # the horn plate simply continues down to the sole
    add(n('foot'),ft,CREAM,n('foot'),'Z','Foot: ankle horn plate on a wide rounded sole, hollow underneath for a replaceable pad. Print sole down.',group='shell')
for side in ['left','right']:
    print(side,'leg');build_leg(side)

# ---------------------------------------------------------------- trunk
print('trunk')
boxes=None
for g in (1,-1):
    j=('left' if g>0 else 'right')+'_hip_yaw'
    c=chan(j,faces=('y+','y-','far','near','back'))
    boxes=c if boxes is None else boxes.union(c)
boxes=boxes.cut(box(10.2,60,-40,40,100,200)) # stay behind the neck tube and its pitch sweep
chassis=cq.Workplane('XY',origin=(-6,0,118)).ellipse(40,31).extrude(3).union(boxes)
for g in (1,-1):chassis=chassis.cut(box(-18.9,15.9,g*6.9 if g>0 else -28.1,g*28.1 if g>0 else -6.9,116,122)) # servos drop through the floor
# Flat electronics deck above the hip servo boxes, clear of the neck plate.
chassis=chassis.union(box(-27,5.5,-26.5,26.5,147,149.5).cut(box(-24,2.5,-23.5,23.5,146,150.5))) # electronics deck
for x in [-24,2.5]:
    for y in [-23.5,23.5]:chassis=chassis.cut(cyl((x,y,146),'Z',1.15,6))
neck_plate=box(6,39,14.5,17.5,145.3,167.4)
for a in range(4):
    t=a*math.pi/2;neck_plate=neck_plate.cut(cyl((26+6*math.cos(t),18,152.4+6*math.sin(t)),'Y',1.15,-6))
neck_plate=neck_plate.cut(cyl((26,18,152.4),'Y',4.2,-6))
chassis=chassis.union(neck_plate)
tray=box(-92,-25,-14,14,118,120).union(box(-92,-25,-20.9,-18.9,120,136)).union(box(-92,-25,18.9,20.9,120,136)).union(box(-92,-89.6,-20.9,20.9,120,136))
chassis=chassis.cut(box(-50,-20.5,-20,20,117,121.5)) # battery corridor through the floor
chassis=chassis.union(tray).cut(cyl((-55,25,128),'Y',1.3,-50))
add('chassis',chassis,GRAPHITE,'trunk','Z','Chassis: floor with two hip-yaw servo boxes, neck horn plate, battery tray and compute board wall. Print floor down; the servo boxes bridge 21 mm.')
buy('battery_pack',rbox(-89,-24,-18.5,18.5,120,139,2),DARK,'trunk',95,'Removable 2S 18650 pack, 65 x 37 x 19 mm class, 7.4 V ~3000 mAh; slides out with the tail cover','battery')
buy('compute_board',box(-23,4,-25,25,149.6,151.2),[.1,.35,.25,1],'trunk',30,'Single-board computer up to 50 x 27 mm on the trunk deck above the hip servos; a larger module needs the reserved head bay','electronics')

# Dome over a straight elliptical tube: the tube keeps full width down at the hip servos,
# which an ellipsoid cannot, and it prints as a clean vertical wall.
tube=lambda a,b,z0:cq.Workplane('XY',origin=(-6,0,z0)).ellipse(a,b).extrude(142-z0)
shell=ell((-6,0,142),(44,37.6,24)).union(tube(43.8,37.5,121))
shell=shell.cut(ell((-6,0,142),(44-WALL,37.6-WALL,24-WALL)).union(tube(43.8-WALL,37.5-WALL,114)))
shell=shell.cut(box(-100,-38,-27,27,100,152)) # tail / battery opening
shell=shell.cut(box(-28,44,-24,24,134,200)) # neck slot, wide enough for the pitch sweep
for z in range(126,148,6):shell=shell.cut(box(28,60,-9,9,z,z+2.5)) # chest grille
for x in [-26,20]:shell=shell.cut(cyl((x,40,132),'Y',1.7,-80))
for x,rch in [(-26,33.5),(20,34.5)]:
    for g in (1,-1):chassis=chassis.union(box(x-2,x+2,min(g*22,g*rch),max(g*22,g*rch),128,136))
add('torso_shell',shell,MINT,'trunk','Z','One-piece egg shell with a chest grille, neck slot and tail opening, open under the hips. Four M3 through the flanks into chassis bosses.',group='shell')
def loft(sections):
    wires=[cq.Workplane('YZ',origin=(x,0,z)).ellipse(w,h).val() for x,z,w,h in sections]
    return cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=False))
# Tapered tail: elliptical loft (plane-cut ellipsoids tessellate badly at the seam).
TAIL=[(-40,129,32,21),(-72,129,31,20),(-92,129,29,18),(-112,132,15,10),(-132,136,4,3.2)]
tail=loft(TAIL).cut(loft([(x,z,w-WALL,h-WALL) for x,z,w,h in TAIL[:-1]]+[(TAIL[-1][0]-2,TAIL[-1][1],.8,.7)]))
tail=tail.cut(cyl((-55,25,128),'Y',1.7,-50)).cut(box(-40,0,-40,40,100,160))
add('tail_cover',tail,MINT,'trunk','-X','Tail doubles as the battery cover: slides over the tray and takes two M3 into it.',group='shell')

# ---------------------------------------------------------------- neck and head
print('neck and head')
neck=box(13.6,38.4,-17.4,14,140.5,212.2).cut(box(15.6,36.4,-15.4,20,142.5,212.3)) # open top: the head base sweeps just above it
neck=neck.cut(box(13,16,-20,20,100,145)) # the hip yaw servos pass within 0.5 mm here
add('neck_link',neck,GRAPHITE,'neck','-Y','Neck tube around the stacked neck-pitch and head-pitch servos, open on the horn side. Print on the closed face.')
sleeve=rbox(10.5,41.5,-20.5,16.9,148,216,9).cut(rbox(12.9,39.1,-18.1,19,146,218,2)) # rounded cover over the neck column
sleeve=sleeve.cut(box(9,44,14.5,24,146,218)).cut(box(9,44,-24,24,146,150)).cut(box(9,44,-24,24,212,218))
add('neck_sleeve',sleeve,MINT,'neck','-Y','Neck cover: rounded shell over the neck column, open on the horn side; pitches with the neck.',group='shell')
head_base=box(20,39,14.5,17.5,196,221.1).union(horn('head_yaw',width=26,length=35))
add('head_base',head_base,GRAPHITE,'head_base','-Z','Head base: head-pitch horn plate joined to the head-yaw horn plate. The only part that stays still while the head yaws.')
yoke=chan('head_yaw',faces=('y+','y-','far','back')).union(horn('head_roll',width=16,length=20))
for g in (1,-1):yoke=yoke.union(box(8.1,15.6,min(g*5,g*8),max(g*5,g*8),225.6,245.6))
add('head_yoke',yoke,GRAPHITE,'head_yoke','-Z','Yoke: box around the head-yaw servo with two ribs out to the head-roll horn plate.')

# Head frame: one shell. A deck above the yoke and the head-roll servo carries the rear
# wall, the servo bays, a forward beam and the camera wall, so it is a single print.
DECK=(261.0,263.4)
frame=box(-18,55,-16,16,*DECK)
for g in (1,-1):frame=frame.union(box(-24.2,7.6,min(g*10.4,g*12.8),max(g*10.4,g*12.8),225.8,262))  # head roll servo walls
frame=frame.union(box(-24.2,-21.8,-12.8,12.8,225.8,262))                              # rear wall
frame=frame.union(box(0,36.5,19.1,21.1,231.6,262)).union(box(0,30,44.9,46.9,244,252))    # jaw servo hanger
frame=frame.union(box(0,36.5,14,34,DECK[0],DECK[1]))                                    # deck reaches out over the jaw bay
frame=frame.union(box(0,30,21.1,46.9,248,250.4))                                         # rib tying the outer hanger wall in
frame=frame.union(box(0,36.5,19.1,34,229.2,231.6))                                      # jaw servo floor
frame=frame.union(box(51,55,-8,8,244,DECK[0])).union(box(39.2,74,-8,8,240,244))         # post and forward beam
frame=frame.union(box(70,74,-14,14,228,246))                                           # camera wall
frame=frame.cut(pock('head_roll')).cut(pock('jaw'))
for y in [-10.5,10.5]:
    for z in [232.85,245.35]:frame=frame.cut(cyl((69,y,z),'X',1.15,6))
frame=frame.cut(cyl((69,0,239),'X',6.5,10))
for x in range(-10,56,14):frame=frame.cut(box(x,x+7,-11,11,DECK[0]-1,DECK[1]+1)) # lighten the deck
BOSSES=[(6,-14,261.5),(6,14,261.5),(46,0,241.0)]
frame=frame.cut(cyl((46,0,250),'Z',5.5,20)) # the skull's front boss passes through the deck
for x,y,z in BOSSES:frame=frame.union(cyl((x,y,z),'Z',4.5,6)).cut(cyl((x,y,z-1),'Z',1.3,10))
add('head_frame',frame,GRAPHITE,'head','-Z','Head frame: one shell with a deck over the yoke, the head-roll and jaw servo bays, a forward beam, the camera wall and three skull bosses.')
buy('camera_module_3',box(74,75.1,-12.5,12.5,227,249),DARK,'head',4,'Raspberry Pi Camera Module 3 Standard class, 25 x 24 mm board','camera')

# Skull: a tapering loft, wide over the servos and narrowing to a snout, so the head reads
# as a T-rex head rather than a dome. Sections are (x, z centre, half width, half height).
SKULL=[(-32,246,36,25),(-8,247,53,31),(18,247,56,32),(42,245,50,29),(64,241,34,22),(80,237,18,13),(88,235,7,5)]
def skull_loft(shrink=0.0):
    return loft([(x,z,w-shrink,h-shrink) for x,z,w,h in SKULL])
skull=skull_loft().cut(skull_loft(2.2))
skull=skull.cut(box(-60,140,-60,60,150,223)) # open underneath for the neck stack
skull=skull.cut(box(-60,50,-60,60,150,229))  # open at the rear and under the neck stack
skull=skull.cut(box(46,68,-60,60,150,236))   # mouth opening; the beak closes it, the snout tip stays solid
skull=skull.union(cyl((82,0,239),'X',9,10)).cut(cyl((70,0,239),'X',6.5,40)) # camera ring / lens hood
for g in (1,-1):skull=skull.cut(cyl((82,g*9,231),'X',1.7,12)) # nostrils
for x,y,z in BOSSES:
    skull=skull.union(cyl((x,y,z+6),'Z',4.5,30).intersect(skull_loft(0.6))).cut(cyl((x,y,z+5),'Z',1.7,34))
add('skull',skull,MINT,'head','Z','Skull: one-piece hollow T-rex head, wide over the servos and tapering to a snout with a camera ring and nostrils. Three M3 down into the head frame; the eyes are painted, not parts.',group='shell')

beak=horn('jaw',width=20,length=18)
scoop=ell((57,0,229),(11,30,11))
beak=beak.union(scoop.cut(ell((57,0,229),(11-WALL,30-WALL,11-WALL))).cut(box(-60,140,-60,60,234,300)))
beak=beak.union(box(30,57,15,18,226,238))
add('jaw_beak',beak,CREAM,'jaw','-Z','Lower beak: rounded scoop on a single arm bolted to the jaw servo horn.',group='shell')

# ---------------------------------------------------------------- assembly, rig, report
print('assembly')
assembly=cq.Assembly(name='Micro_X_RevB')
for p in parts+purchased:assembly.add(p['shape'],name=p['name'],color=cq.Color(*p['color']))
assembly.export(str(R/'models/micro_x.step'))
scene=trimesh.Scene()
pivots={b:(L.JOINT_OF_BODY[b]['P'] if b in L.JOINT_OF_BODY else L.TRUNK_ORIGIN) for b in L.BODIES}
for b in L.BODIES:
    parent=L.PARENT[b];T=np.eye(4);T[:3,3]=(pivots[b]-(pivots[parent] if parent else np.zeros(3)))*.001
    scene.graph.update(frame_to=b,frame_from=parent or 'world',matrix=T)
for p in parts+purchased:
    mesh=trimesh.graph.smooth_shade(p['mesh'],angle=math.radians(35));mesh=paint(mesh,p['name'],p['color'])
    mesh.vertices=(mesh.vertices-pivots[p['body']])*.001
    scene.add_geometry(mesh,node_name='mesh_'+p['name'],geom_name=p['name'],parent_node_name=p['body'])
scene.export(R/'models/micro_x.glb',include_normals=True)
report=dict(revision='RevB design-pose actuated chibi',parts=[{k:v for k,v in p.items() if k not in ['shape','mesh']} for p in parts],
    purchased=[{k:v for k,v in p.items() if k not in ['shape','mesh']} for p in purchased],
    bodies=[dict(name=b,parent=L.PARENT[b],pivot_mm=np.round(pivots[b],3).tolist(),joint=(L.JOINT_OF_BODY[b]['name'] if b in L.JOINT_OF_BODY else None),
                 axis=(np.round(L.JOINT_OF_BODY[b]['axis'],6).tolist() if b in L.JOINT_OF_BODY else None)) for b in L.BODIES],
    printed_mass_g=round(sum(p['mass_g'] for p in parts),1),purchased_mass_g=round(sum(p['mass_g'] for p in purchased),1))
(R/'artifacts/parts.json').write_text(json.dumps(report,indent=2)+'\n')
print('Built',len(parts),'printed parts',report['printed_mass_g'],'g +',len(purchased),'purchased items',report['purchased_mass_g'],'g')
