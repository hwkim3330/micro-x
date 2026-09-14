"""CPU-only deployment sizing: no MuJoCo, torch, motor I/O or physical control."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import resource
import time

import numpy as np
import onnxruntime as ort

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=ROOT/'.cache/compat/alpha_walking.onnx')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    digest = hashlib.sha256(args.model.read_bytes()).hexdigest()
    expected = json.loads((ROOT/'engineering/policy_sources.json').read_text())['alpha_walking.onnx']['sha256']
    if digest != expected:
        parser.error('Expected the pinned official walking model')
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(args.model), sess_options=options, providers=['CPUExecutionProvider'])
    inputs = session.get_inputs()
    if len(inputs) != 1 or inputs[0].shape[-1] != 61:
        raise ValueError('Expected 61 observation inputs')
    # Synthetic bounded inputs exercise inference; they do not validate walking.
    rng = np.random.default_rng(23)
    observations = rng.normal(0, .01, (128, 61)).astype(np.float32)
    observations[:, 5] = -1
    observations[:, 48] = np.linspace(0, .3, 128)
    observations[:, 50] = np.linspace(-.3, .3, 128)
    samples = []
    for i in range(2100):
        start = time.perf_counter_ns()
        action = session.run(None, {inputs[0].name: observations[i % 128:i % 128+1]})[0]
        elapsed = (time.perf_counter_ns()-start)/1e6
        if action.shape != (1, 14) or not np.isfinite(action).all():
            raise ValueError('Invalid action output')
        if i >= 100:
            samples.append(elapsed)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = dict(scope='Single-thread CPU ONNX inference, synthetic observations, 100 warmup + 2000 timed calls. Excludes sensor acquisition, motor bus, scheduling, camera and brain. Not gait or board qualification.',
                  host=dict(architecture=platform.machine(),system=platform.system(),python=platform.python_version()),
                  onnxruntime=ort.__version__,model_sha256=digest,model_bytes=args.model.stat().st_size,
                  latency_ms={name:float(np.percentile(samples,p)) for name,p in [('p50',50),('p95',95),('p99',99),('max',100)]},
                  calls_over_20ms=sum(x>20 for x in samples),peak_rss_bytes=int(rss if platform.system()=='Darwin' else rss*1024),
                  board_qualified=False,physical_verified=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
