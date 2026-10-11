"""Guarded stable integer radix experiment; original remainder preserves both sides."""
import argparse,difflib
from common import *
from auxiliary_support import configure
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',required=True);a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
assert not dest.exists();shutil.copytree(base,dest)
entries=[]
for stem,index in [('Radix8Histogram',80),('Radix8Scan',81),('Radix8ScanSums',81),('Radix8Scatter',83)]:
    shutil.copy2(Path(__file__).parent/'templates'/(stem+'.hlsl'),dest/'shaders/auxiliary'/(stem+'.hlsl'))
    entries.append(dict(name='df_'+stem,source=stem+'.hlsl',original_index=index,kind='authored-integer-helper'))
configure(dest,entries)
path=dest/'src/solver/RadixSort.hpp';s=path.read_text(encoding='utf8');s=s.replace('void upload(unsigned blocks,unsigned pass,unsigned keys);','void upload(unsigned blocks,unsigned pass,unsigned keys);\n    bool reserveWide(unsigned keys);\n    NvFlex::Buffer* wide[4]{};unsigned wideCapacity=0;');path.write_text(s,encoding='utf8')
path=dest/'src/solver/RadixSort.cpp';s=path.read_text(encoding='utf8');s=s.replace('RadixSort::~RadixSort(){','RadixSort::~RadixSort(){for(auto p:wide)delete p;')
pos=s.index('void RadixSort::upload(')
s=s[:pos]+'''bool RadixSort::reserveWide(unsigned keys){
    if(wideCapacity>=keys)return true;
    NvFlex::Buffer* next[4]{};
    try{for(unsigned i=0;i<4;++i){NvFlex::BufferDesc d{};d.dim=i<2?keys:keys/1024;d.stride=4;d.bufferType=3;d.format=eNvFlexFormat_r32_uint;
        next[i]=library->mContext->createBuffer(&d);if(!next[i])throw std::bad_alloc();}}
    catch(...){for(auto p:next)delete p;return false;}
    for(unsigned i=0;i<4;++i){delete wide[i];wide[i]=next[i];}wideCapacity=keys;return true;
}
'''+s[pos:]
needle='    for(unsigned pass=0;pass<bits;pass+=4){';assert s.count(needle)==1
replacement='''    unsigned firstPass=0;
    // Replace exactly four low-nibble passes by two stable byte passes.
    // The original remaining passes restore the same physical front/back data,
    // counter parity, final low-20/28-bit back side and untouched tail bytes.
    // Other lengths/bit counts retain the original kernels and dispatches.
    if(keys%1024==0 && keys<=1048576 && (bits==24 || bits==32) && reserveWide(keys)){
        for(unsigned shift:{0u,8u}){
            upload(blocks,shift,keys);NvFlex::DispatchParams p{};p.rootConstantBuffer=constants;
            p.shader=GetShader(library,"df_Radix8Histogram");p.gridDim={blocks*4,1,1};
            p.readOnly[0]=front.key->getResource();p.readWrite[0]=wide[0]->getResourceRW();dispatch(&p);
            p={};p.rootConstantBuffer=constants;p.shader=GetShader(library,"df_Radix8Scan");p.gridDim={blocks,1,1};
            p.readOnly[0]=wide[0]->getResource();p.readWrite[0]=wide[1]->getResourceRW();p.readWrite[1]=wide[2]->getResourceRW();dispatch(&p);
            p={};p.rootConstantBuffer=constants;p.shader=GetShader(library,"df_Radix8ScanSums");p.gridDim={1,1,1};
            p.readOnly[0]=wide[2]->getResource();p.readWrite[0]=wide[3]->getResourceRW();dispatch(&p);
            p={};p.rootConstantBuffer=constants;p.shader=GetShader(library,"df_Radix8Scatter");p.gridDim={blocks*4,1,1};
            p.readOnly[0]=front.key->getResource();p.readOnly[1]=front.value->getResource();p.readOnly[2]=wide[1]->getResource();p.readOnly[3]=wide[3]->getResource();
            p.readWrite[0]=back.key->getResourceRW();p.readWrite[1]=back.value->getResourceRW();dispatch(&p);std::swap(front,back);
        }
        firstPass=16;
    }
    for(unsigned pass=firstPass;pass<bits;pass+=4){'''
s=s.replace(needle,replacement);path.write_text(s,encoding='utf8')
shutil.copy2(Path(__file__).parent/'templates/radix_extended_oracle.cpp',dest/'tests/radix_oracle.cpp')
diff=[]
for path in dest.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(dest);old=base/rel
    if old.exists() and sha(old)==sha(path):continue
    before=old.read_text(encoding='utf8') if old.exists() else ''
    diff.extend(difflib.unified_diff(before.splitlines(True),path.read_text(encoding='utf8').splitlines(True),fromfile=a.base+'/'+rel.as_posix(),tofile=a.name+'/'+rel.as_posix()))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
row=dict(id='A082-01',version='alpha8.2',candidate=a.name,base=a.base,title='Stable two-byte radix prefix with original remaining passes',status='candidate-prepared',source=str(dest),evidence=str(patch),numerical_change=False,original_shader_change=False,required_validation=['both backend full buffers and physical sides','mixed lengths/bits/duplicate keys stable ordering','original84 hash','all API regressions','FlexDemo completed-frame and long quality'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[x for x in rows if x['id']!=row['id']]+[row]);event('candidate-prepared',**row)
