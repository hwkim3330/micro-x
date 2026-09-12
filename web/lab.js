import {advance,validatePolicy,evaluate} from './learning-core.js';
const $=s=>document.querySelector(s),frame=$('#robot');
const LOCAL=['localhost','127.0.0.1'].includes(location.hostname);
let view,worker,policy,history=[],animation=0,utterance,exploded=false,replay=null,replayTimer=null,replayIndex=0;
const JOINTS={left_hip_yaw:'왼 고관절 요',left_hip_roll:'왼 고관절 롤',left_hip_pitch:'왼 고관절 피치',left_knee:'왼 무릎',left_ankle:'왼 발목',neck_pitch:'목 피치',head_pitch:'머리 피치',head_yaw:'머리 요',head_roll:'머리 롤',jaw:'턱',right_hip_yaw:'오른 고관절 요',right_hip_roll:'오른 고관절 롤',right_hip_pitch:'오른 고관절 피치',right_knee:'오른 무릎',right_ankle:'오른 발목'};
const NAMES={chassis:'섀시',torso_shell:'몸통 쉘',chest_panel:'가슴 패널',tail_cover:'꼬리 · 배터리 커버',neck_link:'목 링크',head_base:'머리 베이스',head_yoke:'머리 요크',head_frame:'머리 프레임',skull:'두개골 쉘',eye_left:'왼쪽 눈',eye_right:'오른쪽 눈',jaw_beak:'아래턱',left_yaw2roll:'왼 요·롤 브래킷',right_yaw2roll:'오른 요·롤 브래킷',left_hip:'왼 고관절 브래킷',right_hip:'오른 고관절 브래킷',left_thigh:'왼 허벅지',right_thigh:'오른 허벅지',left_shin:'왼 종아리',right_shin:'오른 종아리',left_foot:'왼발',right_foot:'오른발',battery_np_f550:'배터리 (NP-F550급)',compute_board:'컴퓨트 보드',camera_module_3:'카메라 모듈'};
const label=n=>NAMES[n]||(n.startsWith('servo_')?'서보 · '+(JOINTS[n.slice(6)]||n.slice(6)):n);
const robot=()=>view?.robot;
function stopMotion(){cancelAnimationFrame(animation);animation=0;window.speechSynthesis?.cancel();utterance=null;if(robot())robot().setJoint('jaw',0);$('#run').textContent='정책 실행';stopReplay()}
function stopReplay(){clearInterval(replayTimer);replayTimer=null;$('#replay-play').textContent='재생'}
function showPart(part){const detail=$('#part-detail');detail.replaceChildren();
  for(const [tag,text]of [['h3',label(part.name)],['p',`${part.dimensions_mm.join(' × ')} mm · ${part.printed?`PLA 꽉 찬 기준 ${part.mass_g} g`:`구매품 ${part.mass_g} g`} · 링크 ${part.body}`],['p',part.note]]){const e=document.createElement(tag);e.textContent=text;detail.append(e)}
  if(part.printed)for(const [l,url]of [['STEP ↓',part.step],['STL ↓',part.stl]]){const a=document.createElement('a');a.textContent=l;a.href='../'+url;detail.append(a)}}
function layer(){if(!robot())return;const v=$('#layer').value;const match=p=>v==='all'||(v==='shell'?p.group==='shell':v==='frame'?p.printed&&p.group!=='shell':v==='purchased'?!p.printed:v==='head'?['head','head_yoke','head_base','jaw','neck'].includes(p.body):v==='legs'?/left_|right_/.test(p.body):p.body==='trunk');
  robot().setVisible(match);const list=$('#part-list');list.replaceChildren();
  for(const p of [...robot().parts.parts,...robot().parts.purchased]){if(!match(p))continue;const b=document.createElement('button');b.textContent=label(p.name);b.onclick=()=>{view.inspect(robot().meshes.find(m=>m.name===p.name));showPart(p)};list.append(b)}}
function resetView(){if(!view)return;frame.contentDocument.querySelector('#reset').click();exploded=false;$('#explode').textContent='분해 보기';$('#layer').value='all';layer();view.inspect(null)}
frame.addEventListener('load',()=>{let attempts=0;const timer=setInterval(()=>{view=frame.contentWindow.microX;
  if(!view){if(++attempts>150){clearInterval(timer);$('#viewer-status').textContent='모델을 불러오지 못했어요. 페이지를 새로 고쳐 주세요.'}return}
  clearInterval(timer);$('#viewer-status').textContent=`실제 CAD · 출력 ${view.parts.length}개 · 구매 ${view.robot.parts.purchased.length}개`;$('#explode').disabled=false;$('#reset-view').disabled=false;
  frame.contentWindow.addEventListener('microx-part',e=>showPart(e.detail));layer();if(policy)$('#run').disabled=false;if(replay)$('#replay-play').disabled=false;buildReadout()},200)});
