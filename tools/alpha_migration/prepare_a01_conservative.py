"""Restrict empty-work removal after the D3D12 long-run variability finding."""
import difflib
from common import *
name='a01-empty-triangle-v3';base=ROOT/'proposals/a01-empty-triangle-v2';dest=ROOT/'proposals'/name
if not dest.exists():shutil.copytree(base,dest)
rel='src/solver/ParticleStep.cpp';old=(base/rel).read_text(encoding='utf8')
needle='    if(shape.count && geometry.vertices.buffer){'
replacement='''    // Removing even an empty GPU dispatch can change scheduling of later
    // floating-point atomics. Keep the original command stream for constraint
    // and diffuse workloads; the small saving is not worth widening numerical
    // variability. The remaining particle/fluid path has no such accumulators.
    const bool preserveAtomicSchedule=s.mNumSprings || s.mNumRigids ||
        s.mNumInflatables || s.mDynamicNumTris || s.mMaxDiffuseParticles;
    if(preserveAtomicSchedule || (shape.count && geometry.vertices.buffer)){'''
assert old.count(needle)==1
new=old.replace(needle,replacement);(dest/rel).write_text(new,encoding='utf8')
(ROOT/'evidence'/f'{name}.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v2/'+rel,tofile='v3/'+rel)),encoding='utf8')
rows=read(LEDGER/'optimizations.json')
for r in rows:
    if r['id']=='A001-01':r.update(candidate=name,source=str(dest),status='candidate-restricted',rejected_scope='v1/v2 unrestricted dispatch removal: D3D12 scene0 1200-frame repeated test widened observed variance beyond control, despite identical 84 shaders and passing API oracles. No minor-difference exception: ~1% gain is insufficient.',restriction='Preserve original command stream with springs, rigids, inflatables, dynamic triangles or any diffuse capacity. Test only the remaining particle/fluid eligibility.',investigation='a01-d12-scene0-investigation-v1')
write(LEDGER/'optimizations.json',rows);state(current_candidate=name);event('candidate-restricted',candidate=name,reason='D3D12 long-run quality gate')
