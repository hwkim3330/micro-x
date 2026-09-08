"""Independent Micro X appearance/assembly prototype. All dimensions in mm.
No upstream robot geometry or kinematics are read by this generator.
NOT an actuated or production-validated robot.
"""
from pathlib import Path
import json, math
import cadquery as cq
import numpy as np
import trimesh
R=Path(__file__).resolve().parents[1]
for folder in ['models/step','models/print','artifacts']: (R/folder).mkdir(parents=True,exist_ok=True)
parts=[]
JADE=[.18,.40,.29,1];GOLD=[.96,.62,.21,1];CREAM=[.87,.86,.68,1];BLACK=[.04,.065,.055,1]
def box(x,y,z,p):return cq.Workplane('XY').box(x,y,z).translate(p)
def loft(sections):
    wires=[cq.Workplane('YZ',origin=(x,0,z)).ellipse(w,h).val() for x,z,w,h in sections]
    return cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=True))
def bore(x,y,z,r,length,axis='Z'):
    plane={'Z':'XY','Y':'XZ','X':'YZ'}[axis]
    return cq.Workplane(plane,origin=(x,y,z)).circle(r).extrude(length)
def add(name,shape,color,group,print_axis='Z',note=''):
    shape=shape.clean();solids=shape.solids().vals()
    if len(solids)!=1 or not shape.val().isValid():raise ValueError(f'{name}: {len(solids)} solids or invalid')
    path=R/'models/step'/f'{name}.step';cq.exporters.export(shape,str(path))
    stl=R/'models'/f'{name}.stl';cq.exporters.export(shape,str(stl),tolerance=.04,angularTolerance=.08)
    mesh=trimesh.load_mesh(stl,process=True)
    mesh.merge_vertices(digits_vertex=7)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    mesh.export(stl)
    if not mesh.is_watertight or mesh.volume<=0:raise ValueError(name+' mesh invalid')
    printable=mesh.copy()
    if print_axis=='Y':printable.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
    if print_axis=='X':printable.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
    printable.vertices-=np.r_[printable.bounds.mean(axis=0)[:2],printable.bounds[0,2]]
    printable.export(R/'models/print'/f'{name}.stl')
    parts.append(dict(name=name,shape=shape,mesh=mesh,color=color,group=group,note=note,dimensions_mm=np.round(mesh.extents,2).tolist(),volume_mm3=round(shape.val().Volume(),2),mass_g=round(shape.val().Volume()*.00124,2),step=f'models/step/{name}.step',stl=f'models/print/{name}.stl'))
# Rear entry neck stays behind the jaw; six translated copies reserve 0.3 mm axial clearance.
neck=loft([(32,193,10,10),(43,210,12,15),(52,223,8,11)])
neck_keep=neck
for shift in [(0.3,0,0),(-0.3,0,0),(0,.3,0),(0,-.3,0),(0,0,.3),(0,0,-.3)]:neck_keep=neck_keep.union(neck.translate(shift))
# Torso: original elliptical loft, 2.4 mm radial allowance, horizontal service split.
sections=[(-58,153,16,18),(-32,163,41,40),(15,174,40,39),(53,185,18,23)]
outer=loft(sections)
inner=loft([(x,z,w-2.4,h-2.4) for x,z,w,h in sections])
shell=outer.cut(inner)
# Close aft and fore loft ends with independent disks (overlapping 1 mm into wall).
for x,z,w,h in [sections[0],sections[-1]]:
    cap=cq.Workplane('YZ',origin=(x,0,z)).ellipse(w,h).extrude(2.4 if x<0 else -2.4)
    shell=shell.union(cap)
for y in [-8,8]:
    shell=shell.union(bore(-58,y,153,4,10,'X')).cut(bore(-59,y,153,1.3,12,'X'))
# Forearm bearing posts meet the existing arm inner faces, shared seam at z180.
for sign in [-1,1]:
    start=34 if sign==1 else -24
    shell=shell.union(bore(36,start,181,5,10,'Y')).cut(bore(36,start+1,181,1.7,12,'Y'))
# Four tubular fastening columns bridge the seam, M3 clearance through roof and pilot below.
mounts=[(-25,-22),(-25,22),(15,-22),(15,22)]
for x,y in mounts:
    column=bore(x,y,136,4.5,68).intersect(outer)
    shell=shell.union(column)
