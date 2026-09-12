import {spawn} from 'node:child_process';import puppeteer from 'puppeteer';import assert from 'node:assert/strict';
const server=spawn('.venv-policy/bin/python',['runtime/training_service.py','--port','5213'],{stdio:'ignore'});const base='http://127.0.0.1:5213';let browser;let checks=0;
try{
  for(let i=0;i<80;i++){try{if((await fetch(base+'/api/status')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
  const post=(path,data,origin=base)=>fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json',Origin:origin},body:JSON.stringify(data)});
  assert.equal((await post('/api/train',{updates:1,steps:32,seed:42},'https://example.com')).status,403);checks++;
  assert.equal((await post('/api/train',{updates:100000,steps:32,seed:42})).status,400);checks++;
  assert.equal((await post('/api/train',{updates:1,steps:32,seed:42,name:'../x'})).status,400);checks++;
  assert.equal((await fetch(base+'/.git/config')).status,404);checks++;
  assert.equal((await fetch(base+'/README.md',{method:'HEAD'})).status,405);checks++;
  assert.equal((await fetch(base+'/api/evaluation/nothing')).status,404);checks++;
  browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH,args:['--no-sandbox','--enable-unsafe-swiftshader']});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewport({width:1280,height:900});await page.goto(base+'/web/lab.html#studio');await page.waitForFunction(()=>window.microXLab?.robot&&!document.querySelector('#ppo-start').disabled,{timeout:60000});
  // Real PPO job through the studio UI, with live progress and a named checkpoint.
  await page.$eval('#ppo-name',e=>e.value='ui_smoke');await page.$eval('#ppo-updates',e=>e.value=2);await page.$eval('#ppo-steps',e=>e.value=64);await page.click('#ppo-start');
  await page.waitForFunction(()=>document.querySelector('#ppo-status').textContent.includes('completed'),{timeout:120000});checks++;
  await page.waitForFunction(()=>[...document.querySelectorAll('.ckpt b')].some(b=>b.textContent==='ui_smoke.onnx'),{timeout:10000});checks++;
  const checkpoint=await fetch(base+'/api/checkpoint?name=ui_smoke');assert.equal(checkpoint.status,200);assert.ok((await checkpoint.arrayBuffer()).byteLength>100000);checks++;
  // Evaluate the new checkpoint with the shared protocol and read the table.
  await page.evaluate(()=>[...document.querySelectorAll('.ckpt')].find(r=>r.querySelector('b').textContent==='ui_smoke.onnx').querySelector('button').click());
  await page.waitForFunction(()=>document.querySelector('#ppo-status').textContent.includes('completed')&&document.querySelector('#evaluation table'),{timeout:180000});
  const rows=await page.$$eval('#evaluation tbody tr',r=>r.length);assert.equal(rows,8);checks++;
  const evaluation=await(await fetch(base+'/api/evaluation/ui_smoke')).json();assert.equal(evaluation.results.length,8);assert.ok(evaluation.custom_walking_sha256);checks++;
  // Simulator can select the trained checkpoint.
  const started=await(await post('/api/sim/start',{seed:0,policy:'ui_smoke.onnx'})).json();assert.equal(started.policy,'ui_smoke.onnx');assert.equal(started.qpos.length,22);checks++;
  await page.screenshot({path:'artifacts/compat_workbench.png',fullPage:true});
  // Concurrency and cancellation.
  assert.equal((await post('/api/train',{updates:100,steps:512,seed:42,name:'cancel_me'})).status,202);assert.equal((await post('/api/train',{updates:1,steps:32,seed:42})).status,409);await post('/api/stop',{});
  for(let i=0;i<60;i++){const state=await(await fetch(base+'/api/status')).json();if(state.status==='cancelled'&&state.exit_code!==undefined)break;await new Promise(r=>setTimeout(r,100));}
  assert.equal((await(await fetch(base+'/api/status')).json()).status,'cancelled');checks++;assert.deepEqual(errors,[]);checks++;
  console.log(`${checks} local studio checks passed: origin/path guards, real PPO job with named checkpoint, ONNX download, shared evaluation table, simulator policy selection, cancel`);
}finally{await browser?.close();server.kill();}
