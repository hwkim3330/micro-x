"""Two structural screens the design has never had: wall thickness, and whether a servo
can break the plate it drives.

WALL THICKNESS. From each face centroid, cast a ray straight into the solid and keep the
first hit whose own surface faces back at the ray. That filter matters: without it, concave
corners return near-zero "thicknesses" that are just the adjacent face. Anything below the
practical FDM minimum (two perimeters each side of a 0.4 mm nozzle) cannot be printed strong.

HORN PLATE AT STALL TORQUE. Closed form, on the as-built plate geometry that cad/servo.py
records while building. Each plate takes the servo's full torque through four M2 bolts on a
12 mm circle, so the tangential force per bolt is T/(n*r). Three failure modes follow from
that: bearing of the bolt on the printed hole, shear-out from the hole to the plate edge,
and in-plane bending of the plate where it meets its link.

HOW MUCH TO TRUST THE WALL NUMBER. It found one unambiguous defect - the neck cover was
62 % under the minimum because a 9 mm fillet on a 31 mm shell ate the wall - and that fix
took it to 0 %. The remaining flags sit in bands next to cut edges and rims, where a shell
legitimately tapers. Raising the shell offsets to chase them added 1.7 kg of plastic and
moved the numbers by nothing. So: treat a HIGH fraction as a prompt to look at the region
the report names, not as a verdict. The per-part thin_region_mm box is there for that.

NOT analysed: the link body beyond the plate, the servo channel walls, screw bosses, and
every impact case. Those need FEA or a physical test. An earlier version of this file tried
to find each link's critical section by slicing the mesh and reported a safety factor of
0.07 for the chassis, which was an artifact of picking up a screw boss - it is gone.
"""
import json,math,sys
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1]
NOZZLE=0.4
MIN_WALL=4*NOZZLE
STALL_NM=0.52          # XL330-M288-T at 5.0 V, engineering/actuator_interface.json
# FDM PLA pulled across the layer lines. Assumptions, not coupon tests.
TENSILE_MPA=25.0;SHEAR_MPA=15.0
TARGET_SF=2.0
def wall_thickness(mesh,samples=6000):
    """Local thickness, ignoring the rims.

    A hollow shell with an opening has a rim, and a tapering tip has a point; both are thin
    where the surface turns a sharp convex corner, by construction and not by mistake. The
    first version of this screen counted those and flagged eight parts, so raising the wall
    offsets "to fix them" only added 1.7 kg of plastic without moving the numbers. Faces on
    or next to a sharp convex edge are excluded here, leaving thin FLAT wall."""
    rng=np.random.default_rng(0)
    sharp=mesh.face_adjacency_angles>math.radians(60)
    convex=mesh.face_adjacency_convex
    bad=set(mesh.face_adjacency[sharp&convex].ravel().tolist())
    keep=np.array([f for f in range(len(mesh.faces)) if f not in bad],dtype=np.int64)
    if len(keep)<50:keep=np.arange(len(mesh.faces))
    idx=rng.choice(keep,size=min(samples,len(keep)),replace=False)
    n=mesh.face_normals[idx];origins=mesh.triangles_center[idx]-n*1e-3
    hit,ray,tri=mesh.ray.intersects_location(origins,-n,multiple_hits=False)
    if not len(hit):return None
    # The ray leaves through the far wall, whose OUTWARD normal points along the ray. Requiring
    # that weeds out concave corners, which otherwise return a near-zero "thickness".
    facing=(mesh.face_normals[tri]*(-n[ray])).sum(1)>0.5
    d=np.linalg.norm(hit-origins[ray],axis=1)
    ok=facing&(d>0.05)
    return (d[ok],origins[ray][ok]) if ok.any() else None
def plate_checks(name,g):
    T=STALL_NM*1000.0                      # N.mm
    r=g['bolt_circle_r_mm'];t=g['thickness_mm'];n=g['bolts']
    F=T/(n*r)                               # tangential force per bolt, N
    bearing=F/(2*g['bolt_hole_r_mm']*t)
    edge=g['width_mm']/2-r-g['bolt_hole_r_mm']
    shear_out=F/(2*max(edge,1e-6)*t)
    Z=t*g['width_mm']**2/6.0                # in-plane bending of the plate at its root
    bending=T/Z
    modes=dict(bolt_bearing_mpa=round(bearing,2),bolt_shear_out_mpa=round(shear_out,2),
               plate_bending_mpa=round(bending,2),edge_distance_mm=round(edge,2),
               force_per_bolt_n=round(F,1))
    sf=dict(bolt_bearing=TENSILE_MPA/bearing,bolt_shear_out=SHEAR_MPA/shear_out,plate_bending=TENSILE_MPA/bending)
    worst=min(sf,key=sf.get)
    modes.update(safety_factors={k:round(v,2) for k,v in sf.items()},
                 governing_mode=worst,safety_factor=round(sf[worst],2))
    return modes
if __name__=='__main__':
    report=json.loads((R/'artifacts/parts.json').read_text())
    rows=[];thin=[]
    for p in report['parts']:
        mesh=trimesh.load_mesh(R/'models'/f"{p['name']}.stl")
        got=wall_thickness(mesh);row=dict(part=p['name'],mass_g=p['mass_g'])
        if got is not None:
            d,where=got
            row.update(p05_wall_mm=round(float(np.percentile(d,5)),2),
                       median_wall_mm=round(float(np.median(d)),2),
                       fraction_below_min_wall=round(float((d<MIN_WALL).mean()),4))
            if row['fraction_below_min_wall']>0.02:
                pts=where[d<MIN_WALL]
                row['thin_region_mm']=[np.round(pts.min(0),1).tolist(),np.round(pts.max(0),1).tolist()]
                thin.append(dict(part=p['name'],fraction=row['fraction_below_min_wall'],where=row['thin_region_mm']))
        rows.append(row)
        print(f"{row['part']:20s} p05 {row.get('p05_wall_mm','-'):>5} median {row.get('median_wall_mm','-'):>6} mm  below {MIN_WALL} mm: {row.get('fraction_below_min_wall',0)*100:4.1f} %",flush=True)
    plates={k:plate_checks(k,g) for k,g in report.get('horn_plates',{}).items()}
    low=[dict(joint=k,safety_factor=v['safety_factor'],mode=v['governing_mode']) for k,v in plates.items() if v['safety_factor']<TARGET_SF]
    print()
    for k,v in sorted(plates.items(),key=lambda kv:kv[1]['safety_factor']):
        print(f"{k:18s} SF {v['safety_factor']:6.2f}  governed by {v['governing_mode']}")
    out=dict(scope=' '.join(l.strip() for l in __doc__.strip().split('\n')),
        nozzle_mm=NOZZLE,minimum_wall_mm=MIN_WALL,stall_torque_nm=STALL_NM,
        allowable_tensile_mpa=TENSILE_MPA,allowable_shear_mpa=SHEAR_MPA,
        allowable_note='assumption for FDM PLA loaded across the layers; no coupon test has been run',
        target_safety_factor=TARGET_SF,parts=rows,parts_with_thin_walls=thin,
        horn_plates=plates,plates_below_target=low,
        not_analysed=['link bodies beyond the horn plate','servo channel walls','screw bosses','impact and drop','fatigue'],
        physical_test=False,fea=False)
    (R/'artifacts/strength.json').write_text(json.dumps(out,indent=1)+'\n')
    print('\nthin-wall parts:',[t['part'] for t in thin] or 'none')
    print('plates below SF',TARGET_SF,':',low or 'none')
