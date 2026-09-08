"""Transparent first-order load screen; cannot certify motor selection."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];c=json.loads((R/'engineering/platforms.json').read_text());rows={}
for key in ['b2','q4']:
 p=c[key];axes=p['legs']*len(p['axes_per_leg'])+c['common_head']['actuator_count'];assert axes==p['total_actuators']
 required=p['target_mass_kg']*9.80665/p['support_legs_for_screening']*p['horizontal_load_arm_m']*p['load_multiplier']
 stall=c['candidate']['published_stall_kg_cm']*.0980665
 assumed=stall*c['screening_only']['assumed_fraction_of_stall']
 rows[key]=dict(actuator_count=axes,assumed_load_torque_nm=round(required,3),assumed_available_nm=round(assumed,3),screen_margin=round(assumed/required,3),passes_assumed_screen=assumed>=required,motor_selection='UNVALIDATED: no continuous torque evidence',retail_axis_budget_usd=[round(axes*c['screening_only'][k],2) for k in ['price_per_axis_usd_low','price_per_axis_usd_high']])
report=dict(platforms=rows,limits='Static body-load screen only. Target mass, lever arm, load multiplier and derating are assumptions. Excludes link self-weight, acceleration, impacts, gait, transmission losses, thermal limits and supply sizing. Price is an illustrative family-range axis budget, not final BOM.')
(R/'artifacts/platform_screen.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
