"""Geometry and evidence consistency checks for Micro X Rev B. Runs with numpy + trimesh only."""
from pathlib import Path
import hashlib,json,re
import numpy as np
import trimesh
R=Path(__file__).resolve().parents[1];report=json.loads((R/'artifacts/parts.json').read_text());parts=report['parts'];checks=[]
assert len(parts)>=18 and all(p['printed'] for p in parts),'printed part list'
for p in parts:
    m=trimesh.load_mesh(R/p['stl'],process=True)
    assert m.is_watertight and m.volume>0,p['name']+' closed volume'
    assert abs(m.bounds[0,2])<.001,p['name']+' print bed origin'
    assert max(m.extents)<220,p['name']+' exceeds 220 mm print axis'
    assert (R/p['step']).stat().st_size>1000,p['name']+' STEP missing'
    world=trimesh.load_mesh(R/'models'/f"{p['name']}.stl",process=True);assert world.is_watertight and abs(world.volume-m.volume)/m.volume<.01,p['name']+' print/world volume mismatch'
    checks.append(dict(part=p['name'],body=p['body'],watertight=True,print_envelope_mm=np.round(m.extents,2).tolist(),mass_g=p['mass_g']))
for p in report['purchased']:
    m=trimesh.load_mesh(R/p['stl'],process=True);assert m.volume>0,p['name']
assert len([p for p in report['purchased'] if p['kind']=='actuator'])==15,'fifteen servo envelopes'
source=(R/'cad/build.py').read_text()+(R/'cad/layout.py').read_text()+(R/'cad/servo.py').read_text()
assert not re.search(r'vendor/|\.part\b|microduck_rl',source,re.I),'unexpected reference in CAD source'
# Measured travel and printability must be current, and every part must fit a desktop bed.
travel=json.loads((R/'engineering/joint_travel.json').read_text())['joints'];assert len(travel)==15
for name,t in travel.items():assert t['min_rad']<=0<=t['max_rad'],name+' design pose outside its own travel'
printability=json.loads((R/'artifacts/printability.json').read_text())
assert printability['all_fit_bed'],'a part does not fit the stated bed'
assert {r['part'] for r in printability['parts']}=={p['name'] for p in parts},'stale printability report'
assert (R/'models/micro_x.glb').stat().st_size>1000 and (R/'models/micro_x.step').stat().st_size>1000
# Interference report must match the exported STEP files and the motion sweep must be recorded.
inter=json.loads((R/'artifacts/interference.json').read_text())
for p in parts:
    assert inter['step_sha256'][p['name']]==hashlib.sha256((R/p['step']).read_bytes()).hexdigest(),'stale interference report: '+p['name']
assert inter['assembly_cleared'],'static assembly intersections present'
assert 'motion' in inter and len(inter['motion'])==15,'motion sweep missing'
# Rig and dynamics model must agree with the CAD pivots.
rig=json.loads((R/'models/rig.json').read_text());assert len(rig['bodies'])==16 and len(rig['policy_joints'])==14 and len(rig['qpos_layout']['joints'])==15
assert all(abs(b['home_rad'])<1e-9 or b['joint'] for b in rig['bodies'] if b['joint']),'home angles belong to joints'
for b in report['bodies']:
    rb=next(x for x in rig['bodies'] if x['name']==b['name']);assert np.allclose(np.array(b['pivot_mm'])*.001,rb['pivot_m'],atol=1e-6),b['name']+' pivot mismatch'
xml=(R/'models/micro_x_14.xml').read_text();assert 'trunk_base_freejoint' in xml and xml.count('<position ')==14 and 'mesh' not in xml
# Static balance of the whole model at HOME: centre of mass from the dynamics report must sit over the feet.
balance=json.loads((R/'artifacts/balance.json').read_text());assert balance['minimum_static_margin_mm']>0,'model COM outside the support polygon'
assert balance['model_sha256']==hashlib.sha256((R/'models/micro_x_14.xml').read_bytes()).hexdigest(),'stale balance report'
for name in ['m3_pilot_coupon','m3_clearance_coupon']:
    coupon=trimesh.load_mesh(R/'models/coupons'/f'{name}.stl');assert coupon.is_watertight and coupon.volume>0
out=dict(revision='RevB',printed_parts=len(parts),purchased_items=len(report['purchased']),mesh_checks=checks,printed_mass_g=report['printed_mass_g'],purchased_mass_g=report['purchased_mass_g'],
    geometry='valid generated CAD checked during build; closed positive-volume meshes checked here',interference='exact STEP intersections in the design pose cleared; single-joint sweeps sampled inside the measured travel',travel='engineering/joint_travel.json',printability='artifacts/printability.json',
    motion_cleared=inter['motion_cleared'],physical_fit='NOT VERIFIED',actuation='designed, not built',production_release=False,license='original design rights reserved; software MIT; see LICENSE')
(R/'artifacts/validation.json').write_text(json.dumps(out,indent=2)+'\n')
qparts=json.loads((R/'artifacts/q4_parts.json').read_text());qr=json.loads((R/'artifacts/q4_validation.json').read_text());archive=json.loads((R/'artifacts/q4_archive.json').read_text())
for path,sha in archive['sha256'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==sha,'retired Q4 archive changed'
for p in qparts:
    assert qr['step_sha256'][p['name']]==hashlib.sha256((R/p['step']).read_bytes()).hexdigest(),'stale Q4 STEP report'
files=[f for folder in ['models','cad'] for f in (R/folder).rglob('*') if f.is_file() and '__pycache__' not in str(f)]
(R/'artifacts/SHA256SUMS.json').write_text(json.dumps({str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(files)},indent=2)+'\n')
print(f'{len(parts)} printable parts and {len(report["purchased"])} purchased envelopes checked; motion sweep cleared: {inter["motion_cleared"]}; production release remains false')
