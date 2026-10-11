"""Alpha0.2-inspired submission batching for the DF D3D12 runtime."""
import argparse,difflib
from common import *
def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a02-descriptor-batch-v1');a=p.parse_args()
    base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
    if not dest.exists():shutil.copytree(base,dest)
    relative='src/runtime/D3D12Context.cpp';original=(base/relative).read_bytes().decode().replace('\r','')
    start=original.index('    auto table=gpu(40);auto destination=table.first;')
    end=original.index('    commands->SetComputeRootDescriptorTable(1,table.second);',start)
    replacement='''    auto table=gpu(40);
    // Keep the original 32 SRV + 8 UAV table layout and resource-transition
    // sequence. Only combine the CPU descriptor-copy submissions.
    D3D12_CPU_DESCRIPTOR_HANDLE sources[40]{};
    UINT sizes[40];std::fill_n(sizes,40,1u);
    for(unsigned i=0;i<32;++i){auto read=static_cast<Read12*>(p->readOnly[i]);sources[i]=read?read->descriptor:nullRead;if(read)transition(read->resource,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);}
    for(unsigned i=0;i<8;++i){auto write=static_cast<Write12*>(p->readWrite[i]);sources[32+i]=write?write->descriptor:nullWrite;if(write)transition(write->resource,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,true);}
    const UINT destinationSize=40;
    device->CopyDescriptors(1,&table.first,&destinationSize,40,sources,sizes,D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);
'''
    updated=original[:start]+replacement+original[end:];(dest/relative).write_text(updated,encoding='utf8')
    patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(difflib.unified_diff(original.splitlines(True),updated.splitlines(True),fromfile=a.base+'/'+relative,tofile=a.name+'/'+relative)),encoding='utf8')
    item=dict(id='A002-01',version='alpha0.2',title='Batch D3D12 descriptor-copy submissions while preserving the table and barriers',status='candidate-prepared',candidate=a.name,base=a.base,source=str(dest),donor='P11.06b resource binding/submission churn and P11.08a operation batching',adaptation='DF-specific D3D12 adaptation of the historical batching idea, not a claim that OF alpha0.2 implements D3D12. 40 single-descriptor calls become one ranged copy with 40 explicit unit source ranges.',shader_change=False,numerical_change=False,invariants=['40 descriptor contents and order','same source non-shader-visible heaps','same per-resource transition and UAV-barrier order','same heap allocation, fences, native retention, root CBV behavior'],evidence=str(patch),documentation='https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12device-copydescriptors',required_validation=['D3D12 pool/external-context/multi-solver oracle','native context/aliasing/readback','exact original 84 shaders','whole-frame paired tests including dense and empty scenes','check no CPU-cache regression; API call count alone is not a win'])
    records=read(LEDGER/'optimizations.json');records=[x for x in records if x['id']!=item['id']]+[item];write(LEDGER/'optimizations.json',records);event('candidate-prepared',**item)
if __name__=='__main__':main()
