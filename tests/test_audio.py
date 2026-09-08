"""Software doubles only: no access to the development host microphone/speaker."""
import io,subprocess,unittest,wave
from pathlib import Path
from unittest.mock import patch
from test_device_service import service
class AudioTests(unittest.TestCase):
 def test_opt_in_is_separate(self):
  with patch.object(service.subprocess,'run') as run:
   for audio,record,code in [(service.Audio(),False,'audio_playback_disabled'),(service.Audio(True),True,'microphone_disabled')]:
    with self.assertRaises(service.DeviceError) as caught:audio.execute(record)
    self.assertEqual(caught.exception.code,code)
   run.assert_not_called()
 def test_missing_driver(self):
  with patch.object(service.shutil,'which',return_value=None):
   with self.assertRaises(service.DeviceError) as caught:service.Audio(True).execute()
   self.assertEqual(caught.exception.code,'audio_driver_missing')
 def test_timeout_unlocks(self):
  audio=service.Audio(True)
  with patch.object(service.shutil,'which',return_value='/test/aplay'),patch.object(service.subprocess,'run',side_effect=subprocess.TimeoutExpired('test',5)):
   with self.assertRaises(service.DeviceError) as caught:audio.execute()
   self.assertEqual(caught.exception.status,504);self.assertFalse(audio.lock.locked())
 def test_playback_does_not_claim_acoustic_validation(self):
  def run(cmd,**kwargs):
   self.assertTrue(Path(cmd[-1]).exists());return subprocess.CompletedProcess(cmd,0)
  with patch.object(service.shutil,'which',return_value='/test/aplay'),patch.object(service.subprocess,'run',side_effect=run):
   result=service.Audio(True).execute();self.assertTrue(result['alsa_playback_completed']);self.assertFalse(result['acoustic_output_verified'])
 def test_record_and_cleanup(self):
  paths=[]
  def run(cmd,**kwargs):
   self.assertIn('--duration',cmd);self.assertEqual(cmd[cmd.index('--duration')+1],'2');p=Path(cmd[-1]);paths.append(p);p.write_bytes(service.chirp());return subprocess.CompletedProcess(cmd,0)
  with patch.object(service.shutil,'which',return_value='/test/arecord'),patch.object(service.subprocess,'run',side_effect=run):
   result=service.Audio(microphone=True).execute(True);self.assertTrue(result.startswith(b'RIFF'))
  self.assertFalse(paths[0].exists())
 def test_failed_record_never_returns_synthetic_audio(self):
  with patch.object(service.shutil,'which',return_value='/test/arecord'),patch.object(service.subprocess,'run',return_value=subprocess.CompletedProcess([],1)):
   with self.assertRaises(service.DeviceError) as caught:service.Audio(microphone=True).execute(True)
   self.assertEqual(caught.exception.code,'audio_operation_failed')
 def test_chirp_is_valid_short_mono_wave(self):
  with wave.open(io.BytesIO(service.chirp())) as wav:
   self.assertEqual(wav.getnchannels(),1);self.assertEqual(wav.getsampwidth(),2);self.assertAlmostEqual(wav.getnframes()/wav.getframerate(),.65,places=3)
if __name__=='__main__':unittest.main()
