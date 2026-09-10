"""Discrete jaw STEP intersection samples, not continuous motion proof."""
from pathlib import Path
import json,itertools
import cadquery as cq
import hashlib
R=Path(__file__).resolve().parents[1];parts=json.loads((R/'artifacts/parts.json').read_text());shapes={p['name']:cq.importers.importStep(str(R/p['step'])) for p in parts};jaw=shapes.pop('jaw');collisions=[];exact=0
for angle in range(0,21,2):
 moving=jaw.rotate((59,0,188),(59,1,188),angle);A=moving.val().BoundingBox()
 for name,shape in shapes.items():
  B=shape.val().BoundingBox()
  if any(getattr(A,k+'max')<=getattr(B,k+'min')+1e-5 or getattr(B,k+'max')<=getattr(A,k+'min')+1e-5 for k in 'xyz'):continue
  exact+=1;volume=sum(v.Volume() for v in moving.intersect(shape).solids().vals())
  if volume>.01:collisions.append(dict(deg=angle,part=name,overlap_mm3=round(volume,3)))
report=dict(angles_deg=list(range(0,21,2)),exact_pairs=exact,collisions=collisions,clear_at_samples=not collisions,scope='CAD volumetric overlaps at discrete 2-degree intervals; fasteners, tolerances, gap width and continuous motion unvalidated')
report['step_sha256']={p['name']:hashlib.sha256((R/p['step']).read_bytes()).hexdigest() for p in parts}
(R/'artifacts/jaw_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
