"""Does the board we picked actually fit the bay we drew?

engineering/electronics.json names a compute board and its outline. cad/build.py draws a
compute_board envelope and a deck around it. Nothing checked that the two agree, so the
deck could be drawn for one board while the documents commit to another. Compare them,
both orientations, and report the shortfall in millimetres.

Outline only. Connectors, the camera FFC, wiring loom, standoffs and any cooling are not
in either number yet.
"""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
MARGIN=1.0 # mm per side for placement tolerance
def main():
    el=json.loads((R/'engineering/electronics.json').read_text())
    parts=json.loads((R/'artifacts/parts.json').read_text())
    env=next((p for p in parts['purchased'] if p['name']=='compute_board'),None)
    board=el.get('compute',{});want=board.get('dimensions_mm')
    if not (env and want):print('no compute envelope or no declared board');return
    have=sorted(env['dimensions_mm'])[-2:]     # the two large axes of the modelled bay
    need=sorted(want)[-2:]   # the two large axes; thickness is not what the bay is short of
    fits=all(h>=n+2*MARGIN for h,n in zip(sorted(have),need))
    short=[round(n+2*MARGIN-h,1) for h,n in zip(sorted(have),need)]
    out=dict(scope=' '.join(l.strip() for l in __doc__.strip().split('\n')),
        declared_board=board.get('candidate'),declared_outline_mm=need,
        modelled_bay_mm=[round(v,1) for v in sorted(have)],placement_margin_mm=MARGIN,
        fits=bool(fits),shortfall_mm=[s for s in short if s>0],
        connectors_and_wiring_included=False)
    (R/'artifacts/electronics_fit.json').write_text(json.dumps(out,indent=1)+'\n')
    print(f"declared {board.get('candidate','?')}\n  outline {need} mm  bay {out['modelled_bay_mm']} mm  fits: {fits}")
    if not fits:print('  SHORT BY',short,'mm (including',2*MARGIN,'mm total placement margin)')
if __name__=='__main__':main()
