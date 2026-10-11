"""Batch the identical ordered D3D12 barriers, without dropping dependencies."""
import argparse,difflib
from common import *
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--name',default='a02-barrier-batch-v1');a=p.parse_args()
base=Path(read(ROOT/'evidence'/f'{a.base}-build.json')['source']);dest=ROOT/'proposals'/a.name
if not dest.exists():shutil.copytree(base,dest)
paths=['src/runtime/D3D12Resources.hpp','src/runtime/D3D12Context.cpp'];old={x:(base/x).read_text(encoding='utf8') for x in paths};new=dict(old)
needle='    void transition(const ResourcePtr12&,D3D12_RESOURCE_STATES,bool uavBarrier=false);'
assert new[paths[0]].count(needle)==1
new[paths[0]]=new[paths[0]].replace(needle,'    bool prepareTransition(const ResourcePtr12&,D3D12_RESOURCE_STATES,bool,D3D12_RESOURCE_BARRIER&);\n'+needle)
text=new[paths[1]];start=text.index('void Context12State::transition(');end=text.index('void Context12State::copy(',start)
text=text[:start]+'''bool Context12State::prepareTransition(const ResourcePtr12& resource,D3D12_RESOURCE_STATES target,bool uavBarrier,D3D12_RESOURCE_BARRIER& barrier){
    if(!resource)return false;keep(resource);if(resource->fixedState)return false;
    barrier={};
    if(resource->state!=target){barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;barrier.Transition={resource->native.Get(),D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,resource->state,target};resource->state=target;}
    else if(target==D3D12_RESOURCE_STATE_UNORDERED_ACCESS&&uavBarrier){barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_UAV;barrier.UAV.pResource=resource->native.Get();}
    else return false;
    return true;
}
void Context12State::transition(const ResourcePtr12& resource,D3D12_RESOURCE_STATES target,bool uavBarrier){
    D3D12_RESOURCE_BARRIER barrier{};
    if(prepareTransition(resource,target,uavBarrier,barrier)){commands->ResourceBarrier(1,&barrier);dirty=true;}
}
'''+text[end:]
start=text.index('void Context12State::bind(');end=text.index('NvFlex::ComputeShader* ContextD3D12::createComputeShader',start);body=text[start:end]
marker='    auto table=gpu(40);';assert body.count(marker)==1
body=body.replace(marker,'''    // D3D12 defines a barrier array as the same individual calls in order.
    // Keep all transition and UAV dependencies, including aliased views.
    D3D12_RESOURCE_BARRIER barriers[40]{};UINT barrierCount=0;
    auto bindTransition=[&](const ResourcePtr12& resource,D3D12_RESOURCE_STATES target,bool uav=false){
        if(prepareTransition(resource,target,uav,barriers[barrierCount]))++barrierCount;
    };
'''+marker)
for needle,replacement in [('transition(read->resource,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE)','bindTransition(read->resource,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE)'),('transition(write->resource,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,true)','bindTransition(write->resource,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,true)')]:
    assert body.count(needle)==1;body=body.replace(needle,replacement)
marker='    commands->SetComputeRootDescriptorTable(1,table.second);';assert body.count(marker)==1
body=body.replace(marker,'    if(barrierCount){commands->ResourceBarrier(barrierCount,barriers);dirty=true;}\n'+marker)
new[paths[1]]=text[:start]+body+text[end:];diff=[]
for path in paths:
    (dest/path).write_text(new[path],encoding='utf8');diff.extend(difflib.unified_diff(old[path].splitlines(True),new[path].splitlines(True),fromfile=a.base+'/'+path,tofile=a.name+'/'+path))
patch=ROOT/'evidence'/f'{a.name}.patch';patch.write_text(''.join(diff),encoding='utf8')
item=dict(id='A002-02',version='alpha0.2',candidate=a.name,base=a.base,title='Preserve and batch per-bind D3D12 resource barriers',status='candidate-prepared',source=str(dest),evidence=str(patch),donor='alpha0.2 P11 operation-batching principle; adapted to DF D3D12',numerical_change=False,shader_change=False,invariants=['same ordered transition/UAV descriptors','same state updates and alias order','same keep/lifetime calls','same clear/copy/indirect barriers outside bind','no barrier elimination'],reference='https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12graphicscommandlist-resourcebarrier',required_validation=['original 84 DXBC exact','context/pool/callback/aliasing oracles','D3D12 debug output if available','FlexDemo quality and whole-frame paired timing'])
rows=read(LEDGER/'optimizations.json');write(LEDGER/'optimizations.json',[x for x in rows if x['id']!=item['id']]+[item]);event('candidate-prepared',**item)
