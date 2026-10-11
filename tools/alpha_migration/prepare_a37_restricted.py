"""Keep structural/atomic-sensitive workloads on the original neighbor program."""
import difflib
from common import *
name='a37-distance-v2';base=Path(read(ROOT/'evidence/a37-distance-v1-build.json')['source']);dest=ROOT/'proposals'/name;assert not dest.exists();shutil.copytree(base,dest)
path=dest/'src/solver/ParticleStep.cpp';before=path.read_text(encoding='utf8');needle='Pass(solver,"df_CollideParticlesDistanceFirst",';assert before.count(needle)==1
after=before.replace(needle,'''// Keep the original program for spring/inflatable/triangle/diffuse paths:
    // their full-simulation repeat envelopes did not establish a robust gain
    // without widened observed variability. No scene-ID or parameter tuning.
    const bool originalNeighbors=s.mNumSprings || s.mNumInflatables || s.mDynamicNumTris || s.mMaxDiffuseParticles;
    Pass(solver,originalNeighbors?"g_Flex_CollideParticles":"df_CollideParticlesDistanceFirst",''');path.write_text(after,encoding='utf8')
patch=ROOT/'evidence'/f'{name}.patch';patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a37-distance-v1/src/solver/ParticleStep.cpp',tofile=name+'/src/solver/ParticleStep.cpp')),encoding='utf8')
rows=read(LEDGER/'optimizations.json')
for r in rows:
    if r['id']=='A037-01':
        prior={k:v for k,v in r.items() if k!='previous_trials'};prior.update(status='rejected-unrestricted-scope',decision='Full20-scene speed intervals include1. Kernel rows/counts are bit-exact, but limited full-simulation cloth repeats do not establish non-widening of the baseline envelope; preserve original program on structural/diffuse workloads. This is a conservative eligibility restriction, not proof the integer neighbor outputs differ.')
        r.setdefault('previous_trials',[]).append(prior);r.update(candidate=name,base='a37-distance-v1',status='restricted-candidate-prepared',source=str(dest),evidence=str(patch),eligibility='zero springs, inflatables, dynamic triangles and diffuse capacity',decision='Pending isolated confirmation and fresh whole-suite validation; no numerical exception invoked.')
write(LEDGER/'optimizations.json',rows);event('candidate-scope-restricted',candidate=name,base='a37-distance-v1',evidence=str(patch),reason='Keep structural/diffuse GPU schedule on original shader; direct450-case proof for derived rows retained.')
