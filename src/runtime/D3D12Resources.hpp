#pragma once
#include "D3D12Context.hpp"
#include "dx/context/Format.h"
#include <array>
#include <unordered_set>
#include <vector>
namespace df {
struct Resource12 {
    ComPtr<ID3D12Resource> native;
    D3D12_RESOURCE_STATES state=D3D12_RESOURCE_STATE_COMMON;
    bool fixedState=false;
};
using ResourcePtr12=std::shared_ptr<Resource12>;
// A resource can be referenced by command lists from more than one external
// Context/fence. Fence values are comparable only within the same fence.
struct PendingUses12 {
    struct Use {ComPtr<ID3D12Fence> fence;UINT64 value;};
    std::vector<Use> uses;
    void record(ID3D12Fence* fence,UINT64 value);
    bool complete(ID3D12Fence* knownFence=nullptr,UINT64 knownValue=0) const;
};
struct Read12 final : NvFlex::Resource {
    NvFlexObject* owner=nullptr;ResourcePtr12 resource;D3D12_CPU_DESCRIPTOR_HANDLE descriptor{};
    NvFlexUint addRef() override{return owner->addRef();}NvFlexUint release() override{return owner->release();}
};
struct Write12 final : NvFlex::ResourceRW {
    NvFlexObject* owner=nullptr;Read12* read=nullptr;ResourcePtr12 resource;D3D12_CPU_DESCRIPTOR_HANDLE descriptor{};
    NvFlexUint addRef() override{return owner->addRef();}NvFlexUint release() override{return owner->release();}NvFlex::Resource* getResource() override{return read;}
};
#define DF_REF12 std::atomic_uint refs{1};NvFlexUint addRef() override{return ++refs;}NvFlexUint release() override{auto n=--refs;if(!n)delete this;return n;}
struct Buffer12 final : NvFlex::Buffer {
    DF_REF12
    ContextD3D12* context;ResourcePtr12 gpu,stage;
    Read12 read;Write12 write;unsigned long long downloadFence=0;
    Buffer12(ContextD3D12*,const NvFlex::BufferDesc&,ID3D12Resource* external=nullptr);
    void views(NvFlexFormat);
    NvFlex::Resource* getResource(NvFlex::BufferResourceTypes=NvFlex::eResource) override;
    NvFlex::ResourceRW* getResourceRW() override{return &write;}
};
struct Constant12 final : NvFlex::ConstantBuffer {
    DF_REF12
    struct Version {
        ResourcePtr12 resource;
        void* mapped=nullptr;
        ID3D12Device* device=nullptr; // The resource owns the native device.
        PendingUses12 pending;
    };
    ResourcePtr12 current;
    std::vector<Version> versions;
    size_t currentVersion=size_t(-1);
    void recordUse(ID3D12Fence*,UINT64);
};
struct Texture12 final : NvFlex::Texture3D {
    DF_REF12
    ResourcePtr12 gpu,upload,download;
    Read12 read;Write12 write;D3D12_PLACED_SUBRESOURCE_FOOTPRINT footprint{};UINT64 uploadBytes=0;
    NvFlex::Resource* getResource() override{return &read;}NvFlex::ResourceRW* getResourceRW() override{return &write;}
};
struct Shader12 final : NvFlex::ComputeShader {DF_REF12 ComPtr<ID3D12PipelineState> pipeline;};
struct Fence12 final : NvFlex::Fence {
    DF_REF12
    ComPtr<ID3D12Fence> fence;HANDLE event=nullptr;unsigned long long value=1;
    ~Fence12(){if(event)CloseHandle(event);}
};
#undef DF_REF12
struct Context12State {
    ComPtr<ID3D12Device> device;ComPtr<ID3D12CommandQueue> queue,graphics;
    ComPtr<ID3D12CommandAllocator> allocator;ComPtr<ID3D12GraphicsCommandList> commands;
    ComPtr<ID3D12RootSignature> root;ComPtr<ID3D12CommandSignature> indirect;
    ComPtr<ID3D12Fence> completion,graphicsCompletion;HANDLE event=nullptr;
    UINT64 nextFence=2,completed=1,graphicsValue=0;
    bool dirty=false;unsigned descriptorSize=0,cpuUsed=4096,gpuUsed=4096;
    struct GpuHeap {
        ComPtr<ID3D12DescriptorHeap> native;
        ID3D12Device* device=nullptr; // The heap owns the native device.
        PendingUses12 pending;
    };
    std::vector<ComPtr<ID3D12DescriptorHeap>> cpuHeaps;
    std::vector<GpuHeap> gpuHeaps;
    size_t gpuHeapIndex=size_t(-1);
    D3D12_CPU_DESCRIPTOR_HANDLE nullRead{},nullWrite{};
    ResourcePtr12 rootConstant,secondConstant;
    std::vector<ComPtr<IUnknown>> retained;std::unordered_set<IUnknown*> retainedSet;
    struct RetiredBatch {PendingUses12 pending;std::vector<ComPtr<IUnknown>> resources;};
    std::vector<RetiredBatch> retired;
    ~Context12State(){if(event)CloseHandle(event);}
    void keep(IUnknown* p){if(p&&retainedSet.insert(p).second)retained.emplace_back(p);}
    void keep(const ResourcePtr12& p){if(p)keep(p->native.Get());}
    void retireRecording();
    void collectRetired();
    ResourcePtr12 buffer(UINT64 bytes,D3D12_HEAP_TYPE heap,bool staging=false,bool uav=false);
    D3D12_CPU_DESCRIPTOR_HANDLE cpu();
    std::pair<D3D12_CPU_DESCRIPTOR_HANDLE,D3D12_GPU_DESCRIPTOR_HANDLE> gpu(unsigned count);
    bool prepareTransition(const ResourcePtr12&,D3D12_RESOURCE_STATES,bool,D3D12_RESOURCE_BARRIER&);
    void transition(const ResourcePtr12&,D3D12_RESOURCE_STATES,bool uavBarrier=false);
    void copy(const ResourcePtr12& dst,UINT64 dstOffset,const ResourcePtr12& src,UINT64 srcOffset,UINT64 bytes);
    void bind(const NvFlex::DispatchParams*);
};
}
