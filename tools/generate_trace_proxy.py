"""Diagnostic-only Context forwarding proxy; never linked into the candidate DLL."""
import re
from pathlib import Path
from ledger import PROJECT
header=(PROJECT/'src/dx/context/Context.h').read_text(encoding='utf-8')
header=re.sub(r'/\*.*?\*/|//[^\n]*','',header,flags=re.S)
start=re.search(r'\bstruct Context\s*\{',header).end()
methods=re.findall(r'virtual\s+([^();{}]+?)\s+(\w+)\(([^)]*)\)\s*=\s*0\s*;',header[start:],re.S)
output=['// Generated diagnostic proxy; the runtime DLL does not use or link this file.',
        'struct TracingContext final : NvFlex::Context {',
        '    NvFlex::Context* wrapped; Trace& trace;',
        '    TracingContext(NvFlex::Context* original, Trace& recorder):wrapped(original),trace(recorder){}']
for ret,name,arguments in methods:
    ret=' '.join(ret.split());arguments=' '.join(arguments.split())
    arguments=re.sub(r'\s*=\s*[^,]+','',arguments)
    parts=[x.strip() for x in arguments.split(',') if x.strip()]
    names=[re.search(r'(\w+)\s*$',x)[1] for x in parts]
    arg0=names[0] if names else None
    signature=f'    {ret} {name}({arguments}) override {{'
    output.append(signature)
    if name.startswith('unmap') and parts:
        output.append(f'        trace.capture({arg0});')
    if name in ('dispatch','dispatchIndirect'):
        output.append(f'        trace.dispatch("{name}",{arg0});')
    else:
        output.append(f'        trace.operation("{name}");')
    if name in ('copy','copyToNative','copyToHost','copyToDevice','upload','download'):
        values=[f'trace.id({n})' if '*' in p else f'static_cast<unsigned long long>({n})' for p,n in zip(parts,names)]
        output.append(f'        trace.arguments("{name}",{{'+','.join(values)+'});')
    call='wrapped->'+name+'('+','.join(names)+')'
    if ret=='void':output.append('        '+call+';')
    else:output.append('        auto result='+call+';')
    if name in ('createBuffer','createBufferView'):output.append('        trace.adopt(result,"created");')
    if name=='createBuffer':output.append(f'        if(result && {arg0}->data) trace.initial(result,{arg0}->data,size_t({arg0}->dim)*{arg0}->stride);')
    if name=='createConstantBuffer':output.append(f'        trace.adopt(result,"created",{arg0});')
    if name=='createComputeShader':output.append('        trace.shader(result);')
    if name=='map' and parts and ('Buffer*' in parts[0]) and not 'Texture' in parts[0]:
        output.append(f'        trace.mapped({arg0},result);')
    if ret!='void':output.append('        return result;')
    output.append('    }')
output.append('};')
(PROJECT/'tests/TraceContext.generated.hpp').write_text('\n'.join(output)+'\n',encoding='utf-8')

layouts=(PROJECT.parent/'Build/NvFlexDisassembly-20261009/pdb/flex_layouts.txt').read_text(encoding='utf-8')
block=re.search(r'    struct NvFlexSolver \[sizeof = 3872\] \{(.*?)\n    \}',layouts,re.S)[1]
fields=[]
for match in re.finditer(r'data \+0x([0-9a-f]+) \[sizeof=(\d+)\] (.+?) (\w+)(\[\d+\])?(?:\n|$)',block):
    offset,size,typ,name,array=match.groups();offset=int(offset,16);size=int(size)
    if typ in ('DxBufferExt','DxComputeBuffer'):
        fields.append(f'{{ void* p=nullptr;std::memcpy(&p,base+{offset},8);trace.field("{name}",{offset},p,"buffer"); }}')
    elif typ=='DxConstantBuffer':
        fields.append(f'{{ void* p=nullptr;std::memcpy(&p,base+{offset+16},8);trace.field("{name}",{offset},p,"constant"); }}')
    elif typ in ('int','float','bool') and not array:
        fields.append(f'{{ unsigned bits=0;std::memcpy(&bits,base+{offset},{size});trace.scalar("{name}",{offset},bits,"{typ}"); }}')
(PROJECT/'tests/TraceSolverFields.generated.hpp').write_text('\n'.join(fields)+'\n',encoding='utf-8')
print('Generated proxy methods',len(methods),'and solver field probes',len(fields))