# Vent slots on dorsal surface and cable opening at front.
for x in [-12,-4,4]:shell=shell.cut(box(2.5,20,18,(x,0,207)))
shell=shell.cut(bore(51,0,188,4,8,'X'))
lower=shell.intersect(box(500,500,300,(0,0,30))) # top z180
upper=shell.intersect(box(500,500,300,(0,0,330))).cut(neck_keep) # bottom z180
for x,y in mounts:
    lower=lower.cut(bore(x,y,167,1.3,14))
    upper=upper.cut(bore(x,y,179,1.7,40))
# Fixed assembly leg interfaces: M3 lateral holes and bosses. Prototype leg pose is fixed.
for sign in [-1,1]:
    pad=bore(-14,sign*39+5,143,7,10,'Y')
    lower=lower.union(pad).cut(bore(-14,sign*39+8,143,1.7,16,'Y'))
add('torso_lower',lower,JADE,'torso',note='4 × M3 pilot Ø2.6 at (-25/15, ±22), z167–180. Verify self-tapping screw fit in coupon.')
add('torso_upper',upper,JADE,'torso',note='4 × Ø3.4 clearance. Roof access; remove four M3 screws for servicing.')
# Thick dinosaur hind limbs, original angular profile with rounded vertices from 2D offset.
leg_profile=[(-24,149),(0,152),(25,126),(31,108),(12,73),(14,37),(37,22),(32,12),(-3,13),(-17,34),(-9,80),(-36,112)]
for sign,side in [(1,'left'),(-1,'right')]:
    y=sign*53+9
    leg=cq.Workplane('XZ',origin=(0,y,0)).polyline(leg_profile).close().extrude(18).edges('|Y').fillet(2)
    for x,z in [(-14,143),(8,27)]:leg=leg.cut(bore(x,y+1,z,1.7,20,'Y'))
    pocket=cq.Workplane('XZ',origin=(0,y+.1,0)).polyline(leg_profile).close().offset2D(-3).extrude(14.1)
    for x,z in [(-14,143),(8,27)]:pocket=pocket.cut(bore(x,y+1,z,6,20,'Y'))
    leg=leg.cut(pocket)
    add('hindleg_'+side,leg,JADE,'legs','Y','Fixed display leg; lateral M3 through bolts. No motor/locomotion claim.')
    foot=box(73,42,12,(18,sign*53,10)).edges('|Z').fillet(6)
    foot=foot.cut(box(53,27,7,(18,sign*53,6.5)))
    # Integral ankle lug mates around the leg with M3 axis.
    for dy in [-12,12]:
        lug=box(15,5,20,(8,sign*53+dy,20))
        foot=foot.union(lug)
    foot=foot.cut(bore(8,sign*53+20,27,1.7,40,'Y'))
    for yy in [-10,0,10]:
        toe=loft([(46,10,4,5),(62,8,2,2)]).translate((0,sign*53+yy,0));foot=foot.union(toe)
    foot=foot.cut(box(55,18.6,20,(8,sign*53,22)))
    add('foot_'+side,foot,GOLD,'legs',note='M3 ankle bolt, three integral rounded toes. Support under lug overhangs.')
# Neck fixed mounting cradle and ball-like visual transition, bolted to front service aperture.
neck=neck.cut(bore(39,0,185,1.7,18,'X'))
add('neck_cradle',neck,CREAM,'neck',note='Appearance bridge; head actuation cartridge not yet integrated.')
# Hollow snout: pronounced broad rear skull, tapered nose, open lower face for service.
head_sections=[(45,227,22,21),(65,237,35,30),(115,233,29,23),(157,223,19,13)]
head_outer=loft(head_sections)
head_inner=loft([(x,z,w-2.2,h-2.2) for x,z,w,h in head_sections])
head=head_outer.cut(head_inner).intersect(box(500,500,200,(0,0,309.5))) # open at z210
for x,z,w,h in [head_sections[0],head_sections[-1]]:
    cap=cq.Workplane('YZ',origin=(x,0,z)).ellipse(w,h).extrude(2.2 if x<100 else -2.2)
    head=head.union(cap.intersect(box(500,500,200,(0,0,309.5))))
# Jaw pivot ears integrate into upper shell.
for sign in [-1,1]:
    ear=bore(59,sign*25+4,212,6,8,'Y')
    head=head.union(ear).cut(bore(59,sign*25+6,212,1.7,12,'Y'))
