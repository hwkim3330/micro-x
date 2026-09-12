"""Loopback-only simulation training workbench. No hardware commands or shell input."""
from pathlib import Path
import argparse,json,mimetypes,subprocess,sys,threading,time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[1]
class Jobs:
    def __init__(self):self.lock=threading.Lock();self.process=None;self.state={'status':'idle','lines':[]}
    def snapshot(self):
        with self.lock:return dict(self.state,lines=list(self.state['lines']))
    def start(self,settings):
        import re
        if set(settings)-{'updates','steps','seed','name'}:raise ValueError('Unknown setting')
        for key,low,high in [('updates',1,100),('steps',32,512),('seed',0,4294967295)]:
            if type(settings.get(key)) is not int or not low<=settings[key]<=high:raise ValueError('Invalid '+key)
        name=settings.get('name','micro_x_14')
        if type(name) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):raise ValueError('Invalid name')
        with self.lock:
            if self.process is not None:raise RuntimeError('Training already running')
            (R/'.cache/checkpoints').mkdir(parents=True,exist_ok=True);(R/'.cache/checkpoints/progress.json').write_text('{"history":[]}')
            args=[sys.executable,'-u',str(R/'tools/train_compat.py'),'--name',name]
            for key,value in settings.items():
                if key!='name':args.extend(['--'+key,str(value)])
            self.process=subprocess.Popen(args,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            self.state={'status':'running','lines':[],'settings':settings,'started':time.time()};process=self.process
        def watch():
            timer=threading.Timer(600,lambda:process.kill() if process.poll() is None else None);timer.start()
            try:
                for line in process.stdout:
                    with self.lock:self.state['lines']=(self.state['lines']+[line.rstrip()])[-60:]
                code=process.wait()
                with self.lock:
                    if self.state['status']=='running':self.state['status']='completed' if code==0 else 'failed'
                    self.state['exit_code']=code;self.process=None
            finally:timer.cancel()
        threading.Thread(target=watch,daemon=True).start()
    def stop(self):
        with self.lock:
            if self.process is not None:self.state['status']='cancelled';self.process.terminate()
    def evaluate(self,settings):
        import re
        if set(settings)-{'checkpoint','seconds','seeds'}:raise ValueError('Unknown setting')
        ckpt=settings.get('checkpoint','official');seconds=settings.get('seconds',10);seeds=settings.get('seeds',2)
        if ckpt!='official' and (type(ckpt) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}\.onnx',ckpt) or not (R/'.cache/checkpoints'/ckpt).is_file()):raise ValueError('Unknown checkpoint')
        if type(seconds) is not int or not 2<=seconds<=60 or type(seeds) is not int or not 1<=seeds<=5:raise ValueError('Invalid evaluation size')
        with self.lock:
            if self.process is not None:raise RuntimeError('A job is already running')
            (R/'.cache/evaluations').mkdir(parents=True,exist_ok=True)
            out=f'.cache/evaluations/{ckpt[:-5] if ckpt!="official" else "official"}.json'
            args=[sys.executable,'-u',str(R/'tools/evaluate_compat.py'),'--seconds',str(seconds),'--seeds',str(seeds),'--seed-start','10','--skip-standing','--output',out]
            if ckpt!='official':args.extend(['--walking-policy',str(R/'.cache/checkpoints'/ckpt)])
            self.process=subprocess.Popen(args,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            self.state={'status':'running','kind':'evaluate','lines':[],'settings':dict(settings,output=out),'started':time.time()};process=self.process
        def watch():
            timer=threading.Timer(900,lambda:process.kill() if process.poll() is None else None);timer.start()
            try:
                for line in process.stdout:
                    with self.lock:self.state['lines']=(self.state['lines']+[line.rstrip()])[-60:]
                code=process.wait()
                with self.lock:
                    if self.state['status']=='running':self.state['status']='completed' if code==0 else 'failed'
                    self.state['exit_code']=code;self.process=None
            finally:timer.cancel()
        threading.Thread(target=watch,daemon=True).start()
def checkpoints():
    folder=R/'.cache/checkpoints';out=[]
    for f in sorted(folder.glob('*.onnx')) if folder.exists() else []:
        meta=folder/(f.stem+'.json');info=json.loads(meta.read_text()) if meta.exists() else {}
        ev=R/'.cache/evaluations'/(f.stem+'.json')
        out.append(dict(file=f.name,size=f.stat().st_size,modified=f.stat().st_mtime,updates=info.get('updates'),steps=info.get('steps_per_update'),seed=info.get('seed'),history=info.get('history'),evaluated=ev.exists()))
    return out
jobs=Jobs()
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
    def log_message(self,*args):pass
    def do_HEAD(self):self.reply(405,{'error':'HEAD not supported'})
    def allowed(self):
        expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        return self.headers.get('Host') in expected and self.headers.get('Origin',f'http://{self.headers.get("Host")}') in {'http://'+h for h in expected}
    def reply(self,status,data):
        raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        if not self.allowed():return self.reply(403,{'error':'Local origin required'})
        if self.headers.get('Content-Type')!='application/json':return self.reply(415,{'error':'JSON required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=2048:raise ValueError('Invalid body size')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):raise ValueError('Object required')
            if self.path in ('/api/sim/start','/api/sim/step'):
                from simulation_session import simulation
                value=simulation.start(data) if self.path.endswith('/start') else simulation.step(data)
                return self.reply(200,value)
            if self.path=='/api/train':jobs.start(data)
            elif self.path=='/api/evaluate':jobs.evaluate(data)
            elif self.path=='/api/stop':jobs.stop()
            else:return self.reply(404,{'error':'Unknown endpoint'})
            self.reply(202,jobs.snapshot())
        except (ValueError,TypeError):self.reply(400,{'error':'Invalid settings'})
        except RuntimeError as error:self.reply(409,{'error':str(error)})
        except (ModuleNotFoundError,FileNotFoundError):self.reply(503,{'error':'Install requirements-policy.txt and run tools/fetch_compat.py first'})
    def do_GET(self):
        if not self.allowed():return self.reply(403,{'error':'Local origin required'})
        path=urlsplit(self.path).path
        if path=='/api/status':return self.reply(200,jobs.snapshot())
        if path=='/api/progress':
            target=R/'.cache/checkpoints/progress.json'
            return self.reply(200,json.loads(target.read_text()) if target.exists() else {'history':[]})
        if path=='/api/checkpoints':return self.reply(200,dict(official=dict(file='official',note='pinned alpha_walking.onnx'),checkpoints=checkpoints()))
        if path.startswith('/api/evaluation/'):
            import re
            name=path.rsplit('/',1)[1]
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):return self.reply(400,{'error':'Invalid name'})
            target=R/'.cache/evaluations'/f'{name}.json'
            if not target.exists():return self.reply(404,{'error':'Not evaluated yet'})
            return self.reply(200,json.loads(target.read_text()))
        if path.startswith('/api/checkpoint'):
            import re
            name=urlsplit(self.path).query.split('name=')[-1] if 'name=' in urlsplit(self.path).query else 'micro_x_14'
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):return self.reply(400,{'error':'Invalid name'})
            target=R/'.cache/checkpoints'/f'{name}.onnx'
            if not target.exists():return self.reply(404,{'error':'No completed checkpoint'})
            data=target.read_bytes();self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Disposition',f'attachment; filename="{name}.onnx"');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if path=='/':self.send_response(302);self.send_header('Location','/web/lab.html');self.end_headers();return
        target=Path(self.translate_path(self.path)).resolve()
        if target.is_dir():target=target/'index.html';self.path=path.rstrip('/')+'/index.html'+('?'+urlsplit(self.path).query if urlsplit(self.path).query else '')
        if not (any(target.is_relative_to(R/folder) for folder in ['web','models','artifacts','docs','engineering']) or target in [R/'LICENSE',R/'README.md',R/'THIRD_PARTY.md']) or not target.is_file():return self.reply(404,{'error':'Not found'})
        super().do_GET()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=5201);a=p.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'Simulation training only: http://127.0.0.1:{a.port}/web/lab.html',flush=True)
    try:server.serve_forever()
    finally:jobs.stop();server.server_close()
