import http from 'node:http';import {readFile} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import puppeteer from 'puppeteer';
const root=path.resolve(import.meta.dirname,'..'),mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.png':'image/png','.pdf':'application/pdf','.wav':'audio/wav'};
const server=http.createServer(async(req,res)=>{try{let p=decodeURIComponent(req.url.split('?')[0]);if(p.endsWith('/'))p+='index.html';const file=path.join(root,p);if(!file.startsWith(root+path.sep))throw Error();const data=await readFile(file);res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream'});res.end(data)}catch{res.writeHead(404);res.end()}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;
const browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox','--enable-unsafe-swiftshader']});let checks=0;
try{for(const [name,width,height]of[['desktop',1440,1000],['mobile',390,844]]){const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewport({width,height});await page.goto(base+'/web/');await page.waitForFunction(()=>window.microX,{timeout:30000});await page.addStyleTag({content:'html {scroll-behavior:auto !important}'});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
assert.ok(await page.evaluate(()=>window.microX.items.length===window.microX.parts.length));checks++;
await page.waitForFunction(()=>document.querySelector('#chirp').readyState>=1);assert.ok(await page.$eval('#chirp',e=>e.controls&&!e.autoplay&&Math.abs(e.duration-.65)<.01));checks++;
await page.screenshot({path:path.join(root,'artifacts',`web_${name}.png`)});
await page.click('#explode');assert.ok(await page.evaluate(()=>window.microX.items.some(m=>!m.position.equals(m.userData.base))));checks++;
await page.click('#explode');assert.ok(await page.evaluate(()=>window.microX.items.every(m=>m.position.equals(m.userData.base))));checks++;
await page.$eval('#jaw',e=>{e.value=15;e.dispatchEvent(new Event('input'))});assert.ok(await page.evaluate(()=>Math.abs(window.microX.jawPivot.rotation.y-Math.PI/12)<1e-9));checks++;
await page.click('#parts button');assert.ok(await page.$eval('#selection',e=>e.textContent.includes('STEP')));checks++;
await page.click('#reset');assert.equal(await page.$eval('#jaw-value',e=>e.textContent),'0°');checks++;
assert.equal(await page.$eval('#cost-result',e=>e.textContent),'$350.38');checks++;
await page.$eval('#yield',e=>{e.value=0;e.dispatchEvent(new Event('input'))});assert.equal(await page.$eval('#cost-result',e=>e.textContent),'입력 확인');checks++;
assert.equal(await page.$$eval('#variant option',e=>e.length),1);checks++;
assert.equal(await page.evaluate(()=>window.microX.items.filter(m=>m.name.includes('hindleg')).length),2);checks++;
const qlinks=await page.$$eval('a[href^="../"]',links=>[...new Set(links.map(a=>a.href))]);for(const url of qlinks){assert.equal((await fetch(url)).status,200,url);checks++}
await page.goto(base+'/web/?model=q4');await page.waitForFunction(()=>window.microX?.variant==='b2');assert.equal(await page.$eval('#part-count',e=>e.textContent),'16');assert.ok(page.url().includes('model=b2'));checks++;
assert.deepEqual(errors,[]);checks++;await page.close()}
const page=await browser.newPage();await page.goto(base+'/web/');await page.waitForFunction(()=>window.microX);const links=await page.$$eval('a[href^="../"]',links=>[...new Set(links.map(a=>a.href))]);for(const url of links){const response=await fetch(url);assert.equal(response.status,200,url);checks++}await page.close();console.log(`${checks} browser and download checks passed`)}finally{await browser.close();server.close()}
