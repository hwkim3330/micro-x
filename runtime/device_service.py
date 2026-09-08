"""Micro X local hardware bring-up service. MIT; no simulated camera fallback.
Camera capture requires operator enablement and an API token. No motor commands.
"""
from __future__ import annotations
import argparse,json,platform,re,secrets,shutil,subprocess,tempfile,threading
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sound import chirp
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

class DeviceError(Exception):
    def __init__(self,code,status=503):self.code=code;self.status=status

class Camera:
    def __init__(self,enabled=False):
        self.enabled=enabled;self.executable=shutil.which('rpicam-still');self.lock=threading.Lock()
    def probe(self):
        result={'enabled':self.enabled,'driver':'rpicam-still','driver_installed':bool(self.executable),'detected_sensors':[],'capture_verified':False}
        if not self.executable:return dict(result,state='driver_missing')
        if not self.lock.acquire(False):return dict(result,state='busy')
        try:
            p=subprocess.run([self.executable,'--list-cameras'],capture_output=True,text=True,timeout=5)
            sensors=re.findall(r'^\s*\d+\s*:\s*([\w-]+)\s*\[',p.stdout+'\n'+p.stderr,re.M)
            return dict(result,detected_sensors=sensors,state='detected' if sensors and p.returncode==0 else 'not_detected')
        except (OSError,subprocess.TimeoutExpired):return dict(result,state='probe_failed')
        finally:self.lock.release()
    def capture(self):
        if not self.enabled:raise DeviceError('camera_disabled')
        if not self.executable:raise DeviceError('camera_driver_missing')
        if not self.lock.acquire(False):raise DeviceError('camera_busy',409)
        try:
            with tempfile.TemporaryDirectory(prefix='micro-x-capture-') as directory:
                output=Path(directory)/'frame.jpg'
                command=[self.executable,'--nopreview','--autofocus-on-capture','--timeout','1000','--width','1280','--height','720','--encoding','jpg','--output',str(output)]
                try:p=subprocess.run(command,capture_output=True,timeout=8)
                except subprocess.TimeoutExpired:raise DeviceError('camera_timeout',504)
                except OSError:raise DeviceError('camera_driver_failed')
                if p.returncode!=0 or not output.exists():raise DeviceError('camera_capture_failed')
                data=output.read_bytes()
                if len(data)<4 or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):raise DeviceError('camera_invalid_jpeg')
                return data
        finally:self.lock.release()

class Audio:
    def __init__(self,playback=False,microphone=False):
        self.playback_enabled=playback;self.microphone_enabled=microphone;self.lock=threading.Lock()
    def execute(self,record=False):
        if record and not self.microphone_enabled:raise DeviceError('microphone_disabled')
        if not record and not self.playback_enabled:raise DeviceError('audio_playback_disabled')
        executable=shutil.which('arecord' if record else 'aplay')
        if not executable:raise DeviceError('audio_driver_missing')
        if not self.lock.acquire(False):raise DeviceError('audio_busy',409)
        try:
            with tempfile.TemporaryDirectory(prefix='micro-x-audio-') as directory:
                output=Path(directory)/'sample.wav'
                if record:command=[executable,'--quiet','--file-type','wav','--format','S16_LE','--rate','16000','--channels','1','--duration','2',str(output)]
                else:
                    output.write_bytes(chirp());command=[executable,'--quiet',str(output)]
                try:p=subprocess.run(command,capture_output=True,timeout=5)
                except subprocess.TimeoutExpired:raise DeviceError('audio_timeout',504)
                except OSError:raise DeviceError('audio_driver_failed')
                if p.returncode!=0:raise DeviceError('audio_operation_failed')
                if not record:return {'alsa_playback_completed':True,'acoustic_output_verified':False}
                data=output.read_bytes() if output.exists() else b''
                if len(data)<44 or data[:4]!=b'RIFF' or data[8:12]!=b'WAVE':raise DeviceError('audio_invalid_wav')
                return data
        finally:self.lock.release()

def alsa_probe(command):
    executable=shutil.which(command)
    result={'tool_installed':bool(executable),'enumerated_endpoints':0,'functional_test_passed':False}
    if not executable:return result
    try:
        p=subprocess.run([executable,'--list-devices'],capture_output=True,text=True,timeout=3)
        result['enumerated_endpoints']=len(re.findall(r'^card\s+\d+:',p.stdout,re.M)) if p.returncode==0 else 0
    except (OSError,subprocess.TimeoutExpired):result['probe_failed']=True
    return result

def health(camera):
    return {'service':'micro-x-device','schema':1,'machine':platform.machine(),'camera':camera.probe(),
        'audio':{'capture':alsa_probe('arecord'),'playback':alsa_probe('aplay'),'voice_pipeline':'not implemented'},
        'sensors':{'imu':'not implemented','range':'not implemented','foot_contact':'not implemented'},
        'motion_control':'not implemented','integrated_robot_validated':False}

def make_server(port=8765,camera=None,token='',audio=None):
    camera=camera or Camera();audio=audio or Audio()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass # never log bearer credentials or frame bytes
        def respond(self,status,payload,kind='application/json'):
            data=json.dumps(payload).encode() if kind=='application/json' else payload
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
        def valid_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        def do_GET(self):
            if not self.valid_host():return self.respond(403,{'error':'invalid_host'})
            route=urlsplit(self.path).path
            if route=='/health':return self.respond(200,health(camera))
            if route=='/camera/status':return self.respond(200,camera.probe())
            return self.respond(404,{'error':'not_found'})
        def do_POST(self):
            if not self.valid_host():return self.respond(403,{'error':'invalid_host'})
            if not token or not secrets.compare_digest(self.headers.get('Authorization',''),f'Bearer {token}'):
                return self.respond(401,{'error':'unauthorized'})
            route=urlsplit(self.path).path
            if route not in ['/camera/snapshot','/audio/chirp','/audio/sample']:return self.respond(404,{'error':'not_found'})
            try:
                if route=='/camera/snapshot':self.respond(200,camera.capture(),'image/jpeg')
                elif route=='/audio/chirp':self.respond(200,audio.execute())
                else:self.respond(200,audio.execute(record=True),'audio/wav')
            except DeviceError as e:self.respond(e.status,{'error':e.code,'simulated_fallback':False})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--enable-camera',action='store_true');parser.add_argument('--enable-audio',action='store_true');parser.add_argument('--enable-microphone',action='store_true');parser.add_argument('--token-file',type=Path);parser.add_argument('--probe',action='store_true');args=parser.parse_args()
    camera=Camera(args.enable_camera)
    if args.probe:print(json.dumps(health(camera),indent=2));return
    token=args.token_file.read_text().strip() if args.token_file else ''
    if (args.enable_camera or args.enable_audio or args.enable_microphone) and len(token)<24:parser.error('device enablement requires --token-file with at least 24 characters')
    server=make_server(args.port,camera,token,Audio(args.enable_audio,args.enable_microphone));print(f'Micro X local service: http://127.0.0.1:{server.server_port}; camera enabled={camera.enabled}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
