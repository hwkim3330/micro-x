"""Original small synthesized chirp for Micro X; MIT, including generated WAV."""
import io,math,struct,wave
def chirp():
    rate=22050;duration=.65;frames=[];phase=0.0
    for i in range(round(rate*duration)):
        t=i/rate;frequency=420+330*math.sin(math.pi*t/duration)**2
        phase+=2*math.pi*frequency/rate
        envelope=math.sin(math.pi*t/duration)**2
        # Low amplitude is a digital setting, not a calibrated acoustic output level.
        value=.07*envelope*(math.sin(phase)+.22*math.sin(2*phase))/1.22
        frames.append(struct.pack('<h',round(value*32767)))
    output=io.BytesIO()
    with wave.open(output,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(b''.join(frames))
    return output.getvalue()
if __name__=='__main__':
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(chirp())
