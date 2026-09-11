import {spawn} from 'node:child_process';import puppeteer from 'puppeteer';import assert from 'node:assert/strict';
const server=spawn('.venv-policy/bin/python',['runtime/training_service.py','--port','5213'],{stdio:'ignore'});const base='http://127.0.0.1:5213';let browser;
try{
  for(let i=0;i<80;i++){try{if((await fetch(base+'/api/status')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
  const post=(path,data,origin=base)=>fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json',Origin:origin},body:JSON.stringify(data)});
  assert.equal((await post('/api/train',{updates:1,steps:32,seed:42},'https://example.com')).status,403);
  assert.equal((await post('/api/train',{updates:100000,steps:32,seed:42})).status,400);
  assert.equal((await fetch(base+'/.git/config')).status,404);
  assert.equal((await fetch(base+'/README.md',{method:'HEAD'})).status,405);
  browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--enable-unsafe-swiftshader']});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewport({width:1280,height:900});await page.goto(base+'/web/lab.html');await page.waitForFunction(()=>document.querySelector('#ppo-start')?.disabled===false);
  await page.$eval('#ppo-updates',e=>e.value=3);await page.$eval('#ppo-steps',e=>e.value=128);await page.click('#ppo-start');await page.waitForFunction(()=>document.querySelector('#ppo-status').textContent.includes('completed'),{timeout:45000});assert.ok(await page.$eval('#ppo-download',e=>!e.hidden));
  const checkpoint=await fetch(base+'/api/checkpoint');assert.equal(checkpoint.status,200);assert.ok((await checkpoint.arrayBuffer()).byteLength>100000);
  await page.screenshot({path:'artifacts/compat_workbench.png',fullPage:true});
  assert.equal((await post('/api/train',{updates:100,steps:512,seed:42})).status,202);assert.equal((await post('/api/train',{updates:1,steps:32,seed:42})).status,409);await post('/api/stop',{});
  for(let i=0;i<40;i++){const state=await(await fetch(base+'/api/status')).json();if(state.status==='cancelled'&&state.exit_code!==undefined)break;await new Promise(r=>setTimeout(r,100));}
  assert.equal((await(await fetch(base+'/api/status')).json()).status,'cancelled');assert.deepEqual(errors,[]);
  console.log('Local 14-axis training UI, real PPO job, ONNX download, cancel, concurrency, origin and path checks passed');
}finally{await browser?.close();server.kill();}
