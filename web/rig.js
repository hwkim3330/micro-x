// MIT. Shared loader that turns models/micro_x.glb + models/rig.json into a poseable robot.
import * as THREE from 'three';
import {GLTFLoader} from './vendor/three/loaders/GLTFLoader.js';

export async function loadRobot(base='../'){
  const [rig,parts,gltf]=await Promise.all([
    fetch(base+'models/rig.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('rig '+r.status);return r.json()}),
    fetch(base+'artifacts/parts.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('parts '+r.status);return r.json()}),
    new GLTFLoader().loadAsync(base+'models/micro_x.glb')]);
  const root=new THREE.Group();root.name='micro_x';
  // GLB is Z-up (CAD frame); three.js is Y-up. Keep the CAD frame inside `robot` and tilt the wrapper.
  const robot=gltf.scene;root.add(robot);root.rotation.x=-Math.PI/2;
  const bodies={};robot.traverse(o=>{if(rig.bodies.some(b=>b.name===o.name))bodies[o.name]=o});
  const meshes=[];robot.traverse(o=>{if(o.isMesh){o.name=o.name.replace(/^mesh_/,'');o.material=o.material.clone();o.material.metalness=0;o.material.roughness=o.name.startsWith('eye_')?.15:o.name.startsWith('servo_')?.45:.6;o.material.vertexColors=true;o.userData.base=o.position.clone();meshes.push(o)}});
  const info={};for(const p of parts.parts)info[p.name]=p;for(const p of parts.purchased)info[p.name]=p;
  const joints={};for(const b of rig.bodies){if(!b.joint)continue;joints[b.joint]={body:b.name,node:bodies[b.name],axis:new THREE.Vector3(...b.axis),home:b.home_rad,angle:b.home_rad}}
  const trunk=bodies[rig.root];
  function setJoint(name,angle){const j=joints[name];if(!j)return;j.angle=angle;j.node.quaternion.setFromAxisAngle(j.axis,angle-j.home)}
  function setPose(qpos){ // MuJoCo qpos: free joint (x y z qw qx qy qz) then joints in rig.qpos_layout order
    const [x,y,z,qw,qx,qy,qz]=qpos;trunk.position.set(x,y,z);trunk.quaternion.set(qx,qy,qz,qw);
    rig.qpos_layout.joints.forEach((name,i)=>setJoint(name,qpos[7+i]))
  }
  function home(){trunk.position.set(...rig.root_position_m);trunk.quaternion.identity();for(const name in joints)setJoint(name,joints[name].home)}
  function explode(on){for(const m of meshes){m.position.copy(m.userData.base);if(!on)continue;const p=info[m.name];if(!p)continue;const d=new THREE.Vector3(0,0,0);if(p.group==='shell'){if(m.name.startsWith('eye_'))d.y=m.name.endsWith('left')?.04:-.04;else if(m.name==='skull')d.z=.05;else if(m.name==='jaw_beak')d.z=-.04;else if(m.name==='torso_shell')d.z=.06;else if(m.name==='chest_panel')d.x=.05;else if(m.name==='tail_cover')d.x=-.05;else if(m.name.includes('foot'))d.z=-.03}else if(!p.printed){d.y=m.name.includes('right')?-.03:m.name.includes('left')?.03:0;if(m.name==='battery_np_f550')d.x=-.03;if(m.name==='compute_board')d.x=.03}m.position.add(d)}}
  function setVisible(filter){for(const m of meshes){const p=info[m.name];m.visible=!p||filter(p)}}
  home();
  return {root,robot,rig,parts,info,meshes,bodies,joints,setJoint,setPose,home,explode,setVisible};
}

export function makeStage(el,opts={}){
  const scene=new THREE.Scene();scene.background=new THREE.Color(opts.background||'#f0eee4');
  const camera=new THREE.PerspectiveCamera(opts.fov||32,1,.001,10);camera.position.set(.34,.27,.46);
  const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;el.append(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xffffff,0x8a7a60,2.6));const key=new THREE.DirectionalLight(0xfff2dc,3);key.position.set(1,2,1.5);scene.add(key);const fill=new THREE.DirectionalLight(0xdbe6ff,1.2);fill.position.set(-1,1,-1);scene.add(fill);
  if(opts.grid!==false)scene.add(new THREE.GridHelper(.8,16,0xc9c4b4,0xe2ded0));
  const resize=()=>{renderer.setSize(el.clientWidth,el.clientHeight);camera.aspect=el.clientWidth/Math.max(1,el.clientHeight);camera.updateProjectionMatrix()};new ResizeObserver(resize).observe(el);resize();
  return {scene,camera,renderer};
}
export const CAMERAS={hero:[.34,.27,.46],front:[.62,.16,0],side:[0,.16,.62],back:[-.6,.2,.1],top:[0,.7,.01],face:[.28,.26,.12]};
