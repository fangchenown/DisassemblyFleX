"""Remove an uninitialized stream that neither original spring program reads."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name;assert not dest.exists();shutil.copytree(base,dest)
for index in ['032','075']:
    path=next((base/'shaders/machine').glob(index+'*.smasm'));s=path.read_text(encoding='utf8');assert not re.search(r'\bt0\b',s)
diff=[]
for file,needle in [('src/api/SpringApi.cpp','df::ReserveBuffer(solver,s.mHalfSpringIndices,capacity,4);'),('src/solver/ParticleStep.cpp','{0,B(s.mHalfSpringIndices)},')]:
    path=dest/file;before=path.read_text(encoding='utf8');assert before.count(needle)==1;after=before.replace(needle,'');path.write_text(after,encoding='utf8');diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=a.base+'/'+file,tofile=a.name+'/'+file))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
row=dict(id='A039-01',version='alpha3.9',candidate=a.name,base=a.base,title='Remove unread HalfSpringIndices allocation and binding',status='candidate-prepared',source=str(dest),evidence=str(patch),numerical_change=False,original_shader_change=False,memory_saving='4 * reserved half-spring capacity bytes per solver; all actual opposite/length/stiffness streams unchanged',required_validation=['original032/075 no t0 declaration/read','API/copy/lifecycle/resources','spring sparse/full-capacity byte oracle','FlexDemo springs plus whole-frame timing'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[r for r in rows if r['id']!=row['id']]+[row]);event('candidate-prepared',**row)
