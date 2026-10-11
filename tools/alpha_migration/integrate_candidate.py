"""Import the composed implementation without overwriting unrelated user edits."""
import argparse
from common import *
p=argparse.ArgumentParser();p.add_argument('--composition',required=True);a=p.parse_args()
composition=read(ROOT/'evidence'/f'{a.composition}-composition.json');source=Path(composition['source']);baseline=ROOT/'baseline/source';changes=[]
for name in ['CMakeLists.txt','include','src','shaders','cmake','tests','tools']:
    root=source/name
    for f in ([root] if root.is_file() else root.rglob('*')):
        if not f.is_file() or '__pycache__' in f.parts:continue
        rel=f.relative_to(source);old=baseline/rel;target=PROJECT/rel;before=sha(old) if old.exists() else None;after=sha(f)
        if before==after:continue
        current=sha(target) if target.exists() else None
        assert current in [before,after],('Unrelated local change; do not overwrite',str(rel))
        changes.append(dict(file=rel.as_posix(),before=before,after=after))
for row in changes:
    target=PROJECT/row['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/row['file'],target)
write(ROOT/'evidence/integrated-source.json',dict(composition=a.composition,files=changes,time=now(),requires_fresh_build_and_final_gates=True));event('source-integrated',composition=a.composition,files=len(changes));print('Integrated',len(changes),'files; all final gates still required.')
