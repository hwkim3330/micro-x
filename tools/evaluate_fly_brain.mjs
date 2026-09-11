// Executes the pinned full Microfly graph from a separately downloaded reference.
// No reference robot assets or brain source are redistributed by this adapter.
import {readFile,writeFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'),reference=process.argv[2];
if(!reference)throw Error('Usage: node tools/evaluate_fly_brain.mjs /path/to/extracted/microfly-source');
const hashes={
  'src/brain-core.js':'34fe05716eabdb5d386c23f088bca486243492bf7a383ab7d85c5266a94fe4b3',
  'src/sensors.js':'bb6d3045f9fb7415050e9c37156fe26c6d7c64c79f28b1551155fdd918d4e4fb',
  'public/brain/connectome.bin.gz':'fbf8d440ca1207c7573e1acdd2366f9d0beb9b533c1710f21681264f81b1cc49',
  'public/brain/channels.json':'faf1490b965da1e69a5e8d0783882326c5a0b1e43571555cb2ab48f6757f5df7'
};
for(const [file,hash]of Object.entries(hashes))if(createHash('sha256').update(await readFile(path.join(reference,file))).digest('hex')!==hash)throw Error('Reference hash mismatch: '+file);
const {FlyBrain,NeuralDecoder}=await import(pathToFileURL(path.resolve(reference,'src/brain-core.js')));
const {encodeStimulus}=await import(pathToFileURL(path.resolve(reference,'src/sensors.js')));
const bytes=gunzipSync(await readFile(path.join(reference,'public/brain/connectome.bin.gz')));
const graph=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const channels=JSON.parse(await readFile(path.join(reference,'public/brain/channels.json'),'utf8'));
const server=spawn(path.join(root,'.venv-policy/bin/python'),['runtime/training_service.py','--port','5220'],{cwd:root,stdio:'ignore'});
const base='http://127.0.0.1:5220';
async function post(route,data){const r=await fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(!r.ok)throw Error(await r.text());return r.json()}
const results=[];
try{
  let ready=false;for(let i=0;i<100;i++){if(server.exitCode!==null)throw Error('Simulation server exited');try{ready=(await fetch(base+'/api/status')).ok}catch{}if(ready)break;await new Promise(r=>setTimeout(r,100))}if(!ready)throw Error('Server not ready');
  for(const condition of ['left','right','no_scent','cut_synapses','disconnected']){
    const brain=new FlyBrain(graph,channels,{seed:23}),decoder=new NeuralDecoder();
    let state=await post('/api/sim/start',{seed:10});const frames=[];
    for(let i=0;i<100;i++){
      const [w,x,y,z]=state.quaternion_wxyz;
      const pose={x:state.position[0],y:state.position[1],yaw:Math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))};
      const scent=condition==='no_scent'?null:{x:.29,y:condition==='right'?-.58:.58};
      const activity=brain.advance(encodeStimulus(pose,scent,.45),10,{cutSynapses:condition==='cut_synapses'});
      const decoded=decoder.update(activity).command;
      const command=condition==='disconnected'?[0,0,0]:[decoded.forward,0,Math.max(-.5,Math.min(.5,decoded.turn))];
      state=await post('/api/sim/step',{session:state.session,steps:5,command});
      frames.push({time:state.time,position:state.position,command,neuralCommand:decoded,spikes:activity.spikes,descending:activity.left+activity.right,fallen:state.fallen});
      if(state.fallen)break;
    }
    const result={condition,neurons:brain.n,edges:brain.edges,model_sha256:state.model_sha256,final_position:state.position,duration_s:state.time,fallen:state.fallen,frames};results.push(result);
    console.log(condition,JSON.stringify({duration:state.time,position:state.position,fallen:state.fallen,lastCommand:frames.at(-1).command}));
  }
  const report={reference_revision:'89ba5406bb456a53b4fb6a14215216dd35a01d10',reference_hashes:hashes,scope:'Full supplied fly graph with engineered Microfly dynamics/decoder, closed-loop virtual scent from X pose, official walking ONNX and X MuJoCo/BAM. No biological learning or physical robot.',timing:'10 neural ticks per 0.1 simulation seconds; not calibrated biological time',turn_limit_rad_s:.5,control_hz:50,neural_weights_trained:false,navigation_accepted:false,physical_verified:false,results};
  await writeFile(path.join(root,'artifacts/fly_brain_x_evaluation.json'),JSON.stringify(report,null,2)+'\n');
}finally{server.kill()}
