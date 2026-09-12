import http from 'node:http';import {readFile} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import puppeteer from 'puppeteer';
const root=path.resolve(import.meta.dirname,'..'),mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.png':'image/png','.pdf':'application/pdf','.wav':'audio/wav','.xml':'application/xml'};
const server=http.createServer(async(req,res)=>{try{let p=decodeURIComponent(req.url.split('?')[0]);if(p.endsWith('/'))p+='index.html';const file=path.join(root,p);if(!file.startsWith(root+path.sep))throw Error();const data=await readFile(file);res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream'});res.end(data)}catch{res.writeHead(404);res.end()}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;
const browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH,args:['--no-sandbox','--enable-unsafe-swiftshader']});let checks=0;
try{for(const [name,width,height]of[['desktop',1440,1000],['mobile',390,844]]){const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewport({width,height});await page.goto(base+'/web/');await page.waitForFunction(()=>window.microX,{timeout:60000});await page.addStyleTag({content:'html {scroll-behavior:auto !important}'});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
assert.equal(await page.evaluate(()=>window.microX.robot.meshes.length),await page.evaluate(()=>window.microX.robot.parts.parts.length+window.microX.robot.parts.purchased.length));checks++;
assert.equal(await page.$eval('#servo-count',e=>e.textContent),'15');checks++;
await page.screenshot({path:path.join(root,'artifacts',`web_${name}.png`)});
await page.click('#explode');assert.ok(await page.evaluate(()=>window.microX.robot.meshes.some(m=>!m.position.equals(m.userData.base))));checks++;
await page.click('#explode');assert.ok(await page.evaluate(()=>window.microX.robot.meshes.every(m=>m.position.equals(m.userData.base))));checks++;
await page.$eval('#joints input[data-joint="left_knee"]',e=>{e.value=30;e.dispatchEvent(new Event('input'))});assert.ok(await page.evaluate(()=>Math.abs(window.microX.robot.joints.left_knee.angle-window.microX.robot.joints.left_knee.home-Math.PI/6)<1e-6));checks++;
await page.select('#layer','shell');assert.ok(await page.evaluate(()=>window.microX.robot.meshes.filter(m=>m.visible).every(m=>window.microX.robot.info[m.name].group==='shell')));checks++;
await page.select('#layer','all');
await page.waitForFunction(()=>!document.querySelector('#replay-toggle').disabled,{timeout:30000});await page.click('#replay-toggle');await page.waitForFunction(()=>window.microX.playing);await new Promise(r=>setTimeout(r,400));assert.ok(await page.evaluate(()=>Math.abs(window.microX.robot.joints.left_hip_pitch.angle-window.microX.robot.joints.left_hip_pitch.home)>1e-4||Math.abs(window.microX.robot.bodies.trunk.position.x)>1e-4));checks++;
await page.click('#replay-toggle');assert.ok(await page.evaluate(()=>!window.microX.playing));checks++;
await page.click('#parts button');assert.ok(await page.$eval('#selection',e=>e.textContent.includes('STEP')||e.textContent.includes('구매품')));checks++;
await page.click('#reset');assert.ok(await page.evaluate(()=>Math.abs(window.microX.robot.joints.left_knee.angle-window.microX.robot.joints.left_knee.home)<1e-9));checks++;
assert.equal(await page.$eval('#cost-result',e=>e.textContent),'$'+((15*27.49+110+45)/.95).toFixed(2));checks++;
await page.$eval('#yield',e=>{e.value=0;e.dispatchEvent(new Event('input'))});assert.equal(await page.$eval('#cost-result',e=>e.textContent),'입력 확인');checks++;
const links=await page.$$eval('a[href^="../"]',links=>[...new Set(links.map(a=>a.href))]);for(const url of links){assert.equal((await fetch(url)).status,200,url);checks++}
assert.deepEqual(errors,[]);checks++;await page.close()}
console.log(`${checks} browser and download checks passed`)}finally{await browser.close();server.close()}
