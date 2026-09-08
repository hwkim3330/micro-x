"""Micro X Q4 packaging prototype, sharing only Micro X original parts.
Fixed leg geometry demonstrates packaging, not a released actuated chassis.
"""
from pathlib import Path
import json,hashlib,itertools
import cadquery as cq
import trimesh,numpy as np
R=Path(__file__).resolve().parents[1];out=R/'models/q4';out.mkdir(exist_ok=True)
for p in ['step','print']:(out/p).mkdir(exist_ok=True)
base=json.loads((R/'artifacts/parts.json').read_text());assembly=cq.Assembly(name='Micro_X_Q4');scene=trimesh.Scene();parts=[];shapes={}
colors={'torso':[.18,.4,.29,1],'head':[.18,.4,.29,1],'neck':[.87,.86,.68,1],'jaw':[.87,.86,.68,1],'tail':[.18,.4,.29,1],'legs':[.18,.4,.29,1],'frame':[.1,.15,.12,1]}
def add(name,shape,group,source=None,offset=(0,0,0),axis='Z',note=''):
 shape=shape.clean();assert shape.val().isValid() and len(shape.solids().vals())==1,name
 cq.exporters.export(shape,str(out/'step'/f'{name}.step'));cq.exporters.export(shape,str(out/f'{name}.stl'),tolerance=.04,angularTolerance=.08)
 m=trimesh.load_mesh(out/f'{name}.stl');m.merge_vertices(digits_vertex=7);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();assert m.is_watertight and m.volume>0,name
 m.export(out/f'{name}.stl')
 color=colors[group];
 if name.startswith('eye_') or 'foot_' in name:color=[.96,.62,.21,1]
 visual=m.copy();visual.vertices*=.001;visual.visual.vertex_colors=(np.array(color)*255).astype(np.uint8);scene.add_geometry(visual,node_name=name)
 printed=m.copy()
 if axis=='Y':printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
 printed.vertices-=np.r_[printed.bounds.mean(0)[:2],printed.bounds[0,2]];printed.export(out/'print'/f'{name}.stl')
 assembly.add(shape,name=name,color=cq.Color(*color));shapes[name]=shape
 parts.append(dict(name=name,group=group,dimensions_mm=np.round(m.extents,2).tolist(),mass_g=round(shape.val().Volume()*.00124,2),volume_mm3=round(shape.val().Volume(),2),source_part=source,assembly_offset_mm=list(offset),step=f'models/q4/step/{name}.step',stl=f'models/q4/print/{name}.stl',note=note))
# Nine common upper-body parts; small cosmetic forearms are replaced by front load-bearing legs.
for p in base:
 if p['group'] in ['legs','arms']:continue
 shape=cq.importers.importStep(str(R/p['step']));add(p['name'],shape,p['group'],p['name'],note='Shared Micro X P0 geometry; drive integration not complete.')
# Four instances of the same left/right leg and foot modules, 110 mm fore/aft hip spacing.
for row,dx in [('front',64),('rear',-46)]:
 for side in ['left','right']:
  dy=6 if side=='left' else -6
  for stem in ['hindleg','foot']:
   p=next(p for p in base if p['name']==f'{stem}_{side}');shape=cq.importers.importStep(str(R/p['step'])).translate((dx,dy,0))
   add(f'{row}_{stem}_{side}',shape,'legs',p['name'],(dx,dy,0),'Y' if stem=='hindleg' else 'Z','Repeated fixed leg/foot for packaging; powered leg cartridge not yet integrated.')
# Two hollowed side rails connect front/rear pivots to the existing original torso axis.
# Rails sit outside torso bosses and inside leg cheeks; see docs/PLATFORMS.md for gaps.
for sign,side in [(1,'left'),(-1,'right')]:
 y=sign*47.2
 rail=cq.Workplane('XY').box(128,5.4,16).translate((-5,y,143)).edges('|Y').fillet(3)
 for x in [-60,-14,50]:
  hole=cq.Workplane('XZ',origin=(x,y+4,143)).circle(1.7).extrude(8);rail=rail.cut(hole)
 # Open slots remove material between the three bearing lands.
 for x,width in [(-39,28),(19,43)]:
  slot=cq.Workplane('XZ',origin=(x,y+4,143)).slot2D(width,7,0).extrude(8);rail=rail.cut(slot)
 add('side_rail_'+side,rail,'frame',axis='Y',note='M3 axes X=-60/-14/50 Z143. Pilot packaging rail; anti-rotation and joint bearing stack unresolved.')
assembly.export(str(out/'micro_x_q4.step'));scene.export(out/'micro_x_q4.glb')
report=[]
for a,b in itertools.combinations(shapes,2):
 A=shapes[a].val().BoundingBox();B=shapes[b].val().BoundingBox()
 if any(getattr(A,k+'max')<=getattr(B,k+'min')+1e-5 or getattr(B,k+'max')<=getattr(A,k+'min')+1e-5 for k in 'xyz'):continue
 vol=sum(s.Volume() for s in shapes[a].intersect(shapes[b]).solids().vals())
 if vol>.01:report.append(dict(parts=[a,b],overlap_mm3=round(vol,3)))
(R/'artifacts/q4_parts.json').write_text(json.dumps(parts,indent=2)+'\n')
(R/'artifacts/q4_validation.json').write_text(json.dumps(dict(parts=len(parts),unique_common_designs=len(set(p['source_part'] for p in parts if p['source_part'])),new_designs=2,reference_overlaps=report,walking_validated=False,production_release=False,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_step_sha256={p['name']:hashlib.sha256((R/p['step']).read_bytes()).hexdigest() for p in base if p['group']!='arms'},step_sha256={p['name']:hashlib.sha256((R/p['step']).read_bytes()).hexdigest() for p in parts}),indent=2)+'\n')
print(f'Q4: {len(parts)} part instances; {len(report)} reference intersections',report)
