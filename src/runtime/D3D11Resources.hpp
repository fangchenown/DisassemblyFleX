#pragma once
#include "D3D11Context.hpp"
namespace df {
struct ReadView final : NvFlex::Resource {
    NvFlexObject* owner=nullptr;
    ComPtr<ID3D11ShaderResourceView> view;
    NvFlexUint addRef() override{return owner->addRef();}
    NvFlexUint release() override{return owner->release();}
};
struct WriteView final : NvFlex::ResourceRW {
    NvFlexObject* owner=nullptr;ReadView* read=nullptr;
    ComPtr<ID3D11UnorderedAccessView> view;
    NvFlexUint addRef() override{return owner->addRef();}
    NvFlexUint release() override{return owner->release();}
    NvFlex::Resource* getResource() override{return read;}
};
#define DF_OBJECT_REFCOUNT \
    std::atomic_uint refs{1}; \
    NvFlexUint addRef() override{return ++refs;} \
    NvFlexUint release() override{auto n=--refs;if(!n)delete this;return n;}
struct Buffer final : NvFlex::Buffer {
    DF_OBJECT_REFCOUNT
    ContextD3D11* context=nullptr;
    ComPtr<ID3D11Buffer> gpu,stage,uploadBuffer,graphicsBuffer;
    ReadView read;WriteView write;
    bool mapped=false;bool mappedGpu=false;
    Buffer(ContextD3D11*,const NvFlex::BufferDesc&,ID3D11Buffer* external=nullptr);
    NvFlex::Resource* getResource(NvFlex::BufferResourceTypes=NvFlex::eResource) override;
    NvFlex::ResourceRW* getResourceRW() override{return &write;}
    void makeViews(NvFlexFormat);
    ID3D11Buffer* handle(NvFlex::BufferResourceTypes);
    void ensureStage();
};
struct ConstantBuffer final : NvFlex::ConstantBuffer {
    DF_OBJECT_REFCOUNT
    ComPtr<ID3D11Buffer> buffer;
};
struct Texture final : NvFlex::Texture3D {
    DF_OBJECT_REFCOUNT
    ComPtr<ID3D11Texture3D> gpu,stage;
    ReadView read;WriteView write;bool uploadMapped=false;
    NvFlex::Resource* getResource() override{return &read;}
    NvFlex::ResourceRW* getResourceRW() override{return &write;}
};
struct Shader final : NvFlex::ComputeShader {
    DF_OBJECT_REFCOUNT
    ComPtr<ID3D11ComputeShader> shader;
};
struct Fence final : NvFlex::Fence {
    DF_OBJECT_REFCOUNT
    ComPtr<ID3D11Query> query;
};
#undef DF_OBJECT_REFCOUNT
}
