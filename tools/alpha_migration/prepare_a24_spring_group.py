"""Try 256-thread groups, preserving each original eight-lane spring reduction."""
import argparse,difflib
from common import *
from auxiliary_support import configure
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a24-spring-group-v1');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
sys.path.insert(0,str(PROJECT/'tools'));from shader_lowering import Lifter
from dxbc_assembler import instruction_lines
entries=[];proof=[]
for index,suffix in [(32,'NV'),(75,'')]:
    path=next((base/'shaders/machine').glob(f'{index:03d}_*.smasm'));old=list(instruction_lines(path.read_text(encoding='utf8')))
    assert old.count('dcl_thread_group 512, 1, 1')==1 and old.count('dcl_tgsm_structured g0, 12, 512')==1
    new=[x.replace('dcl_thread_group 512, 1, 1','dcl_thread_group 256, 1, 1').replace('dcl_tgsm_structured g0, 12, 512','dcl_tgsm_structured g0, 12, 256') for x in old]
    assert [x for x in old if not x.startswith(('dcl_thread_group','dcl_tgsm_structured'))]==[x for x in new if not x.startswith(('dcl_thread_group','dcl_tgsm_structured'))]
    stem='Spring256'+suffix;assembly='// Original eight-lane particle arithmetic; only independent-row group packing changes.\ncs_5_0\n'+'\n'.join(new)+'\n'
    (dest/'shaders/auxiliary'/(stem+'.smasm')).write_text(assembly,encoding='utf8');(dest/'shaders/auxiliary'/(stem+'.hlsl')).write_text(Lifter({},assembly).run(),encoding='utf8')
    entries.append(dict(name='df_SolveSprings256'+suffix,source=stem+'.hlsl',instructions=stem+'.smasm',original_index=index,kind='preserved-eight-lane-arithmetic-group256'))
    proof.append(dict(original=str(path),source_sha256=sha(path),only_changes=['threadgroup512→256','TGSM elements512→256'],all_other_instructions_identical=True,particles_per_group=32))
configure(dest,entries)
path=dest/'src/solver/ParticleStep.cpp';text=path.read_text(encoding='utf8');needle='        if(s.mNumSprings){const char* spring=library->enableExtensions&&library->fp32AtomicSupported?"g_Flex_SolveSpringsNV":"g_Flex_SolveSprings";';assert text.count(needle)==1
text=text.replace(needle,'''        if(s.mNumSprings){
            // Preserve the original dispatch-X limit for very large capacities.
            const bool group256=s.mMaxParticles>0 && unsigned(s.mMaxParticles)<=32u*65535u;
            const bool nv=library->enableExtensions&&library->fp32AtomicSupported;
            const char* spring=group256?(nv?"df_SolveSprings256NV":"df_SolveSprings256"):(nv?"g_Flex_SolveSpringsNV":"g_Flex_SolveSprings");
            const unsigned groupParticles=group256?32u:64u;''')
needle='unsigned(s.mMaxParticles*8+511)/512';assert text.count(needle)==1;text=text.replace(needle,'(unsigned(s.mMaxParticles)+groupParticles-1u)/groupParticles');path.write_text(text,encoding='utf8')
path=dest/'src/api/SpringApi.cpp';text=path.read_text(encoding='utf8');needle='unsigned values[4]={unsigned(count),unsigned(s.mMaxParticles),0,0};';assert text.count(needle)==1
text=text.replace(needle,'unsigned values[4]={unsigned(count),unsigned(s.mMaxParticles),unsigned(s.mMaxParticles)<=32u*65535u?32u:64u,0};');path.write_text(text,encoding='utf8')
path=dest/'shaders/auxiliary/SpringDispatchArgs.hlsl';text=path.read_text(encoding='utf8').replace('uint2 unused;','uint particlesPerGroup; uint unused;').replace('    dispatchArguments.Store3(0,uint3((extent+63u)/64u,1u,1u));','    uint shift=particlesPerGroup==32u?5u:6u;\n    dispatchArguments.Store3(0,uint3((extent+((1u<<shift)-1u))>>shift,1u,1u));');path.write_text(text,encoding='utf8')
path=dest/'tests/spring_extent_oracle.cpp';text=path.read_text(encoding='utf8');needle='unsigned expectedX=(maximum+1u+63u)/64u;';assert text.count(needle)==1
text=text.replace(needle,'unsigned groupParticles=capacity<=32u*65535u?32u:64u;unsigned expectedX=(maximum+1u+groupParticles-1u)/groupParticles;');path.write_text(text,encoding='utf8')
files=[];diff=[]
for path in dest.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(dest);old=base/rel
    if old.exists() and sha(old)==sha(path):continue
    files.append(str(rel));before=old.read_text(encoding='utf8') if old.exists() else '';after=path.read_text(encoding='utf8');diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=a.base+'/'+rel.as_posix(),tofile=a.name+'/'+rel.as_posix()))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8');write(ROOT/'evidence'/f'{a.name}-proof.json',proof)
item=dict(id='A024-01',version='alpha2.4',candidate=a.name,base=a.base,title='256-thread spring groups with unchanged eight-lane particle arithmetic',status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha2.4 W33 exact independent-output group packing, adapted to DF original per-particle eight-lane TGSM reduction',numerical_change=False,original_shader_change=False,required_validation=['original84 unchanged and two derived instruction proofs','direct/indirect group agreement; sparse/high ID/replace/clear','whole-capacity bit-exact spring oracle','large-capacity original512 fallback policy','FlexDemo dense/spare cloth, render fields and complete-frame timing'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[r for r in rows if r['id']!=item['id']]+[item]);event('candidate-prepared',**item)
