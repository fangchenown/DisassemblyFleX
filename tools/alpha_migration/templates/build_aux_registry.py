"""Build authored integer helpers and instruction-preserved derived programs."""
import argparse,hashlib,json,re
from pathlib import Path
from dxbc_tools import compile_hlsl,disassemble,select_compiler
from dxbc_assembler import assemble_program,replace_program,instruction_lines
from shader_lowering import Lifter
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--hash-helper',type=Path,required=True);a=p.parse_args();select_compiler(a.compiler);a.output.mkdir(parents=True,exist_ok=True)
registry=json.loads((a.source.parent/'registry.json').read_text(encoding='utf8'));entries=[];manifest=[];body=['#include "NvFlexAuxShaders.generated.hpp"','#include <cstring>','namespace df {']
for i,item in enumerate(registry):
    path=a.source.parent/item['source'];source=path.read_text(encoding='utf8');instructions=None
    if item.get('instructions'):
        instructions=(a.source.parent/item['instructions']).read_text(encoding='utf8');assert Lifter({},instructions).run()==source,'HLSL/instruction mismatch: '+path.name
    hr,code,error=compile_hlsl(source,path.name);assert hr>=0,error
    if instructions is not None:
        code=replace_program(code,assemble_program(instructions),a.hash_helper);normalize=lambda s:re.sub(r'\s+','',s)
        assert list(map(normalize,instruction_lines(disassemble(code))))==list(map(normalize,instruction_lines(instructions)))
    stem=path.stem;(a.output/(stem+'.dxbc')).write_bytes(code);(a.output/(stem+'.asm')).write_text(disassemble(code),encoding='utf8')
    body.append(f'alignas(16) static const std::uint8_t code{i}[]={{'+','.join(str(x) for x in code)+'};')
    if 'original_index' in item:
        original='kRecoveredShaders['+str(item['original_index'])+']';label=original+'.label';slot=original+'.nvSlot';vendor=original+'.vendorEncoding'
    else:label='L'+json.dumps(item['label']);slot='~0u';vendor='0u'
    entries.append('{'+json.dumps(item['name'])+','+label+f',code{i},sizeof(code{i}),'+slot+','+vendor+'}')
    manifest.append(dict(item,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),dxbc_sha256=hashlib.sha256(code).hexdigest(),instruction_sha256=hashlib.sha256(instructions.encode()).hexdigest() if instructions else None,preserved_schedule=instructions is not None,compiler_sha256=hashlib.sha256(a.compiler.read_bytes()).hexdigest()))
body+=['static const ShaderCode shaders[]={'+','.join(entries)+'};','const ShaderCode* FindAuxiliaryShaderCode(const char* name){for(const auto& shader:shaders)if(std::strcmp(name,shader.name)==0)return &shader;return nullptr;}','}']
(a.output/'NvFlexAuxShaders.generated.hpp').write_text('#pragma once\n#include "NvFlexShaders.generated.hpp"\nnamespace df {const ShaderCode* FindAuxiliaryShaderCode(const char*); }\n',encoding='utf8')
(a.output/'NvFlexAuxShaders.generated.cpp').write_text('\n'.join(body)+'\n',encoding='utf8');(a.output/'aux_shader_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
