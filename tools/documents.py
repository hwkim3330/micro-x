from pathlib import Path
import json,csv,argparse
import numpy as np
import trimesh
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['b2','q4'],default='b2');variant=parser.parse_args().variant
R=Path(__file__).resolve().parents[1];quad=variant=='q4';parts=json.loads((R/('artifacts/q4_parts.json' if quad else 'artifacts/parts.json')).read_text())
c=canvas.Canvas(str(R/('artifacts/drawings_q4.pdf' if quad else 'artifacts/drawings.pdf')),pagesize=landscape(A3));W,H=landscape(A3)
for p in parts:
 c.setFont('Helvetica-Bold',22);c.drawString(40,H-48,('MICRO X Q4 / ' if quad else 'MICRO X B2 / ')+p['name'])
 c.setFont('Helvetica',10);c.drawString(40,H-70,'P0 independent appearance / assembly prototype | millimetres | not production released')
 m=trimesh.load_mesh(R/('models/q4' if quad else 'models')/f"{p['name']}.stl")
 for k,(axes,label) in enumerate([([0,2],'SIDE X-Z'),([0,1],'TOP X-Y'),([1,2],'FRONT Y-Z')]):
  v=m.vertices[:,axes];lo=v.min(0);hi=v.max(0);extent=hi-lo;scale=min(300/max(extent[0],1),340/max(extent[1],1));origin=np.array([55+k*380,240]);uv=(v-lo)*scale+origin
  c.setStrokeColorRGB(.19,.35,.26);c.setLineWidth(.25)
  # Boundary and feature edges avoid clutter from every triangulation diagonal.
  feature=m.face_adjacency_edges[m.face_adjacency_angles>.15]
  for a,b in feature:c.line(*uv[a],*uv[b])
  c.setFont('Helvetica-Bold',11);c.drawString(origin[0],H-112,label)
  c.setFont('Helvetica',10);c.drawString(origin[0],210,f'Overall: {extent[0]:.2f} x {extent[1]:.2f} mm')
  c.setStrokeColorRGB(.45,.45,.45);y=origin[1]-14;c.line(origin[0],y,origin[0]+extent[0]*scale,y)
  for x in [origin[0],origin[0]+extent[0]*scale]:c.line(x,y-4,x,y+4)
 c.setFont('Helvetica',10);c.drawString(40,170,'Model dimensions X/Y/Z: '+' / '.join(str(x) for x in p['dimensions_mm'])+' mm')
 c.drawString(40,150,f"Material volume: {p['volume_mm3']} mm3 | PLA solid-equivalent: {p['mass_g']} g (not slicer mass)")
 text=c.beginText(40,120);text.setFont('Helvetica',10)
 import textwrap
 for line in textwrap.wrap(p['note'],155):text.textLine(line)
 text.textLine('Use STEP for exact geometry. Overall views do not constitute full production GD&T.')
 text.textLine('Clearance, fastening, interference and physical fit require prototype verification. Rights: root LICENSE.')
 c.drawText(text);c.showPage()
c.save()
with (R/('artifacts/bom_q4.csv' if quad else 'artifacts/bom.csv')).open('w',newline='') as f:
 writer=csv.writer(f,lineterminator="\n");writer.writerow(['part','quantity','material_basis','mass_g','status','file'])
 for p in parts:writer.writerow([p['name'],1,'PLA volume estimate; material not frozen',p['mass_g'],'P0 prototype',p['step']])
 writer.writerow(['Eye M3 plastic thread-forming screw',2,'Candidate length 8 mm; verify chosen supplier and installed torque','','Prototype fit/pull test required','docs/DESIGN_QUALITY.md'])
 writer.writerow(['Eye M3 washer',2,'Candidate 1 mm thickness; verify bearing area and actual screw head','','Prototype fit required','docs/DESIGN_QUALITY.md'])
 writer.writerow(['Camera carrier M2 screws/nuts/washers',4,'Candidate M2 x 10; PCB and nut clearance fit pending','','Not procurement-ready','docs/FUNCTIONS.md'])
 writer.writerow(['Camera carrier M3 plastic thread-forming screws',2,'Candidate M3 x 10; engagement and torque test pending','','Not procurement-ready','docs/FUNCTIONS.md'])
 writer.writerow(['M3 screws and nuts','TBD','Purchased; length/retention audit pending','','Not procurement-ready','docs/ASSEMBLY.md'])
 writer.writerow(['Actuators/electronics','TBD','Not integrated','','Architecture decision required','docs/COST.md'])
print('Wrote',len(parts),'drawing pages and provisional BOM')
