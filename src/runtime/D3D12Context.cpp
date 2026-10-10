#include "D3D12Resources.hpp"
#include <algorithm>
#include <cfloat>
#include <cstring>
#include <cwchar>
#include <stdexcept>
namespace df {
void Context12State::retireRecording(){
    if(!retained.empty()){
        RetiredBatch batch;batch.pending.record(completion.Get(),nextFence);
        batch.resources=std::move(retained);retired.push_back(std::move(batch));retainedSet.clear();
    }
    collectRetired();
}
void Context12State::collectRetired(){
    retired.erase(std::remove_if(retired.begin(),retired.end(),[](const RetiredBatch& batch){return batch.pending.complete();}),retired.end());
}
D3D12_CPU_DESCRIPTOR_HANDLE Context12State::cpu(){
    if(cpuUsed==4096){D3D12_DESCRIPTOR_HEAP_DESC desc{D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV,4096,D3D12_DESCRIPTOR_HEAP_FLAG_NONE,0};ComPtr<ID3D12DescriptorHeap> heap;Check(device->CreateDescriptorHeap(&desc,IID_PPV_ARGS(&heap)),"Create CPU descriptors");cpuHeaps.push_back(heap);cpuUsed=0;}
    auto handle=cpuHeaps.back()->GetCPUDescriptorHandleForHeapStart();handle.ptr+=SIZE_T(cpuUsed++)*descriptorSize;return handle;
}
std::pair<D3D12_CPU_DESCRIPTOR_HANDLE,D3D12_GPU_DESCRIPTOR_HANDLE> Context12State::gpu(unsigned count){
    if(gpuUsed+count>4096){
        size_t index=0;
        const auto done=completion->GetCompletedValue();
        for(;index<gpuHeaps.size();++index)if(index!=gpuHeapIndex&&gpuHeaps[index].device==device.Get()&&gpuHeaps[index].pending.complete(completion.Get(),done))break;
        if(index==gpuHeaps.size()){
            D3D12_DESCRIPTOR_HEAP_DESC desc{D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV,4096,D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE,0};
            GpuHeap heap;heap.device=device.Get();Check(device->CreateDescriptorHeap(&desc,IID_PPV_ARGS(&heap.native)),"Create GPU descriptors");gpuHeaps.push_back(std::move(heap));
        }
        gpuHeapIndex=index;gpuUsed=0;
    }
    auto& entry=gpuHeaps[gpuHeapIndex];entry.pending.record(completion.Get(),nextFence);
    auto heap=entry.native.Get();commands->SetDescriptorHeaps(1,&heap);auto cpu=heap->GetCPUDescriptorHandleForHeapStart();auto gpu=heap->GetGPUDescriptorHandleForHeapStart();cpu.ptr+=SIZE_T(gpuUsed)*descriptorSize;gpu.ptr+=UINT64(gpuUsed)*descriptorSize;gpuUsed+=count;return {cpu,gpu};
}
void Context12State::transition(const ResourcePtr12& resource,D3D12_RESOURCE_STATES target,bool uavBarrier){
    if(!resource)return;keep(resource);if(resource->fixedState)return;
    D3D12_RESOURCE_BARRIER barrier{};
    if(resource->state!=target){barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;barrier.Transition={resource->native.Get(),D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,resource->state,target};resource->state=target;}
    else if(target==D3D12_RESOURCE_STATE_UNORDERED_ACCESS&&uavBarrier){barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_UAV;barrier.UAV.pResource=resource->native.Get();}
    else return;
    commands->ResourceBarrier(1,&barrier);dirty=true;
}
void Context12State::copy(const ResourcePtr12& dst,UINT64 offset,const ResourcePtr12& src,UINT64 start,UINT64 bytes){
    if(!bytes)return;if(!dst||!src)throw std::runtime_error("Missing D3D12 copy resource");transition(dst,D3D12_RESOURCE_STATE_COPY_DEST);transition(src,D3D12_RESOURCE_STATE_COPY_SOURCE);commands->CopyBufferRegion(dst->native.Get(),offset,src->native.Get(),start,bytes);dirty=true;
}
ContextD3D12::ContextD3D12(ID3D12Device* device,ID3D12CommandQueue* queue,ID3D12CommandQueue* graphics):state(std::make_unique<Context12State>()){
    auto& s=*state;s.device=device;s.queue=queue;s.graphics=graphics;s.descriptorSize=device->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);auto type=queue->GetDesc().Type;
    Check(device->CreateCommandAllocator(type,IID_PPV_ARGS(&s.allocator)),"Create D3D12 allocator");Check(device->CreateCommandList(0,type,s.allocator.Get(),nullptr,IID_PPV_ARGS(&s.commands)),"Create D3D12 command list");
    Check(device->CreateFence(1,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&s.completion)),"Create completion fence");Check(device->CreateFence(0,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&s.graphicsCompletion)),"Create graphics fence");s.event=CreateEventW(nullptr,FALSE,FALSE,nullptr);if(!s.event)throw std::runtime_error("Create D3D12 completion event");
    D3D12_DESCRIPTOR_RANGE ranges[2]={{D3D12_DESCRIPTOR_RANGE_TYPE_SRV,32,0,0,D3D12_DESCRIPTOR_RANGE_OFFSET_APPEND},{D3D12_DESCRIPTOR_RANGE_TYPE_UAV,8,0,0,D3D12_DESCRIPTOR_RANGE_OFFSET_APPEND}};
    D3D12_ROOT_PARAMETER parameters[4]{};parameters[0].ParameterType=D3D12_ROOT_PARAMETER_TYPE_CBV;parameters[0].Descriptor={0,0};parameters[1].ParameterType=D3D12_ROOT_PARAMETER_TYPE_DESCRIPTOR_TABLE;parameters[1].DescriptorTable={1,&ranges[0]};parameters[2].ParameterType=D3D12_ROOT_PARAMETER_TYPE_DESCRIPTOR_TABLE;parameters[2].DescriptorTable={1,&ranges[1]};parameters[3].ParameterType=D3D12_ROOT_PARAMETER_TYPE_CBV;parameters[3].Descriptor={1,0};
    D3D12_STATIC_SAMPLER_DESC sampler{};sampler.Filter=D3D12_FILTER_MIN_MAG_MIP_LINEAR;sampler.AddressU=sampler.AddressV=sampler.AddressW=D3D12_TEXTURE_ADDRESS_MODE_CLAMP;sampler.ComparisonFunc=D3D12_COMPARISON_FUNC_NEVER;sampler.MaxLOD=FLT_MAX;
    D3D12_ROOT_SIGNATURE_DESC root{4,parameters,1,&sampler,D3D12_ROOT_SIGNATURE_FLAG_NONE};ComPtr<ID3DBlob> code,errors;auto hr=D3D12SerializeRootSignature(&root,D3D_ROOT_SIGNATURE_VERSION_1,&code,&errors);if(FAILED(hr)&&errors)throw std::runtime_error(static_cast<const char*>(errors->GetBufferPointer()));Check(hr,"Serialize compute root signature");Check(device->CreateRootSignature(0,code->GetBufferPointer(),code->GetBufferSize(),IID_PPV_ARGS(&s.root)),"Create compute root signature");
    D3D12_SHADER_RESOURCE_VIEW_DESC srv{};srv.Format=DXGI_FORMAT_R32_UINT;srv.ViewDimension=D3D12_SRV_DIMENSION_BUFFER;srv.Shader4ComponentMapping=D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;srv.Buffer.NumElements=256;s.nullRead=s.cpu();device->CreateShaderResourceView(nullptr,&srv,s.nullRead);
    D3D12_UNORDERED_ACCESS_VIEW_DESC uav{};uav.Format=DXGI_FORMAT_R32_UINT;uav.ViewDimension=D3D12_UAV_DIMENSION_BUFFER;uav.Buffer.NumElements=256;s.nullWrite=s.cpu();device->CreateUnorderedAccessView(nullptr,nullptr,&uav,s.nullWrite);
    D3D12_INDIRECT_ARGUMENT_DESC arg{};arg.Type=D3D12_INDIRECT_ARGUMENT_TYPE_DISPATCH;D3D12_COMMAND_SIGNATURE_DESC indirect{12,1,&arg,0};Check(device->CreateCommandSignature(&indirect,nullptr,IID_PPV_ARGS(&s.indirect)),"Create indirect dispatch signature");
    GFSDK_Aftermath_DX12_Initialize(static_cast<GFSDK_Aftermath_Version>(0x121),device);
}
ContextD3D12::~ContextD3D12(){try{if(state->dirty)flush();}catch(...){} }
void ContextD3D12::updateContext(const NvFlexContextDesc* opaque){
    struct Desc {ID3D12Device* device;ID3D12CommandQueue* queue;ID3D12CommandQueue* graphics;ID3D12CommandAllocator* allocator;ID3D12Fence* fence;ID3D12GraphicsCommandList* list;UINT64 completed,next;void** event;};static_assert(sizeof(Desc)==72);
    auto& input=*reinterpret_cast<const Desc*>(opaque);auto& s=*state;
    if(s.commands.Get()!=input.list||s.completion.Get()!=input.fence||s.nextFence!=input.next||s.queue.Get()!=input.queue){
        // Native callers may submit the previous list themselves. Its retained
        // objects must follow that list's fence, not the new Context's value.
        s.retireRecording();s.gpuHeapIndex=size_t(-1);s.gpuUsed=4096;
    }
    s.device=input.device;s.queue=input.queue;s.graphics=input.graphics;s.allocator=input.allocator;s.completion=input.fence;s.commands=input.list;s.completed=input.completed;s.nextFence=input.next;
}
void Context12State::bind(const NvFlex::DispatchParams* p){
    auto shader=static_cast<Shader12*>(p->shader);commands->SetComputeRootSignature(root.Get());commands->SetPipelineState(shader->pipeline.Get());keep(shader->pipeline.Get());
    auto table=gpu(40);auto destination=table.first;
    for(unsigned i=0;i<32;++i){auto read=static_cast<Read12*>(p->readOnly[i]);device->CopyDescriptorsSimple(1,destination,read?read->descriptor:nullRead,D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);destination.ptr+=descriptorSize;if(read)transition(read->resource,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);}
    for(unsigned i=0;i<8;++i){auto write=static_cast<Write12*>(p->readWrite[i]);device->CopyDescriptorsSimple(1,destination,write?write->descriptor:nullWrite,D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);destination.ptr+=descriptorSize;if(write)transition(write->resource,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,true);}
    commands->SetComputeRootDescriptorTable(1,table.second);table.second.ptr+=UINT64(descriptorSize)*32;commands->SetComputeRootDescriptorTable(2,table.second);
    if(p->rootConstantBuffer){auto constant=static_cast<Constant12*>(p->rootConstantBuffer);constant->recordUse(completion.Get(),nextFence);auto current=constant->current;if(current!=rootConstant){rootConstant=current;keep(current);commands->SetComputeRootConstantBufferView(0,current->native->GetGPUVirtualAddress());}}
    if(p->secondConstantBuffer){auto constant=static_cast<Constant12*>(p->secondConstantBuffer);constant->recordUse(completion.Get(),nextFence);auto current=constant->current;if(current!=secondConstant){secondConstant=current;keep(current);commands->SetComputeRootConstantBufferView(3,current->native->GetGPUVirtualAddress());}}
}
NvFlex::ComputeShader* ContextD3D12::createComputeShader(const NvFlex::ComputeShaderDesc* desc){
    auto shader=std::make_unique<Shader12>();shader->m_desc=*desc;D3D12_COMPUTE_PIPELINE_STATE_DESC p{};p.pRootSignature=state->root.Get();p.CS={desc->cs,size_t(desc->cs_length)};
    if(desc->NvAPI_Slot!=~0u){NVAPI_D3D12_PSO_SET_SHADER_EXTENSION_SLOT_DESC extension{};extension.baseVersion=NV_PSO_EXTENSION_DESC_VER;extension.psoExtension=NV_PSO_SET_SHADER_EXTNENSION_SLOT_AND_SPACE;extension.version=NV_SET_SHADER_EXTENSION_SLOT_DESC_VER;extension.uavSlot=desc->NvAPI_Slot;extension.registerSpace=0;const NVAPI_D3D12_PSO_EXTENSION_DESC* extensions[]={&extension};NvAPI_D3D12_CreateComputePipelineState(state->device.Get(),&p,1,extensions,&shader->pipeline);}
    if(!shader->pipeline)Check(state->device->CreateComputePipelineState(&p,IID_PPV_ARGS(&shader->pipeline)),"Create D3D12 compute pipeline");return shader.release();
}
void ContextD3D12::dispatch(const NvFlex::DispatchParams* p){state->bind(p);pixBeginEvent(p->shader->m_desc.label);state->commands->Dispatch(p->gridDim.x,p->gridDim.y,p->gridDim.z);pixEndEvent();state->dirty=true;}
void ContextD3D12::dispatchIndirect(const NvFlex::DispatchParams* p){state->bind(p);auto arguments=static_cast<Buffer12*>(p->IndirectLaunchArgs);state->transition(arguments->gpu,D3D12_RESOURCE_STATE_INDIRECT_ARGUMENT);state->commands->ExecuteIndirect(state->indirect.Get(),1,arguments->gpu->native.Get(),0,nullptr,0);state->dirty=true;}
void ContextD3D12::clearUnorderedAccessViewUint(NvFlex::Buffer* input,const unsigned* values){auto b=static_cast<Buffer12*>(input);auto& s=*state;auto table=s.gpu(1);s.device->CopyDescriptorsSimple(1,table.first,b->write.descriptor,D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);s.transition(b->gpu,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,true);s.commands->ClearUnorderedAccessViewUint(table.second,b->write.descriptor,b->gpu->native.Get(),values,0,nullptr);s.dirty=true;}
void ContextD3D12::clearUnorderedAccessViewFloat(NvFlex::Buffer* input,const float* values){auto b=static_cast<Buffer12*>(input);auto& s=*state;auto table=s.gpu(1);s.device->CopyDescriptorsSimple(1,table.first,b->write.descriptor,D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV);s.transition(b->gpu,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,true);s.commands->ClearUnorderedAccessViewFloat(table.second,b->write.descriptor,b->gpu->native.Get(),values,0,nullptr);s.dirty=true;}
void ContextD3D12::flush(){auto& s=*state;if(!s.dirty)return;Check(s.commands->Close(),"Close D3D12 commands");ID3D12CommandList* lists[]={s.commands.Get()};s.queue->ExecuteCommandLists(1,lists);UINT64 value=s.nextFence++;Check(s.queue->Signal(s.completion.Get(),value),"Signal D3D12 completion");Check(s.completion->SetEventOnCompletion(value,s.event),"Arm D3D12 completion");WaitForSingleObject(s.event,INFINITE);s.completed=value;
    Check(s.allocator->Reset(),"Reset D3D12 allocator");Check(s.commands->Reset(s.allocator.Get(),nullptr),"Reset D3D12 commands");s.dirty=false;s.rootConstant.reset();s.secondConstant.reset();s.retained.clear();s.retainedSet.clear();s.collectRetired();s.gpuHeapIndex=size_t(-1);s.gpuUsed=4096;
}
NvFlex::Fence* ContextD3D12::createFence(){auto f=std::make_unique<Fence12>();Check(state->device->CreateFence(0,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&f->fence)),"Create D3D12 API fence");f->event=CreateEventW(nullptr,FALSE,FALSE,nullptr);return f.release();}
void ContextD3D12::fenceSet(NvFlex::Fence* input){auto f=static_cast<Fence12*>(input);UINT64 value=f->value++;Check(state->queue->Signal(f->fence.Get(),value),"Signal D3D12 API fence");Check(f->fence->SetEventOnCompletion(value,f->event),"Arm D3D12 API fence");}
void ContextD3D12::fenceWait(NvFlex::Fence* input){WaitForSingleObject(static_cast<Fence12*>(input)->event,INFINITE);}
void ContextD3D12::computeWaitForGraphics(){auto& s=*state;if(s.graphics){UINT64 value=++s.graphicsValue;Check(s.graphics->Signal(s.graphicsCompletion.Get(),value),"Signal graphics queue");Check(s.queue->Wait(s.graphicsCompletion.Get(),value),"Compute wait for graphics queue");}}
void ContextD3D12::startFrame(){}
// RVA 0x5a180 calls native ClearState but leaves the CPU CBV caches intact.
// Preserve that observable behavior, including after the NVIDIA substep clear.
void ContextD3D12::clearState(){state->commands->ClearState(nullptr);}
void ContextD3D12::contextPush(){}
void ContextD3D12::contextPop(){}
void ContextD3D12::pixBeginEvent(const wchar_t* label){state->commands->BeginEvent(0,label,UINT(std::wcslen(label)*2));}
void ContextD3D12::pixEndEvent(){state->commands->EndEvent();}
void ContextD3D12::eventMarker(const wchar_t* label){state->commands->SetMarker(0,label,UINT(std::wcslen(label)*2));}
int ContextD3D12::setEventMarkerAftermath(void* p,unsigned size){return int(GFSDK_Aftermath_DX12_SetEventMarker(state->commands.Get(),p,size));}
int ContextD3D12::getDataAftermath(GFSDK_Aftermath_ContextData* data,GFSDK_Aftermath_Status* status){auto list=state->commands.Get();return int(GFSDK_Aftermath_DX12_GetData(1,&list,data,status));}
class Timers12 final : public NvFlex::TimerPool {
    ContextD3D12* context;ComPtr<ID3D12QueryHeap> queries;ResourcePtr12 readback;std::vector<UINT64> host;UINT64 frequency=0;
public:
    explicit Timers12(ContextD3D12* c):context(c){reserve(200);}
    int begin() override{int index=-1;auto& s=*context->state;if(m_usedElemCount<m_timerPoolSize){index=int(m_usedElemCount++);s.commands->EndQuery(queries.Get(),D3D12_QUERY_TYPE_TIMESTAMP,index*2);s.keep(queries.Get());s.dirty=true;}++m_requestedElemCount;return index;}
    void end(int index) override{if(index>=0){auto& s=*context->state;s.commands->EndQuery(queries.Get(),D3D12_QUERY_TYPE_TIMESTAMP,index*2+1);s.keep(queries.Get());s.dirty=true;}}
    void resolve() override{if(m_usedElemCount){auto& s=*context->state;if(!frequency)Check(s.queue->GetTimestampFrequency(&frequency),"Get D3D12 timestamp frequency");s.commands->ResolveQueryData(queries.Get(),D3D12_QUERY_TYPE_TIMESTAMP,0,UINT(m_usedElemCount*2),readback->native.Get(),0);s.keep(queries.Get());s.keep(readback);s.dirty=true;}}
    void sync() override{if(m_usedElemCount){void* data=nullptr;D3D12_RANGE range{0,m_usedElemCount*16};Check(readback->native->Map(0,&range,&data),"Map timestamps");std::memcpy(host.data(),data,m_usedElemCount*16);D3D12_RANGE empty{};readback->native->Unmap(0,&empty);}reserve(m_requestedElemCount);m_requestedElemCount=0;}
    void clear() override{m_usedElemCount=0;}
    float get(int index,UINT64* begin=nullptr,UINT64* end=nullptr,UINT64* outFrequency=nullptr) override{if(index<0)return 0;auto a=host.at(index*2),b=host.at(index*2+1);if(begin)*begin=a;if(end)*end=b;if(outFrequency)*outFrequency=frequency;return float(double(b-a)/double(frequency))*1000.0f;}
    void reserve(size_t n) override{if(n<=m_timerPoolSize)return;auto& s=*context->state;s.keep(queries.Get());s.keep(readback);D3D12_QUERY_HEAP_DESC desc{D3D12_QUERY_HEAP_TYPE_TIMESTAMP,UINT(n*2),0};queries.Reset();Check(s.device->CreateQueryHeap(&desc,IID_PPV_ARGS(&queries)),"Create timestamp heap");readback=s.buffer(UINT64(n)*16,D3D12_HEAP_TYPE_READBACK);host.resize(n*2);m_timerPoolSize=n;}
};
NvFlex::TimerPool* ContextD3D12::createTimerPool(){return new Timers12(this);}
}
