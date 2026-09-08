"""Exact BREP static intersections; this is not a dynamic clearance sweep."""
from pathlib import Path
import itertools,json,time
import cadquery as cq
import hashlib
R=Path(__file__).resolve().parents[1];parts=json.loads((R/'artifacts/parts.json').read_text())
shapes={p['name']:cq.importers.importStep(str(R/p['step'])) for p in parts};overlaps=[];tested=0
for a,b in itertools.combinations(shapes,2):
 A=shapes[a].val().BoundingBox();B=shapes[b].val().BoundingBox()
 if any(getattr(A,k+'max')<=getattr(B,k+'min')+1e-5 or getattr(B,k+'max')<=getattr(A,k+'min')+1e-5 for k in 'xyz'):continue
 intersection=shapes[a].intersect(shapes[b]);volume=sum(s.Volume() for s in intersection.solids().vals());tested+=1
 if volume>.01:overlaps.append(dict(parts=[a,b],overlap_mm3=round(volume,3)))
report=dict(scope='zero-pose exact STEP intersection; no swept-volume, tolerance or strength inference',broadphase_pairs=105,exact_pairs=tested,overlaps=overlaps,assembly_cleared=len(overlaps)==0)
report['step_sha256']={p['name']:hashlib.sha256((R/p['step']).read_bytes()).hexdigest() for p in parts}
(R/'artifacts/interference.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
