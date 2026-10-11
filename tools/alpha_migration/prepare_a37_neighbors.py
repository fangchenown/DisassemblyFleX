"""Two independently measured, order-preserving transformations of original shader058."""
import argparse,difflib
from common import *
from auxiliary_support import configure
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);p.add_argument('--kind',choices=['distance-first','full-row-return'],required=True);a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
sys.path.insert(0,str(PROJECT/'tools'));from shader_lowering import Lifter
from dxbc_assembler import instruction_lines
path=base/'shaders/machine/058_g_Flex_CollideParticles.smasm';old=list(instruction_lines(path.read_text(encoding='utf8')));new=list(old)
def matching_end(lines,start):
    assert lines[start].startswith('if_');depth=1
    for i in range(start+1,len(lines)):
        if lines[i].startswith('if_'):depth+=1
        if lines[i]=='endif':
            depth-=1
            if depth==0:return i
    raise AssertionError('Unbalanced original shader')
if a.kind=='distance-first':
    begin=old.index('and r5.x, r1.z, r5.x');end=matching_end(old,begin+1)
    distance=old[end+1:end+5];assert len(distance)==4 and 't3.xyzx' in distance[0] and distance[-1]=='lt r5.x, r5.x, cb0[25].x'
    assert old[end+5]=='if_nz r5.x'
    rest=old[begin+1:end+1];assert rest[0]=='if_nz r5.x';rest[0]='if_nz r5.y'
    new=old[:begin]+['and r5.y, r1.z, r5.x']+distance+['if_nz r5.x']+rest+old[end+6:]
    name='df_CollideParticlesDistanceFirst';stem='NeighborsDistanceFirst';key='A037-01';reason='Phase acceptance unchanged; evaluate the same current-distance predicate before the same rest-space predicate. Preserve candidate iteration and bounded append order.'
else:
    begin=old.index('ilt r5.x, r8.z, cb0[30].w');assert old[begin+1]=='if_nz r5.x';end=matching_end(old,begin+1)
    assert old[begin+2:end]==['store_structured u0.x, r8.y, l(0x00000000), r8.x','iadd r8.y, r8.y, cb0[23].y','iadd r8.z, r8.z, l(0x00000001)']
    assert not any(x.startswith(('dcl_tgsm','sync','atomic','imm_atomic')) for x in old)
    new=old[:end]+['else','store_structured u1.x, vThreadID.x, l(0x00000000), r8.z','ret']+old[end:]
    name='df_CollideParticlesFullRow';stem='NeighborsFullRow';key='A037-02';reason='Only on the existing capacity-test failure: publish the already saturated count and return. Original DF increments count only inside capacity and exposes no full-overflow statistic; unlike OF alpha7.1b, this loses no required overflow count. Non-full path gets no extra predicate.'
assembly='// Derived from original shader058; ordered rows and capacity semantics retained.\ncs_5_0\n'+'\n'.join(new)+'\n';directory=dest/'shaders/auxiliary';(directory/(stem+'.smasm')).write_text(assembly,encoding='utf8');(directory/(stem+'.hlsl')).write_text(Lifter({},assembly).run(),encoding='utf8')
configure(dest,[dict(name=name,source=stem+'.hlsl',instructions=stem+'.smasm',original_index=58,kind=a.kind)])
path=dest/'src/solver/ParticleStep.cpp';text=path.read_text(encoding='utf8');needle='Pass(solver,"g_Flex_CollideParticles",';assert text.count(needle)==1;text=text.replace(needle,'Pass(solver,"'+name+'",');path.write_text(text,encoding='utf8')
test=Path(__file__).parent/'templates/neighbor_kernel_oracle.cpp';assert test.exists();shutil.copy2(test,dest/'tests/neighbor_kernel_oracle.cpp')
path=dest/'CMakeLists.txt';text=path.read_text(encoding='utf8');text+='''
add_executable(DisassemblyNeighborKernelOracle tests/neighbor_kernel_oracle.cpp)
target_compile_features(DisassemblyNeighborKernelOracle PRIVATE cxx_std_17)
target_compile_definitions(DisassemblyNeighborKernelOracle PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN _CRT_SECURE_NO_WARNINGS)
target_include_directories(DisassemblyNeighborKernelOracle PRIVATE include src "${DISASSEMBLYFLEX_WORKSPACE}/FleX")
''';path.write_text(text,encoding='utf8')
diff=[]
for path in dest.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(dest);original=base/rel
    if original.exists() and sha(original)==sha(path):continue
    before=original.read_text(encoding='utf8') if original.exists() else '';after=path.read_text(encoding='utf8');diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=a.base+'/'+rel.as_posix(),tofile=a.name+'/'+rel.as_posix()))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8');proof=dict(source_sha256=sha(base/'shaders/machine/058_g_Flex_CollideParticles.smasm'),transformation=reason,original_instructions=len(old),derived_instructions=len(new),original_shaders_retained=84,auxiliary_dxBC=stem+'.dxbc');write(ROOT/'evidence'/f'{a.name}-proof.json',proof)
item=dict(id=key,version='alpha3.7',candidate=a.name,base=a.base,title=reason,status='candidate-prepared',source=str(dest),evidence=str(patch),proof=proof,numerical_change=False,original_shader_change=False,required_validation=['direct original-vs-derived full row/count byte equality','phase/self/rest/current thresholds, wrapped hash aliases and nonidentity original map','zero/capacity/overflow/untouched-tail cases','API/callback/physics/whole-frame FlexDemo in both backends'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[r for r in rows if r['id']!=key]+[item]);event('candidate-prepared',**item)
