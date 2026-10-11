"""Alpha0.6 allocation/cache/compiler ideas adapted without changing GPU work."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);p.add_argument('--kind',choices=['shader-names','retained-set','ipo'],required=True);a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
changes={}
def edit(path,old,new):
    assert old!=new;changes[path]=(old,new);(dest/path).write_text(new,encoding='utf8')
if a.kind=='shader-names':
    path='src/runtime/Runtime.hpp';old=(base/path).read_text(encoding='utf8');needle='std::map<std::string,NvFlex::ComputeShader*> shaders;';assert old.count(needle)==1
    edit(path,old,old.replace(needle,'std::map<std::string,NvFlex::ComputeShader*,std::less<>> shaders;'))
    path='src/solver/ParticleStep.cpp';old=(base/path).read_text(encoding='utf8');start=old.index('    std::string suffix=');end=old.index('    Pass(solver,bounds.c_str()',start)
    new=old[:start]+'''    const bool boundsNv=library->enableExtensions&&library->shflSupported;
    const char* bounds=library->swizzleSupported?"g_Flex_CalculateBoundsAMD":boundsNv?"g_Flex_CalculateBoundsNV":"g_Flex_CalculateBounds";
    const char* group=library->swizzleSupported?"g_Flex_CalculateBoundsGroupAMD":boundsNv?"g_Flex_CalculateBoundsGroupNV":"g_Flex_CalculateBoundsGroup";
    const char* finalize=library->swizzleSupported?"g_Flex_CalculateBoundsFinalizeAMD":boundsNv?"g_Flex_CalculateBoundsFinalizeNV":"g_Flex_CalculateBoundsFinalize";
'''+old[end:]
    for name in ['bounds','group','finalize']:new=new.replace(name+'.c_str()',name)
    start=new.index('            bool plastic=B(s.mRigidPlasticThresholds)');end=new.index('            Pass(solver,name.c_str()',start)
    new=new[:start]+'''            bool plastic=B(s.mRigidPlasticThresholds)&&B(s.mRigidPlasticCreeps);
            const char* name=plastic?"g_Flex_SolveShapesPlasticDeformation":"g_Flex_SolveShapes";
            if(library->enableExtensions&&library->shflSupported&&library->fp32AtomicSupported){
                int average=s.mNumRigidIndices/s.mNumRigids;
                if(plastic)name=average<=32?"g_Flex_SolveShapesPlasticDeformation32NV":average>127?"g_Flex_SolveShapesPlasticDeformation128NV":"g_Flex_SolveShapesPlasticDeformationNV";
                else name=average<=32?"g_Flex_SolveShapes32NV":average>127?"g_Flex_SolveShapes128NV":"g_Flex_SolveShapesNV";
            }
'''+new[end:];new=new.replace('Pass(solver,name.c_str(),','Pass(solver,name,');edit(path,old,new)
    id='A006-01';mechanism='Transparent ordered-map lookup avoids temporary std::string allocation on every GetShader cache hit; fixed literals replace transient bounds/rigid shader-name concatenation. Preserve exact keys, vendor precedence and ordered shader destruction.'
elif a.kind=='retained-set':
    path='src/runtime/D3D12Resources.hpp';old=(base/path).read_text(encoding='utf8');assert old.count('std::set<IUnknown*> retainedSet;')==1
    new=old.replace('#include <set>','#include <unordered_set>').replace('std::set<IUnknown*> retainedSet;','std::unordered_set<IUnknown*> retainedSet;');edit(path,old,new)
    id='A006-02';mechanism='The private membership set is never iterated; unordered lookup preserves retained vector first-use order, AddRef count, fence retirement and destruction. No resource lifetime or barrier removed.'
else:
    path='CMakeLists.txt';old=(base/path).read_text(encoding='utf8');needle='  target_compile_options(NvFlexReconstructed PRIVATE /W4 /permissive- /fp:precise)';assert old.count(needle)==1
    new=old.replace(needle,needle+'''
  option(DISASSEMBLYFLEX_RELEASE_IPO "Enable Release whole-program optimization" ON)
  if(DISASSEMBLYFLEX_RELEASE_IPO)
    set_property(TARGET NvFlexReconstructed PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
    target_compile_options(NvFlexReconstructed PRIVATE $<$<CONFIG:Release>:/Gy> $<$<CONFIG:Release>:/Gw>)
    target_link_options(NvFlexReconstructed PRIVATE $<$<CONFIG:Release>:/OPT:REF> $<$<CONFIG:Release>:/OPT:ICF>)
  endif()''');edit(path,old,new)
    id='A006-03';mechanism='Release /GL + /LTCG, /Gy /Gw and linker folding while retaining /fp:precise, exact exports and all shader blobs. CPU parameter bytes and callback/API layout must pass unchanged.'
diff=[]
for path,(old,new) in changes.items():diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a.base+'/'+path,tofile=a.name+'/'+path))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
item=dict(id=id,version='alpha0.6',candidate=a.name,base=a.base,kind=a.kind,title=mechanism,status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha0.6 CPU allocation/cache/LTCG audit; adapted to DF actual hot-path structures',numerical_change=False,shader_change=False,required_validation=['exact 84 shaders','ABI/export/KernelParams/callback/particle oracles','external D3D11/D3D12 lifecycle','whole-frame paired FlexDemo','separate CPU and shader claims'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[x for x in rows if x['id']!=id]+[item]);event('candidate-prepared',**item)
