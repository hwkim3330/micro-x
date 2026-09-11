// Run the separately installed official simulator on localhost:5178 first.
import puppeteer from 'puppeteer';
import {writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
const out=path.resolve(import.meta.dirname,'../.cache/reference-check');
await mkdir(out,{recursive:true});
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--enable-unsafe-swiftshader']});
try {
const page=await browser.newPage(); await page.setViewport({width:1280,height:900});
await page.evaluateOnNewDocument(()=>{window.WebSocket=class{constructor(){throw Error('External signaling disabled for local test')}};window.RTCPeerConnection=class{constructor(){throw Error('Peer connections disabled for local test')}}});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('http://127.0.0.1:5178/?boot=1',{waitUntil:'domcontentloaded'});
await page.waitForFunction(()=>window.rl,{timeout:180000});
await page.keyboard.press('Enter');
await page.waitForFunction(()=>!rl.inputLocked,{timeout:90000});
const before=await page.evaluate(()=>({time:rl.data.time,xyz:Array.from(rl.data.qpos).slice(0,3)}));
await page.keyboard.down('ArrowUp');
await page.waitForFunction(t=>rl.data.time>=t+10,{timeout:120000},before.time);
await page.keyboard.up('ArrowUp');
const after=await page.evaluate(()=>({time:rl.data.time,qpos:Array.from(rl.data.qpos).slice(0,7),obs:rl.buildObs().length,watchdog:rl.watchdogEvents}));
await writeFile(path.join(out,'walk.json'),JSON.stringify({before,after,errors},null,2));
console.log('WALK',JSON.stringify({before,after}));
console.log('READY',await page.evaluate(()=>({obs:rl.buildObs().length,qpos:Array.from(rl.data.qpos).slice(0,7),text:document.body.innerText.slice(-1200)})));
await page.screenshot({path:path.join(out,'official-browser.png')});
await writeFile(path.join(out,'boot.json'),JSON.stringify({errors,ready:true}));
} finally {await browser.close()}
