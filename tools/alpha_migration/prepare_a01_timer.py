"""Preserve original detail-timer labels without reinstating empty GPU work."""
import difflib
from common import *
name='a01-empty-triangle-v2'
base=ROOT/'proposals/a01-empty-triangle-v1';dest=ROOT/'proposals'/name
if not dest.exists():shutil.copytree(base,dest)
rel='src/solver/ParticleStep.cpp';old=(base/rel).read_text(encoding='utf8')
needle='    }\n    uploadSubstep();\n    Pass(solver,"g_Flex_CollideShapes"'
replacement='''    }else if(frameTimers.mEnabled){
        // Preserve the original detail-timer label identity and ordering when
        // this pass is empty. Timing records the skipped pass, not fake work.
        const auto shader=GetShader(library,"g_Flex_CollideTriangles");
        const int timer=frameTimers.mTimerPool->begin();
        frameTimers.mNameToTimerMapW.emplace(shader->m_desc.label,timer);
        frameTimers.mTimerPool->end(timer);
    }
    uploadSubstep();
    Pass(solver,"g_Flex_CollideShapes"'''
assert old.count(needle)==1
new=old.replace(needle,replacement);(dest/rel).write_text(new,encoding='utf8')
(ROOT/'evidence'/f'{name}.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v1/'+rel,tofile='v2/'+rel)),encoding='utf8')
rows=read(LEDGER/'optimizations.json')
for r in rows:
    if r['id']=='A001-01':
        r.update(candidate=name,source=str(dest),status='candidate-repair',previous_candidate='a01-empty-triangle-v1',repair='Original diagnostic oracle exposed changed timer-name multiplicity. Retain the original shader label address and begin/end timer for skipped passes; no fake dispatch or physics changes. Original failed receipts remain immutable.')
write(LEDGER/'optimizations.json',rows);event('candidate-repair',candidate=name)
