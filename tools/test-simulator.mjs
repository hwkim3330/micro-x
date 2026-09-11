import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import path from 'node:path';
import puppeteer from 'puppeteer';
const root=path.resolve(import.meta.dirname,'..');
const server=spawn(path.join(root,'.venv-policy/bin/python'),['runtime/training_service.py','--port','5217'],{cwd:root,stdio:'ignore'});
let browser;let checks=0;
try{
  for(let n=0;n<100;n++){try{if((await fetch('http://127.0.0.1:5217/api/status')).ok)break}catch{}await new Promise(r=>setTimeout(r,100))}
  const api=async(endpoint,data,headers={})=>fetch('http://127.0.0.1:5217'+endpoint,{method:'POST',headers:{'Content-Type':'application/json',...headers},body:JSON.stringify(data)});
  assert.equal((await api('/api/sim/start',{seed:0},{Origin:'https://example.com'})).status,403);checks++;
  assert.equal((await api('/api/sim/start',{seed:-1})).status,400);checks++;
  browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--enable-unsafe-swiftshader']});
  const page=await browser.newPage();await page.setViewport({width:1200,height:900});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('http://127.0.0.1:5217/web/simulator.html');await page.waitForFunction(()=>window.microXSimulation?.state&&!document.querySelector('#sim-reset').disabled);
  assert.equal(await page.$eval('#sim-toggle',b=>b.disabled),true);checks++;
  await page.click('#sim-reset');await page.waitForFunction(()=>!document.querySelector('#sim-toggle').disabled);
  const initial=await page.evaluate(()=>microXSimulation.state);
  assert.ok(initial.geometries.length>14);assert.equal(initial.time,0);checks+=2;
  assert.equal((await api('/api/sim/step',{session:initial.session,steps:100,command:[0,0,0]})).status,400);checks++;
  assert.equal((await api('/api/sim/step',{session:initial.session,steps:5,command:[99,0,0]})).status,400);checks++;
  assert.equal((await api('/api/sim/step',{session:'stale',steps:5,command:[0,0,0]})).status,409);checks++;
  await page.click('#sim-toggle');await page.keyboard.down('ArrowUp');
  await page.waitForFunction(()=>microXSimulation.state.time>=3,{timeout:30000});await page.keyboard.up('ArrowUp');await page.click('#sim-toggle');
  const moved=await page.evaluate(()=>microXSimulation.state);assert.ok(moved.position[0]>.005);assert.ok(moved.time>=3);checks+=2;
  await new Promise(r=>setTimeout(r,400));const paused=await page.evaluate(()=>microXSimulation.state.time);await new Promise(r=>setTimeout(r,400));assert.equal(await page.evaluate(()=>microXSimulation.state.time),paused);checks++;
  await page.screenshot({path:path.join(root,'artifacts/simulator_desktop.png')});
  await page.setViewport({width:390,height:844});await new Promise(r=>setTimeout(r,300));assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
  await page.click('#sim-reset');await page.waitForFunction(()=>microXSimulation.state.time===0);checks++;
  await page.screenshot({path:path.join(root,'artifacts/simulator_mobile.png')});assert.deepEqual(errors,[]);checks++;
  console.log(`${checks} live simulator checks passed: real time/position advance, pause, reset, commands, sessions, origins, desktop/mobile`);
}finally{await browser?.close();server.kill()}
