"""Replay X-generated neural commands on both bodies with the same BAM runtime.

Reference hardware stays outside this repository. This is not a reproduction of
Microfly's XML position-actuator browser runtime or independent scent navigation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from compat_env import Environment

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference_xml', type=Path)
    args = parser.parse_args()
    source = args.reference_xml.resolve()
    trace_path = ROOT / 'artifacts/fly_brain_x_evaluation.json'
    trace = json.loads(trace_path.read_text())
    tree = ET.parse(source)
    compiler = tree.getroot().find('compiler')
    compiler.set('meshdir', str(source.parent / compiler.get('meshdir', '.')))
    ET.SubElement(tree.getroot().find('worldbody'), 'geom',
                  name='comparison_floor', type='plane', size='0 0 .05', friction='.8 .005 .0001')
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        reference = Path(tmp) / 'reference.xml'
        tree.write(reference)
        for body, model in [('microduck_reference', reference), ('micro_x', ROOT / 'models/micro_x_14.xml')]:
            env = Environment(model_path=model)
            for trial in trace['results']:
                env.reset(seed=10)
                previous = env.data.qpos[:2].copy()
                distance, first_fall = 0., None
                for frame in trial['frames']:
                    env.policy.set_vel_cmd(*frame['command'])
                    for _ in range(5):
                        _, fallen, _ = env.step(env.policy.infer())
                        position = env.data.qpos[:2].copy()
                        distance += float(np.linalg.norm(position - previous))
                        previous = position
                        if fallen and first_fall is None:
                            first_fall = float(env.data.time)
                result = dict(body=body, condition=trial['condition'], duration_s=float(env.data.time),
                              path_m=distance, final_position=env.data.qpos[:3].tolist(), first_fall_s=first_fall)
                results.append(result)
                print(json.dumps(result), flush=True)
    report = dict(scope='Paired replay of X-generated neural commands. Same pinned Python policy/BAM M6 runtime, seed 10, reset height .125 m, 50 Hz. Reference robot_walk XML is NOT Microfly browser robot_allcollisions XML. Body/contact differences remain; no isolated causal conclusion.',
                  trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                  reference_xml_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  x_xml_sha256=hashlib.sha256((ROOT/'models/micro_x_14.xml').read_bytes()).hexdigest(),
                  physical_verified=False, results=results)
    (ROOT/'artifacts/fly_brain_paired_replay.json').write_text(json.dumps(report, indent=2)+'\n')

if __name__ == '__main__':
    main()
