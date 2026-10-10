#include "D3D12Resources.hpp"
#include <algorithm>
#include <cstring>
namespace df {
void PendingUses12::record(ID3D12Fence* fence,UINT64 value){
    for(auto& use:uses)if(use.fence.Get()==fence){use.value=std::max(use.value,value);return;}
    // Context changes are uncommon. Retire completed timelines here, while
    // keeping the common single-fence dispatch path free of allocations.
    uses.erase(std::remove_if(uses.begin(),uses.end(),[](const Use& use){
        const auto done=use.fence->GetCompletedValue();
        return done!=UINT64(-1)&&done>=use.value;
    }),uses.end());
    uses.push_back({fence,value});
}
bool PendingUses12::complete(ID3D12Fence* knownFence,UINT64 knownValue) const{
    for(const auto& use:uses){const auto done=use.fence.Get()==knownFence?knownValue:use.fence->GetCompletedValue();if(done==UINT64(-1)||done<use.value)return false;}
    return true;
}
void Constant12::recordUse(ID3D12Fence* fence,UINT64 value){
    if(currentVersion!=size_t(-1))versions[currentVersion].pending.record(fence,value);
}
ResourcePtr12 Context12State::buffer(UINT64 bytes,D3D12_HEAP_TYPE heap,bool staging,bool uav){
    if(!bytes)return {};auto output=std::make_shared<Resource12>();D3D12_HEAP_PROPERTIES properties{};properties.Type=heap;properties.CreationNodeMask=properties.VisibleNodeMask=1;
    if(staging){properties=device->GetCustomHeapProperties(0,D3D12_HEAP_TYPE_READBACK);properties.CPUPageProperty=D3D12_CPU_PAGE_PROPERTY_WRITE_BACK;output->state=D3D12_RESOURCE_STATE_COPY_SOURCE;}
    else if(heap==D3D12_HEAP_TYPE_UPLOAD){output->state=D3D12_RESOURCE_STATE_GENERIC_READ;output->fixedState=true;}
    else if(heap==D3D12_HEAP_TYPE_READBACK){output->state=D3D12_RESOURCE_STATE_COPY_DEST;output->fixedState=true;}
    else output->state=D3D12_RESOURCE_STATE_COPY_DEST;
    D3D12_RESOURCE_DESC desc{};desc.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;desc.Width=bytes;desc.Height=1;desc.DepthOrArraySize=1;desc.MipLevels=1;desc.SampleDesc.Count=1;desc.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;desc.Flags=uav?D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS:D3D12_RESOURCE_FLAG_NONE;
    Check(device->CreateCommittedResource(&properties,D3D12_HEAP_FLAG_NONE,&desc,output->state,nullptr,IID_PPV_ARGS(&output->native)),"Create D3D12 buffer");return output;
}
Buffer12::Buffer12(ContextD3D12* c,const NvFlex::BufferDesc& desc,ID3D12Resource* external):context(c){
    m_desc=desc;read.owner=this;write.owner=this;write.read=&read;auto& s=*c->state;UINT64 bytes=UINT64(desc.dim)*desc.stride;
    if(external){gpu=std::make_shared<Resource12>();gpu->native=external;gpu->state=D3D12_RESOURCE_STATE_COMMON;return;}
    if(desc.bufferType&NvFlex::eBuffer)gpu=s.buffer(bytes,D3D12_HEAP_TYPE_DEFAULT,false,true);
    if((desc.bufferType&NvFlex::eStage)||desc.data)stage=s.buffer(bytes,D3D12_HEAP_TYPE_CUSTOM,true);
    if(desc.bufferType&NvFlex::eUAV_SRV)views(desc.format);
    if(desc.data&&bytes){void* data=nullptr;D3D12_RANGE empty{};Check(stage->native->Map(0,&empty,&data),"Initialize D3D12 stage");std::memcpy(data,desc.data,size_t(bytes));stage->native->Unmap(0,nullptr);if(gpu)s.copy(gpu,0,stage,0,bytes);}
}
void Buffer12::views(NvFlexFormat format){
    if(!gpu)return;auto& s=*context->state;bool raw=(m_desc.bufferType&NvFlex::eRaw)!=0,structured=(m_desc.bufferType&NvFlex::eStructured)&&format==eNvFlexFormat_unknown;
    unsigned bytes=m_desc.dim*m_desc.stride;unsigned stride=raw?4:structured?m_desc.stride:NvFlex::getFormatSizeInBytes(format);if(!stride)stride=m_desc.stride;
    D3D12_SHADER_RESOURCE_VIEW_DESC srv{};srv.Format=raw?DXGI_FORMAT_R32_TYPELESS:NvFlex::convertToDXGI(format);srv.ViewDimension=D3D12_SRV_DIMENSION_BUFFER;srv.Shader4ComponentMapping=D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;srv.Buffer.NumElements=bytes/stride;srv.Buffer.StructureByteStride=structured?m_desc.stride:0;srv.Buffer.Flags=raw?D3D12_BUFFER_SRV_FLAG_RAW:D3D12_BUFFER_SRV_FLAG_NONE;
    read.resource=gpu;read.descriptor=s.cpu();s.device->CreateShaderResourceView(gpu->native.Get(),&srv,read.descriptor);
    D3D12_UNORDERED_ACCESS_VIEW_DESC uav{};uav.Format=srv.Format;uav.ViewDimension=D3D12_UAV_DIMENSION_BUFFER;uav.Buffer.NumElements=srv.Buffer.NumElements;uav.Buffer.StructureByteStride=srv.Buffer.StructureByteStride;uav.Buffer.Flags=raw?D3D12_BUFFER_UAV_FLAG_RAW:D3D12_BUFFER_UAV_FLAG_NONE;
    write.resource=gpu;write.descriptor=s.cpu();s.device->CreateUnorderedAccessView(gpu->native.Get(),nullptr,&uav,write.descriptor);
}
NvFlex::Resource* Buffer12::getResource(NvFlex::BufferResourceTypes type){if(type==NvFlex::eResource)return &read;auto resource=type==NvFlex::eDefaultBuffer?gpu:stage;return reinterpret_cast<NvFlex::Resource*>(resource?resource->native.Get():nullptr);}
NvFlex::Buffer* ContextD3D12::createBuffer(const NvFlex::BufferDesc* desc,void* native){return new Buffer12(this,*desc,(desc->bufferType&NvFlex::eShared)?static_cast<ID3D12Resource*>(native):nullptr);}
NvFlex::Buffer* ContextD3D12::createBufferView(NvFlex::Buffer* original,const NvFlex::BufferViewDesc* desc){
    auto source=static_cast<Buffer12*>(original);auto view=std::make_unique<Buffer12>(this,NvFlex::BufferDesc{});view->m_desc=source->m_desc;view->gpu=source->gpu;view->stage=source->stage;
    unsigned bytes=source->m_desc.dim*source->m_desc.stride,stride=NvFlex::getFormatSizeInBytes(desc->format);view->m_desc.format=desc->format;view->m_desc.dim=bytes/stride;
    // The ABI descriptor retains original stride; native typed views use the
    // true resource byte width, as the original view constructor does.
    unsigned saved=view->m_desc.stride;view->m_desc.stride=stride;view->views(desc->format);view->m_desc.stride=saved;return view.release();
}
void* ContextD3D12::map(NvFlex::Buffer* input,NvFlex::MapType type,bool){
    auto b=static_cast<Buffer12*>(input);if(state->dirty&&(type==NvFlex::eMapRead||type==NvFlex::eMapReadWrite))flush();
    if(type!=NvFlex::eMapWriteDiscard&&b->downloadFence>state->completed)return nullptr;if(!b->stage)return nullptr;
    void* data=nullptr;D3D12_RANGE range{0,size_t(b->m_desc.dim)*b->m_desc.stride};Check(b->stage->native->Map(0,&range,&data),"Map D3D12 buffer");return data;
}
void ContextD3D12::unmap(NvFlex::Buffer* input){auto b=static_cast<Buffer12*>(input);D3D12_RANGE empty{};if(b->stage)b->stage->native->Unmap(0,&empty);}
void ContextD3D12::upload(NvFlex::Buffer* b){upload(b,0,b->m_desc.dim*b->m_desc.stride);}
void ContextD3D12::upload(NvFlex::Buffer* input,NvFlexUint offset,NvFlexUint bytes){auto b=static_cast<Buffer12*>(input);state->copy(b->gpu,offset,b->stage,offset,bytes);}
void ContextD3D12::download(NvFlex::Buffer* b){download(b,0,b->m_desc.dim*b->m_desc.stride);}
void ContextD3D12::download(NvFlex::Buffer* input,NvFlexUint offset,NvFlexUint bytes){auto b=static_cast<Buffer12*>(input);state->copy(b->stage,offset,b->gpu,offset,bytes);b->downloadFence=state->nextFence;}
void ContextD3D12::copy(NvFlex::Buffer* dst,unsigned offset,NvFlex::Buffer* src,unsigned start,unsigned bytes){state->copy(static_cast<Buffer12*>(dst)->gpu,offset,static_cast<Buffer12*>(src)->gpu,start,bytes);}
void ContextD3D12::copyToHost(NvFlex::Buffer* dst,unsigned offset,NvFlex::Buffer* src,unsigned start,unsigned bytes){auto a=static_cast<Buffer12*>(dst);state->copy(a->stage,offset,static_cast<Buffer12*>(src)->gpu,start,bytes);a->downloadFence=state->nextFence;}
void ContextD3D12::copyToDevice(NvFlex::Buffer* dst,unsigned offset,NvFlex::Buffer* src,unsigned start,unsigned bytes,NvFlex::BufferResourceTypes type){
    ResourcePtr12 source;if(type==NvFlex::eNativeBuffer){source=std::make_shared<Resource12>();source->native=reinterpret_cast<ID3D12Resource*>(src);source->state=D3D12_RESOURCE_STATE_COMMON;}
    else{auto b=static_cast<Buffer12*>(src);source=type==NvFlex::eDefaultBuffer?b->gpu:b->stage;}
    state->copy(static_cast<Buffer12*>(dst)->gpu,offset,source,start,bytes);if(type==NvFlex::eNativeBuffer)state->transition(source,D3D12_RESOURCE_STATE_COMMON);
}
void ContextD3D12::copyToNative(void* native,unsigned offset,NvFlex::Buffer* src,unsigned start,unsigned bytes){
    // Preserve RVA 0x582e0's legacy native transition behavior. The reference
    // reads private BufferD3D12 fields from the native argument itself. With a
    // standard ID3D12Resource this faults on the tested driver; the isolated
    // native probe records that original API defect. Do not silently turn this
    // recovery into a repaired API with different observable behavior.
    auto base=static_cast<unsigned char*>(native);ID3D12Resource* transitionResource=nullptr;std::memcpy(&transitionResource,base+0x68,sizeof(transitionResource));
    auto trackedState=reinterpret_cast<D3D12_RESOURCE_STATES*>(base+0x228);
    if(*trackedState!=D3D12_RESOURCE_STATE_COPY_DEST){D3D12_RESOURCE_BARRIER barrier{};barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;barrier.Transition={transitionResource,0,*trackedState,D3D12_RESOURCE_STATE_COPY_DEST};state->commands->ResourceBarrier(1,&barrier);*trackedState=D3D12_RESOURCE_STATE_COPY_DEST;}
    auto source=static_cast<Buffer12*>(src)->gpu;state->keep(source);state->keep(static_cast<ID3D12Resource*>(native));state->commands->CopyBufferRegion(static_cast<ID3D12Resource*>(native),offset,source->native.Get(),start,bytes);state->dirty=true;
}
void ContextD3D12::copyResourceState(NvFlex::Buffer* from,NvFlex::Buffer* to){auto a=static_cast<Buffer12*>(from),b=static_cast<Buffer12*>(to);if(a->gpu&&b->gpu)b->gpu->state=a->gpu->state;}
NvFlex::ConstantBuffer* ContextD3D12::createConstantBuffer(const NvFlex::ConstantBufferDesc* desc){auto b=new Constant12;b->m_desc=*desc;if(!desc->uploadAccess)b->current=state->buffer((UINT64(desc->dim)*desc->stride+255)&~UINT64(255),D3D12_HEAP_TYPE_DEFAULT);return b;}
void* ContextD3D12::map(NvFlex::ConstantBuffer* input){
    auto b=static_cast<Constant12*>(input);auto& s=*state;
    const auto completed=s.completion->GetCompletedValue();
    for(size_t i=0;i<b->versions.size();++i){
        auto& version=b->versions[i];
        // Keep front distinct, including across ClearState: bind() uses the
        // resource identity to preserve the recovered CBV cache protocol.
        if(i!=b->currentVersion&&version.device==s.device.Get()&&version.pending.complete(s.completion.Get(),completed)){
            b->currentVersion=i;b->current=version.resource;
            version.pending.record(s.completion.Get(),s.nextFence);return version.mapped;
        }
    }
    Constant12::Version version;
    version.resource=s.buffer((UINT64(b->m_desc.dim)*b->m_desc.stride+255)&~UINT64(255),D3D12_HEAP_TYPE_UPLOAD);
    version.device=s.device.Get();D3D12_RANGE empty{};
    Check(version.resource->native->Map(0,&empty,&version.mapped),"Map D3D12 constant");
    version.pending.record(s.completion.Get(),s.nextFence);
    b->versions.push_back(std::move(version));b->currentVersion=b->versions.size()-1;
    b->current=b->versions.back().resource;return b->versions.back().mapped;
}
// Upload heaps stay mapped for their lifetime. Visibility and reuse are gated
// by submission fences, not by Unmap, matching the original versioned path.
void ContextD3D12::unmap(NvFlex::ConstantBuffer*){}
void ContextD3D12::copy(NvFlex::ConstantBuffer* dst,NvFlex::Buffer* src){auto a=static_cast<Constant12*>(dst);a->recordUse(state->completion.Get(),state->nextFence);state->copy(a->current,0,static_cast<Buffer12*>(src)->gpu,0,a->m_desc.dim*a->m_desc.stride);state->transition(a->current,D3D12_RESOURCE_STATE_VERTEX_AND_CONSTANT_BUFFER);}
}
