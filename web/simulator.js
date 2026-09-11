import * as THREE from 'three';
import {OrbitControls} from './vendor/three/controls/OrbitControls.js';
const $=s=>document.querySelector(s),host=$('#simulation-view');
const scene=new THREE.Scene();scene.background=new THREE.Color('#f0eee4');
const camera=new THREE.PerspectiveCamera(40,1,.005,20);camera.up.set(0,0,1);camera.position.set(.38,-.45,.30);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(.02,0,.13);
scene.add(new THREE.HemisphereLight(0xffffff,0x476452,2.5));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(1,-1,2);scene.add(light);
const meshes=[];let state,ready=false,running=false,version=0,timer,frameCount=0;
const pressed=new Set();
function draw(data){
  state=data;
  if(data.geometries){for(const m of meshes){scene.remove(m);m.geometry.dispose();m.material.dispose()}meshes.length=0;
    for(const g of data.geometries){const [x,y,z]=g.size;let geometry;
      if(g.type===0)geometry=new THREE.PlaneGeometry(6,6);
      else if(g.type===6)geometry=new THREE.BoxGeometry(2*x,2*y,2*z);
      else if(g.type===3){geometry=new THREE.CapsuleGeometry(x,2*y,6,14);geometry.rotateX(Math.PI/2)}
      else{geometry=new THREE.SphereGeometry(1,20,14);geometry.scale(x,g.type===4?y:x,g.type===4?z:x)}
      const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color:new THREE.Color(...g.rgba.slice(0,3)),roughness:.65}));scene.add(mesh);meshes.push(mesh);
    }
  }
  const mat=new THREE.Matrix4();data.transforms.forEach((t,i)=>{const r=t.rotation;mat.set(r[0],r[1],r[2],0,r[3],r[4],r[5],0,r[6],r[7],r[8],0,0,0,0,1);meshes[i].position.fromArray(t.position);meshes[i].quaternion.setFromRotationMatrix(mat)});
  const target=new THREE.Vector3(data.position[0]+.02,data.position[1],.13);
  camera.position.add(target.clone().sub(controls.target));controls.target.copy(target);controls.update();
  $('#sim-metrics').textContent=`물리 시간 ${data.time.toFixed(2)}초 · X ${data.position[0].toFixed(3)}m · Y ${data.position[1].toFixed(3)}m · ${data.fallen?'넘어짐 감지':'계산 중인 자세'}`;
  frameCount++;renderer.render(scene,camera);
}
async function post(path,data){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw Error(result.error||'시뮬레이션 오류');return result}
function pause(){running=false;version++;clearTimeout(timer);pressed.clear();$('#sim-toggle').textContent='실행'}
async function loop(token){if(!running||token!==version)return;const start=performance.now();
  try{const command=[(pressed.has('forward')?.3:0)-(pressed.has('back')?.3:0),0,(pressed.has('left')?.3:0)-(pressed.has('right')?.3:0)];const result=await post('/api/sim/step',{session:state.session,command,steps:5});if(token!==version)return;draw(result);if(result.fallen){pause();$('#sim-status').textContent='넘어짐을 감지해 멈췄습니다. 초기화 후 다시 시험하세요.';return}timer=setTimeout(()=>loop(token),Math.max(0,100-(performance.now()-start)))}catch(e){pause();$('#sim-status').textContent=e.message}}
$('#sim-reset').onclick=async()=>{pause();$('#sim-reset').disabled=true;try{draw(await post('/api/sim/start',{seed:0}));ready=true;$('#sim-toggle').disabled=false;document.querySelectorAll('[data-drive]').forEach(b=>b.disabled=false);$('#sim-status').textContent='실제 물리 계산 준비 완료 · 실행을 눌러 조작하세요.'}catch(e){$('#sim-status').textContent=e.message}finally{$('#sim-reset').disabled=false}};
$('#sim-toggle').onclick=()=>{if(running){pause();$('#sim-status').textContent='물리 시간 일시정지'}else if(ready&&!state.fallen){running=true;$('#sim-toggle').textContent='일시정지';$('#sim-status').textContent='MuJoCo + BAM + 공식 ONNX 실행 중';loop(++version)}};
document.querySelectorAll('[data-drive]').forEach(b=>{b.onpointerdown=e=>{b.setPointerCapture(e.pointerId);pressed.add(b.dataset.drive)};b.onpointerup=b.onpointercancel=b.onlostpointercapture=()=>pressed.delete(b.dataset.drive)});
const keys={ArrowUp:'forward',ArrowDown:'back',ArrowLeft:'left',ArrowRight:'right'};
addEventListener('keydown',e=>{if(running&&keys[e.key]&&!['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)){e.preventDefault();pressed.add(keys[e.key])}});addEventListener('keyup',e=>pressed.delete(keys[e.key]));addEventListener('blur',()=>pressed.clear());addEventListener('pagehide',pause);document.addEventListener('visibilitychange',()=>{if(document.hidden)pause()});
controls.addEventListener('change',()=>renderer.render(scene,camera));new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer.render(scene,camera)}).observe(host);
try{const r=await fetch('../artifacts/simulation_preview.json');if(!r.ok)throw Error();draw(await r.json());$('#sim-status').textContent='정지 미리 보기 · 실제 조작은 로컬 학습 서버에서 가능합니다.'}catch{$('#sim-status').textContent='정지 모델을 불러오지 못했습니다.'}
if(['localhost','127.0.0.1'].includes(location.hostname)){try{const r=await fetch('/api/status');if(r.ok){$('#sim-reset').disabled=false;$('#sim-status').textContent='로컬 서버 연결됨 · 초기화를 눌러 실제 시뮬레이션을 준비하세요.'}}catch{}}
window.microXSimulation={get state(){return state},get running(){return running},get frameCount(){return frameCount},meshes};
