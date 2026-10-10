"""Compile all restored HLSL and emit a native registry; no input DXBC is used."""
import argparse,hashlib,json,re
from pathlib import Path
from dxbc_tools import compile_hlsl,disassemble,select_compiler
from dxbc_precision import restore_driver_refactoring,repair_checksum
from dxbc_assembler import assemble_program,replace_program,instruction_lines
from shader_lowering import Lifter

def precise_float_boundaries(source):
    replacements=[]
    for match in re.finditer(r'\basuint\(',source):
        start=match.end();end=start;depth=1
        while depth:
            if source[end]=='(':depth+=1
            elif source[end]==')':depth-=1
            end+=1
        expression=source[start:end-1]
        if 'asfloat(' in expression or '(float)' in expression or re.search(r'_(?:sin|cos)_',expression):replacements.append((match.start(),match.start()+6))
    for start,end in reversed(replacements):source=source[:start]+'df_precise_bits'+source[end:]
    helpers='\n'.join(f'uint{n} df_precise_bits(float{n} value) {{ precise float{n} result=value; return asuint(result); }}' for n in ['',2,3,4])+'\n'
    return helpers+source

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--instruction-source',type=Path);parser.add_argument('--schedule',choices=['fxc','preserved'],default='fxc');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--compiler',type=Path);parser.add_argument('--fp-policy',choices=['default','precise','frontend','float_frontend'],default='default');parser.add_argument('--hash-helper',type=Path);parser.add_argument('--relaxed-shaders',default='');args=parser.parse_args()
    if args.compiler:select_compiler(args.compiler)
    args.output.mkdir(parents=True,exist_ok=True)
    files=sorted(args.source.glob('*.hlsl'));assert len(files)==84
    header=['#pragma once','#include <cstddef>','#include <cstdint>',
            'namespace df { struct ShaderCode { const char* name; const wchar_t* label; const std::uint8_t* bytes; std::size_t size; std::uint32_t nvSlot; unsigned vendorEncoding; };',
            'extern const ShaderCode kRecoveredShaders[84];','const ShaderCode* FindShaderCode(const char* name);','}']
    body=['#include "NvFlexShaders.generated.hpp"','#include <cstring>','namespace df {'];entries=[];manifest=[]
    for index,path in enumerate(files):
        policy='default' if path.stem[4:] in args.relaxed_shaders.split(',') else args.fp_policy
        source=path.read_text(encoding='utf-8')
        instructions=None;instruction_hash=None
        if args.schedule=='preserved':
            instruction_path=args.instruction_source/(path.stem+'.smasm');instructions=instruction_path.read_text(encoding='utf-8')
            expected=Lifter({},instructions).run()
            normalize=lambda s:re.sub(r'\s+','',re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S))
            assert normalize(expected)==normalize(source),path.name+': HLSL and instruction source differ; update the paired sources before preserving the schedule'
            instruction_hash=hashlib.sha256(instruction_path.read_bytes()).hexdigest()
        if policy in ('precise','frontend','float_frontend'):source=re.sub(r'(?m)^(\s*)uint4 ([rx]\d+)([;\[])',r'\1precise uint4 \2\3',source)
        if policy=='float_frontend':source=precise_float_boundaries(source)
        (args.output/path.name).write_text(source,encoding='utf-8')
        hr,code,errors=compile_hlsl(source,path.name)
        (args.output/(path.stem+'.compile.log')).write_text(errors,encoding='utf-8')
        if hr<0:raise RuntimeError(path.name+'\n'+errors)
        changed=0
        if policy in ('frontend','float_frontend'):
            assert args.hash_helper and repair_checksum(code,args.hash_helper)==code,'DXBC checksum implementation validation failed'
            code,changed=restore_driver_refactoring(code,args.hash_helper)
        if instructions is not None:
            code=replace_program(code,assemble_program(instructions),args.hash_helper)
            normalize_instruction=lambda line:re.sub(r'\s+','',line)
            assert list(map(normalize_instruction,instruction_lines(disassemble(code))))==list(map(normalize_instruction,instruction_lines(instructions))),path.name+': encoded instruction roundtrip failed'
        (args.output/(path.stem+'.dxbc')).write_bytes(code)
        assembly=disassemble(code)
        group=re.search(r'dcl_thread_group\s+(\d+),\s*(\d+),\s*(\d+)',assembly);assert group
        nv='.IncrementCounter()' in source
        amd='InterlockedCompareExchange' in source and re.search(r'0x50[0-9a-f]{6}u',source) is not None
        name=path.stem[4:];label=re.sub(r'^g_(?:Flex_|bvh_)?','',name)
        if label.startswith('RadixSort'):label='r'+label[1:]
        body.append(f'alignas(16) static const std::uint8_t shader_{index}[] = {{')
        body.extend('  '+','.join(f'0x{x:02x}' for x in code[i:i+24])+',' for i in range(0,len(code),24));body.append('};')
        slot='7u' if nv else '~0u';vendor=1 if nv else (2 if amd else 0)
        entries.append(f'{{"{name}",L"{label}",shader_{index},sizeof(shader_{index}),{slot},{vendor}u}}')
        manifest.append({'index':index,'name':name,'source':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'schedule':args.schedule,'instruction_source_sha256':instruction_hash,'hlsl_lowering_verified':instructions is not None,'instruction_roundtrip_verified':instructions is not None,
                         'compiled_source_sha256':hashlib.sha256((args.output/path.name).read_bytes()).hexdigest(),'fp_policy':policy,'precise_masks_removed':changed,
                         'dxbc_sha256':hashlib.sha256(code).hexdigest(),'bytes':len(code),'vendor_encoding':vendor,'thread_group':list(map(int,group.groups()))})
    body+=['const ShaderCode kRecoveredShaders[84] = {',',\n'.join(entries),'};',
           'const ShaderCode* FindShaderCode(const char* name){ for(const auto& s:kRecoveredShaders)if(std::strcmp(s.name,name)==0)return &s;return nullptr;}','}']
    (args.output/'NvFlexShaders.generated.hpp').write_text('\n'.join(header)+'\n',encoding='utf-8')
    (args.output/'NvFlexShaders.generated.cpp').write_text('\n'.join(body)+'\n',encoding='utf-8')
    (args.output/'shader_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    if args.compiler:(args.output/'shader_compiler.json').write_text(json.dumps({'path':str(args.compiler),'sha256':hashlib.sha256(args.compiler.read_bytes()).hexdigest()},indent=2),encoding='utf-8')
    print('Compiled and embedded',len(files),'HLSL shaders,',sum(r['bytes'] for r in manifest),'DXBC bytes')
if __name__=='__main__':main()
