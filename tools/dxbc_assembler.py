"""Encode SM5 compute instructions from text using Microsoft's token format.

This module never reads an original DXBC/DLL. It accepts textual instructions
and builds every instruction/operand token. Reflection/signatures are supplied
by an independently compiled HLSL container, not by the original binary.
"""
from pathlib import Path
import re,struct
from dxbc_precision import repair_checksum

def read_enums():
    source=(Path(__file__).parent/'third_party/directx_tokens/D3D12TokenizedProgramFormat.hpp').read_text(encoding='utf-8-sig')
    source=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S);values={}
    for body in re.findall(r'typedef\s+enum\s+\w+\s*\{(.*?)\}',source,re.S):
        value=-1
        for part in body.split(','):
            part=part.strip()
            if not part:continue
            pair=part.split('=',1);name=pair[0].strip()
            if len(pair)==2:
                expr=pair[1].strip()
                if expr in values:value=values[expr]
                else:
                    try:value=int(expr,0)
                    except ValueError:break
            else:value+=1
            values[name]=value
    return values
ENUM=read_enums()
OP={name.split('_SB_OPCODE_',1)[1].lower():v for name,v in ENUM.items() if '_SB_OPCODE_' in name}
TYPE={name.split('_SB_OPERAND_TYPE_',1)[1].lower():v for name,v in ENUM.items() if '_SB_OPERAND_TYPE_' in name}
DIM={name.split('_SB_RESOURCE_DIMENSION_',1)[1].lower():v for name,v in ENUM.items() if '_SB_RESOURCE_DIMENSION_' in name}
RET={name.split('_SB_RETURN_TYPE_',1)[1].lower():v for name,v in ENUM.items() if '_SB_RETURN_TYPE_' in name}
AXES='xyzw'

def split_args(text):
    out=[];depth=0;start=0
    for i,ch in enumerate(text):
        if ch in '([':depth+=1
        elif ch in ')]':depth-=1
        elif ch==',' and not depth:out.append(text[start:i].strip());start=i+1
    if text[start:].strip():out.append(text[start:].strip())
    return out
def split_op(line):
    depth=0
    for i,ch in enumerate(line):
        if ch=='(':depth+=1
        elif ch==')':depth-=1
        elif ch.isspace() and not depth:return line[:i],split_args(line[i:].strip())
    return line,[]
def integer(text):return int(text.strip(),0)&0xffffffff
def instruction_lines(source):
    started=False;out=[]
    for line in source.splitlines():
        line=line.strip()
        if line=='cs_5_0':started=True;continue
        if started and line and not line.startswith('//'):out.append(line)
    if not started:raise ValueError('Expected cs_5_0 textual program')
    return out

def encode_operand(text,destination=False):
    text=text.strip();modifier=0
    if text.startswith('-'):modifier=1;text=text[1:]
    if text.startswith('|') and text.endswith('|'):modifier=3 if modifier else 2;text=text[1:-1]
    extra=[];indices=[]
    if text.startswith('l('):
        values=[integer(x) for x in split_args(text[2:-1])];assert len(values) in (1,4)
        token=(TYPE['immediate32']<<12)|(1 if len(values)==1 else 2);extra=values
    elif text=='null':token=TYPE['null']<<12
    else:
        # A component suffix lies outside any relative-address expression.
        match=re.fullmatch(r'(.*?)(?:\.([xyzw]+))?',text);stem,components=match.groups()
        specials={'vThreadID':'input_thread_id','vThreadGroupID':'input_thread_group_id','vThreadIDInGroup':'input_thread_id_in_group','vThreadIDInGroupFlattened':'input_thread_id_in_group_flattened'}
        if stem in specials:kind=TYPE[specials[stem]]
        else:
            match=re.fullmatch(r'(cb|CB|r|x|t|u|s|g)(\d+)(?:\[(.*)\])?',stem)
            if not match:raise ValueError('Operand '+text)
            prefix,first,second=match.groups();kind=TYPE[{'r':'temp','x':'indexable_temp','t':'resource','u':'unordered_access_view','s':'sampler','g':'thread_group_shared_memory','cb':'constant_buffer','CB':'constant_buffer'}[prefix]]
            indices=[first]+([second] if second is not None else [])
        token=kind<<12
        if components:
            token|=2
            if destination:token|=sum(1<<(4+AXES.index(ch)) for ch in components)
            elif len(components)==1:token|=(2<<2)|(AXES.index(components)<<4)
            else:
                if len(components)!=4:raise ValueError('Source swizzle '+text)
                token|=(1<<2)|sum(AXES.index(ch)<<(4+2*i) for i,ch in enumerate(components))
        token|=len(indices)<<20
        for i,index in enumerate(indices):
            index=index.strip()
            if re.fullmatch(r'(?:0x[\da-fA-F]+|\d+)',index):extra.append(integer(index))
            else:
                relative=re.fullmatch(r'(r\d+\.[xyzw])(?:\s*\+\s*(0x[\da-fA-F]+|\d+))?',index)
                if not relative:raise ValueError('Relative index '+index)
                register,offset=relative.groups()
                if offset is None or integer(offset)==0:token|=2<<(22+3*i)
                else:token|=3<<(22+3*i);extra.append(integer(offset))
                extra.extend(encode_operand(register))
    if modifier:token|=0x80000000;extra=[1|(modifier<<6)]+extra
    return [token]+extra

