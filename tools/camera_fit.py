"""Conservative port screen using declared assumptions, not optical validation."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).resolve().parents[1]
source=R/'engineering/electronics.json';c=json.loads(source.read_text())['camera']
d=c['nose_plane_x_mm']-c['assumed_pupil_x_mm']
assert d>0
r=c['conservative_lens_radius_mm']+c['alignment_allowance_mm']
h=d*math.tan(math.radians(c['horizontal_fov_deg']/2))+r
v=d*math.tan(math.radians(c['vertical_fov_deg']/2))+r
required=math.hypot(h,v)
report={'scope':'Rectangular field corner within circular nose opening; assumed pupil and lens envelope, not measured vignetting', 'manifest_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pupil_to_nose_mm':round(d,3),'required_port_radius_mm':round(required,3),'designed_port_radius_mm':c['nose_port_radius_mm'],'radial_margin_mm':round(c['nose_port_radius_mm']-required,3),'assumed_port_screen_passed':required<=c['nose_port_radius_mm'],'physical_fit_verified':False,'optical_validation':False,'exclusions':['cable bend and routing','full camera component geometry','assembly tolerances','autofocus travel','real entrance pupil location','image quality and vignetting']}
(R/'artifacts/camera_fit.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['assumed_port_screen_passed']
print(json.dumps(report,indent=2))
