"""Adapt OF's exact constant reuse to the duplicate upload actually present in DF."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a21-substep-constants-v1');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
relative='src/solver/ParticleStep.cpp';old=(base/relative).read_text(encoding='utf8');needle='    uploadSubstep();\n';assert old.count(needle)==2
first=old.index(needle);last=old.index(needle,first+len(needle));assert 'ExecuteCallback' not in old[first:last]
new=old.replace(needle,'');line='    auto uploadSubstep=[&](){std::memcpy(context->map(second),values,sizeof(values));context->unmap(second);};';assert new.count(line)==1
new=new.replace(line,line+'''
    // Triangle and analytic collision consume the identical immutable fraction
    // pair, with no callback or constant write between them. One upload keeps
    // both consumers on the same data version, including the empty-triangle path.
    uploadSubstep();''')
(dest/relative).write_text(new,encoding='utf8');patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a.base+'/'+relative,tofile=a.name+'/'+relative)),encoding='utf8')
item=dict(id='A021-01',version='alpha2.1',candidate=a.name,base=a.base,title='Reuse identical substep constants across triangle and analytic collision',status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha2.1 W21-W23 and alpha2.3 exact-content CB reuse, adapted to DF single shared substep buffer',numerical_change=False,shader_change=False,invariants=['same eight uploaded fraction bytes','no callback between consumers','all collision dispatches and contact-count clears retained','constant is read-only to both shaders','D3D12 records both uses against its fence even when reusing the same version'],required_validation=['original84 shader identity','ABI/timers/callback/native context/CB pool regression','shape/mesh and multiple-substep cases','FlexDemo output contracts, rendering fields and both-backend timing','D3D12 constant-version memory effect'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[r for r in rows if r['id']!=item['id']]+[item]);event('candidate-prepared',**item)