ALIASES={'dcl_constantbuffer':'dcl_constant_buffer','dcl_indexableTemp':'dcl_indexable_temp','dcl_globalFlags':'dcl_global_flags','dcl_uav_structured':'dcl_unordered_access_view_structured','dcl_uav_raw':'dcl_unordered_access_view_raw','dcl_tgsm_raw':'dcl_thread_group_shared_memory_raw','dcl_tgsm_structured':'dcl_thread_group_shared_memory_structured'}
def encode_instruction(line):
    op,args=split_op(line);extended=[];controls=0;words=[];base=op
    if op=='dcl_globalFlags':
        if args!=['refactoringAllowed']:raise ValueError(line)
        controls=1<<11
    elif op=='dcl_constantbuffer':
        controls=(1<<11) if args[1]=='dynamicIndexed' else 0;words=encode_operand(args[0]+'.xyzw')
    elif op=='dcl_input':words=encode_operand(args[0],True)
    elif op in ('dcl_temps','dcl_thread_group'):words=[integer(x) for x in args]
    elif op=='dcl_indexableTemp':
        m=re.fullmatch(r'x(\d+)\[(\d+)\]',args[0]);words=[int(m[1]),int(m[2]),integer(args[1])]
    elif op=='dcl_sampler':
        if args[1]!='mode_default':raise ValueError(line)
        words=encode_operand(args[0],True)
    elif op.startswith('dcl_resource_buffer') or op.startswith('dcl_resource_texture3d') or op.startswith('dcl_uav_typed_buffer'):
        m=re.fullmatch(r'(dcl_resource|dcl_uav_typed)_(\w+)\s+\(([^)]+)\)\s+(\w+)',line)
        base='dcl_resource' if m[1]=='dcl_resource' else 'dcl_unordered_access_view_typed';controls=DIM[m[2]]<<11
        returns=[RET[x] for x in m[3].split(',')];words=encode_operand(m[4],True)+[sum(v<<(4*i) for i,v in enumerate(returns))]
    elif op.startswith(('dcl_resource_','dcl_uav_','dcl_tgsm_')):
        if base.endswith('_opc'):base=base[:-4];controls|=1<<23
        if base.endswith('_glc'):base=base[:-4];controls|=1<<16
        words=encode_operand(args[0],True)+[integer(x) for x in args[1:]]
    else:
        if '_indexable(' in base:
            m=re.fullmatch(r'(.*?)_indexable\((.*?)\)\((.*?)\)',base)
            base=m[1];dimensions=split_args(m[2]);dimension=DIM[dimensions[0]];stride=int(dimensions[1].split('=')[1]) if len(dimensions)>1 else 0
            extended=[0x80000000|2|(dimension<<6)|(stride<<11),3|sum(RET[x]<<(6+4*i) for i,x in enumerate(m[3].split(',')))]
        if base.endswith('_sat'):base=base[:-4];controls|=1<<13
        if base.endswith('_nz'):base=base[:-3];controls|=1<<18
        elif base.endswith('_z') and base in ('if_z','breakc_z','retc_z','continuec_z'):base=base[:-2]
        if base=='sync_g_t':base='sync';controls|=0x1800
        source_only={'if','breakc','retc','continuec','switch','case'}
        dest_count=0 if base in source_only else 2 if base in ('imul','umul','sincos','udiv') else 1
        for i,arg in enumerate(args):words.extend(encode_operand(arg,i<dest_count))
    name=ALIASES.get(base,base).lower()
    if name not in OP:raise ValueError('Opcode '+name)
    length=1+len(extended)+len(words);assert length<128,line
    token=OP[name]|controls|(length<<24)|(0x80000000 if extended else 0)
    return [token]+extended+words

def assemble_program(source):
    words=[0x00050050,0]
    for line in instruction_lines(source):
        try:words.extend(encode_instruction(line))
        except Exception as error:raise ValueError(f'{line}: {error}') from error
    words[1]=len(words);return struct.pack('<'+'I'*len(words),*words)

def replace_program(compiled,program,hash_helper):
    count=struct.unpack_from('<I',compiled,28)[0];chunks=[]
    for offset in struct.unpack_from('<'+'I'*count,compiled,32):
        tag=compiled[offset:offset+4];size=struct.unpack_from('<I',compiled,offset+4)[0];payload=compiled[offset+8:offset+8+size]
        if tag in (b'SHEX',b'SHDR'):payload=program
        if tag==b'STAT':continue # FXC statistics describe its alternative schedule.
        chunks.append(tag+struct.pack('<I',len(payload))+payload)
    offsets=[];position=32+len(chunks)*4;body=b''
    for chunk in chunks:
        offsets.append(position);body+=chunk;position+=len(chunk)
        padding=(-position)%4;body+=bytes(padding);position+=padding
    output=b'DXBC'+bytes(16)+struct.pack('<III',1,position,len(chunks))+struct.pack('<'+'I'*len(offsets),*offsets)+body
    return repair_checksum(output,hash_helper)
