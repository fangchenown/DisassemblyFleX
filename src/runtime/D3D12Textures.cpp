#include "D3D12Resources.hpp"
#include <cstring>
namespace df {
NvFlex::Texture3D* ContextD3D12::createTexture3D(const NvFlex::Texture3DDesc* desc){
    auto out=std::make_unique<Texture12>();out->m_desc=*desc;out->read.owner=out.get();out->write.owner=out.get();out->write.read=&out->read;auto& s=*state;
    out->gpu=std::make_shared<Resource12>();out->gpu->state=D3D12_RESOURCE_STATE_COPY_DEST;
    D3D12_RESOURCE_DESC d{};d.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE3D;d.Width=desc->dim.x;d.Height=desc->dim.y;d.DepthOrArraySize=UINT16(desc->dim.z);d.MipLevels=1;d.Format=NvFlex::convertToDXGI(desc->format);d.SampleDesc.Count=1;d.Flags=D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
    D3D12_HEAP_PROPERTIES heap{};heap.Type=D3D12_HEAP_TYPE_DEFAULT;heap.CreationNodeMask=heap.VisibleNodeMask=1;
    Check(s.device->CreateCommittedResource(&heap,D3D12_HEAP_FLAG_NONE,&d,out->gpu->state,nullptr,IID_PPV_ARGS(&out->gpu->native)),"Create D3D12 texture");
    s.device->GetCopyableFootprints(&d,0,1,0,&out->footprint,nullptr,nullptr,&out->uploadBytes);
    D3D12_SHADER_RESOURCE_VIEW_DESC srv{};srv.Format=d.Format;srv.ViewDimension=D3D12_SRV_DIMENSION_TEXTURE3D;srv.Shader4ComponentMapping=D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;srv.Texture3D.MipLevels=1;out->read.resource=out->gpu;out->read.descriptor=s.cpu();s.device->CreateShaderResourceView(out->gpu->native.Get(),&srv,out->read.descriptor);
    D3D12_UNORDERED_ACCESS_VIEW_DESC uav{};uav.Format=d.Format;uav.ViewDimension=D3D12_UAV_DIMENSION_TEXTURE3D;uav.Texture3D.WSize=desc->dim.z;out->write.resource=out->gpu;out->write.descriptor=s.cpu();s.device->CreateUnorderedAccessView(out->gpu->native.Get(),nullptr,&uav,out->write.descriptor);
    if(desc->data){auto p=map(out.get());unsigned row=desc->dim.x*NvFlex::getFormatSizeInBytes(desc->format);
        for(unsigned z=0;z<desc->dim.z;++z)for(unsigned y=0;y<desc->dim.y;++y)std::memcpy(static_cast<char*>(p.data)+z*p.depthPitch+y*p.rowPitch,static_cast<const char*>(desc->data)+(size_t(z)*desc->dim.y+y)*row,row);
        unmap(out.get());
    }return out.release();
}
NvFlex::MappedData ContextD3D12::map(NvFlex::Texture3D* input){auto t=static_cast<Texture12*>(input);t->upload=state->buffer(t->uploadBytes,D3D12_HEAP_TYPE_UPLOAD);void* data=nullptr;D3D12_RANGE empty{};Check(t->upload->native->Map(0,&empty,&data),"Map D3D12 texture upload");return {data,t->footprint.Footprint.RowPitch,t->footprint.Footprint.RowPitch*t->m_desc.dim.y};}
void ContextD3D12::unmap(NvFlex::Texture3D* input){auto t=static_cast<Texture12*>(input);t->upload->native->Unmap(0,nullptr);state->transition(t->gpu,D3D12_RESOURCE_STATE_COPY_DEST);state->keep(t->upload);D3D12_TEXTURE_COPY_LOCATION source{},target{};source.pResource=t->upload->native.Get();source.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;source.PlacedFootprint=t->footprint;target.pResource=t->gpu->native.Get();target.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;state->commands->CopyTextureRegion(&target,0,0,0,&source,nullptr);state->dirty=true;}
void ContextD3D12::download(NvFlex::Texture3D* input){auto t=static_cast<Texture12*>(input);if(!t->download)t->download=state->buffer(t->uploadBytes,D3D12_HEAP_TYPE_READBACK);state->transition(t->gpu,D3D12_RESOURCE_STATE_COPY_SOURCE);state->keep(t->download);D3D12_TEXTURE_COPY_LOCATION source{},target{};source.pResource=t->gpu->native.Get();source.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;target.pResource=t->download->native.Get();target.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;target.PlacedFootprint=t->footprint;state->commands->CopyTextureRegion(&target,0,0,0,&source,nullptr);state->dirty=true;}
NvFlex::MappedData ContextD3D12::mapDownload(NvFlex::Texture3D* input){if(state->dirty)flush();auto t=static_cast<Texture12*>(input);void* data=nullptr;D3D12_RANGE range{0,size_t(t->uploadBytes)};Check(t->download->native->Map(0,&range,&data),"Map D3D12 texture readback");return {data,t->footprint.Footprint.RowPitch,t->footprint.Footprint.RowPitch*t->m_desc.dim.y};}
void ContextD3D12::unmapDownload(NvFlex::Texture3D* input){auto t=static_cast<Texture12*>(input);D3D12_RANGE empty{};t->download->native->Unmap(0,&empty);}
void ContextD3D12::copy(NvFlex::Texture3D* dst,NvFlex::Texture3D* src){auto a=static_cast<Texture12*>(dst),b=static_cast<Texture12*>(src);state->transition(a->gpu,D3D12_RESOURCE_STATE_COPY_DEST);state->transition(b->gpu,D3D12_RESOURCE_STATE_COPY_SOURCE);state->commands->CopyResource(a->gpu->native.Get(),b->gpu->native.Get());state->dirty=true;}
}
