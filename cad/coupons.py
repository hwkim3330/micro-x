"""Printer calibration coupons; independent Micro X design data, root LICENSE."""
from pathlib import Path
import cadquery as cq
import trimesh
R=Path(__file__).resolve().parents[1]
# Five M3 pilot holes: 2.4, 2.5, 2.6, 2.7, 2.8 mm. Mark order in drawing, no guessed insert fit.
pilot=cq.Workplane('XY').box(62,16,12,centered=(False,False,False))
for i,d in enumerate([2.4,2.5,2.6,2.7,2.8]):pilot=pilot.cut(cq.Workplane('XY',origin=(9+i*11,8,1)).circle(d/2).extrude(12))
# Through clearance holes, 3.1..3.5 mm, different width avoids mixing coupons.
clear=cq.Workplane('XY').box(62,20,4,centered=(False,False,False))
for i,d in enumerate([3.1,3.2,3.3,3.4,3.5]):clear=clear.cut(cq.Workplane('XY',origin=(9+i*11,10,-1)).circle(d/2).extrude(6))
for name,shape in [('m3_pilot_coupon',pilot),('m3_clearance_coupon',clear)]:
 folder=R/'models/coupons';folder.mkdir(exist_ok=True)
 assert shape.val().isValid()
 cq.exporters.export(shape,str(folder/(name+'.step')));cq.exporters.export(shape,str(folder/(name+'.stl')))
 assert trimesh.load_mesh(folder/(name+'.stl')).is_watertight
print('2 independent M3 calibration coupons exported')
