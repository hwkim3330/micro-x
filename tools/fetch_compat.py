"""Fetch only pinned Apache-licensed policy software and weights, no robot CAD."""
from pathlib import Path
import hashlib,json,urllib.request
R=Path(__file__).resolve().parents[1];dest=R/'.cache/compat';dest.mkdir(parents=True,exist_ok=True)
for name,record in json.loads((R/'engineering/policy_sources.json').read_text()).items():
    target=dest/name
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==record['sha256']:continue
    data=urllib.request.urlopen(record['url'],timeout=60).read()
    if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Source hash mismatch: '+name)
    target.write_bytes(data)
print('Pinned inference software and policy weights verified; no upstream hardware downloaded')
