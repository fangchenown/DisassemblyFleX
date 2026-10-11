"""Pack exact spring metadata; preserve every original floating-point instruction."""
import argparse,difflib
from common import *
from auxiliary_support import configure
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name;assert not dest.exists();shutil.copytree(base,dest)
sys.path.insert(0,str(PROJECT/'tools'));from dxbc_assembler import instruction_lines
from shader_lowering import Lifter
entries=[];proof=[]
for index,stem,name in [(32,'SpringPacked12','df_SpringPacked12'),(75,'SpringPacked12NV','df_SpringPacked12NV')]:
    path=next((base/'shaders/machine').glob(f'{index:03}*.smasm'));old=list(instruction_lines(path.read_text(encoding='utf8')));new=[]
    for line in old:
        if line in ['dcl_resource_structured t2, 4','dcl_resource_structured t3, 4']:continue
        if line=='dcl_resource_structured t1, 4':line='dcl_resource_structured t1, 12'
        elif line=='dcl_temps 7':line='dcl_temps 8'
        elif line.endswith('r3.w, r1.w, l(0x00000000), t1.xxxx'):
            new.append('ld_structured_indexable(structured_buffer, stride=12)(mixed,mixed,mixed,mixed) r7.xyz, r1.w, l(0x00000000), t1.xyzx');line='mov r3.w, r7.x'
        elif line.endswith('r5.z, r1.w, l(0x00000000), t2.xxxx'):line='mov r5.z, r7.y'
        elif line.endswith('r6.y, r1.w, l(0x00000000), t3.xxxx'):line='mov r6.y, r7.z'
        new.append(line)
    unchanged=lambda lines:[s for s in lines if not s.startswith(('dcl_','ld_','store_','mov '))]
    assert unchanged(old)==unchanged(new)
    assembly='// Derived metadata layout; original floating-point instructions retained.\ncs_5_0\n'+'\n'.join(new)+'\n'
    (dest/'shaders/auxiliary'/(stem+'.smasm')).write_text(assembly,encoding='utf8');(dest/'shaders/auxiliary'/(stem+'.hlsl')).write_text(Lifter({},assembly).run(),encoding='utf8')
    entries.append(dict(name=name,source=stem+'.hlsl',instructions=stem+'.smasm',original_index=index,kind='exact-bit-metadata-packing'))
    proof.append(dict(index=index,original_sha256=sha(path),non_memory_arithmetic_unchanged=True))
path=next((base/'shaders/machine').glob('*SpringsReorder.smasm'));index=int(path.name[:3]);old=list(instruction_lines(path.read_text(encoding='utf8')));new=[]
for line in old:
    if line in ['dcl_uav_structured u1, 4','dcl_uav_structured u2, 4']:continue
    if line=='dcl_uav_structured u0, 4':line='dcl_uav_structured u0, 12'
    line=line.replace('store_structured u1.x, vThreadID.x, l(0x00000000),','store_structured u0.x, vThreadID.x, l(0x00000004),').replace('store_structured u2.x, vThreadID.x, l(0x00000000),','store_structured u0.x, vThreadID.x, l(0x00000008),')
    new.append(line)
assembly='// Exact-bit twelve-byte output record.\ncs_5_0\n'+'\n'.join(new)+'\n';stem='SpringReorderPacked12'
(dest/'shaders/auxiliary'/(stem+'.smasm')).write_text(assembly,encoding='utf8');(dest/'shaders/auxiliary'/(stem+'.hlsl')).write_text(Lifter({},assembly).run(),encoding='utf8');entries.append(dict(name='df_'+stem,source=stem+'.hlsl',instructions=stem+'.smasm',original_index=index,kind='exact-bit-metadata-packing'));configure(dest,entries)
path=dest/'src/api/SpringApi.cpp';s=path.read_text(encoding='utf8');s=s.replace('df::ReserveBuffer(solver,s.mHalfSpringOpposites,capacity,4);','df::ReserveBuffer(solver,s.mHalfSpringOpposites,capacity,12);').replace('df::ReserveBuffer(solver,s.mHalfSpringLengths,capacity,4);df::ReserveBuffer(solver,s.mHalfSpringStiffness,capacity,4);','').replace('"g_Flex_SpringsReorder"','"df_SpringReorderPacked12"').replace('p.readWrite[1]=df::Slot(s.mHalfSpringLengths).buffer->getResourceRW();p.readWrite[2]=df::Slot(s.mHalfSpringStiffness).buffer->getResourceRW();','');path.write_text(s,encoding='utf8')
path=dest/'src/solver/ParticleStep.cpp';s=path.read_text(encoding='utf8').replace('"g_Flex_SolveSprings"','"df_SpringPacked12"').replace('"g_Flex_SolveSpringsNV"','"df_SpringPacked12NV"').replace('{2,B(s.mHalfSpringLengths)},{3,B(s.mHalfSpringStiffness)},','');path.write_text(s,encoding='utf8')
path=dest/'tests/spring_extent_oracle.cpp';s=path.read_text(encoding='utf8');s=s.replace('springs(128)','springs(1024)').replace('lengths(64,.21f),stiffness(64,.5f)','lengths(512),stiffness(512)').replace('i<64;++i){springs','i<512;++i){lengths[i]=.11f+.003f*float(i%71);const float k[]={-1.f,-.3f,-0.f,0.f,.1f,.7f,1.f};stiffness[i]=k[i%7];springs').replace('buffer(128,4,springs.data())','buffer(1024,4,springs.data())').replace('buffer(64,4,lengths.data())','buffer(512,4,lengths.data())').replace('buffer(64,4,stiffness.data())','buffer(512,4,stiffness.data())').replace('frame==3)set(64)','frame==3)set(256)').replace('frame==8)set(32)','frame==8)set(128)').replace('frame==10)set(64)','frame==10)set(512)');path.write_text(s,encoding='utf8')
diff=[]
for path in dest.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(dest);old=base/rel
    if old.exists() and sha(old)==sha(path):continue
    before=old.read_text(encoding='utf8') if old.exists() else '';diff.extend(difflib.unified_diff(before.splitlines(True),path.read_text(encoding='utf8').splitlines(True),fromfile=a.base+'/'+rel.as_posix(),tofile=a.name+'/'+rel.as_posix()))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
row=dict(id='A042-01',version='alpha4.2',also_inspired_by='alpha7.3 exact metadata packing',candidate=a.name,base=a.base,title='Exact twelve-byte spring metadata, unchanged floating-point schedule',status='candidate-prepared',source=str(dest),evidence=str(patch),instruction_proof=proof,numerical_change=False,original_shader_change=False,required_validation=['both generic/NV full-capacity outputs with mixed signed stiffness/high degree','source plus instruction arithmetic proof','API/resource regressions','FlexDemo long quality and completed-frame timings'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[r for r in rows if r['id']!=row['id']]+[row]);event('candidate-prepared',**row)
