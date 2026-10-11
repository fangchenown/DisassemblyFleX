"""Conservative final rollback of the only modified floating-point program."""
from common import *
base=ROOT/'sources/alpha-migration-final-v1';dest=ROOT/'proposals/integrated-v2';assert not dest.exists();shutil.copytree(base,dest)
path=dest/'src/solver/ParticleStep.cpp';s=path.read_text(encoding='utf8')
start=s.index('    // Keep the original program for spring/inflatable/triangle/diffuse paths:')
end=s.index('blocks,{{0,library->cellBucketStarts}',start)
s=s[:start]+'    Pass(solver,"g_Flex_CollideParticles",'+s[end:];path.write_text(s,encoding='utf8')
registry=dest/'shaders/auxiliary/registry.json';items=read(registry);assert sum(r['name']=='df_CollideParticlesDistanceFirst' for r in items)==1;write(registry,[r for r in items if r['name']!='df_CollideParticlesDistanceFirst'])
retired=dest/'tools/alpha_migration/retired_shaders';retired.mkdir(parents=True,exist_ok=True)
deleted=[]
for name in ['NeighborsDistanceFirst.hlsl','NeighborsDistanceFirst.smasm']:
    source=dest/'shaders/auxiliary'/name;shutil.copy2(source,retired/name);source.unlink();deleted.append('shaders/auxiliary/'+name)
changed=['src/solver/ParticleStep.cpp','shaders/auxiliary/registry.json'];record=[]
for relative in changed+deleted:
    target=PROJECT/relative;expected=base/relative;assert target.resolve().is_relative_to(PROJECT.resolve());assert sha(target)==sha(expected),('Unrelated change',relative)
for relative in changed:
    before=sha(PROJECT/relative);shutil.copy2(dest/relative,PROJECT/relative);record.append(dict(file=relative,before=before,after=sha(PROJECT/relative)))
for relative in deleted:
    target=PROJECT/relative;before=sha(target);target.unlink();record.append(dict(file=relative,before=before,after=None))
for name in ['NeighborsDistanceFirst.hlsl','NeighborsDistanceFirst.smasm']:
    target=PROJECT/'tools/alpha_migration/retired_shaders'/name;target.parent.mkdir(exist_ok=True);assert not target.exists();shutil.copy2(retired/name,target)
write(ROOT/'evidence/integrated-v2-removal.json',dict(base='alpha-migration-final-v1',source=str(dest),changes=record,time=now(),reason='A037 local D11 performance regressions plus unresolved rare D12 Soft Rope tail. Roll back rather than invoke a numerical exception. All original floating-point DXBC programs remain in active use; retained new programs are integer-only.'))
rows=read(LEDGER/'optimizations.json')
for r in rows:
    if r['id']=='A037-01':r.update(status='rejected-final-conservative',decision='Restricted v2 retained local plastic-body gains but reproduced D11 regressions on17/31. Most quality flags reproduced in original controls; one rare D12 Soft Rope ~0.007 position-RMS tail was not fully explained by the8-repeat follow-up. Causality is not asserted. Remove this floating-point program transformation conservatively instead of broadening tolerance; keep all evidence and retired source.',rollback='integrated-v2-removal.json')
write(LEDGER/'optimizations.json',rows);event('neighbor-program-rollback',changes=record,reason='Preserve original floating-point programs; no approximation exception used');print('Removed active derived neighbor program; integer helpers and other changes retained.')
