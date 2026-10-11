#include "D3D11Resources.hpp"
#include "dx/context/Format.h"
#include <algorithm>
#include <stdexcept>
#include "NvApiInterop.hpp"

namespace df {
ContextD3D11::ContextD3D11(ID3D11Device* d,ID3D11DeviceContext* c,ID3D11Device* rd,ID3D11DeviceContext* rc):device(d),immediate(c),renderDevice(rd),renderContext(rc){
    D3D11_SAMPLER_DESC sampler{};sampler.Filter=D3D11_FILTER_MIN_MAG_MIP_LINEAR;
    sampler.AddressU=sampler.AddressV=sampler.AddressW=D3D11_TEXTURE_ADDRESS_CLAMP;
    sampler.MaxLOD=D3D11_FLOAT32_MAX;sampler.ComparisonFunc=D3D11_COMPARISON_NEVER;
    Check(device->CreateSamplerState(&sampler,&linearSampler),"Create linear sampler");
    GFSDK_Aftermath_DX11_Initialize(static_cast<GFSDK_Aftermath_Version>(0x121),device.Get());
    if(renderDevice){NvCheck(NvInterop(0x76101e1f,device.Get(),&computeFinished,&computeCount),"Create compute synchronization");NvCheck(NvInterop(0x76101e1f,device.Get(),&graphicsFinished,&graphicsCount),"Create graphics synchronization");D3D11_QUERY_DESC query{D3D11_QUERY_EVENT,0};Check(renderDevice->CreateQuery(&query,&renderCompletion),"Create render completion query");Check(device->CreateQuery(&query,&computeCompletion),"Create compute completion query");}
}
struct ContextD3D11::SavedState {
    ID3D11Buffer* constants[8]{};ID3D11SamplerState* samplers[8]{};ID3D11ShaderResourceView* reads[16]{};ID3D11UnorderedAccessView* writes[8]{};ID3D11ComputeShader* shader=nullptr;
    ~SavedState(){for(auto p:constants)if(p)p->Release();for(auto p:samplers)if(p)p->Release();for(auto p:reads)if(p)p->Release();for(auto p:writes)if(p)p->Release();if(shader)shader->Release();}
};
ContextD3D11::~ContextD3D11(){if(renderDevice){NvInterop(0xda5b591e,device.Get(),computeFinished);NvInterop(0xda5b591e,device.Get(),graphicsFinished);}}
void ContextD3D11::updateContext(const NvFlexContextDesc* opaque){
    invalidateBindings();
    // This backend's private descriptor is 40 bytes (PDB layout), distinct
    // from the 72-byte D3D12 descriptor with the same source type name.
    struct Desc {ID3D11Device* device;ID3D11Device* renderDevice;ID3D11DeviceContext* immediate;ID3D11DeviceContext* renderContext;bool async;};static_assert(sizeof(Desc)==40);
    auto& input=*reinterpret_cast<const Desc*>(opaque);device=input.device;renderDevice=input.renderDevice;immediate=input.immediate;renderContext=input.renderContext;
}
NvFlex::Texture3D* ContextD3D11::createTexture3D(const NvFlex::Texture3DDesc* desc){
    auto out=std::make_unique<Texture>();out->m_desc=*desc;out->read.owner=out.get();out->write.owner=out.get();out->write.read=&out->read;
    D3D11_TEXTURE3D_DESC td{};td.Width=desc->dim.x;td.Height=desc->dim.y;td.Depth=desc->dim.z;td.MipLevels=1;
    td.Format=NvFlex::convertToDXGI(desc->format);td.BindFlags=D3D11_BIND_SHADER_RESOURCE|D3D11_BIND_UNORDERED_ACCESS;
    D3D11_SUBRESOURCE_DATA data{desc->data,desc->dim.x*NvFlex::getFormatSizeInBytes(desc->format),desc->dim.x*desc->dim.y*NvFlex::getFormatSizeInBytes(desc->format)};
    Check(device->CreateTexture3D(&td,desc->data?&data:nullptr,&out->gpu),"CreateTexture3D");
    Check(device->CreateShaderResourceView(out->gpu.Get(),nullptr,&out->read.view),"Create texture SRV");
    Check(device->CreateUnorderedAccessView(out->gpu.Get(),nullptr,&out->write.view),"Create texture UAV");
    td.Usage=D3D11_USAGE_STAGING;td.BindFlags=0;td.CPUAccessFlags=D3D11_CPU_ACCESS_READ|D3D11_CPU_ACCESS_WRITE;
    Check(device->CreateTexture3D(&td,nullptr,&out->stage),"Create staging texture");return out.release();
}
NvFlex::MappedData ContextD3D11::map(NvFlex::Texture3D* input){
    auto texture=static_cast<Texture*>(input);D3D11_MAPPED_SUBRESOURCE mapped{};
    Check(immediate->Map(texture->stage.Get(),0,D3D11_MAP_WRITE,0,&mapped),"Map texture upload");texture->uploadMapped=true;
    return {mapped.pData,mapped.RowPitch,mapped.DepthPitch};
}
void ContextD3D11::unmap(NvFlex::Texture3D* input){auto t=static_cast<Texture*>(input);immediate->Unmap(t->stage.Get(),0);if(t->uploadMapped)immediate->CopyResource(t->gpu.Get(),t->stage.Get());t->uploadMapped=false;}
void ContextD3D11::download(NvFlex::Texture3D* input){auto t=static_cast<Texture*>(input);immediate->CopyResource(t->stage.Get(),t->gpu.Get());}
NvFlex::MappedData ContextD3D11::mapDownload(NvFlex::Texture3D* input){auto t=static_cast<Texture*>(input);D3D11_MAPPED_SUBRESOURCE mapped{};Check(immediate->Map(t->stage.Get(),0,D3D11_MAP_READ,0,&mapped),"Map texture readback");return {mapped.pData,mapped.RowPitch,mapped.DepthPitch};}
void ContextD3D11::unmapDownload(NvFlex::Texture3D* input){immediate->Unmap(static_cast<Texture*>(input)->stage.Get(),0);}
void ContextD3D11::copy(NvFlex::Texture3D* dst,NvFlex::Texture3D* src){immediate->CopyResource(static_cast<Texture*>(dst)->gpu.Get(),static_cast<Texture*>(src)->gpu.Get());}
NvFlex::ComputeShader* ContextD3D11::createComputeShader(const NvFlex::ComputeShaderDesc* desc){
    auto out=std::make_unique<Shader>();out->m_desc=*desc;
    if(desc->NvAPI_Slot!=~0u)NvAPI_D3D11_SetNvShaderExtnSlot(device.Get(),desc->NvAPI_Slot);
    HRESULT hr=device->CreateComputeShader(desc->cs,static_cast<SIZE_T>(desc->cs_length),nullptr,&out->shader);
    if(desc->NvAPI_Slot!=~0u)NvAPI_D3D11_SetNvShaderExtnSlot(device.Get(),~0u);
    Check(hr,"CreateComputeShader");return out.release();
}
void ContextD3D11::invalidateBindings(){resourcesKnownClear=false;samplerKnown=false;lastReadSpan=32;for(unsigned i=0;i<2;++i){constantKnown[i]=false;boundConstants[i]=nullptr;}}
void ContextD3D11::invalidateConstant(ID3D11Buffer* buffer){if(solverBatchDepth)for(unsigned i=0;i<2;++i)if(boundConstants[i]==buffer)constantKnown[i]=false;}
void ContextD3D11::beginSolverBatch(){++solverBatchDepth;invalidateBindings();}
void ContextD3D11::endSolverBatch(){if(solverBatchDepth)--solverBatchDepth;invalidateBindings();}
void ContextD3D11::bind(const NvFlex::DispatchParams* params){
    auto shader=static_cast<Shader*>(params->shader);immediate->CSSetShader(shader->shader.Get(),nullptr,0);
    ID3D11ShaderResourceView* reads[32]{};ID3D11UnorderedAccessView* writes[8]{};
    unsigned readSpan=solverBatchDepth&&resourcesKnownClear?0u:32u;
    for(unsigned i=0;i<32;++i)if(params->readOnly[i]){reads[i]=static_cast<ReadView*>(params->readOnly[i])->view.Get();readSpan=std::max(readSpan,i+1);}
    for(unsigned i=0;i<8;++i)if(params->readWrite[i])writes[i]=static_cast<WriteView*>(params->readWrite[i])->view.Get();
    if(readSpan)immediate->CSSetShaderResources(0,readSpan,reads);
    // Keep all eight UAV binds/unbinds, including the reserved NV extension
    // slot and every read/write hazard boundary from the original runtime.
    immediate->CSSetUnorderedAccessViews(0,8,writes,nullptr);lastReadSpan=readSpan;
    auto constant=[&](unsigned slot,NvFlex::ConstantBuffer* input){
        if(!input)return;auto cb=static_cast<ConstantBuffer*>(input)->buffer.Get();
        if(!solverBatchDepth||!constantKnown[slot]||boundConstants[slot]!=cb)immediate->CSSetConstantBuffers(slot,1,&cb);
        if(solverBatchDepth){boundConstants[slot]=cb;constantKnown[slot]=true;}
    };
    constant(0,params->rootConstantBuffer);constant(1,params->secondConstantBuffer);
    auto sampler=linearSampler.Get();if(!solverBatchDepth||!samplerKnown)immediate->CSSetSamplers(0,1,&sampler);samplerKnown=solverBatchDepth!=0;
#if defined(DF_VALIDATE_BINDINGS)
    if(solverBatchDepth){
        bool mismatch=false;ID3D11ShaderResourceView* actualReads[32]{};immediate->CSGetShaderResources(0,32,actualReads);
        for(unsigned i=0;i<32;++i){
            if(actualReads[i]!=reads[i]){
                bool alias=false;if(reads[i]){ComPtr<ID3D11Resource> resource;reads[i]->GetResource(&resource);for(auto write:writes)if(write){ComPtr<ID3D11Resource> output;write->GetResource(&output);alias=alias||resource.Get()==output.Get();}}
                if(!(actualReads[i]==nullptr&&alias))mismatch=true;
            }
            if(actualReads[i])actualReads[i]->Release();
        }
        ID3D11UnorderedAccessView* actualWrites[8]{};immediate->CSGetUnorderedAccessViews(0,8,actualWrites);
        for(unsigned i=0;i<8;++i){mismatch=mismatch||actualWrites[i]!=writes[i];if(actualWrites[i])actualWrites[i]->Release();}
        for(unsigned i=0;i<2;++i)if(constantKnown[i]){ComPtr<ID3D11Buffer> actual;immediate->CSGetConstantBuffers(i,1,&actual);mismatch=mismatch||actual.Get()!=boundConstants[i];}
        ComPtr<ID3D11SamplerState> actualSampler;immediate->CSGetSamplers(0,1,&actualSampler);mismatch=mismatch||actualSampler.Get()!=sampler;
        if(mismatch)throw std::runtime_error("D3D11 solver binding state differs from submitted resources");
    }
#endif
}
void ContextD3D11::unbindResources(){
    ID3D11ShaderResourceView* reads[32]{};ID3D11UnorderedAccessView* writes[8]{};
    unsigned readSpan=solverBatchDepth?lastReadSpan:32u;
    if(readSpan)immediate->CSSetShaderResources(0,readSpan,reads);
    immediate->CSSetUnorderedAccessViews(0,8,writes,nullptr);resourcesKnownClear=solverBatchDepth!=0;
#if defined(DF_VALIDATE_BINDINGS)
    if(solverBatchDepth){
        bool mismatch=false;immediate->CSGetShaderResources(0,32,reads);immediate->CSGetUnorderedAccessViews(0,8,writes);
        for(auto p:reads)if(p){mismatch=true;p->Release();}for(auto p:writes)if(p){mismatch=true;p->Release();}
        if(mismatch)throw std::runtime_error("D3D11 solver hazard boundary retains a resource binding");
    }
#endif
}
void ContextD3D11::dispatch(const NvFlex::DispatchParams* params){bind(params);immediate->Dispatch(params->gridDim.x,params->gridDim.y,params->gridDim.z);unbindResources();}
void ContextD3D11::dispatchIndirect(const NvFlex::DispatchParams* params){bind(params);auto b=static_cast<Buffer*>(params->IndirectLaunchArgs);immediate->DispatchIndirect(b->handle(NvFlex::eDefaultBuffer),0);unbindResources();}
NvFlex::Fence* ContextD3D11::createFence(){auto out=std::make_unique<Fence>();D3D11_QUERY_DESC desc{D3D11_QUERY_EVENT,0};Check(device->CreateQuery(&desc,&out->query),"Create event fence");return out.release();}
void ContextD3D11::fenceSet(NvFlex::Fence* fence){immediate->End(static_cast<Fence*>(fence)->query.Get());}
void ContextD3D11::fenceWait(NvFlex::Fence* fence){BOOL complete=FALSE;immediate->Flush();HRESULT hr;while((hr=immediate->GetData(static_cast<Fence*>(fence)->query.Get(),&complete,sizeof(complete),0))==S_FALSE)SwitchToThread();Check(hr,"Wait event fence");}
void ContextD3D11::startFrame(){}
void ContextD3D11::flush(){immediate->Flush();}
void ContextD3D11::clearState(){immediate->ClearState();invalidateBindings();resourcesKnownClear=solverBatchDepth!=0;}
void ContextD3D11::computeWaitForGraphics(){if(renderContext){renderContext->End(renderCompletion.Get());while(renderContext->GetData(renderCompletion.Get(),nullptr,0,0)!=S_OK)SwitchToThread();}}
void ContextD3D11::pixBeginEvent(const wchar_t* text){ComPtr<ID3DUserDefinedAnnotation> annotation;if(SUCCEEDED(immediate.As(&annotation)))annotation->BeginEvent(text);}
void ContextD3D11::pixEndEvent(){ComPtr<ID3DUserDefinedAnnotation> annotation;if(SUCCEEDED(immediate.As(&annotation)))annotation->EndEvent();}
void ContextD3D11::eventMarker(const wchar_t* text){ComPtr<ID3DUserDefinedAnnotation> annotation;if(SUCCEEDED(immediate.As(&annotation)))annotation->SetMarker(text);}
void ContextD3D11::contextPush(){
    invalidateBindings();
    auto state=std::make_unique<SavedState>();immediate->CSGetConstantBuffers(0,8,state->constants);immediate->CSGetSamplers(0,8,state->samplers);immediate->CSGetShaderResources(0,16,state->reads);immediate->CSGetUnorderedAccessViews(0,8,state->writes);immediate->CSGetShader(&state->shader,nullptr,nullptr);
    immediate->RSSetState(nullptr);immediate->OMSetBlendState(nullptr,nullptr,~0u);immediate->OMSetDepthStencilState(nullptr,0);immediate->CSSetShader(nullptr,nullptr,0);
    immediate->VSSetShader(nullptr,nullptr,0);immediate->PSSetShader(nullptr,nullptr,0);immediate->GSSetShader(nullptr,nullptr,0);immediate->HSSetShader(nullptr,nullptr,0);immediate->DSSetShader(nullptr,nullptr,0);saved.push_back(std::move(state));
}
void ContextD3D11::contextPop(){invalidateBindings();if(saved.empty())throw std::runtime_error("Unbalanced contextPop");auto state=std::move(saved.back());saved.pop_back();immediate->CSSetConstantBuffers(0,8,state->constants);immediate->CSSetSamplers(0,8,state->samplers);immediate->CSSetShaderResources(0,16,state->reads);immediate->CSSetUnorderedAccessViews(0,8,state->writes,nullptr);immediate->CSSetShader(state->shader,nullptr,0);}
#if ENABLE_AFTERMATH_SUPPORT
int ContextD3D11::setEventMarkerAftermath(void* marker,unsigned size){return int(GFSDK_Aftermath_DX11_SetEventMarker(immediate.Get(),marker,size));}
int ContextD3D11::getDataAftermath(GFSDK_Aftermath_ContextData* data,GFSDK_Aftermath_Status* status){auto context=immediate.Get();return int(GFSDK_Aftermath_DX11_GetData(1,&context,data,status));}
#endif
class QueryTimers final : public NvFlex::TimerPool {
    struct Pair {ComPtr<ID3D11Query> disjoint,begin,end;unsigned state=0;};
    ContextD3D11* context;std::vector<Pair> queries;
public:
    explicit QueryTimers(ContextD3D11* c):context(c){reserve(200);}
    int begin() override{
        int index=-1;
        if(m_usedElemCount<m_timerPoolSize){
            index=int(m_usedElemCount++);auto& q=queries[index];
            if(q.state==0){context->immediate->Begin(q.disjoint.Get());context->immediate->End(q.begin.Get());q.state=1;}
        }
        ++m_requestedElemCount;return index;
    }
    void end(int index) override{
        if(index!=-1){auto& q=queries.at(index);if(q.state==1){context->immediate->End(q.end.Get());context->immediate->End(q.disjoint.Get());q.state=2;}}
    }
    void resolve() override{}
    void sync() override{reserve(m_requestedElemCount);m_requestedElemCount=0;}
    void clear() override{m_usedElemCount=0;}
    float get(int index,unsigned long long* b=nullptr,unsigned long long* e=nullptr,unsigned long long* f=nullptr) override{
        if(index==-1)return 0.0f;
        auto& q=queries.at(index);D3D11_QUERY_DATA_TIMESTAMP_DISJOINT info{};UINT64 first=0,last=0;
        if(context->immediate->GetData(q.disjoint.Get(),nullptr,0,0)==S_OK
            &&context->immediate->GetData(q.disjoint.Get(),&info,sizeof(info),0)==S_OK&&!info.Disjoint
            &&context->immediate->GetData(q.begin.Get(),&first,sizeof(first),0)==S_OK
            &&context->immediate->GetData(q.end.Get(),&last,sizeof(last),0)==S_OK){
            if(b)*b=first;if(e)*e=last;if(f)*f=info.Frequency;q.state=0;
            return (float(last-first)/float(info.Frequency))*1000.0f;
        }
        return 1.0f; // Exact reference sentinel while results are unavailable.
    }
    void reserve(size_t count) override{
        while(queries.size()<count){Pair q;D3D11_QUERY_DESC d{D3D11_QUERY_TIMESTAMP_DISJOINT,0};Check(context->device->CreateQuery(&d,&q.disjoint),"Create disjoint query");d.Query=D3D11_QUERY_TIMESTAMP;
            Check(context->device->CreateQuery(&d,&q.begin),"Create begin timestamp");Check(context->device->CreateQuery(&d,&q.end),"Create end timestamp");queries.push_back(std::move(q));}
        m_timerPoolSize=queries.size();
    }
};
NvFlex::TimerPool* ContextD3D11::createTimerPool(){return new QueryTimers(this);}
}
