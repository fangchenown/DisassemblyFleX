"""Compose disjoint reviewed source deltas; refuse implicit conflict resolution."""
import argparse
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);p.add_argument('--components',required=True);a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name;assert not dest.exists()
shutil.copytree(base,dest);modified={};records=[]
for name in a.components.split(','):
    source=Path(read(ROOT/'evidence'/f'{name}-build.json')['source']);paths={p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}|{p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    delta=[]
    for relative in sorted(paths):
        old,new=base/relative,source/relative;before=sha(old) if old.exists() else None;after=sha(new) if new.exists() else None
        if before==after:continue
        assert after is not None,'Deletion requires explicit implementation review: '+relative
        if relative in modified:assert modified[relative]==after,'Overlapping candidate change: '+relative
        modified[relative]=after;(dest/relative).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(new,dest/relative);delta.append(dict(file=relative,before=before,after=after))
    records.append(dict(candidate=name,changes=delta))
write(ROOT/'evidence'/f'{a.name}-composition.json',dict(base=a.base,components=records,files=len(modified),source=str(dest),time=now()));event('candidate-composition',name=a.name,base=a.base,components=a.components.split(','),files=len(modified));print('Composed',len(modified),'disjoint changed files.')
