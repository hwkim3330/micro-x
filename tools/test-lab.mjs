import puppeteer from 'puppeteer';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
import {spawn} from 'node:child_process';
const root=path.resolve(import.meta.dirname,'..'),directory=await mkdtemp(path.join(os.tmpdir(),'micro-x-lab-'));
const server=spawn('python3',['-m','http.server','5197','--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});
let browser;let checks=0;
try{
  for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:5197/web/lab.html')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
  browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH,args:['--no-sandbox','--enable-unsafe-swiftshader']});
  for(const [name,width,height]of [['desktop',1440,1100],['mobile',390,844]]){
    const page=await browser.newPage(),errors=[],missing=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!/\/api\//.test(r.url()))missing.push(r.status()+' '+r.url())});await page.setViewport({width,height});await page.goto('http://127.0.0.1:5197/web/lab.html');await page.waitForFunction(()=>window.microXLab?.robot,{timeout:60000});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
    await page.select('#layer','purchased');assert.equal(await page.evaluate(()=>window.microXLab.robot.meshes.filter(m=>m.visible).length),await page.evaluate(()=>window.microXLab.robot.parts.purchased.length));checks++;
    await page.select('#layer','shell');await page.click('#part-list button');assert.ok(await page.$eval('#part-detail',e=>e.textContent.includes('STEP')));checks++;
    await page.click('#reset-view');assert.equal(await page.evaluate(()=>window.microXLab.robot.meshes.filter(m=>m.visible).length),await page.evaluate(()=>window.microXLab.robot.parts.parts.length+window.microXLab.robot.parts.purchased.length));checks++;
    // Studio tab shows the recorded evidence cards without a local server.
    await page.click('#tab-studio');await page.waitForFunction(()=>/시험/.test(document.querySelector('#card-official').textContent));assert.ok(await page.$eval('#ppo-start',e=>e.disabled));checks++;
    // Replay tab plays the recorded qpos on the real CAD rig.
    await page.click('#tab-replay');await page.waitForFunction(()=>!document.querySelector('#replay-play').disabled,{timeout:30000});await page.click('#replay-play');await new Promise(r=>setTimeout(r,500));
    assert.ok(await page.evaluate(()=>[...document.querySelectorAll('#joint-readout div')].some(d=>/-?\d+\.\d°/.test(d.textContent))));checks++;
    await page.click('#replay-stop');assert.ok(await page.evaluate(()=>Math.abs(window.microXLab.robot.joints.left_knee.angle-window.microXLab.robot.joints.left_knee.home)<1e-9));checks++;
    // 1-axis teaching tab still trains, replays, exports and imports.
    await page.click('#tab-learn');await page.click('#train');await page.waitForFunction(()=>window.microXLab.policy,{timeout:30000});assert.ok(await page.evaluate(()=>window.microXLab.policy.heldout.rmseDegrees<4));checks++;
    await page.click('#run');await page.waitForFunction(()=>window.microXLab.robot.joints.jaw.angle>.01);await page.click('#run');assert.equal(await page.evaluate(()=>window.microXLab.robot.joints.jaw.angle),0);checks++;
    await page.screenshot({path:path.join(root,`artifacts/lab_${name}.png`),fullPage:true});
    const session=await page.createCDPSession();await session.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory});await page.click('#export');
    let downloaded;for(let i=0;i<50;i++){try{downloaded=JSON.parse(await readFile(path.join(directory,'micro-x-virtual-jaw-policy.json'),'utf8'));break;}catch{}await new Promise(r=>setTimeout(r,100));}assert.equal(downloaded.environment,'micro-x-virtual-jaw-v1');checks++;
    const good=path.join(directory,`policy-${name}.json`);await writeFile(good,JSON.stringify(downloaded));await(await page.$('#import')).uploadFile(good);await page.waitForFunction(()=>document.querySelector('#training-status').textContent.includes('다시 평가'));checks++;
    const bad=path.join(directory,'foreign.json');await writeFile(bad,JSON.stringify({...downloaded,environment:'microduck'}));await(await page.$('#import')).uploadFile(bad);await page.waitForFunction(()=>document.querySelector('#training-status').textContent.includes('가상 턱 정책 파일만'));
    await page.$eval('#generations',e=>e.value=100);await page.evaluate(()=>{document.querySelector('#train').click();document.querySelector('#stop').click();});assert.match(await page.$eval('#training-status',e=>e.textContent),/중지/);assert.ok(await page.$eval('#stop',e=>e.disabled));checks++;
    await page.click('#tab-voice');await page.$eval('#speech',e=>e.value='');await page.click('#speak');assert.match(await page.$eval('#voice-status',e=>e.textContent),/입력|지원/);checks++;
    assert.deepEqual(errors,[]);
    // A 404 is a broken page even when nothing throws: the lab shipped with a renamed
    // audio file and two artifacts that were never generated, and no test noticed.
    assert.deepEqual(missing,[],'requests that 404ed: '+missing.join(', '));checks++;checks++;await page.close();await rm(path.join(directory,'micro-x-virtual-jaw-policy.json'),{force:true});
  }
  console.log(`${checks} lab browser checks passed: anatomy, studio cards, replay, 1-axis training, download/import, rejection, stop, mobile layout`);
}finally{await browser?.close();server.kill();await rm(directory,{recursive:true,force:true});}
