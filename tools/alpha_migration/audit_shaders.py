"""Compare all original shader containers and verified instruction schedules."""
import argparse
from common import *
p=argparse.ArgumentParser();p.add_argument('builds',nargs='+');a=p.parse_args()
baseline=read(ROOT/'builds/control-v0/generated/shader_manifest.json');assert len(baseline)==84
for name in a.builds:
    manifest=read(ROOT/'builds'/name/'generated/shader_manifest.json');assert len(manifest)==len(baseline)
    checks=[dict(name=l['name'],bytecode_equal=l['name']==r['name'] and l['dxbc_sha256']==r['dxbc_sha256'],lowering_verified=r['hlsl_lowering_verified'],instruction_verified=r['instruction_roundtrip_verified']) for l,r in zip(baseline,manifest)]
    assert all(x['bytecode_equal'] and x['lowering_verified'] and x['instruction_verified'] for x in checks)
    write(ROOT/'evidence'/f'{name}-shader-audit.json',dict(status='PASS',exact_containers=84,checks=checks));print(name,'84 original containers exact')