# Independent stylized recessed eye plugs; sockets are subtraction of same generated tool.
for sign,side in [(1,'left'),(-1,'right')]:
    eye=cq.Workplane('XY').sphere(10).translate((72,sign*31,243))
    head=head.cut(eye)
    # Smaller sphere leaves 0.2 radial adhesive allowance in the shell socket.
    inset=cq.Workplane('XY').sphere(9.8).translate((72,sign*31,243))
    add('eye_'+side,inset,GOLD,'head',note='Adhesive-fit eye insert, 0.2 mm nominal radial allowance; captive retention pending.')
# Two nostrils on nose, camera functionality deliberately not implied.
for sign in [-1,1]:head=head.cut(bore(148,sign*20,228,2.3,12,'Y'))
head=head.cut(neck_keep)
add('skull',head,JADE,'head',note='Open underside hollow skull, Ø3.4 jaw hinge holes. Electronics mount pending.')
# Lower jaw has integral cheek ears and broad rounded chin; teeth are integral blunt bumps.
jaw=loft([(57,203,35,3),(105,201,28,4),(157,207,18,3)])
for sign in [-1,1]:
    ear=bore(59,sign*31+2,212,6,4,'Y')
    connector=box(14,4,10,(60,sign*31,206))
    jaw=jaw.union(ear).union(connector).cut(bore(59,sign*31+4,212,1.7,8,'Y'))
    for x,y,z in [(92,24,205),(112,24,206),(132,21,208)]:
        tooth=cq.Workplane('XY').sphere(3).translate((x,sign*y,z));jaw=jaw.union(tooth)
add('jaw',jaw,CREAM,'jaw',note='Two M3 hinge bolts. Manual pose prototype; powered linkage and pinch protection pending.')
# Lightweight tapered tail, split longitudinally into two printable shells with locating pins.
tail_sections=[(-205,130,2.8,3),(-160,132,7,8),(-108,143,13,15),(-58,153,17,18)]
to=loft(tail_sections)
ti=loft([(x,z,max(1,w-2),max(1,h-2)) for x,z,w,h in tail_sections])
ti=ti.intersect(box(142,100,100,(-132,0,145))) # cavity stops at -203 and -60; integral end walls
tail=to.cut(ti)
for x,z,w in [(-100,145,14),(-155,133,8)]:
    cross=bore(x,w,z,4,w*2,'Y').intersect(to)
    tail=tail.union(cross).cut(bore(x,w+1,z,1.7,w*2+2,'Y'))
for y in [-8,8]:tail=tail.cut(bore(-63,y,153,1.7,7,'X'))
for sign,side in [(1,'left'),(-1,'right')]:
    half=tail.intersect(box(400,100,400,(-100,sign*50,150)))
    add('tail_'+side,half,JADE,'tail','Y','M3 seam bolts at X -100/-155, Z145/133; two axial M3 mount holes at Y ±8, Z153. Physical fit unverified.')
# Small two-finger forearms, visually separate from the load-bearing hind limbs.
for sign,side in [(1,'left'),(-1,'right')]:
    profile=[(31,184),(40,187),(58,173),(63,173),(68,168),(64,165),(56,169),(54,163),(49,164),(42,176),(32,176)]
    arm=cq.Workplane('XZ',origin=(0,sign*37+3,0)).polyline(profile).close().extrude(6)
    arm=arm.cut(bore(36,sign*37+4,181,1.7,8,'Y'))
    add('forearm_'+side,arm,JADE,'arms','Y','Manual M3 pivot mating torso bearing posts at X36 Z181. Actuator and motion stops not integrated.')
assembly=cq.Assembly(name='Micro_X_P0')
scene=trimesh.Scene()
report=[]
for p in parts:
    assembly.add(p['shape'],name=p['name'],color=cq.Color(*p['color']))
    mesh=p['mesh'].copy();mesh.vertices*=.001;mesh.visual.vertex_colors=(np.array(p['color'])*255).astype(np.uint8)
    scene.add_geometry(mesh,node_name=p['name'])
    report.append({k:v for k,v in p.items() if k not in ['shape','mesh','color']})
assembly.export(str(R/'models/micro_x.step'));scene.export(R/'models/micro_x.glb')
(R/'artifacts/parts.json').write_text(json.dumps(report,indent=2)+'\n')
print('Built',len(parts),'independent parts; solid PLA-equivalent mass',round(sum(p['mass_g'] for p in parts),1),'g')
