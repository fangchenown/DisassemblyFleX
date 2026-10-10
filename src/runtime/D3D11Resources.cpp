#include "D3D11Resources.hpp"
#include "dx/context/Format.h"
#include <algorithm>
#include <stdexcept>
#include <string>
#include "NvApiInterop.hpp"

namespace NvFlex {
static const DXGI_FORMAT formats[]={DXGI_FORMAT_UNKNOWN,DXGI_FORMAT_R32_TYPELESS,
 DXGI_FORMAT_R32_FLOAT,DXGI_FORMAT_R32G32_FLOAT,DXGI_FORMAT_R32G32B32A32_FLOAT,
 DXGI_FORMAT_R16_FLOAT,DXGI_FORMAT_R16G16_FLOAT,DXGI_FORMAT_R16G16B16A16_FLOAT,
 DXGI_FORMAT_R32_UINT,DXGI_FORMAT_R32G32_UINT,DXGI_FORMAT_R32G32B32A32_UINT,
 DXGI_FORMAT_R8_UNORM,DXGI_FORMAT_R8G8_UNORM,DXGI_FORMAT_R8G8B8A8_UNORM,
 DXGI_FORMAT_R16_UNORM,DXGI_FORMAT_R16G16_UNORM,DXGI_FORMAT_R16G16B16A16_UNORM,
 DXGI_FORMAT_D32_FLOAT,DXGI_FORMAT_D24_UNORM_S8_UINT,
 DXGI_FORMAT_R8_SNORM,DXGI_FORMAT_R8G8_SNORM,DXGI_FORMAT_R8G8B8A8_SNORM};
DXGI_FORMAT convertToDXGI(NvFlexFormat f){return unsigned(f)<unsigned(eNvFlexFormat_max)?formats[f]:DXGI_FORMAT_UNKNOWN;}
NvFlexFormat convertToNvFlex(DXGI_FORMAT f){for(unsigned i=0;i<unsigned(eNvFlexFormat_max);++i)if(formats[i]==f)return NvFlexFormat(i);return eNvFlexFormat_unknown;}
NvFlexUint getFormatSizeInBytes(NvFlexFormat f){static const unsigned sizes[]={0,4,4,8,16,2,4,8,4,8,16,1,2,4,2,4,8,4,4,1,2,4};return unsigned(f)<unsigned(eNvFlexFormat_max)?sizes[f]:0;}
void* Allocable::operator new(size_t n){return ::operator new(n);}
void* Allocable::operator new[](size_t n){return ::operator new[](n);}
void Allocable::operator delete(void* p){::operator delete(p);}
void Allocable::operator delete[](void* p){::operator delete[](p);}
NvFlexUint Object::addRefInternal(){return ++m_refCount;}
NvFlexUint Object::releaseInternal(){auto n=--m_refCount;if(!n)delete this;return n;}
Object::~Object()=default;
Context::Context():mEnableTimers(false){}
Context::~Context()=default;
}
namespace df {
void Check(HRESULT hr,const char* name){if(FAILED(hr))throw std::runtime_error(std::string(name)+" HRESULT="+std::to_string(static_cast<unsigned>(hr)));}
Buffer::Buffer(ContextD3D11* c,const NvFlex::BufferDesc& desc,ID3D11Buffer* external):context(c){
    m_desc=desc;read.owner=this;write.owner=this;write.read=&read;
    if(external){ComPtr<IDXGIResource> shared;Check(external->QueryInterface(IID_PPV_ARGS(&shared)),"Get shared resource interface");HANDLE handle=nullptr;Check(shared->GetSharedHandle(&handle),"Get shared buffer handle");Check(c->device->OpenSharedResource(handle,IID_PPV_ARGS(&gpu)),"Open shared buffer");D3D11_BUFFER_DESC actual{};gpu->GetDesc(&actual);
        m_desc.dim=actual.StructureByteStride?actual.ByteWidth/actual.StructureByteStride:actual.ByteWidth;
        m_desc.stride=actual.StructureByteStride?actual.StructureByteStride:1;
        m_desc.bufferType=NvFlex::eShared|NvFlex::eBuffer;
        if(actual.MiscFlags&D3D11_RESOURCE_MISC_BUFFER_STRUCTURED)m_desc.bufferType|=NvFlex::eStructured;
        if(actual.MiscFlags&D3D11_RESOURCE_MISC_BUFFER_ALLOW_RAW_VIEWS)m_desc.bufferType|=NvFlex::eRaw;
        if(actual.BindFlags&(D3D11_BIND_UNORDERED_ACCESS|D3D11_BIND_SHADER_RESOURCE))m_desc.bufferType|=NvFlex::eUAV_SRV;
        return;
    }
    unsigned bytes=desc.dim*desc.stride;
    if(!bytes)return;
    if(desc.bufferType&NvFlex::eBuffer){
        D3D11_BUFFER_DESC bd{};bd.ByteWidth=bytes;bd.Usage=D3D11_USAGE_DEFAULT;
        bd.BindFlags=D3D11_BIND_SHADER_RESOURCE|D3D11_BIND_UNORDERED_ACCESS;
        if(desc.bufferType&NvFlex::eStructured){bd.MiscFlags|=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;bd.StructureByteStride=desc.stride;}
        if(desc.bufferType&NvFlex::eRaw){bd.MiscFlags|=D3D11_RESOURCE_MISC_BUFFER_ALLOW_RAW_VIEWS;bd.StructureByteStride=0;}
        if(desc.bufferType&NvFlex::eIndirect)bd.MiscFlags|=D3D11_RESOURCE_MISC_DRAWINDIRECT_ARGS;
        D3D11_SUBRESOURCE_DATA initial{desc.data,0,0};
        if(c->renderDevice){bd.MiscFlags|=D3D11_RESOURCE_MISC_SHARED;Check(c->renderDevice->CreateBuffer(&bd,desc.data?&initial:nullptr,&graphicsBuffer),"Create GPU buffer on render device");ID3D11Buffer* opened=nullptr;NvCheck(NvInterop(0x69c2d61e,c->device.Get(),graphicsBuffer.Get(),&opened),"Open resource on compute device");gpu.Attach(opened);}
        else Check(c->device->CreateBuffer(&bd,desc.data?&initial:nullptr,&gpu),"Create GPU buffer");
    }
    if(desc.bufferType&NvFlex::eStage){ensureStage();if(desc.data){D3D11_MAPPED_SUBRESOURCE mapped{};Check(c->immediate->Map(stage.Get(),0,D3D11_MAP_WRITE,0,&mapped),"Initialize staging buffer");std::memcpy(mapped.pData,desc.data,bytes);c->immediate->Unmap(stage.Get(),0);}}
    if(desc.bufferType&NvFlex::eDynamic){
        D3D11_BUFFER_DESC bd{};bd.ByteWidth=bytes;bd.Usage=D3D11_USAGE_DYNAMIC;bd.BindFlags=D3D11_BIND_SHADER_RESOURCE;bd.CPUAccessFlags=D3D11_CPU_ACCESS_WRITE;
        if(desc.bufferType&NvFlex::eRaw)bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_ALLOW_RAW_VIEWS;
        else if(desc.bufferType&NvFlex::eIndirect)bd.MiscFlags=D3D11_RESOURCE_MISC_DRAWINDIRECT_ARGS;
        else if(desc.bufferType&NvFlex::eStructured){bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;bd.StructureByteStride=desc.stride;}
        D3D11_SUBRESOURCE_DATA initial{desc.data,0,0};Check(c->device->CreateBuffer(&bd,desc.data?&initial:nullptr,&uploadBuffer),"Create dynamic upload buffer");
    }
    if(desc.bufferType&NvFlex::eUAV_SRV)makeViews(desc.format);
}
void Buffer::ensureStage(){
    if(stage||!m_desc.dim||!m_desc.stride)return;
    D3D11_BUFFER_DESC bd{};bd.ByteWidth=m_desc.dim*m_desc.stride;bd.Usage=D3D11_USAGE_STAGING;bd.CPUAccessFlags=D3D11_CPU_ACCESS_READ|D3D11_CPU_ACCESS_WRITE;
    if((m_desc.bufferType&NvFlex::eStructured)&&!(m_desc.bufferType&NvFlex::eRaw)){bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;bd.StructureByteStride=m_desc.stride;}
    Check(context->device->CreateBuffer(&bd,nullptr,&stage),"Create staging buffer");
}
void Buffer::makeViews(NvFlexFormat format){
    if(!gpu)return;
    D3D11_BUFFER_DESC desc{};gpu->GetDesc(&desc);
    bool raw=(desc.MiscFlags&D3D11_RESOURCE_MISC_BUFFER_ALLOW_RAW_VIEWS)!=0&&(format==eNvFlexFormat_unknown||format==eNvFlexFormat_r32_typeless);
    bool structured=(desc.MiscFlags&D3D11_RESOURCE_MISC_BUFFER_STRUCTURED)!=0&&format==eNvFlexFormat_unknown;
    DXGI_FORMAT viewFormat=raw?DXGI_FORMAT_R32_TYPELESS:(structured?DXGI_FORMAT_UNKNOWN:NvFlex::convertToDXGI(format));
    unsigned stride=raw?4u:(structured?desc.StructureByteStride:NvFlex::getFormatSizeInBytes(format));
    if(!stride)stride=m_desc.stride;
    if(desc.BindFlags&D3D11_BIND_SHADER_RESOURCE){
        D3D11_SHADER_RESOURCE_VIEW_DESC srv{};srv.Format=viewFormat;srv.ViewDimension=D3D11_SRV_DIMENSION_BUFFEREX;
        srv.BufferEx.NumElements=desc.ByteWidth/stride;srv.BufferEx.Flags=raw?D3D11_BUFFEREX_SRV_FLAG_RAW:0;
        Check(context->device->CreateShaderResourceView(gpu.Get(),&srv,read.view.ReleaseAndGetAddressOf()),"Create buffer SRV");
    }
    if(desc.BindFlags&D3D11_BIND_UNORDERED_ACCESS){
        D3D11_UNORDERED_ACCESS_VIEW_DESC uav{};uav.Format=viewFormat;uav.ViewDimension=D3D11_UAV_DIMENSION_BUFFER;
        uav.Buffer.NumElements=desc.ByteWidth/stride;uav.Buffer.Flags=raw?D3D11_BUFFER_UAV_FLAG_RAW:0;
        Check(context->device->CreateUnorderedAccessView(gpu.Get(),&uav,write.view.ReleaseAndGetAddressOf()),"Create buffer UAV");
    }
}
ID3D11Buffer* Buffer::handle(NvFlex::BufferResourceTypes type){
    if(type==NvFlex::eUploadBuffer)return uploadBuffer.Get();
    if(type==NvFlex::eDownloadBuffer){ensureStage();return stage.Get();}
    return gpu?gpu.Get():stage.Get();
}
NvFlex::Resource* Buffer::getResource(NvFlex::BufferResourceTypes type){
    if(type==NvFlex::eResource)return &read;
    return reinterpret_cast<NvFlex::Resource*>(handle(type));
}
NvFlex::ConstantBuffer* ContextD3D11::createConstantBuffer(const NvFlex::ConstantBufferDesc* desc){
    auto out=std::make_unique<ConstantBuffer>();out->m_desc=*desc;D3D11_BUFFER_DESC bd{};
    bd.ByteWidth=(desc->dim*desc->stride+15u)&~15u;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
    bd.Usage=desc->uploadAccess?D3D11_USAGE_DYNAMIC:D3D11_USAGE_DEFAULT;bd.CPUAccessFlags=desc->uploadAccess?D3D11_CPU_ACCESS_WRITE:0;
    Check(device->CreateBuffer(&bd,nullptr,&out->buffer),"Create constant buffer");return out.release();
}
void* ContextD3D11::map(NvFlex::ConstantBuffer* buffer){D3D11_MAPPED_SUBRESOURCE mapped{};Check(immediate->Map(static_cast<ConstantBuffer*>(buffer)->buffer.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"Map constant buffer");return mapped.pData;}
void ContextD3D11::unmap(NvFlex::ConstantBuffer* buffer){immediate->Unmap(static_cast<ConstantBuffer*>(buffer)->buffer.Get(),0);}
void ContextD3D11::copy(NvFlex::ConstantBuffer* dst,NvFlex::Buffer* src){immediate->CopyResource(static_cast<ConstantBuffer*>(dst)->buffer.Get(),static_cast<Buffer*>(src)->handle(NvFlex::eDefaultBuffer));}
NvFlex::Buffer* ContextD3D11::createBuffer(const NvFlex::BufferDesc* desc,void* external){return new Buffer(this,*desc,(desc->bufferType==NvFlex::eShared)?static_cast<ID3D11Buffer*>(external):nullptr);}
NvFlex::Buffer* ContextD3D11::createBufferView(NvFlex::Buffer* original,const NvFlex::BufferViewDesc* desc){
    auto source=static_cast<Buffer*>(original);auto view=std::make_unique<Buffer>(this,NvFlex::BufferDesc{});
    view->gpu=source->gpu;view->stage=source->stage;view->uploadBuffer=source->uploadBuffer;view->m_desc=source->m_desc;
    unsigned size=source->m_desc.dim*source->m_desc.stride;unsigned stride=NvFlex::getFormatSizeInBytes(desc->format);
    view->m_desc.format=desc->format;if(stride)view->m_desc.dim=size/stride;view->makeViews(desc->format);return view.release();
}
void* ContextD3D11::map(NvFlex::Buffer* input,NvFlex::MapType type,bool wait){
    auto buffer=static_cast<Buffer*>(input);buffer->mappedGpu=type==NvFlex::eMapWriteDiscard;
    auto native=buffer->mappedGpu?buffer->uploadBuffer.Get():buffer->stage.Get();
    static const D3D11_MAP modes[]={D3D11_MAP_READ,D3D11_MAP_WRITE,D3D11_MAP_READ_WRITE,D3D11_MAP_WRITE_DISCARD};
    D3D11_MAPPED_SUBRESOURCE mapped{};HRESULT hr=immediate->Map(native,0,modes[type],wait?0:D3D11_MAP_FLAG_DO_NOT_WAIT,&mapped);
    if(hr!=S_OK)return nullptr;buffer->mapped=true;return mapped.pData;
}
void ContextD3D11::unmap(NvFlex::Buffer* input){auto b=static_cast<Buffer*>(input);if(b->mapped){immediate->Unmap(b->mappedGpu?b->uploadBuffer.Get():b->stage.Get(),0);b->mapped=false;}}
static void copyBytes(ID3D11DeviceContext* context,ID3D11Buffer* dst,unsigned dstOffset,ID3D11Buffer* src,unsigned srcOffset,unsigned bytes){
    if(!bytes)return;D3D11_BOX box{srcOffset,0,0,srcOffset+bytes,1,1};context->CopySubresourceRegion(dst,0,dstOffset,0,0,src,0,&box);
}
void ContextD3D11::upload(NvFlex::Buffer* b){upload(b,0,b->m_desc.dim*b->m_desc.stride);}
void ContextD3D11::upload(NvFlex::Buffer* input,NvFlexUint offset,NvFlexUint bytes){auto b=static_cast<Buffer*>(input);copyBytes(immediate.Get(),b->gpu.Get(),offset,b->uploadBuffer?b->uploadBuffer.Get():b->handle(NvFlex::eDownloadBuffer),offset,bytes);}
void ContextD3D11::download(NvFlex::Buffer* b){download(b,0,b->m_desc.dim*b->m_desc.stride);}
void ContextD3D11::download(NvFlex::Buffer* input,NvFlexUint offset,NvFlexUint bytes){auto b=static_cast<Buffer*>(input);copyBytes(immediate.Get(),b->handle(NvFlex::eDownloadBuffer),offset,b->gpu.Get(),offset,bytes);}
void ContextD3D11::copy(NvFlex::Buffer* dst,unsigned dstOffset,NvFlex::Buffer* src,unsigned srcOffset,unsigned bytes){copyBytes(immediate.Get(),static_cast<Buffer*>(dst)->handle(NvFlex::eDefaultBuffer),dstOffset,static_cast<Buffer*>(src)->handle(NvFlex::eDefaultBuffer),srcOffset,bytes);}
void ContextD3D11::copyToNative(void* dst,unsigned dstOffset,NvFlex::Buffer* src,unsigned srcOffset,unsigned bytes){auto source=static_cast<Buffer*>(src);
    if(!source->graphicsBuffer){copyBytes(immediate.Get(),static_cast<ID3D11Buffer*>(dst),dstOffset,source->handle(NvFlex::eDefaultBuffer),srcOffset,bytes);return;}
    NvCheck(NvInterop(0x053f62d6,immediate.Get(),computeFinished,computeCount),"Signal compute completion");NvCheck(NvInterop(0x05f17e9e,renderContext.Get(),computeFinished,computeCount++),"Wait compute completion");
    copyBytes(renderContext.Get(),static_cast<ID3D11Buffer*>(dst),dstOffset,source->graphicsBuffer.Get(),srcOffset,bytes);
    NvCheck(NvInterop(0x053f62d6,renderContext.Get(),graphicsFinished,graphicsCount),"Signal graphics completion");NvCheck(NvInterop(0x05f17e9e,immediate.Get(),graphicsFinished,graphicsCount++),"Wait graphics completion");}
void ContextD3D11::copyToDevice(NvFlex::Buffer* dst,unsigned dstOffset,NvFlex::Buffer* src,unsigned srcOffset,unsigned bytes,NvFlex::BufferResourceTypes type){auto input=type==NvFlex::eNativeBuffer?reinterpret_cast<ID3D11Buffer*>(src):static_cast<Buffer*>(src)->handle(type);copyBytes(immediate.Get(),static_cast<Buffer*>(dst)->handle(NvFlex::eDefaultBuffer),dstOffset,input,srcOffset,bytes);}
void ContextD3D11::copyToHost(NvFlex::Buffer* dst,unsigned dstOffset,NvFlex::Buffer* src,unsigned srcOffset,unsigned bytes){copyBytes(immediate.Get(),static_cast<Buffer*>(dst)->handle(NvFlex::eDownloadBuffer),dstOffset,static_cast<Buffer*>(src)->handle(NvFlex::eDefaultBuffer),srcOffset,bytes);}
void ContextD3D11::clearUnorderedAccessViewUint(NvFlex::Buffer* b,const unsigned* values){immediate->ClearUnorderedAccessViewUint(static_cast<Buffer*>(b)->write.view.Get(),values);}
void ContextD3D11::clearUnorderedAccessViewFloat(NvFlex::Buffer* b,const float* values){immediate->ClearUnorderedAccessViewFloat(static_cast<Buffer*>(b)->write.view.Get(),values);}
void ContextD3D11::copyResourceState(NvFlex::Buffer*,NvFlex::Buffer*){ /* D3D11 has implicit resource transitions. */ }
}
