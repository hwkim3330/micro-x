// Photograph the shipped CAD viewer, not a concept illustration.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import puppeteer from 'puppeteer';
const root=path.resolve(import.meta.dirname,'..');
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.glb':'model/gltf-binary'};
const server=http.createServer(async(req,res)=>{
  try {
    let url=decodeURIComponent(req.url.split('?')[0]);if(url.endsWith('/'))url+='index.html';
    const file=path.resolve(root,'.'+url);if(!file.startsWith(root+path.sep))throw Error('path');
    const data=await readFile(file);res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream'});res.end(data);
  } catch {res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try {
  browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox','--enable-unsafe-swiftshader']});
  const page=await browser.newPage();await page.setViewport({width:1800,height:1200,deviceScaleFactor:1});
  await page.goto(`http://127.0.0.1:${server.address().port}/web/`);await page.waitForFunction(()=>window.microX);
  await page.evaluate(()=>{
    const {scene,camera,renderer,controls}=window.microX;
    scene.children.filter(x=>x.type==='GridHelper').forEach(x=>scene.remove(x));
    const stage=document.querySelector('#view');document.body.replaceChildren(stage);
    stage.style.cssText='position:fixed;inset:0;width:100%;height:100%;background:#f0eee4';
    [...stage.children].filter(x=>x.tagName!=='CANVAS').forEach(x=>x.remove());
    camera.position.set(.29,.22,.49);controls.target.set(-.005,.125,0);controls.update();
    const label=document.createElement('div');label.style.cssText='position:fixed;top:65px;left:75px;color:#173d30;font-family:Arial,sans-serif';
    label.innerHTML='<div style="font-size:58px;font-weight:800;letter-spacing:3px">MICRO <span style="color:#d87832">X</span></div><div style="font-size:20px;letter-spacing:5px;margin-top:14px">YOUR LITTLE T-REX</div>';
    const note=document.createElement('div');note.style.cssText='position:fixed;bottom:45px;left:75px;color:#476454;font:18px Arial,sans-serif';note.textContent='Original commercial design · Actual 16-part CAD · P0 assembly prototype';
    document.body.append(label,note);renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.render(scene,camera);
  });
  await page.screenshot({path:path.join(root,'artifacts/readme_hero.png')});
  console.log('Rendered actual Micro X CAD to artifacts/readme_hero.png');
} finally {await browser?.close();server.close();}
