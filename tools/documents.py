"""Part drawings (PDF) and BOM (CSV) from the Rev A parts report."""
from pathlib import Path
import json,csv,textwrap
import numpy as np
import trimesh
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
R=Path(__file__).resolve().parents[1];report=json.loads((R/'artifacts/parts.json').read_text());parts=report['parts']
c=canvas.Canvas(str(R/'artifacts/drawings.pdf'),pagesize=landscape(A3));W,H=landscape(A3)
c.setFont('Helvetica-Bold',26);c.drawString(40,H-60,'MICRO X Rev A — printed part reference drawings');c.setFont('Helvetica',12)
y=H-100
for line in ['Actuated chibi T-rex; 14 policy joints + jaw. Millimetres. Assembly frame: X forward, Y left, Z up, floor Z=0.',
             f"{len(parts)} printed parts ({report['printed_mass_g']} g solid PLA equivalent) + {len(report['purchased'])} purchased items ({report['purchased_mass_g']} g catalogue).",
             'Overall views generated from the actual meshes; use STEP for exact geometry. Not production GD&T; prototype fit and fastener checks are still required.']:
    c.drawString(40,y,line);y-=18
c.setFont('Helvetica-Bold',13);c.drawString(40,y-10,'Printed parts');c.setFont('Helvetica',10);y-=30
for p in parts:
    c.drawString(40,y,f"{p['name']:<20} link {p['body']:<16} {p['dimensions_mm'][0]:>7.1f} x {p['dimensions_mm'][1]:>7.1f} x {p['dimensions_mm'][2]:>7.1f} mm   {p['mass_g']:>6.1f} g");y-=14
c.setFont('Helvetica-Bold',13);y-=10;c.drawString(40,y,'Purchased items (envelopes)');c.setFont('Helvetica',10);y-=18
for p in report['purchased']:
    c.drawString(40,y,f"{p['name']:<24} {p['kind']:<12} link {p['body']:<16} {p['mass_g']:>6.1f} g  {p['note'][:70]}");y-=13
c.showPage()
for p in parts:
    c.setFont('Helvetica-Bold',22);c.drawString(40,H-48,'MICRO X Rev A / '+p['name'])
    c.setFont('Helvetica',10);c.drawString(40,H-70,f"link: {p['body']} | millimetres | original design, prototype reference, not production released")
    m=trimesh.load_mesh(R/'models'/f"{p['name']}.stl")
    for k,(axes,label) in enumerate([([0,2],'SIDE X-Z'),([0,1],'TOP X-Y'),([1,2],'FRONT Y-Z')]):
        v=m.vertices[:,axes];lo=v.min(0);hi=v.max(0);extent=hi-lo;scale=min(300/max(extent[0],1),340/max(extent[1],1));origin=np.array([55+k*380,240]);uv=(v-lo)*scale+origin
        c.setStrokeColorRGB(.19,.35,.26);c.setLineWidth(.25)
        feature=m.face_adjacency_edges[m.face_adjacency_angles>.15]
        for a,b in feature:c.line(*uv[a],*uv[b])
        c.setFont('Helvetica-Bold',11);c.drawString(origin[0],H-112,label)
        c.setFont('Helvetica',10);c.drawString(origin[0],210,f'Overall: {extent[0]:.2f} x {extent[1]:.2f} mm')
        c.setStrokeColorRGB(.45,.45,.45);yy=origin[1]-14;c.line(origin[0],yy,origin[0]+extent[0]*scale,yy)
        for x in [origin[0],origin[0]+extent[0]*scale]:c.line(x,yy-4,x,yy+4)
    c.setFont('Helvetica',10);c.drawString(40,170,'Assembly-frame extents X/Y/Z: '+' / '.join(str(x) for x in p['dimensions_mm'])+' mm')
    c.drawString(40,150,f"Material volume: {p['volume_mm3']} mm3 | PLA solid-equivalent: {p['mass_g']} g (slicer mass will be lower)")
    text=c.beginText(40,120);text.setFont('Helvetica',10)
    for line in textwrap.wrap(p['note'],155):text.textLine(line)
    text.textLine('Use STEP for exact geometry. Clearance, fastening, interference and physical fit require prototype verification. Rights: root LICENSE.')
    c.drawText(text);c.showPage()
c.save()
with (R/'artifacts/bom.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['item','quantity','kind','link','basis','mass_g','status','file'])
    for p in parts:w.writerow([p['name'],1,'printed',p['body'],'PLA solid-equivalent volume; infill and material not frozen',p['mass_g'],'Rev A digital design',p['step']])
    for p in report['purchased']:w.writerow([p['name'],1,p['kind'],p['body'],p['note'],p['mass_g'],'purchased envelope; supplier quote pending',p['stl']])
    for item,qty,basis,status in [
        ('M2 x 6 screws, servo horn/idler to clevis plates',15*8,'Four per horn and four per idler pattern; confirm thread engagement in the printed plate','Not procurement-ready'),
        ('M2 case screws or keeper clips, servo body retention',15*2,'Depends on the confirmed XL330 case hole pattern','Not procurement-ready'),
        ('M3 x 8 plastic thread-forming screws (shell to chassis, skull to rail, eyes, tail cover)',12,'Pilot Ø2.6 in printed bosses; coupon test first','Not procurement-ready'),
        ('16 x 22 x 4 mm bearing (optional hip yaw support)',2,'Optional plain/rolling bearing under each hip yaw plate','Design option'),
        ('IMU board, microphone, speaker, wiring, TTL bus adapter, power board',1,'Not yet placed in CAD; chest board volume reserved','Architecture decision required'),
        ('TPU sole pads',2,'Fill the hollow sole underside; durometer to be chosen','Follow-up')]:
        w.writerow([item,qty,'hardware','',basis,'',status,''])
print('Wrote',len(parts),'drawing pages and the Rev A BOM')
