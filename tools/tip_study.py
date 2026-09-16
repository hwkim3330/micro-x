"""Report tipping limits for the current model and any extra models given as arguments.

Analysis lives in tools/tip_study_lib.py.
"""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from tip_study_lib import study,rel,__doc__ as LIBDOC
MODEL=next(p for p in sorted((R/'models').glob('*_14.xml')))  # this repo's own 14-axis model
paths=[MODEL]+[Path(a) for a in sys.argv[1:]]
res=[study(p) for p in paths]
(R/'artifacts/tip_study.json').write_text(json.dumps(dict(
    scope=' '.join(l.strip() for l in __doc__.strip().split('\n')[2:8]),pose='policy HOME',
    method='quasi-static rocking: rotate, drop to the floor, recompute contacts, fall when every contact is behind the centre of mass',
    model_sha256={rel(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},
    results=res,contact_tested=False,walking_tested=False,physical_validation=False),indent=1)+'\n')
for r in res:print(r)
