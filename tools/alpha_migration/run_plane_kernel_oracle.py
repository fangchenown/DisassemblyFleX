import argparse
from common import *
from locksafe_power import SystemRequired
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--name',required=True);a=p.parse_args()
candidate=read(ROOT/'evidence'/f'{a.candidate}-build.json');build=Path(candidate['dll']).parent;out=ROOT/'runs'/a.name;out.mkdir(exist_ok=False)
env=clean_env(ROOT/'temp'/a.name);env['PATH']=str(build)+os.pathsep+str(WS/'FleX/bin/win64')+os.pathsep+env['PATH']
with SystemRequired(),gpu_lock():command([build/'DisassemblyPlaneKernelOracle.exe',candidate['dll'],build/'generated/070_g_Flex_CollideShapes.dxbc',build/'generated/CollidePlanes.dxbc',out/'result.json'],a.name,env,cwd=WS,timeout=300)
result=read(out/'result.json');assert result['status']=='PASS';event('plane-kernel-oracle',name=a.name,**result);print(json.dumps(result))
