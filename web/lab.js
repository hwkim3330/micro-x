import {advance,validatePolicy,evaluate} from './learning-core.js';
const $=s=>document.querySelector(s),frame=$('#robot');
let robot,worker,policy,history=[],animation=0,utterance,exploded=false;
const names={torso_lower:'아랫몸통',torso_upper:'윗몸통',hindleg_left:'왼쪽 다리',hindleg_right:'오른쪽 다리',foot_left:'왼발',foot_right:'오른발',neck_cradle:'목 받침',eye_left:'왼쪽 눈',eye_right:'오른쪽 눈',camera_carrier:'카메라 브래킷',skull:'머리 쉘',jaw:'턱',tail_left:'왼쪽 꼬리',tail_right:'오른쪽 꼬리',forearm_left:'왼쪽 앞팔',forearm_right:'오른쪽 앞팔'};
function stopMotion(){cancelAnimationFrame(animation);animation=0;window.speechSynthesis?.cancel();utterance=null;if(robot)robot.jawPivot.rotation.y=0;$('#run').textContent='정책 실행';}
function showPart(part){
  const detail=$('#part-detail');detail.replaceChildren();
  for(const [tag,text]of [['h3',names[part.name]||part.name],['p',`${part.dimensions_mm.join(' × ')} mm · PLA 재료 추정 ${part.mass_g} g`],['p',part.note]]){const e=document.createElement(tag);e.textContent=text;detail.append(e);}
  for(const [label,url]of [['STEP ↓',part.step],['STL ↓',part.stl]]){const a=document.createElement('a');a.textContent=label;a.href='../'+url;detail.append(a);}
}
function layer(){
  if(!robot)return;const selected=$('#layer').value;
  const matches=p=>selected==='all'||(selected==='head'?['head','jaw'].includes(p.group):selected==='torso'?['torso','neck','arms'].includes(p.group):selected==='camera'?p.name==='camera_carrier':p.group===selected);
  const list=$('#part-list');list.replaceChildren();
  for(const p of robot.parts){const mesh=robot.items.find(m=>m.name===p.name);mesh.visible=matches(p);if(!mesh.visible)continue;const b=document.createElement('button');b.textContent=names[p.name]||p.name;b.onclick=()=>{robot.inspect(mesh);showPart(p);};list.append(b);}
}
function resetView(){if(!robot)return;frame.contentDocument.querySelector('#reset').click();exploded=false;$('#explode').textContent='분해 보기';$('#layer').value='all';layer();robot.inspect(null);}
frame.addEventListener('load',()=>{
  let attempts=0;const timer=setInterval(()=>{
    robot=frame.contentWindow.microX;
    if(!robot){if(++attempts>150){clearInterval(timer);$('#viewer-status').textContent='모델을 불러오지 못했어요. 페이지를 새로 고쳐 주세요.';}return;}
    clearInterval(timer);$('#viewer-status').textContent=`실제 CAD · ${robot.parts.length}개 부품`;$('#explode').disabled=false;$('#reset-view').disabled=false;
    frame.contentWindow.addEventListener('microx-part',e=>showPart(e.detail));layer();if(policy)$('#run').disabled=false;
  },200);
});
$('#layer').onchange=layer;$('#reset-view').onclick=()=>{stopMotion();resetView();};
$('#explode').onclick=()=>{stopMotion();frame.contentDocument.querySelector('#explode').click();exploded=!exploded;$('#explode').textContent=exploded?'조립 보기':'분해 보기';};
const tabs=[...document.querySelectorAll('[data-tab]')];
for(const tab of tabs){tab.onclick=()=>{stopMotion();resetView();for(const b of tabs){const active=b===tab;b.setAttribute('aria-selected',active);b.tabIndex=active?0:-1;$('#'+b.dataset.tab).hidden=!active;}};tab.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const index=e.key==='Home'?0:e.key==='End'?tabs.length-1:(tabs.indexOf(tab)+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length;tabs[index].click();tabs[index].focus();};}
function graph(){const canvas=$('#loss'),c=canvas.getContext('2d'),w=canvas.width,h=canvas.height;c.clearRect(0,0,w,h);if(!history.length)return;const maximum=Math.max(...history.map(p=>p.loss),.0001);c.strokeStyle='#38734e';c.lineWidth=3;c.beginPath();history.forEach((p,i)=>{const x=20+i/Math.max(1,history.length-1)*(w-40),y=h-25-p.loss/maximum*(h-50);i?c.lineTo(x,y):c.moveTo(x,y);});c.stroke();c.fillStyle='#315542';c.font='16px sans-serif';c.fillText(`Loss ${history.at(-1).loss.toFixed(5)} · ${history.length} generations`,20,20);}
function busy(value){$('#train').disabled=value;$('#stop').disabled=!value;for(const id of ['generations','population','seed','import'])$('#'+id).disabled=value;}
$('#train').onclick=()=>{
  stopMotion();const settings=Object.fromEntries(['seed','generations','population'].map(id=>[id,Number($('#'+id).value)]));
  if(!['seed','generations','population'].every(id=>$('#'+id).value!==''&&$('#'+id).checkValidity()&&Number.isInteger(settings[id]))){$('#training-status').textContent='설정 범위 안의 정수를 입력해 주세요.';return;}
  worker?.terminate();history=[];graph();busy(true);$('#training-status').textContent='후보 정책을 평가하고 있어요…';
  try {worker=new Worker('./learning-worker.js',{type:'module'});}catch{$('#training-status').textContent='이 브라우저에서 학습 Worker를 시작할 수 없어요.';busy(false);return;}
  worker.onerror=()=>{$('#training-status').textContent='학습 실행 오류. 설정을 확인하고 다시 시작해 주세요.';worker.terminate();busy(false);};
  worker.onmessage=({data})=>{
    if(data.type==='progress'){history.push({generation:data.generation,loss:data.loss});graph();$('#training-status').textContent=`${data.generation} / ${settings.generations} 세대 · 학습 오차 ${data.rmseDegrees.toFixed(2)}°`;}
    if(data.type==='complete'){policy=data.policy;validatePolicy(policy);$('#evaluation').textContent=evaluate(policy.weights,true).rmseDegrees.toFixed(2)+'°';$('#training-status').textContent='학습 완료. 별도 목표에서 평가했어요. 정책을 실행하거나 저장해 보세요.';$('#export').disabled=false;$('#run').disabled=!robot;busy(false);worker.terminate();worker=null;}
    if(data.type==='error'){$('#training-status').textContent=data.message;busy(false);worker.terminate();worker=null;}
  };worker.postMessage(settings);
};
$('#stop').onclick=()=>{worker?.terminate();worker=null;busy(false);$('#training-status').textContent='학습을 중지했어요. 중단한 후보는 저장하지 않습니다.';};
$('#target').oninput=()=>{$('#target-value').textContent=$('#target').value+'°';};
$('#run').onclick=()=>{
  if(animation){stopMotion();return;}if(!policy||!robot)return;stopMotion();resetView();let state={q:0,v:0},last=performance.now(),accumulator=0;
  const tick=now=>{accumulator+=Math.min((now-last)/1000,.05);last=now;while(accumulator>=1/60){state=advance(state,Number($('#target').value)/20,policy.weights);accumulator-=1/60;}robot.jawPivot.rotation.y=state.q*20*Math.PI/180;animation=requestAnimationFrame(tick);};
  $('#run').textContent='실행 중지';animation=requestAnimationFrame(tick);
};
$('#export').onclick=()=>{if(!policy)return;const url=URL.createObjectURL(new Blob([JSON.stringify(policy,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='micro-x-virtual-jaw-policy.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('#import').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;
  try{if(file.size>1024*1024)throw Error('정책 파일은 1 MB 이하여야 합니다.');const data=JSON.parse(await file.text());const weights=validatePolicy(data);stopMotion();policy={schema:data.schema,environment:data.environment,algorithm:data.algorithm,joint:data.joint,angleRangeDegrees:[0,20],weights,heldout:evaluate(weights,true),hardwareValidated:false};history=[];graph();$('#evaluation').textContent=policy.heldout.rmseDegrees.toFixed(2)+'°';$('#run').disabled=!robot;$('#export').disabled=false;$('#training-status').textContent='정책을 불러오고 이 브라우저에서 다시 평가했어요.';}catch(error){$('#training-status').textContent=error.message;}finally{e.target.value='';}
};
$('#speak').onclick=()=>{
  stopMotion();if(!('speechSynthesis'in window)){$('#voice-status').textContent='이 브라우저는 음성 합성을 지원하지 않습니다.';return;}
  const text=$('#speech').value.trim();if(!text){$('#voice-status').textContent='읽을 문장을 입력해 주세요.';return;}resetView();utterance=new SpeechSynthesisUtterance(text);utterance.lang='ko-KR';
  utterance.onstart=()=>{$('#voice-status').textContent='문장을 읽고 있어요. 턱은 표현용으로 움직입니다.';const tick=t=>{if(robot)robot.jawPivot.rotation.y=(6+5*Math.sin(t*.017))*Math.PI/180;animation=requestAnimationFrame(tick);};animation=requestAnimationFrame(tick);};
  utterance.onend=()=>{stopMotion();$('#voice-status').textContent='읽기를 마쳤어요.';};utterance.onerror=()=>{stopMotion();$('#voice-status').textContent='음성을 재생하지 못했어요. 브라우저 음성 설정을 확인해 주세요.';};window.speechSynthesis.speak(utterance);
};
$('#silence').onclick=()=>{stopMotion();$('#voice-status').textContent='음성 재생을 멈췄어요.';};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopMotion();});
window.addEventListener('pagehide',()=>{worker?.terminate();stopMotion();});
window.microXLab={get policy(){return policy;},get robot(){return robot;}};