$('#layer').onchange=layer;$('#reset-view').onclick=()=>{stopMotion();resetView()};
$('#explode').onclick=()=>{stopMotion();frame.contentDocument.querySelector('#explode').click();exploded=!exploded;$('#explode').textContent=exploded?'조립 보기':'분해 보기'};
const tabs=[...document.querySelectorAll('[data-tab]')];
for(const tab of tabs){tab.onclick=()=>{stopMotion();resetView();for(const b of tabs){const active=b===tab;b.setAttribute('aria-selected',active);b.tabIndex=active?0:-1;$('#'+b.dataset.tab).hidden=!active}history.replaceState?.(null,'','#'+tab.dataset.tab)};tab.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const index=e.key==='Home'?0:e.key==='End'?tabs.length-1:(tabs.indexOf(tab)+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length;tabs[index].click();tabs[index].focus()}}
if(location.hash){const t=tabs.find(b=>'#'+b.dataset.tab===location.hash||(location.hash==='#compatibility'&&b.dataset.tab==='studio'));if(t)t.click()}

// ---------------------------------------------------------------- replay tab
function buildReadout(){const host=$('#joint-readout');host.replaceChildren();for(const name of robot().rig.qpos_layout.joints){const row=document.createElement('div');row.dataset.joint=name;row.textContent=`${JOINTS[name]||name}: —`;host.append(row)}}
async function loadReplay(){try{const r=await fetch('../artifacts/compat_replay.json',{cache:'no-store'});if(!r.ok)throw Error();replay=await r.json();$('#replay-status').textContent=`${replay.result.policy} · 명령 ${replay.result.command.join(', ')} · ${(replay.qpos.length*replay.dt).toFixed(1)}초 · ${replay.result.first_fall_s===null?'넘어짐 없음':'넘어짐 '+replay.result.first_fall_s+'초'} · 평균 몸체 속도 ${replay.result.mean_body_velocity?.map(v=>v.toFixed(3)).join(' / ')||'—'}`;if(robot())$('#replay-play').disabled=false}catch{$('#replay-status').textContent='보행 기록을 불러오지 못했습니다.'}}
$('#replay-play').onclick=()=>{if(replayTimer){stopReplay();return}if(!replay||!robot())return;if(exploded)$('#explode').click();$('#replay-play').textContent='일시정지';replayIndex=0;
  replayTimer=setInterval(()=>{if(replayIndex>=replay.qpos.length)replayIndex=0;const q=replay.qpos[replayIndex];robot().setPose(q);view.controls.target.set(q[0],.14,-q[1]);robot().rig.qpos_layout.joints.forEach((name,i)=>{const row=$(`#joint-readout [data-joint="${name}"]`);if(row)row.textContent=`${JOINTS[name]||name}: ${(q[7+i]*180/Math.PI).toFixed(1)}°`});replayIndex++},replay.dt*1000)};
$('#replay-stop').onclick=()=>{stopReplay();robot()?.home()};
loadReplay();

// ---------------------------------------------------------------- studio tab (records + local server)
async function json(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error(r.status);return r.json()}
async function cards(){
  try{const r=await json('../artifacts/compat_evaluation.json');const falls=r.results.filter(x=>x.first_fall_s!==null).length,gate=r.results.filter(x=>x.tracking_gate_passed).length;$('#card-official').textContent=`CAD 기반 모델에서 ${r.results.length}회 시험: 넘어짐 ${falls}회, 속도·방향 기준 통과 ${gate}회. 서 있기는 되지만 전진·회전 명령 추종은 아직 미달입니다.`}catch{$('#card-official').textContent='기록을 불러오지 못했습니다.'}
  try{const r=await json('../artifacts/compat_training.json');$('#card-training').textContent=`같은 액터로 PPO ${r.updates}회 × ${r.steps_per_update}스텝 실행, 변환 오차 ${r.initial_actor_max_error.toExponential(1)}, ONNX 재내보내기 완료. 원본 학습 설정과의 동일성은 미검증입니다.`}catch{$('#card-training').textContent='기록을 불러오지 못했습니다.'}
  try{const r=await json('../artifacts/trained_500_evaluation.json');const gate=r.results.filter(x=>x.tracking_gate_passed).length;$('#card-500').textContent=`256개 환경·500회 학습 정책의 ${r.results.length}회 시험 중 ${gate}회 통과. 정지만 통과했고 이동 명령은 미달이라 기본 정책으로 채택하지 않았습니다.`}catch{$('#card-500').textContent='기록을 불러오지 못했습니다.'}}
