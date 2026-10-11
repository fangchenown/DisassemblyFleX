"""Specialize a provably untaken shape branch; preserve live NVIDIA instructions."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a03-planes-v1');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
sys.path.insert(0,str(PROJECT/'tools'));from shader_lowering import Lifter
from dxbc_assembler import instruction_lines
changes={}
def put(path,new):
    old=(base/path).read_text(encoding='utf8') if (base/path).exists() else '';changes[path]=(old,new);(dest/path).parent.mkdir(parents=True,exist_ok=True);(dest/path).write_text(new,encoding='utf8')
original=(base/'shaders/machine/070_g_Flex_CollideShapes.smasm').read_text(encoding='utf8');lines=list(instruction_lines(original));start=lines.index('if_nz cb0[26].x');depth=1;end=None
for i in range(start+1,len(lines)):
    opcode=lines[i].split()[0]
    if opcode.startswith('if_'):depth+=1
    if opcode=='else' and depth==1:raise AssertionError('Unexpected outer else')
    if opcode=='endif':
        depth-=1
        if depth==0:end=i;break
assert end is not None
remaining=lines[:start]+lines[end+1:]
# The stack belongs exclusively to the removed BVH walk. No active instruction
# may access it. Leave all resources and constant declarations unchanged.
assert not any(re.search(r'\bx0\[',l) for l in remaining if not l.startswith('dcl_'))
remaining=[l for l in remaining if not l.startswith('dcl_indexableTemp')]
registers=[int(n) for line in remaining if not line.startswith('dcl_') for n in re.findall(r'\br(\d+)\b',line)]
remaining=[f'dcl_temps {max(registers)+1}' if l.startswith('dcl_temps ') else l for l in remaining]
assembly='// Derived only for uploaded kNumShapes==0; live instructions retain original order.\ncs_5_0\n'+'\n'.join(remaining)+'\n'
put('shaders/auxiliary/CollidePlanes.smasm',assembly);put('shaders/auxiliary/CollidePlanes.hlsl',Lifter({},assembly).run())
assert [l for l in remaining if not l.startswith('dcl_')]==[l for l in lines[:start]+lines[end+1:] if not l.startswith('dcl_')]
proof=dict(original_source_sha256=sha(base/'shaders/machine/070_g_Flex_CollideShapes.smasm'),normalized_text_sha256=hashlib.sha256(original.encode()).hexdigest(),condition='uploaded kNumShapes==0; no callbacks; no shape instances',removed_branch_instructions=end-start+1,live_instructions_unchanged=True,thread_group='128,1,1',temps=max(registers)+1,removed_dead_indexable_stack=True)
write(ROOT/'evidence'/f'{a.name}-specialization-proof.json',proof)
put('tools/build_aux_shaders.py','''"""Compile scheduling helper and exact dead-branch specialization separately."""
import argparse,hashlib,json,re
from pathlib import Path
from dxbc_tools import compile_hlsl,disassemble,select_compiler
from dxbc_assembler import assemble_program,replace_program,instruction_lines
from shader_lowering import Lifter
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--hash-helper',type=Path,required=True);a=p.parse_args();select_compiler(a.compiler);a.output.mkdir(parents=True,exist_ok=True)
body=['#include "NvFlexAuxShaders.generated.hpp"','#include <cstring>','namespace df {'];entries=[];manifest=[]
for index,(stem,name,label) in enumerate([('SpringDispatchArgs','df_BuildSpringDispatchArgs','L"BuildSpringDispatchArgs"'),('CollidePlanes','df_Flex_CollidePlanes','kRecoveredShaders[70].label')]):
    path=a.source.parent/(stem+'.hlsl');source=path.read_text(encoding='utf8');instructions=None
    if stem=='CollidePlanes':
        instructions=path.with_suffix('.smasm').read_text(encoding='utf8');assert Lifter({},instructions).run()==source
    hr,code,error=compile_hlsl(source,path.name);assert hr>=0,error
    if instructions is not None:
        code=replace_program(code,assemble_program(instructions),a.hash_helper)
        normalize=lambda x:re.sub(r'\\s+','',x)
        assert list(map(normalize,instruction_lines(disassemble(code))))==list(map(normalize,instruction_lines(instructions)))
    (a.output/(stem+'.dxbc')).write_bytes(code);(a.output/(stem+'.asm')).write_text(disassemble(code),encoding='utf8')
    body.append('alignas(16) static const std::uint8_t code'+str(index)+'[]={'+','.join(str(x) for x in code)+'};')
    entries.append('{"'+name+'",'+label+',code'+str(index)+',sizeof(code'+str(index)+'),~0u,0u}')
    manifest.append(dict(name=name,source=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),dxbc_sha256=hashlib.sha256(code).hexdigest(),kind='integer scheduling helper' if instructions is None else 'exact original live instruction sequence with provably false branch removed',preserved_schedule=instructions is not None,compiler_sha256=hashlib.sha256(a.compiler.read_bytes()).hexdigest()))
body+=['static const ShaderCode shaders[]={'+','.join(entries)+'};','const ShaderCode* FindAuxiliaryShaderCode(const char* name){for(const auto& shader:shaders)if(std::strcmp(name,shader.name)==0)return &shader;return nullptr;}','}']
(a.output/'NvFlexAuxShaders.generated.hpp').write_text('#pragma once\\n#include "NvFlexShaders.generated.hpp"\\nnamespace df {const ShaderCode* FindAuxiliaryShaderCode(const char*); }\\n',encoding='utf8')
(a.output/'NvFlexAuxShaders.generated.cpp').write_text('\\n'.join(body)+'\\n',encoding='utf8');(a.output/'aux_shader_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
''')
path='CMakeLists.txt';s=(base/path).read_text(encoding='utf8');old='    --output "${CMAKE_BINARY_DIR}/generated" --compiler "${DISASSEMBLYFLEX_SHADER_COMPILER_DLL}"';assert s.count(old)==1
s=s.replace(old,old+' --hash-helper "$<TARGET_FILE:DisassemblyDxbcHash>"');old='  DEPENDS tools/build_aux_shaders.py tools/dxbc_tools.py shaders/auxiliary/SpringDispatchArgs.hlsl VERBATIM)';assert s.count(old)==1
s=s.replace(old,'  DEPENDS tools/build_aux_shaders.py tools/dxbc_tools.py tools/dxbc_assembler.py tools/shader_lowering.py shaders/auxiliary/SpringDispatchArgs.hlsl shaders/auxiliary/CollidePlanes.hlsl shaders/auxiliary/CollidePlanes.smasm DisassemblyDxbcHash VERBATIM)');put(path,s)
path='src/solver/ParticleStep.cpp';s=(base/path).read_text(encoding='utf8');needle='if(std::strcmp(shader,"g_Flex_CollideShapes")==0&&library->geometry->sdfCount)';assert s.count(needle)==1
s=s.replace(needle,'if((std::strcmp(shader,"g_Flex_CollideShapes")==0||std::strcmp(shader,"df_Flex_CollidePlanes")==0)&&library->geometry->sdfCount)')
needle='    Pass(solver,"g_Flex_CollideShapes",boundsBlocks,';assert s.count(needle)==1
replacement='''    bool hasCallbacks=false;
    for(int stage=0;stage<int(eNvFlexStageCount);++stage){
        NvFlexSolverCallback callback{};std::memcpy(&callback,s.mCallbacks+sizeof(callback)*stage,sizeof(callback));
        hasCallbacks=hasCallbacks||callback.function!=nullptr;
    }
    const char* shapeShader=!hasCallbacks && shape.count==0 && s.mKernelParamsHost.kNumShapes==0
        ?"df_Flex_CollidePlanes":"g_Flex_CollideShapes";
    Pass(solver,shapeShader,boundsBlocks,'''
s=s.replace(needle,replacement);put(path,s)
put('tests/plane_kernel_oracle.cpp',(Path(__file__).parent/'templates/plane_kernel_oracle.cpp').read_text(encoding='utf8'))
path='CMakeLists.txt';s=(dest/path).read_text(encoding='utf8');s+='''
add_executable(DisassemblyPlaneKernelOracle tests/plane_kernel_oracle.cpp)
target_compile_features(DisassemblyPlaneKernelOracle PRIVATE cxx_std_17)
target_compile_definitions(DisassemblyPlaneKernelOracle PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN _CRT_SECURE_NO_WARNINGS)
target_include_directories(DisassemblyPlaneKernelOracle PRIVATE include src "${DISASSEMBLYFLEX_WORKSPACE}/FleX")
''';put(path,s)
diff=[]
for path,(old,new) in changes.items():diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a.base+'/'+path,tofile=a.name+'/'+path))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
item=dict(id='A003-02',version='alpha0.3',candidate=a.name,base=a.base,title='Plane-only shape collision with the original live instruction sequence',status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha0.3 C09 plane-only specialization idea, applied to original DF shader 070 rather than OF equations',proof=proof,numerical_change=False,original_shader_change=False,new_auxiliary_shader='Derived original instructions, not a guessed plane solver; original84 general path retained.',required_validation=['original84 exact; aux assembly roundtrip and false-path sequence proof','direct GPU original-vs-specialized counts/planes/velocities across threshold/capacity cases','zero/nonzero shape transition and callback fallback','diagnostic labels unchanged','FlexDemo all output domains and complete-frame paired timing'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[x for x in rows if x['id']!=item['id']]+[item]);event('candidate-prepared',**item)
