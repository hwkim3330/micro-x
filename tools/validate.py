from pathlib import Path
import hashlib,json,re
import numpy as np
import trimesh
R=Path(__file__).resolve().parents[1];parts=json.loads((R/'artifacts/parts.json').read_text());checks=[]
for p in parts:
 m=trimesh.load_mesh(R/p['stl'],process=True)
 assert m.is_watertight and m.volume>0,p['name']+' closed volume'
 assert abs(m.bounds[0,2])<.001,p['name']+' print bed origin'
 assert max(m.extents)<220,p['name']+' exceeds 220 mm print axis'
 assert (R/p['step']).stat().st_size>1000,p['name']+' STEP missing'
 checks.append(dict(part=p['name'],watertight=True,print_envelope_mm=np.round(m.extents,2).tolist(),step_exists=True))
source=(R/'cad/build.py').read_text()
assert not re.search(r'microduck|micro.rex|vendor/',source,re.I),'unexpected reference in CAD source'
assert (R/'models/micro_x.glb').stat().st_size>1000
static=json.loads((R/'artifacts/interference.json').read_text());jaw=json.loads((R/'artifacts/jaw_clearance.json').read_text())
for p in parts:
    sha=hashlib.sha256((R/p['step']).read_bytes()).hexdigest()
    assert static['step_sha256'][p['name']]==sha and jaw['step_sha256'][p['name']]==sha, 'stale collision report'
assert not static['overlaps'], 'static assembly intersections present'
assert not jaw['collisions'], 'sampled jaw intersections present'
for name in ['m3_pilot_coupon','m3_clearance_coupon']:
    coupon=trimesh.load_mesh(R/'models/coupons'/f'{name}.stl');assert coupon.is_watertight and coupon.volume>0
report=dict(revision='P0',parts=len(parts),mesh_checks=checks,geometry='valid generated CAD checked during build; closed positive-volume meshes checked here',physical_fit='NOT VERIFIED',actuation='NOT INTEGRATED',interference='No exact STEP volume overlap at reference pose; jaw 0–20 degrees sampled every 2 degrees clear. Continuous sweep/tolerance/fasteners NOT VERIFIED',production_release=False,license='original design rights reserved; software MIT; see LICENSE')
(R/'artifacts/validation.json').write_text(json.dumps(report,indent=2)+'\n')
files=[f for folder in ['models','cad'] for f in (R/folder).rglob('*') if f.is_file() and '__pycache__' not in str(f)]
(R/'artifacts/SHA256SUMS.json').write_text(json.dumps({str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(files)},indent=2)+'\n')
print(f'{len(parts)} printable models checked; production release remains false')
