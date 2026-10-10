"""DXBC SM5 instruction lifting to HLSL using uint register bit patterns.

Input constants are disassembled as hexadecimal to avoid decimal float loss.
Unknown operations raise an error; no operation is silently omitted.
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
from dxbc_tools import disassemble, compile_hlsl

AXES='xyzw'

def split_args(text):
    result=[]; begin=0; depth=0
    for i,char in enumerate(text):
        if char in '([': depth+=1
        elif char in ')]':depth-=1
        elif char==',' and depth==0:
            result.append(text[begin:i].strip());begin=i+1
    if text[begin:].strip():result.append(text[begin:].strip())
    return result

def split_op(line):
    depth=0
    for i,char in enumerate(line):
        if char=='(':depth+=1
        elif char==')':depth-=1
        elif char.isspace() and depth==0:
            return line[:i],split_args(line[i:].strip())
    return line,[]

def operand(token):
    match=re.match(r'^(.*?)(?:\.([xyzw]+))?$',token)
    return match[1],match[2] or 'xyzw'

def const(token):
    assert token.startswith('l(')
    return [int(s.strip(),0)&0xffffffff for s in token[2:-1].split(',')]

class Lifter:
    def __init__(self,shader,assembly):
        self.shader=shader;self.assembly=assembly
        self.declarations=[];self.body=[];self.resources={};self.indent=1
        self.counter=0;self.opcodes=collections.Counter();self.thread_group=None
        self.names={}
        for line in assembly.splitlines():
            m=re.match(r'//\s+(\S+)\s+(texture|UAV|cbuffer|sampler)\s+.*?\s+(t\d+|u\d+|cb\d+|s\d+)\s+\d+\s*$',line)
            if m:self.names[m[3]]=m[1]
        self.reg_count=0;self.indexable=[]

    def emit(self,line):self.body.append('    '*self.indent+line)

    def src(self,token,i=0,kind='u'):
        token=token.strip();negative=False;absolute=False
        if token.startswith('-'):negative=True;token=token[1:]
        if token.startswith('|') and token.endswith('|'):
            absolute=True;token=token[1:-1]
        if token.startswith('l('):
            values=const(token);bits=values[0] if len(values)==1 else values[i]
            expr=f'0x{bits:08x}u'
        else:
            stem,swizzle=operand(token)
            lane=swizzle[0] if len(swizzle)==1 else swizzle[i]
            expr=f'{stem}.{lane}'
        if kind=='f':expr=f'asfloat({expr})'
        elif kind=='i':expr=f'asint({expr})'
        if absolute:expr=f'abs({expr})'
        if negative:expr=f'(-({expr}))'
        return expr

    def assign(self,dest,values):
        if dest=='null':return
        stem,mask=operand(dest)
        # All expressions are evaluated before any destination component changes.
        vals=[values(AXES.index(c)) for c in mask]
        expr=vals[0] if len(vals)==1 else f'uint{len(vals)}('+', '.join(vals)+')'
        self.emit(f'{stem}.{mask} = {expr};')

    def name(self,reg):return self.resources[reg]['name']

    def declare(self,op,args):
        if op in ('dcl_globalFlags','dcl_input'):return
        if op=='dcl_temps':self.reg_count=int(args[0]);return
        if op=='dcl_indexableTemp':
            self.indexable.append(args[0]);return
        if op=='dcl_thread_group':self.thread_group=tuple(map(int,args));return
        if op=='dcl_constantbuffer':
            m=re.match(r'CB(\d+)\[(\d+)\]',args[0]);idx,count=m.groups()
            self.declarations.append(f'cbuffer RecoveredConstants{idx} : register(b{idx}) {{ uint4 cb{idx}[{count}]; }};')
            return
        if op=='dcl_sampler':
            reg=args[0];self.declarations.append(f'SamplerState {reg} : register({reg});');return
        if op.startswith('dcl_resource_') or op.startswith('dcl_uav_') or op.startswith('dcl_tgsm_'):
            is_tgsm=op.startswith('dcl_tgsm_');is_uav=op.startswith('dcl_uav_')
            if '_structured' in op:
                reg=args[0];stride=int(args[1]);count=int(args[2]) if is_tgsm else None
                kind='structured';decl=f'struct S_{reg} {{ uint w[{stride//4}]; }}; '
                storage='groupshared S_'+reg if is_tgsm else ('globallycoherent ' if '_glc' in op else '')+('RWStructuredBuffer' if is_uav else 'StructuredBuffer')+f'<S_{reg}>'
            elif '_raw' in op:
                reg=args[0];stride=4;count=int(args[1])//4 if is_tgsm else None
                kind='raw';decl='';storage='groupshared uint' if is_tgsm else ('RWByteAddressBuffer' if is_uav else 'ByteAddressBuffer')
            else:
                match=re.match(r'\(([^)]+)\)\s+(\w+)',args[0]+','+','.join(args[1:]))
                # The parenthesized return-type tuple contains commas at depth one.
                if not match:
                    match=re.match(r'\(([^)]+)\)\s+(\w+)',args[0])
                if not match:raise ValueError((op,args))
                types,reg=match.groups();stride=16;count=None
                scalar=types.split(',')[0]
                if 'texture3d' in op:kind='texture3d';storage=f'Texture3D<{scalar}4>'
                else:kind='typed';storage=('RWBuffer' if is_uav else 'Buffer')+f'<{scalar}4>'
                decl=''
            readable=re.sub(r'[^A-Za-z0-9_]','_',self.names.get(reg,reg))
            name=reg if is_tgsm else reg+'_'+readable
            self.resources[reg]={'kind':kind,'name':name,'stride':stride,'tgsm':is_tgsm,'counter':'_opc' in op,'declaration':op}
            if is_tgsm:decl+=f'{storage} {name}[{count}];'
            else:decl+=f'{storage} {name} : register({reg});'
            self.declarations.append(decl);return
        raise NotImplementedError(op)

    def memory(self,reg,index,offset,component):
        r=self.resources[reg];name=r['name'];kind=r['kind']
        if kind=='structured':return f'{name}[{index}].w[({offset}) / 4u + {component}u]'
        if kind=='raw' and r['tgsm']:return f'{name}[({offset}) / 4u + {component}u]'
        if kind=='typed':return f'{name}[{index}].{AXES[component]}'
        if kind=='raw':return f'{name}.Load(({offset}) + {component*4}u)'
        raise NotImplementedError((reg,r))

    def instruction(self,op,a,original):
        self.opcodes[op]+=1
        self.emit('// '+original)
        if op.startswith('if_'):
            condition=self.src(a[0]);self.emit(f'if ({condition} '+('!=' if op=='if_nz' else '==')+' 0u) {');self.indent+=1;return
        if op=='else':self.indent-=1;self.emit('} else {');self.indent+=1;return
        if op in ('endif','endloop','endswitch'):self.indent-=1;self.emit('}');return
        if op=='loop':self.emit('[loop] while (true) {');self.indent+=1;return
        if op=='switch':self.emit(f'switch ({self.src(a[0])}) {{');self.indent+=1;return
        if op=='case':self.emit(f'case {self.src(a[0])}:');return
        if op=='default':self.emit('default:');return
        if op in ('break','continue','ret'):self.emit(('return' if op=='ret' else op)+';');return
        if op in ('breakc_nz','breakc_z'):
            self.emit(f'if ({self.src(a[0])} '+('!=' if op.endswith('nz') else '==')+' 0u) break;');return
        if op=='sync_g_t':self.emit('GroupMemoryBarrierWithGroupSync();');return
        if op.startswith('ld_structured'):
            dst,idx,off,resource=a;reg,swizzle=operand(resource)
            self.assign(dst,lambda i:self.memory(reg,self.src(idx),self.src(off),AXES.index(swizzle[i] if len(swizzle)>1 else swizzle[0])));return
        if op.startswith('ld_raw'):
            dst,off,resource=a;reg,swizzle=operand(resource)
            self.assign(dst,lambda i:self.memory(reg,'0u',self.src(off),AXES.index(swizzle[i] if len(swizzle)>1 else swizzle[0])));return
        if op.startswith('ld_indexable'):
            dst,idx,resource=a;reg,swizzle=operand(resource)
            self.assign(dst,lambda i:self.memory(reg,self.src(idx),'0u',AXES.index(swizzle[i] if len(swizzle)>1 else swizzle[0])));return
        if op in ('store_structured','store_raw','store_uav_typed'):
            reg,mask=operand(a[0]);resource=self.resources[reg]
            idx=self.src(a[1]);off=self.src(a[2]) if op=='store_structured' else idx
            value=a[-1]
            if op=='store_uav_typed':
                assert mask=='xyzw'
                self.emit(f'{resource["name"]}[{idx}] = uint4('+', '.join(self.src(value,i) for i in range(4))+');');return
            for c in mask:
                component=AXES.index(c);val=self.src(value,component)
                if resource['kind']=='raw' and not resource['tgsm']:
                    self.emit(f'{resource["name"]}.Store(({off}) + {component*4}u, {val});')
                else:self.emit(self.memory(reg,idx,off,component)+' = '+val+';')
            return
        if op.startswith('sample_l'):
            dst,coord,texture,sampler,lod=a;reg,swizzle=operand(texture)
            temp=f'_sample{self.counter}';self.counter+=1
            self.emit(f'float4 {temp} = {self.name(reg)}.SampleLevel({sampler}, float3('+', '.join(self.src(coord,i,'f') for i in range(3))+f'), {self.src(lod,0,"f")});')
            self.assign(dst,lambda i:f'asuint({temp}.{swizzle[i]})');return
        if op.startswith('imm_atomic_'):
            dst,reg=a[:2];resource=self.resources[reg];temp=f'_atomic{self.counter}';self.counter+=1
            self.emit(f'uint {temp};')
            if op=='imm_atomic_alloc':self.emit(f'{temp} = {self.name(reg)}.IncrementCounter();')
            else:
                addr=a[2]
                index=self.src(addr,0);offset=self.src(addr,1) if resource['kind']=='structured' else self.src(addr,0)
                operations={'imm_atomic_cmp_exch':'InterlockedCompareExchange','imm_atomic_exch':'InterlockedExchange','imm_atomic_iadd':'InterlockedAdd','imm_atomic_or':'InterlockedOr'}
                operation=operations[op]
                params=[self.src(arg) for arg in a[3:]]+[temp]
                if resource['kind']=='raw' and not resource['tgsm']:
                    self.emit(f'{self.name(reg)}.{operation}('+', '.join([index]+params)+');')
                else:
                    target=self.memory(reg,index,offset,0)
                    self.emit(f'{operation}('+', '.join([target]+params)+');')
            self.assign(dst,lambda i:temp);return
        if op=='sincos':
            sine,cosine,source=a;temp=f'_trig{self.counter}';self.counter+=1
            self.emit(f'float4 {temp} = float4('+', '.join(self.src(source,i,'f') for i in range(4))+');')
            self.assign(sine,lambda i:f'asuint(sin({temp}.{AXES[i]}))')
            self.assign(cosine,lambda i:f'asuint(cos({temp}.{AXES[i]}))');return
        if op=='imul':
            high,low,lhs,rhs=a
            assert high=='null','Signed high multiplication not present in this input set'
            self.assign(low,lambda i:f'({self.src(lhs,i)} * {self.src(rhs,i)})');return
        dest=a[0];args=a[1:]
        saturate=op.endswith('_sat');base_op=op[:-4] if saturate else op
        def expression(i):
            u=lambda k:self.src(args[k],i,'u')
            f=lambda k:self.src(args[k],i,'f')
            si=lambda k:self.src(args[k],i,'i')
            float_expr=None
            if base_op in ('add','mul','div'):float_expr=f'({f(0)} '+{'add':'+','mul':'*','div':'/'}[base_op]+f' {f(1)})'
            elif base_op=='mad':float_expr=f'mad({f(0)}, {f(1)}, {f(2)})'
            elif base_op in ('min','max'):float_expr=f'{base_op}({f(0)}, {f(1)})'
            elif base_op in ('sqrt','rsq','rcp','exp','round_z'):
                fun={'sqrt':'sqrt','rsq':'rsqrt','rcp':'rcp','exp':'exp2','round_z':'trunc'}[base_op]
                float_expr=f'{fun}({f(0)})'
            elif re.match(r'dp[234]$',base_op):
                n=int(base_op[-1]);vectors=[f'float{n}('+', '.join(self.src(args[k],j,'f') for j in range(n))+')' for k in (0,1)]
                float_expr='dot('+', '.join(vectors)+')'
            elif base_op in ('itof','utof'):float_expr='(float)'+(si(0) if base_op=='itof' else u(0))
            if float_expr is not None:
                if saturate:float_expr='saturate('+float_expr+')'
                return f'asuint({float_expr})'
            if base_op=='mov':
                # A float source modifier on mov changes float sign/absolute bits.
                if args[0].startswith(('-', '|')):return f'asuint({f(0)})'
                return u(0)
            if base_op=='movc':
                value=lambda k:f'asuint({f(k)})' if args[k].startswith(('-', '|')) else u(k)
                return f'({u(0)} != 0u ? {value(1)} : {value(2)})'
            if base_op in ('and','or','xor','iadd'):return f'({u(0)} '+{'and':'&','or':'|','xor':'^','iadd':'+'}[base_op]+f' {u(1)})'
            if base_op=='not':return f'(~{u(0)})'
            if base_op in ('ishl','ushr','ishr'):
                lhs=si(0) if base_op=='ishr' else u(0);shift='<<' if base_op=='ishl' else '>>'
                return f'asuint({lhs} {shift} ({u(1)} & 31u))'
            if base_op=='imad':return f'({u(0)} * {u(1)} + {u(2)})'
            if base_op=='imin':return f'asuint(min({si(0)}, {si(1)}))'
            if base_op in ('ftoi','ftou'):return f'asuint(({"int" if base_op=="ftoi" else "uint"}){f(0)})'
            if base_op=='bfi':return f'recovered_bfi({u(0)}, {u(1)}, {u(2)}, {u(3)})'
            comparisons={'lt':('<','f'),'ge':('>=','f'),'eq':('==','f'),'ne':('!=','f'),
                         'ilt':('<','i'),'ige':('>=','i'),'ieq':('==','u'),'ine':('!=','u'),
                         'ult':('<','u'),'uge':('>=','u')}
            if base_op in comparisons:
                sign,kind=comparisons[base_op]
                return f'({self.src(args[0],i,kind)} {sign} {self.src(args[1],i,kind)} ? 0xffffffffu : 0u)'
            raise NotImplementedError((op,args))
        self.assign(dest,expression)

    def run(self):
        in_code=False
        for line in self.assembly.splitlines():
            line=line.strip()
            if line=='cs_5_0':in_code=True;continue
            if not in_code or not line or line.startswith('//'):continue
            op,args=split_op(line)
            if op.startswith('dcl_'):self.declare(op,args)
            else:self.instruction(op,args,line)
        assert self.thread_group and self.indent==1
        header=self.assembly[:self.assembly.index('cs_5_0')]
        register_decls=[f'    uint4 r{i};' for i in range(self.reg_count)]
        register_decls.extend(f'    uint4 {r};' for r in self.indexable)
        helper='uint recovered_bfi(uint width, uint offset, uint value, uint baseValue) {\n    width &= 31u; offset &= 31u;\n    uint mask = ((1u << width) - 1u) << offset;\n    return (baseValue & ~mask) | ((value << offset) & mask);\n}\n'
        result='// Reconstructed from DXBC; not original HLSL source.\n// uint temporaries preserve DXBC bits. All literals retain their original IEEE-754 encoding.\n// Instruction comments map this source to the original shader.\n'+header+'\n'+'\n'.join(self.declarations)+'\n\n'+helper
        result+='\n[numthreads('+', '.join(map(str,self.thread_group))+')]\n'
        result+='void main(uint3 vThreadID : SV_DispatchThreadID, uint3 vThreadIDInGroup : SV_GroupThreadID, uint3 vThreadGroupID : SV_GroupID, uint vThreadIDInGroupFlattened : SV_GroupIndex)\n{\n'
        result+='\n'.join(register_decls+self.body)+'\n}\n'
        return result
