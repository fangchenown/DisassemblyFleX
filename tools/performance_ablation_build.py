"""Isolated causal experiments, never replacing the delivered candidate DLL.

cbpool: reuse completed constant-buffer versions, keep each upload mapping.
heapreuse: recycle shader-visible descriptor heaps only after blocking completion.
"""
import argparse,msvcrt,time,shutil,subprocess
import performance_benchmark as b
from build import environment
def replace(path,old,new):
    text=path.read_text();assert text.count(old)==1,(path,old);path.write_text(text.replace(old,new))
def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=['cbpool','heapreuse','cbpool-heapreuse'],required=True);a=p.parse_args()
    name='ablation-'+a.variant+'-v1';source=b.ROOT/'source-snapshots'/name;binary=b.ROOT/'builds'/name
    assert not source.exists() and not binary.exists();source.mkdir(parents=True);binary.mkdir(parents=True)
    for top in ['include','src','shaders','cmake','reference','tools','tests']:shutil.copytree(b.PROJECT/top,source/top,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy2(b.PROJECT/'CMakeLists.txt',source/'CMakeLists.txt')
    header=source/'src/runtime/D3D12Resources.hpp';resource=source/'src/runtime/D3D12Resources.cpp';context=source/'src/runtime/D3D12Context.cpp'
    if 'cbpool' in a.variant:
        replace(header,'struct Constant12 final : NvFlex::ConstantBuffer {DF_REF12 ResourcePtr12 current;};','''struct Constant12 final : NvFlex::ConstantBuffer {DF_REF12 ResourcePtr12 current;
    struct Version {ResourcePtr12 resource;void* mapped;UINT64 fence;};std::vector<Version> versions;
};''')
        replace(resource,'void* ContextD3D12::map(NvFlex::ConstantBuffer* input){auto b=static_cast<Constant12*>(input);b->current=state->buffer((UINT64(b->m_desc.dim)*b->m_desc.stride+255)&~UINT64(255),D3D12_HEAP_TYPE_UPLOAD);void* data=nullptr;D3D12_RANGE empty{};Check(b->current->native->Map(0,&empty,&data),"Map D3D12 constant");return data;}','''void* ContextD3D12::map(NvFlex::ConstantBuffer* input){
    auto b=static_cast<Constant12*>(input);
    // Exclude front so a new upload preserves the original CBV-change protocol.
    for(auto& v:b->versions)if(v.resource!=b->current&&v.fence<=state->completed){b->current=v.resource;v.fence=state->nextFence;return v.mapped;}
    b->current=state->buffer((UINT64(b->m_desc.dim)*b->m_desc.stride+255)&~UINT64(255),D3D12_HEAP_TYPE_UPLOAD);
    void* data=nullptr;D3D12_RANGE empty{};Check(b->current->native->Map(0,&empty,&data),"Map D3D12 constant");b->versions.push_back({b->current,data,state->nextFence});return data;
}''')
        replace(resource,'void ContextD3D12::unmap(NvFlex::ConstantBuffer* input){static_cast<Constant12*>(input)->current->native->Unmap(0,nullptr);}','void ContextD3D12::unmap(NvFlex::ConstantBuffer*){} // Diagnostic: persistent mapping until resource destruction.')
    if 'heapreuse' in a.variant:
        replace(header,'std::vector<ComPtr<ID3D12DescriptorHeap>> cpuHeaps,gpuHeaps;','std::vector<ComPtr<ID3D12DescriptorHeap>> cpuHeaps,gpuHeaps,recycledGpuHeaps;')
        replace(context,'Check(device->CreateDescriptorHeap(&desc,IID_PPV_ARGS(&heap)),"Create GPU descriptors");gpuHeaps.push_back(heap);','if(recycledGpuHeaps.empty()){Check(device->CreateDescriptorHeap(&desc,IID_PPV_ARGS(&heap)),"Create GPU descriptors");}else{heap=std::move(recycledGpuHeaps.back());recycledGpuHeaps.pop_back();}gpuHeaps.push_back(heap);')
        replace(context,'s.gpuHeaps.clear();s.gpuUsed=4096;','for(auto& heap:s.gpuHeaps)s.recycledGpuHeaps.push_back(std::move(heap));s.gpuHeaps.clear();s.gpuUsed=4096;')
    b.write(source/'source_manifest.json',{p.relative_to(source).as_posix():b.sha(p) for p in sorted(source.rglob('*')) if p.is_file()})
    temp=b.ROOT/'temp'/name;temp.mkdir();env=environment(temp)
    configure=['cmake','-S',str(source),'-B',str(binary),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_MAKE_PROGRAM='+str(b.WS/'Build/Toolchains/ninja/1.13.2/ninja.exe'),'-DDISASSEMBLYFLEX_WORKSPACE='+str(b.WS)]
    with b.SystemRequired(),(b.WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock').open('a+b') as lock:
        while True:
            try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:time.sleep(.1)
        with (b.ROOT/'logs'/f'{name}-build.log').open('wb') as log:
            for cmd in [configure,['cmake','--build',str(binary),'--target','NvFlexReconstructed','--parallel','4']]:
                result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:raise RuntimeError(str(name)+' build failed')
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    receipt=dict(status='PASS',variant=a.variant,source=str(source),binary=str(binary),dll_sha256=b.sha(binary/'NvFlexReleaseD3D_x64.dll'),diagnostic_only=True)
    b.write(b.ROOT/'evidence'/f'{name}.json',receipt);b.event('ablation-build',**receipt);print(receipt)
if __name__=='__main__':main()
