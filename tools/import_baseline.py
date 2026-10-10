"""Seed independent sources from verified local reconstruction inputs."""
import csv,hashlib,json,re,shutil
from pathlib import Path
from ledger import PROJECT,LEDGER,write_json,event
WS=PROJECT.parent
OLD=WS/'Build/NvFlexSourceRecovery-20261009'
ASM=WS/'Build/NvFlexDisassembly-20261009'
OUTPUT=WS/'Build/DisassemblyFleX-20261009'
for name in ['include','src/api','src/runtime','src/solver','shaders/recovered','shaders/readable','reference','tests/demo','cmake']:
    (PROJECT/name).mkdir(parents=True,exist_ok=True)
files={}
def copy(source,destination):
    destination=PROJECT/destination
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        equal=source.read_bytes()==destination.read_bytes()
        adapted=destination.name=='NvFlex.h' and destination.read_text(encoding='utf-8')==source.read_text(encoding='utf-8').replace('#define NV_FLEX_API __declspec(dllexport)','#define NV_FLEX_API')
        if not equal and not adapted:raise RuntimeError('Refusing baseline overwrite: '+str(destination))
    else:shutil.copyfile(source,destination)
    files[destination.relative_to(PROJECT).as_posix()]={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
for src in sorted((OLD/'hlsl/recovered').glob('*.hlsl')):copy(src,'shaders/recovered/'+src.name)
for src in sorted((OLD/'hlsl/readable').iterdir()):copy(src,'shaders/readable/'+src.name)
for name in ['FlexLayouts.hpp','FlexCore.hpp']:copy(OLD/'cpp/recovered'/name,'include/recovered/'+name)
for name in ['NvFlex.h','NvFlexExt.h','NvFlexDevice.h']:copy(WS/'FleX/include'/name,'include/'+name)
# Keep public declarations/inline helpers, but .def exclusively controls DLL exports.
header=PROJECT/'include/NvFlex.h'
source=header.read_text(encoding='utf-8')
source=source.replace('#define NV_FLEX_API __declspec(dllexport)','#define NV_FLEX_API')
header.write_text(source,encoding='utf-8')
files['include/NvFlex.h']['adaptation']='Export attributes removed; module definition preserves exact names/ordinals.'
files['include/NvFlex.h']['adapted_sha256']=hashlib.sha256(header.read_bytes()).hexdigest()
copy(ASM/'exports.csv','reference/exports.csv')
copy(ASM/'metadata.json','reference/input_metadata.json')
copy(OLD/'cpp/source_index.json','reference/recovered_source_index.json')
copy(OLD/'verification.json','reference/prior_verification.json')
copy(OLD/'hlsl/recovery_results.json','reference/prior_shader_validation.json')
record={'schema_version':1,'origin':files,'disassembly_root':str(ASM),'decompilation_root':str(OLD),
        'scope':'Public SDK declarations + source HLSL + verified small C++ functions. No original DLL/PE instruction payload in candidate sources.'}
write_json(PROJECT/'reference/provenance.json',record)
write_json(OUTPUT/'evidence/P00_inputs.json',record)
event('baseline-sources-imported','已固定84个HLSL、3个人工整理Shader、公共头文件和可编译布局；DLL/PDB作为只读对照输入。',evidence=str(OUTPUT/'evidence/P00_inputs.json'))
print('Imported',len(files),'files')
