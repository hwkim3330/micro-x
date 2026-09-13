"""Printability report for the bed-oriented STL of every part.

For each part in models/print/ this measures the bed footprint, the height, the share of
surface area that overhangs more than 45 degrees (support territory), and the largest flat
face lying on the bed. It is a geometry report, not a slicer run: bridging, seams, warping
and material behaviour still need a real print.
"""
from pathlib import Path
import json
import numpy as np, trimesh
R=Path(__file__).resolve().parents[1]
BED=(220,220,250)           # a common desktop FDM envelope
STEEP=-np.cos(np.radians(45)) # face normals below this need support
report=json.loads((R/'artifacts/parts.json').read_text());rows=[]
for p in report['parts']:
    m=trimesh.load_mesh(R/p['stl'])
    area=m.area_faces;n=m.face_normals[:,2]
    overhang=float(area[n<STEEP].sum());bed=float(area[(n<-0.999)&(m.triangles[:,:,2].max(axis=1)<m.bounds[0,2]+.05)].sum())
    fits=all(e<=b for e,b in zip(m.extents,BED))
    rows.append(dict(part=p['name'],print_axis=p['print_axis'],footprint_mm=[round(float(m.extents[0]),1),round(float(m.extents[1]),1)],
        height_mm=round(float(m.extents[2]),1),bed_contact_mm2=round(bed,1),overhang_area_mm2=round(overhang,1),
        overhang_fraction=round(overhang/float(area.sum()),4),fits_bed=fits,mass_g=p['mass_g']))
rows.sort(key=lambda r:-r['overhang_fraction'])
total=sum(r['mass_g'] for r in rows)
out=dict(scope='Geometry-only printability of models/print/*.stl in their shipped orientation. Overhang = surface area whose normal tilts more than 45 degrees below horizontal. Not a slicer run: no bridging, seam, warping or material check.',
    bed_envelope_mm=list(BED),overhang_rule_deg=45,parts=rows,
    worst_overhang_fraction=rows[0]['overhang_fraction'],all_fit_bed=all(r['fits_bed'] for r in rows),
    total_printed_mass_g=round(total,1),
    note='Parts print in the orientation stored in models/print/. Solid-PLA mass is an upper bound; sliced mass with normal infill is lower.')
(R/'artifacts/printability.json').write_text(json.dumps(out,indent=2)+'\n')
for r in rows:print(f"{r['part']:20s} {r['footprint_mm'][0]:6.1f} x {r['footprint_mm'][1]:6.1f} x {r['height_mm']:6.1f} mm  bed {r['bed_contact_mm2']:7.1f} mm2  overhang {r['overhang_fraction']*100:5.1f} %")
print(f"all parts fit a {BED[0]}x{BED[1]} bed: {out['all_fit_bed']}; worst overhang {out['worst_overhang_fraction']*100:.1f} %")
