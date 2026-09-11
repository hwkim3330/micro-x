// Headless CPU benchmark. Run this unchanged on each proposed physical board.
import {readFile,writeFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import os from 'node:os';
const reference=path.resolve(process.argv[2]??'');
if(!process.argv[2])throw Error('Usage: node tools/benchmark_brain.mjs REFERENCE_DIR [OUTPUT_JSON]');
const expected={
 'src/brain-core.js':'34fe05716eabdb5d386c23f088bca486243492bf7a383ab7d85c5266a94fe4b3',
 'public/brain/connectome.bin.gz':'fbf8d440ca1207c7573e1acdd2366f9d0beb9b533c1710f21681264f81b1cc49',
 'public/brain/channels.json':'faf1490b965da1e69a5e8d0783882326c5a0b1e43571555cb2ab48f6757f5df7'
};
for(const [file,hash] of Object.entries(expected))if(createHash('sha256').update(await readFile(path.join(reference,file))).digest('hex')!==hash)throw Error('Unexpected reference: '+file);
const {FlyBrain}=await import(pathToFileURL(path.join(reference,'src/brain-core.js')));
const bytes=gunzipSync(await readFile(path.join(reference,'public/brain/connectome.bin.gz')));
const brain=new FlyBrain(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),JSON.parse(await readFile(path.join(reference,'public/brain/channels.json'),'utf8')));
const samples=[];
for(let i=0;i<330;i++){
 const start=performance.now();
 brain.advance({visual_left:.3,visual_right:.3,olfactory_left:.4,olfactory_right:.1},10);
 if(i>=30)samples.push(performance.now()-start);
}
samples.sort((a,b)=>a-b);
const percentile=p=>samples[Math.ceil(p*samples.length)-1];
const report={scope:'Headless full graph CPU benchmark, 10 neural ticks/update, 30 warmup + 300 timed updates. No renderer, camera, motor I/O or concurrent workload; not physical robot validation.',host:{arch:os.arch(),cpu:os.cpus()[0].model,node:process.version,platform:os.platform()},reference_hashes:expected,neurons:brain.n,edges:brain.edges,latency_ms:{p50:percentile(.5),p95:percentile(.95),p99:percentile(.99),max:samples.at(-1)},updates_over_100ms:samples.filter(x=>x>100).length,peak_rss_bytes:process.resourceUsage().maxRSS*1024,board_qualified:false};
console.log(JSON.stringify(report,null,2));
if(process.argv[3])await writeFile(process.argv[3],JSON.stringify(report,null,2)+'\n');