cards();
function chart(hist){const c=$('#ppo-chart').getContext('2d'),w=700,h=200;c.clearRect(0,0,w,h);if(!hist.length){c.fillStyle='#5a6a5f';c.font='14px sans-serif';c.fillText('학습을 시작하면 업데이트별 평균 보상(초록)과 넘어짐 수(주황)가 그려집니다.',16,h/2);return}
  const rewards=hist.map(p=>p.mean_reward),falls=hist.map(p=>p.falls);const rmin=Math.min(...rewards),rmax=Math.max(...rewards),fmax=Math.max(1,...falls);const x=i=>24+i/Math.max(1,hist.length-1)*(w-48);
  c.strokeStyle='#38734e';c.lineWidth=3;c.beginPath();rewards.forEach((r,i)=>{const y=h-28-(rmax===rmin?.5:(r-rmin)/(rmax-rmin))*(h-56);i?c.lineTo(x(i),y):c.moveTo(x(i),y)});c.stroke();
  c.strokeStyle='#d87832';c.lineWidth=2;c.beginPath();falls.forEach((f,i)=>{const y=h-28-f/fmax*(h-56);i?c.lineTo(x(i),y):c.moveTo(x(i),y)});c.stroke();
  c.fillStyle='#183e32';c.font='13px sans-serif';c.fillText(`업데이트 ${hist.length} · 평균 보상 ${rewards.at(-1).toFixed(3)} (${rmin.toFixed(2)}–${rmax.toFixed(2)}) · 넘어짐 ${falls.at(-1)}`,16,18)}
chart([]);
let poll,serverOk=false;
function busy(state){const running=state==='running';$('#ppo-start').disabled=running||!LOCAL||!serverOk;$('#ppo-stop').disabled=!running;for(const id of ['ppo-name','ppo-updates','ppo-steps','ppo-seed'])$('#'+id).disabled=running}
async function status(){try{const state=await json('/api/status');serverOk=true;$('#ppo-status').textContent=`로컬 서버 · 상태: ${state.status}${state.kind==='evaluate'?' (평가 실행 중)':''}`;$('#ppo-log').textContent=state.lines.join('\n');busy(state.status);
  if(state.status==='running'&&state.kind!=='evaluate'){try{chart((await json('/api/progress')).history||[])}catch{}}
  if(state.status==='running')poll=setTimeout(status,1000);else{await checkpoints();if(state.kind==='evaluate'&&state.status==='completed')await showEvaluation(state.settings?.checkpoint||'official')}}
  catch{serverOk=false;$('#ppo-status').textContent='로컬 학습 서버 연결을 확인해 주세요. 정적 서버에서는 기록만 볼 수 있습니다.';busy('idle');$('#local-steps').hidden=false}}
async function checkpoints(){const host=$('#checkpoints');try{const data=await json('/api/checkpoints');host.replaceChildren();
  const rows=[{file:'official',label:'공식 alpha_walking (변경 없음)',evaluated:true,history:null},...data.checkpoints.map(c=>({...c,label:c.file}))];
  for(const c of rows){const row=document.createElement('div');row.className='ckpt';const b=document.createElement('b');b.textContent=c.label;row.append(b);
    if(c.history){const s=document.createElement('span');s.className='pill';s.textContent=`${c.updates}회 · 시드 ${c.seed} · 마지막 보상 ${c.history.at(-1)?.mean_reward}`;row.append(s)}
    const ev=document.createElement('button');ev.textContent=c.evaluated&&c.file!=='official'?'다시 평가':'평가 실행';ev.onclick=()=>runEvaluation(c.file);row.append(ev);
    const show=document.createElement('button');show.textContent='결과 보기';show.onclick=()=>showEvaluation(c.file);row.append(show);
    if(c.file!=='official'){const a=document.createElement('a');a.href='/api/checkpoint?name='+encodeURIComponent(c.file.replace(/\.onnx$/,''));a.textContent='ONNX 저장 ↓';row.append(a);const sim=document.createElement('a');sim.href='simulator.html';sim.textContent='보행 실험에서 조작 ↗';row.append(sim);
      if(c.history){const g=document.createElement('button');g.textContent='학습 곡선';g.onclick=()=>chart(c.history);row.append(g)}}
    host.append(row)}}catch{host.innerHTML='<p class="scope">로컬 서버에 연결되면 저장된 ONNX가 여기에 나타납니다.</p>'}}
