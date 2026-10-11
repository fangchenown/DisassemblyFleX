"""Frozen DF + stable CPU control, separate from inherited NVIDIA ABI regressions."""
import argparse
from common import *
from locksafe_power import SystemRequired
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--candidate',required=True);p.add_argument('--name',required=True);a=p.parse_args()
base=read(ROOT/'evidence'/f'{a.base}-build.json');candidate=read(ROOT/'evidence'/f'{a.candidate}-build.json');out=ROOT/'runs'/a.name;out.mkdir(exist_ok=False)
build=Path(candidate['dll']).parent;env=clean_env(ROOT/'temp'/a.name);env['PATH']=str(build)+os.pathsep+str(WS/'FleX/bin/win64')+os.pathsep+env['PATH']
with SystemRequired(),gpu_lock():command([build/'DisassemblyRadixExtendedOracle.exe',base['dll'],candidate['dll'],out/'result.json'],a.name,env,cwd=WS,timeout=300)
result=read(out/'result.json');assert result['status']=='PASS';write(out/'identities.json',dict(base_sha256=base['dll_sha256'],candidate_sha256=candidate['dll_sha256'],scope='DF private-interface comparison plus CPU stable ordering; not an NVIDIA D3D12 private-interface acceptance.'));event('extended-radix-oracle',name=a.name,**result);print(json.dumps(result))
