"""Fill the measured tables in README.md and docs/DESIGN.md from artifacts/.

Docs must not carry hand-typed performance numbers: micro-x's README advertised joint
ranges that its own measurement file contradicted. Every block between
<!-- measured:NAME --> and <!-- /measured --> is regenerated here.
"""
import json,math,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def j(p):
    f=R/p
    return json.loads(f.read_text()) if f.exists() else None
parts=j('artifacts/parts.json');travel=j('engineering/joint_travel.json');tip=j('artifacts/tip_study.json')
bal=j('artifacts/balance.json');pr=j('artifacts/printability.json');itf=j('artifacts/interference.json');ev=j('artifacts/compat_evaluation.json')
harness=j('artifacts/harness_check.json');spur=j('artifacts/heel_spur_sweep.json')
KO={'hip_yaw':'고관절 요','hip_roll':'고관절 롤','hip_pitch':'고관절 피치','knee':'무릎','ankle':'발목',
    'neck_pitch':'목 피치','head_pitch':'머리 피치','head_yaw':'머리 요','head_roll':'머리 롤','jaw':'턱'}
def deg(x):return math.degrees(x)
def block_travel():
    rows=['| 관절 | 왼쪽 | 오른쪽 |','|---|---|---|'];t=travel['joints']
    for key,label in KO.items():
        names=[n for n in t if n.replace('left_','').replace('right_','')==key]
        cell=lambda n:f"{deg(t[n]['min_rad']):+.1f}° … {deg(t[n]['max_rad']):+.1f}°" if n in t else '—'
        if len(names)==2:rows.append(f"| {label} | {cell('left_'+key)} | {cell('right_'+key)} |")
        else:rows.append(f"| {label} | {cell(names[0])} | (단일) |")
    rows.append('')
    rows.append(f"탐색 상한: {', '.join(f'{KO[k]} ±{deg(v):.0f}°' for k,v in travel['search_limit_rad'].items())}. 상한에 도달한 값은 기구가 아니라 탐색 범위가 끝난 것입니다.")
    return rows
def block_tip():
    rows=['| | ' + ' | '.join(Path(r['model']).stem for r in tip['results']) + ' |','|---|'+'---|'*len(tip['results'])]
    for label,key in [('**뒤로 기울기**','tip_aft_deg'),('앞으로','tip_fwd_deg'),('옆으로','tip_lat_deg'),
                      ('무게중심 높이 (mm)','com_height_above_sole_mm'),('질량 (g)','mass_g')]:
        unit='°' if key.startswith('tip_') else ''
        rows.append(f"| {label} | "+' | '.join(f"{r[key]}{unit}" for r in tip['results'])+' |')
    return rows
def block_summary():
    n=len(parts['parts']);static=len(itf.get('static_overlaps',[])) if itf else None
    sweep=sum(len(v) for v in itf.get('sweeps',{}).values()) if itf and isinstance(itf.get('sweeps'),dict) else None
    rows=['| 항목 | 값 | 출처 |','|---|---|---|',
      f"| 출력 부품 | {n}개, {parts['printed_mass_g']} g (PLA 꽉 찬 기준, 실제 인필은 더 가벼움) | `artifacts/parts.json` |",
      f"| 구매품 | {len(parts['purchased'])}개, {parts['purchased_mass_g']} g (카탈로그) | 같은 파일 |"]
    if bal:rows.append(f"| 모델 총질량 · 무게중심 | {bal['mass_g']} g, 무게중심 z {bal['center_of_mass_mm'][2]} mm, 지지영역 여유 {bal['minimum_static_margin_mm']} mm | `artifacts/balance.json` |")
    if itf:rows.append(f"| 간섭 | 설계 자세 정적 겹침 {static}건 / 측정 가동 범위 안 스윕 충돌 {'0' if itf.get('motion_cleared') else '있음'} | `artifacts/interference.json` |")
    if pr:
        worst=max(p['overhang_fraction'] for p in pr['parts']);nobed=[p['part'] for p in pr['parts'] if p['bed_contact_mm2']<1]
        rows.append(f"| 출력성 | {len(pr['parts'])}개 모두 {pr['bed_envelope_mm'][0]:.0f}×{pr['bed_envelope_mm'][1]:.0f} 침대, 최악 오버행 {worst*100:.0f} %"
                    +(f", 침대 접촉 0 mm² {len(nobed)}개({', '.join(nobed)})는 브림/서포트 필요" if nobed else '')+" | `artifacts/printability.json` |")
    if ev:
        res=ev.get('results',[]);up=sum(1 for r in res if r.get('first_fall_s') is None);gate=sum(1 for r in res if r.get('tracking_gate_passed'))
        rows.append(f"| 공식 가중치 (무수정) | {len(res)}회 중 {up}회 직립, 추종 게이트 {gate}/{len(res)} 통과 | `artifacts/compat_evaluation.json` |")
    return rows
def block_harness():
    rows=['| 모델 | 전진 명령 추종 (최대) | 회전 명령 추종 (최대) |','|---|---|---|']
    for r in harness['best_tracking_ratio']:
        rows.append(f"| {r['model']} | {r['best_forward_tracking']*100:.0f} % | {r['best_yaw_tracking']*100:.0f} % |")
    rows.append('')
    rows.append('기준 로봇 자신이 자기 명령을 못 따르므로, **이 하네스의 절대 속도·회전 숫자는 설계 근거로 쓸 수 없습니다.** 같은 하네스 안에서의 모델 간 상대 비교만 의미가 있습니다.')
    return rows
def block_spur():
    rows=['| 뒤꿈치 돌기 높이 | 맞물림 각도 | 뒤로 기울기 | 여유 |','|---|---|---|---|']
    for r in spur['results']:
        eng='—' if r.get('engagement_deg') is None else f"{r['engagement_deg']}°"
        mar='—' if r.get('margin_deg') is None else f"{r['margin_deg']:+.1f}°"
        rows.append(f"| {r['spur_lift']} | {eng} | {r['tip_aft_deg']}° | {mar} |")
    rows.append('')
    rows.append('맞물림 각도 = 돌기가 바닥에 닿기 시작하는 뒤쪽 기울기. 여유 = 닿은 뒤로도 더 기울 수 있는 각도이며, **음수면 닿기 전에 넘어져서 돌기가 아무 일도 하지 않습니다.**')
    return rows
BLOCKS={'travel':block_travel,'tip':block_tip,'summary':block_summary,'harness':block_harness,'spur':block_spur}
for doc in ['README.md','docs/DESIGN.md']:
    f=R/doc
    if not f.exists():continue
    s=f.read_text();out=s
    for name,fn in BLOCKS.items():
        pat=re.compile(r'(<!-- measured:'+name+r' -->\n).*?(<!-- /measured -->)',re.S)
        if not pat.search(out):continue
        try:body='\n'.join(fn())+'\n'
        except Exception as e:body=f'_{name} 블록 생성 실패: {e}_\n'
        out=pat.sub(lambda m:m.group(1)+body+m.group(2),out)
    if out!=s:f.write_text(out);print('updated',doc)