async function runEvaluation(file){try{const r=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({checkpoint:file,seconds:10,seeds:2})});if(!r.ok)throw Error((await r.json()).error);clearTimeout(poll);status()}catch(e){$('#ppo-status').textContent=e.message}}
function resultsTable(title,data){const wrap=document.createElement('div');const h=document.createElement('h4');h.textContent=title;wrap.append(h);
  const t=document.createElement('table');t.className='results';t.innerHTML='<thead><tr><th>명령 (vx, vy, ωz)</th><th>시드</th><th>넘어짐</th><th>평균 몸체 속도</th><th>오차 MAE</th><th>판정</th></tr></thead>';const tb=document.createElement('tbody');
  for(const r of data.results){const tr=document.createElement('tr');tr.innerHTML=`<td>${r.command.join(', ')}</td><td>${r.seed}</td><td>${r.first_fall_s===null?'없음':r.first_fall_s+'초'}</td><td>${r.mean_body_velocity.map(v=>v.toFixed(3)).join(' / ')}</td><td>${r.tracking_mae.map(v=>v.toFixed(3)).join(' / ')}</td><td class="${r.tracking_gate_passed?'pass':'fail'}">${r.tracking_gate_passed?'통과':'미달'}</td>`;tb.append(tr)}
  t.append(tb);wrap.append(t);const s=document.createElement('p');s.className='scope';s.textContent=`${data.results.length}회 중 ${data.results.filter(r=>r.tracking_gate_passed).length}회 통과 · 모델 ${data.model_sha256.slice(0,12)}… · ${data.scope}`;wrap.append(s);return wrap}
