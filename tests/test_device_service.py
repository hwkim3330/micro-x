"""Unit tests use command doubles, never claim a physical camera test."""
import importlib.util,json,subprocess,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('device_service',Path(__file__).resolve().parents[1]/'runtime/device_service.py');service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
class CameraTests(unittest.TestCase):
 def test_disabled_never_executes(self):
  with patch.object(service.subprocess,'run') as run:
   with self.assertRaises(service.DeviceError) as caught:service.Camera().capture()
   self.assertEqual(caught.exception.code,'camera_disabled');run.assert_not_called()
 def test_no_driver_no_fake_frame(self):
  with patch.object(service.shutil,'which',return_value=None):
   camera=service.Camera(True);self.assertEqual(camera.probe()['state'],'driver_missing')
   with self.assertRaises(service.DeviceError):camera.capture()
 def test_probe_does_not_claim_capture(self):
  with patch.object(service.shutil,'which',return_value='/test/rpicam-still'),patch.object(service.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'0 : imx708 [4608x2592]\n','')):
   p=service.Camera().probe();self.assertEqual(p['detected_sensors'],['imx708']);self.assertFalse(p['capture_verified'])
 def test_capture_command_and_cleanup(self):
  saved=[]
  def run(command,**kwargs):
   path=Path(command[command.index('--output')+1]);saved.append(path);path.write_bytes(b'\xff\xd8unit-test-only\xff\xd9');self.assertNotIn('shell',kwargs);return subprocess.CompletedProcess(command,0,b'',b'')
  with patch.object(service.shutil,'which',return_value='/test/rpicam-still'),patch.object(service.subprocess,'run',side_effect=run):
   self.assertEqual(service.Camera(True).capture(),b'\xff\xd8unit-test-only\xff\xd9')
  self.assertFalse(saved[0].exists())
 def test_timeout_releases_lock(self):
  camera=service.Camera(True);camera.executable='/test/rpicam-still'
  with patch.object(service.subprocess,'run',side_effect=subprocess.TimeoutExpired('test',8)):
   with self.assertRaises(service.DeviceError) as caught:camera.capture()
  self.assertEqual(caught.exception.status,504);self.assertFalse(camera.lock.locked())
 def test_busy(self):
  camera=service.Camera(True);camera.executable='/test/rpicam-still';camera.lock.acquire()
  with self.assertRaises(service.DeviceError) as caught:camera.capture()
  self.assertEqual(caught.exception.status,409);camera.lock.release()
 def test_http_auth_and_disabled_state(self):
  server=service.make_server(0,service.Camera(False),'test-only-long-bearer-token');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}/camera/snapshot'
  try:
   with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(urllib.request.Request(url,method='POST'))
   self.assertEqual(caught.exception.code,401)
   with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(urllib.request.Request(url,method='POST',headers={'Authorization':'Bearer test-only-long-bearer-token'}))
   self.assertEqual(caught.exception.code,503);self.assertFalse(json.load(caught.exception)['simulated_fallback'])
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
