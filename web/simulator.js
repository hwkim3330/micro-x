import * as THREE from 'three';
import {OrbitControls} from './vendor/three/controls/OrbitControls.js';
import {loadRobot,makeStage} from './rig.js';
const $=s=>document.querySelector(s),host=$('#simulation-view');
const {scene,camera,renderer}=makeStage(host,{grid:false});camera.position.set(.5,.32,.55);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,.14,0);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(6,6),new THREE.MeshStandardMaterial({color:0xe6e2d4,roughness:1}));floor.rotation.x=-Math.PI/2;scene.add(floor);scene.add(new THREE.GridHelper(4,40,0xd2cdbd,0xe0dccd));
let robot,state,ready=false,running=false,version=0,timer,frameCount=0,replay=null,replayIndex=0,replayTimer;
const pressed=new Set();
function pose(qpos){robot.setPose(qpos);const t=new THREE.Vector3(qpos[0],.14,-qpos[1]);camera.position.add(t.clone().sub(controls.target));controls.target.copy(t);controls.update();renderer.render(scene,camera)}
function draw(data){state=data;pose(data.qpos);$('#sim-metrics').textContent=`물리 시간 ${data.time.toFixed(2)}초 · X ${data.position[0].toFixed(3)}m · Y ${data.position[1].toFixed(3)}m · 정책 ${data.policy||'official'} · ${data.fallen?'넘어짐 감지':'계산 중인 자세'}`;frameCount++}
async function post(path,data){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw Error(result.error||'시뮬레이션 오류');return result}
function pause(){running=false;version++;clearTimeout(timer);pressed.clear();$('#sim-toggle').textContent='실행'}
async function loop(token){if(!running||token!==version)return;const start=performance.now();
  try{const command=[(pressed.has('forward')?.3:0)-(pressed.has('back')?.3:0),0,(pressed.has('left')?.3:0)-(pressed.has('right')?.3:0)];const result=await post('/api/sim/step',{session:state.session,command,steps:5});if(token!==version)return;draw(result);if(result.fallen){pause();$('#sim-status').textContent='넘어짐을 감지해 멈췄습니다. 초기화 후 다시 시험하세요.';return}timer=setTimeout(()=>loop(token),Math.max(0,100-(performance.now()-start)))}catch(e){pause();$('#sim-status').textContent=e.message}}
function stopReplay(){clearInterval(replayTimer);replayTimer=null;$('#replay-toggle').textContent='기록 재생'}
$('#replay-toggle').onclick=()=>{if(replayTimer){stopReplay();return}if(!replay||!robot)return;pause();replayIndex=0;$('#replay-toggle').textContent='재생 중지';replayTimer=setInterval(()=>{if(replayIndex>=replay.qpos.length)replayIndex=0;pose(replay.qpos[replayIndex]);$('#sim-metrics').textContent=`기록 재생 ${(replayIndex*replay.dt).toFixed(2)}초 · 공식 가중치 · 명령 ${replay.result.command.join(', ')}`;replayIndex++},replay.dt*1000)};
$('#sim-reset').onclick=async()=>{pause();stopReplay();$('#sim-reset').disabled=true;try{draw(await post('/api/sim/start',{seed:0,policy:$('#sim-policy').value}));ready=true;$('#sim-toggle').disabled=false;document.querySelectorAll('[data-drive]').forEach(b=>b.disabled=false);$('#sim-status').textContent='실제 물리 계산 준비 완료 · 실행을 눌러 조작하세요.'}catch(e){$('#sim-status').textContent=e.message}finally{$('#sim-reset').disabled=false}};
$('#sim-toggle').onclick=()=>{if(running){pause();$('#sim-status').textContent='물리 시간 일시정지'}else if(ready&&!state.fallen){stopReplay();running=true;$('#sim-toggle').textContent='일시정지';$('#sim-status').textContent='MuJoCo + BAM + ONNX 실행 중 · 새 CAD에서 생성한 14축 모델';loop(++version)}};
document.querySelectorAll('[data-drive]').forEach(b=>{b.onpointerdown=e=>{b.setPointerCapture(e.pointerId);pressed.add(b.dataset.drive)};b.onpointerup=b.onpointercancel=b.onlostpointercapture=()=>pressed.delete(b.dataset.drive)});
const keys={ArrowUp:'forward',ArrowDown:'back',ArrowLeft:'left',ArrowRight:'right'};
addEventListener('keydown',e=>{if(running&&keys[e.key]&&!['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)){e.preventDefault();pressed.add(keys[e.key])}});addEventListener('keyup',e=>pressed.delete(keys[e.key]));addEventListener('blur',()=>pressed.clear());addEventListener('pagehide',()=>{pause();stopReplay()});document.addEventListener('visibilitychange',()=>{if(document.hidden){pause();stopReplay()}});
controls.addEventListener('change',()=>renderer.render(scene,camera));new ResizeObserver(()=>renderer.render(scene,camera)).observe(host);
try{robot=await loadRobot('../');scene.add(robot.root);renderer.render(scene,camera);
  try{const r=await fetch('../artifacts/compat_replay.json',{cache:'no-store'});if(!r.ok)throw Error();replay=await r.json();$('#replay-toggle').disabled=false;$('#sim-status').textContent='공개 페이지: 공식 가중치로 계산한 보행 기록을 실제 CAD 위에 재생합니다. 실시간 조작은 로컬 서버에서 가능합니다.'}catch{$('#sim-status').textContent='보행 기록을 불러오지 못했습니다.'}
}catch(e){$('#sim-status').textContent='모델을 불러오지 못했습니다.';console.error(e)}
async function refreshPolicies(){try{const r=await fetch('/api/checkpoints',{cache:'no-store'});if(!r.ok)return;const data=await r.json();const sel=$('#sim-policy');sel.replaceChildren(new Option('공식 alpha_walking','official'));for(const c of data.checkpoints)sel.append(new Option(`학습 체크포인트 ${c.file}`,c.file))}catch{}}
if(['localhost','127.0.0.1'].includes(location.hostname)){try{const r=await fetch('/api/status');if(r.ok){$('#sim-reset').disabled=false;$('#sim-policy').disabled=false;await refreshPolicies();$('#sim-status').textContent='로컬 서버 연결됨 · 정책을 고르고 초기화를 눌러 실제 시뮬레이션을 준비하세요.'}}catch{}}
window.microXSimulation={get state(){return state},get running(){return running},get frameCount(){return frameCount},get robot(){return robot}};
