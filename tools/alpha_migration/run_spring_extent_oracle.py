import argparse
from common import *
from locksafe_power import SystemRequired
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--candidate',required=True);p.add_argument('--name',required=True);a=p.parse_args()
base=read(ROOT/'evidence'/f'{a.base}-build.json');candidate=read(ROOT/'evidence'/f'{a.candidate}-build.json')
output=ROOT/'runs'/a.name;output.mkdir(exist_ok=False)
env=clean_env(ROOT/'temp'/a.name);env['PATH']=str(Path(candidate['dll']).parent)+os.pathsep+str(WS/'FleX/bin/win64')+os.pathsep+env['PATH']
with SystemRequired(),gpu_lock():
    command([Path(candidate['dll']).parent/'DisassemblySpringExtentOracle.exe',base['dll'],candidate['dll'],output/'result.json'],a.name,env,cwd=WS,timeout=300)
result=read(output/'result.json');assert result['status']=='PASS';write(output/'identities.json',dict(base=base['dll_sha256'],candidate=candidate['dll_sha256'],time=now()));event('spring-extent-oracle',name=a.name,**result);print(json.dumps(result))
