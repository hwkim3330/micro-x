"""Freeze the retired Q4's own files, independently of the evolving B2 design."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
if (R/'artifacts/q4_archive.json').exists():raise SystemExit('Archive already frozen; refusing to replace provenance')
files=sorted(p for p in (R/'models/q4').rglob('*') if p.is_file())
record={'status':'retired; not a current product','source_repository_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(R/'artifacts/q4_archive.json').write_text(json.dumps(record,indent=2)+'\n')
print('Archived provenance for',len(files),'existing Q4 files')