async function showEvaluation(file){const host=$('#evaluation');try{const name=file==='official'?'official':file.replace(/\.onnx$/,'');const data=await json('/api/evaluation/'+name);host.replaceChildren(resultsTable(file==='official'?'공식 가중치 (변경 없음)':'학습 체크포인트 '+file,data))}catch{host.innerHTML=`<p class="scope">${file}의 평가 기록이 아직 없습니다. "평가 실행"을 누르면 로컬 서버가 계산합니다.</p>`}}
$('#ppo-start').onclick=async()=>{const data=Object.fromEntries(['updates','steps','seed'].map(k=>[k,Number($('#ppo-'+k).value)]));data.name=$('#ppo-name').value.trim();
  if(!['updates','steps','seed'].every(k=>$('#ppo-'+k).value!==''&&$('#ppo-'+k).checkValidity()&&Number.isInteger(data[k]))||!/^[A-Za-z0-9_-]{1,40}$/.test(data.name)){$('#ppo-status').textContent='설정 범위 안의 정수와 영문·숫자 이름을 입력하세요.';return}
  try{const r=await fetch('/api/train',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(!r.ok)throw Error((await r.json()).error);chart([]);clearTimeout(poll);status()}catch(e){$('#ppo-status').textContent=e.message}};
$('#ppo-stop').onclick=async()=>{await fetch('/api/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});clearTimeout(poll);status()};
if(LOCAL){status();$('#local-steps').hidden=true}
window.addEventListener('pagehide',()=>clearTimeout(poll));

// ---------------------------------------------------------------- 1-axis teaching tab (browser CEM)
function graph(){const canvas=$('#loss'),c=canvas.getContext('2d'),w=canvas.width,h=canvas.height;c.clearRect(0,0,w,h);if(!history.length)return;const maximum=Math.max(...history.map(p=>p.loss),.0001);c.strokeStyle='#38734e';c.lineWidth=3;c.beginPath();history.forEach((p,i)=>{const x=20+i/Math.max(1,history.length-1)*(w-40),y=h-25-p.loss/maximum*(h-50);i?c.lineTo(x,y):c.moveTo(x,y)});c.stroke();c.fillStyle='#315542';c.font='16px sans-serif';c.fillText(`Loss ${history.at(-1).loss.toFixed(5)} · ${history.length} generations`,20,20)}
function busyJaw(value){$('#train').disabled=value;$('#stop').disabled=!value;for(const id of ['generations','population','seed','import'])$('#'+id).disabled=value}
$('#train').onclick=()=>{stopMotion();const settings=Object.fromEntries(['seed','generations','population'].map(id=>[id,Number($('#'+id).value)]));
  if(!['seed','generations','population'].every(id=>$('#'+id).value!==''&&$('#'+id).checkValidity()&&Number.isInteger(settings[id]))){$('#training-status').textContent='설정 범위 안의 정수를 입력해 주세요.';return}
  worker?.terminate();history=[];graph();busyJaw(true);$('#training-status').textContent='후보 정책을 평가하고 있어요…';
  try{worker=new Worker('./learning-worker.js',{type:'module'})}catch{$('#training-status').textContent='이 브라우저에서 학습 Worker를 시작할 수 없어요.';busyJaw(false);return}
  worker.onerror=()=>{$('#training-status').textContent='학습 실행 오류. 설정을 확인하고 다시 시작해 주세요.';worker.terminate();busyJaw(false)};
  worker.onmessage=({data})=>{if(data.type==='progress'){history.push({generation:data.generation,loss:data.loss});graph();$('#training-status').textContent=`${data.generation} / ${settings.generations} 세대 · 학습 오차 ${data.rmseDegrees.toFixed(2)}°`}
    if(data.type==='complete'){policy=data.policy;validatePolicy(policy);$('#evaluation-jaw').textContent=evaluate(policy.weights,true).rmseDegrees.toFixed(2)+'°';$('#training-status').textContent='학습 완료. 별도 목표에서 평가했어요. 정책을 실행하거나 저장해 보세요.';$('#export').disabled=false;$('#run').disabled=!robot();busyJaw(false);worker.terminate();worker=null}
    if(data.type==='error'){$('#training-status').textContent=data.message;busyJaw(false);worker.terminate();worker=null}};worker.postMessage(settings)};
$('#stop').onclick=()=>{worker?.terminate();worker=null;busyJaw(false);$('#training-status').textContent='학습을 중지했어요. 중단한 후보는 저장하지 않습니다.'};
$('#target').oninput=()=>{$('#target-value').textContent=$('#target').value+'°'};
$('#run').onclick=()=>{if(animation){stopMotion();return}if(!policy||!robot())return;stopMotion();resetView();let state={q:0,v:0},last=performance.now(),accumulator=0;
  const tick=now=>{accumulator+=Math.min((now-last)/1000,.05);last=now;while(accumulator>=1/60){state=advance(state,Number($('#target').value)/20,policy.weights);accumulator-=1/60}robot().setJoint('jaw',state.q*20*Math.PI/180);animation=requestAnimationFrame(tick)};$('#run').textContent='실행 중지';animation=requestAnimationFrame(tick)};
$('#export').onclick=()=>{if(!policy)return;const url=URL.createObjectURL(new Blob([JSON.stringify(policy,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='micro-x-virtual-jaw-policy.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
$('#import').onchange=async e=>{const file=e.target.files[0];if(!file)return;
  try{if(file.size>1024*1024)throw Error('정책 파일은 1 MB 이하여야 합니다.');const data=JSON.parse(await file.text());const weights=validatePolicy(data);stopMotion();policy={schema:data.schema,environment:data.environment,algorithm:data.algorithm,joint:data.joint,angleRangeDegrees:[0,20],weights,heldout:evaluate(weights,true),hardwareValidated:false};history=[];graph();$('#evaluation-jaw').textContent=policy.heldout.rmseDegrees.toFixed(2)+'°';$('#run').disabled=!robot();$('#export').disabled=false;$('#training-status').textContent='정책을 불러오고 이 브라우저에서 다시 평가했어요.'}catch(error){$('#training-status').textContent=error.message}finally{e.target.value=''}};

// ---------------------------------------------------------------- voice tab
$('#speak').onclick=()=>{stopMotion();if(!('speechSynthesis'in window)){$('#voice-status').textContent='이 브라우저는 음성 합성을 지원하지 않습니다.';return}
  const text=$('#speech').value.trim();if(!text){$('#voice-status').textContent='읽을 문장을 입력해 주세요.';return}resetView();utterance=new SpeechSynthesisUtterance(text);utterance.lang='ko-KR';
  utterance.onstart=()=>{$('#voice-status').textContent='문장을 읽고 있어요. 턱은 표현용으로 움직입니다.';const tick=t=>{if(robot())robot().setJoint('jaw',(.12+.1*Math.sin(t*.017)));animation=requestAnimationFrame(tick)};animation=requestAnimationFrame(tick)};
  utterance.onend=()=>{stopMotion();$('#voice-status').textContent='읽기를 마쳤어요.'};utterance.onerror=()=>{stopMotion();$('#voice-status').textContent='음성을 재생하지 못했어요. 브라우저 음성 설정을 확인해 주세요.'};window.speechSynthesis.speak(utterance)};
$('#silence').onclick=()=>{stopMotion();$('#voice-status').textContent='음성 재생을 멈췄어요.'};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopMotion()});
window.addEventListener('pagehide',()=>{worker?.terminate();stopMotion()});
window.microXLab={get policy(){return policy},get robot(){return robot()},get view(){return view},get replay(){return replay}};
