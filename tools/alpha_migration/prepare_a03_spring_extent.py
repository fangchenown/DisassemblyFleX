"""Prototype GPU-derived spring extent; retain original 84 solver shader programs."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a03-spring-extent-v1');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
changes={}
def put(path,new):
    old=(base/path).read_text(encoding='utf8') if (base/path).exists() else ''
    changes[path]=(old,new);(dest/path).parent.mkdir(parents=True,exist_ok=True);(dest/path).write_text(new,encoding='utf8')
put('shaders/auxiliary/SpringDispatchArgs.hlsl','''// New integer-only helper, not reconstructed NVIDIA shader source.
// The sorted endpoint keys remain intact here, immediately after SetSprings.
cbuffer Arguments : register(b0) { uint springCount; uint capacity; uint2 unused; };
Buffer<uint> endpointKeys : register(t0);
RWByteAddressBuffer dispatchArguments : register(u0);
[numthreads(1,1,1)]
void main() {
    uint extent=capacity;
    if(springCount!=0 && capacity!=0) {
        uint maximum=endpointKeys[springCount*2u-1u];
        // Keep the original full launch for out-of-range input; this helper
        // never tries to repair or reinterpret invalid spring endpoints.
        if(maximum<capacity)extent=maximum+1u;
    }
    dispatchArguments.Store3(0,uint3((extent+63u)/64u,1u,1u));
}
''')
put('tools/build_aux_shaders.py','''"""Compile newly authored integer-only scheduling helpers separately from original kernels."""
import argparse,hashlib,json
from pathlib import Path
from dxbc_tools import compile_hlsl,disassemble,select_compiler
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True);a=p.parse_args();select_compiler(a.compiler);a.output.mkdir(parents=True,exist_ok=True)
source=a.source.read_text(encoding='utf8');hr,code,error=compile_hlsl(source,a.source.name);assert hr>=0,error
assembly=disassemble(code);(a.output/'SpringDispatchArgs.dxbc').write_bytes(code);(a.output/'SpringDispatchArgs.asm').write_text(assembly,encoding='utf8')
header='#pragma once\\n#include "NvFlexShaders.generated.hpp"\\nnamespace df { const ShaderCode* FindAuxiliaryShaderCode(const char*); }\\n'
body='#include "NvFlexAuxShaders.generated.hpp"\\n#include <cstring>\\nnamespace df {\\nalignas(16) static const std::uint8_t bytes[]={'+','.join(str(x) for x in code)+'};\\nstatic const ShaderCode shader={"df_BuildSpringDispatchArgs",L"BuildSpringDispatchArgs",bytes,sizeof(bytes),~0u,0u};\\nconst ShaderCode* FindAuxiliaryShaderCode(const char* name){return std::strcmp(name,shader.name)==0?&shader:nullptr;}\\n}\\n'
(a.output/'NvFlexAuxShaders.generated.hpp').write_text(header,encoding='utf8');(a.output/'NvFlexAuxShaders.generated.cpp').write_text(body,encoding='utf8')
(a.output/'aux_shader_manifest.json').write_text(json.dumps(dict(source=str(a.source),source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),dxbc_sha256=hashlib.sha256(code).hexdigest(),compiler=str(a.compiler),compiler_sha256=hashlib.sha256(a.compiler.read_bytes()).hexdigest(),new_helper=True,integer_only=True),indent=2),encoding='utf8')
''')
path='CMakeLists.txt';s=(base/path).read_text(encoding='utf8');marker='file(GLOB_RECURSE restored_sources CONFIGURE_DEPENDS src/*.cpp)';assert s.count(marker)==1
command='''add_custom_command(OUTPUT "${CMAKE_BINARY_DIR}/generated/NvFlexAuxShaders.generated.cpp"
  "${CMAKE_BINARY_DIR}/generated/NvFlexAuxShaders.generated.hpp" "${CMAKE_BINARY_DIR}/generated/aux_shader_manifest.json"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_aux_shaders.py"
    --source "${CMAKE_CURRENT_SOURCE_DIR}/shaders/auxiliary/SpringDispatchArgs.hlsl"
    --output "${CMAKE_BINARY_DIR}/generated" --compiler "${DISASSEMBLYFLEX_SHADER_COMPILER_DLL}"
  DEPENDS tools/build_aux_shaders.py tools/dxbc_tools.py shaders/auxiliary/SpringDispatchArgs.hlsl VERBATIM)
'''
s=s.replace(marker,command+marker).replace('add_library(NvFlexReconstructed SHARED ${restored_sources}','add_library(NvFlexReconstructed SHARED ${restored_sources}\n  "${CMAKE_BINARY_DIR}/generated/NvFlexAuxShaders.generated.cpp"');put(path,s)
path='src/runtime/ShaderLibrary.cpp';s=(base/path).read_text(encoding='utf8').replace('#include "NvFlexShaders.generated.hpp"','#include "NvFlexShaders.generated.hpp"\n#include "NvFlexAuxShaders.generated.hpp"').replace('auto code=FindShaderCode(name);if(!code)throw','auto code=FindShaderCode(name);if(!code)code=FindAuxiliaryShaderCode(name);if(!code)throw');put(path,s)
path='src/solver/SolverState.hpp';s=(base/path).read_text(encoding='utf8');marker='    std::unique_ptr<RadixSort> radix;';assert s.count(marker)==1
s=s.replace(marker,marker+'''
    BufferSlot springDispatchArgs;
    ConstantSlot springDispatchParams;
    bool springDispatchReady=false;
    unsigned springDispatchCapacity=0;
    int springDispatchCount=0;''');put(path,s)
path='src/api/SpringApi.cpp';s=(base/path).read_text(encoding='utf8');marker='    auto& s=solver->state;auto library=SolverLibrary(solver);auto context=library->mContext;';assert s.count(marker)==1
s=s.replace(marker,marker+'\n    solver->storage.springDispatchReady=false;')
marker='        radix.sort(unsigned(count*2),32);';assert s.count(marker)==1
s=s.replace(marker,marker+'''
        // Prepare a bound without any CPU readback. Only large spare-capacity
        // solvers can amortize indirect-launch overhead; sparse high IDs are
        // still included because the actual maximum endpoint comes from GPU.
        if(s.mMaxParticles>=16384 && (s.mNumParticles==0 ||
                unsigned(s.mMaxParticles)/2u>=unsigned(s.mNumParticles))){
            auto& storage=solver->storage;
            if(!storage.springDispatchArgs.buffer){
                df::Allocate(solver,&storage.springDispatchArgs,3,4,
                    NvFlex::eBuffer|NvFlex::eUAV_SRV|NvFlex::eRaw|NvFlex::eIndirect);
                df::AllocateConstant(solver,&storage.springDispatchParams,16);
            }
            unsigned values[4]={unsigned(count),unsigned(s.mMaxParticles),0,0};
            auto constant=storage.springDispatchParams.buffer;
            std::memcpy(context->map(constant),values,sizeof(values));context->unmap(constant);
            NvFlex::DispatchParams args{};args.shader=df::GetShader(library,"df_BuildSpringDispatchArgs");
            args.rootConstantBuffer=constant;args.gridDim={1,1,1};
            args.readOnly[0]=radix.front.key->getResource();
            args.readWrite[0]=storage.springDispatchArgs.buffer->getResourceRW();
            context->dispatch(&args);
            storage.springDispatchCapacity=unsigned(s.mMaxParticles);
            storage.springDispatchCount=count;storage.springDispatchReady=true;
        }''');put(path,s)
path='src/solver/ParticleStep.cpp';s=(base/path).read_text(encoding='utf8');s=s.replace('NvFlex::ConstantBuffer* second=nullptr){','NvFlex::ConstantBuffer* second=nullptr,NvFlex::Buffer* indirect=nullptr){',1)
s=s.replace('    library->mContext->dispatch(&p);','    if(indirect){p.IndirectLaunchArgs=indirect;library->mContext->dispatchIndirect(&p);}\n    else library->mContext->dispatch(&p);',1)
start=s.index('        if(s.mNumSprings){');end=s.index('        if(s.mNumInflatables){',start);block=s[start:end]
needle='            Pass(solver,spring,';assert block.count(needle)==1
block=block.replace(needle,'''            auto& storage=solver->storage;
            const bool useExtent=storage.springDispatchReady &&
                storage.springDispatchCapacity==unsigned(s.mMaxParticles) &&
                storage.springDispatchCount==s.mNumSprings &&
                unsigned(s.mMaxParticles)/2u>=unsigned(s.mNumParticles);
'''+needle)
needle='{{0,B(s.mDeltas)}});}';assert block.count(needle)==1
block=block.replace(needle,'{{0,B(s.mDeltas)}},true,nullptr,useExtent?storage.springDispatchArgs.buffer:nullptr);}')
s=s[:start]+block+s[end:];put(path,s)
path='src/api/CopySolverApi.cpp';s=(base/path).read_text(encoding='utf8');needle='    auto& dst=destination->state;auto& src=source->state;';assert s.count(needle)==1
s=s.replace(needle,'    destination->storage.springDispatchReady=false;\n'+needle);put(path,s)
put('tests/spring_extent_oracle.cpp',(Path(__file__).parent/'templates/spring_extent_oracle.cpp').read_text(encoding='utf8'))
path='CMakeLists.txt';s=(dest/path).read_text(encoding='utf8');s+='''
add_executable(DisassemblySpringExtentOracle tests/spring_extent_oracle.cpp)
target_compile_features(DisassemblySpringExtentOracle PRIVATE cxx_std_17)
target_compile_definitions(DisassemblySpringExtentOracle PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN _CRT_SECURE_NO_WARNINGS)
target_include_directories(DisassemblySpringExtentOracle PRIVATE include src "${DISASSEMBLYFLEX_WORKSPACE}/FleX")
''';put(path,s)
diff=[]
for path,(old,new) in changes.items():diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a.base+'/'+path,tofile=a.name+'/'+path))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
item=dict(id='A003-01',version='alpha0.3',candidate=a.name,base=a.base,title='GPU-derived maximum spring endpoint bounds an otherwise empty dispatch tail',status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha0.3 C03 work-bound audit, reinforced by alpha1.1/alpha2.0/alpha2.1/alpha2.3 exact-extent ideas',numerical_change=False,original_shader_change=False,new_auxiliary_shader='Integer-only SpringDispatchArgs, separately compiled and manifested; not NVIDIA recovered code.',invariants=['maximum actual referenced particle, not activeCount','full 64-particle groups; original eight-lane reduction unchanged','empty rows have no global UAV writes in original 032/075 kernels','no CPU readback or wait','default direct launch for dense/small/unprepared/copy-invalidated topology'],required_validation=['84 original containers unchanged','helper integer code / args readback for low/high/sparse/invalid endpoint bounds','SetSprings replace/clear/grow and sparse-active high IDs','D3D11/D3D12 generic and NV original particle results','FlexDemo spare-capacity and ordinary scenes with same workload','startup/memory/whole-frame regression'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[x for x in rows if x['id']!=item['id']]+[item]);event('candidate-prepared',**item)
