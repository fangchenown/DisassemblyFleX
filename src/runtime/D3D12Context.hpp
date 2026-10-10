#pragma once
#include "D3D11Context.hpp"
#include <d3d12.h>
namespace df {
struct Context12State;
class ContextD3D12 final : public NvFlex::Context {
public:
    ContextD3D12(ID3D12Device*,ID3D12CommandQueue*,ID3D12CommandQueue*);
    ~ContextD3D12() override;
    std::unique_ptr<Context12State> state;
    void updateContext(const NvFlexContextDesc*) override;
    NvFlex::ConstantBuffer* createConstantBuffer(const NvFlex::ConstantBufferDesc*) override;
    void* map(NvFlex::ConstantBuffer*) override;
    void unmap(NvFlex::ConstantBuffer*) override;
    void copy(NvFlex::ConstantBuffer*,NvFlex::Buffer*) override;
    NvFlex::Buffer* createBuffer(const NvFlex::BufferDesc*,void* = nullptr) override;
    NvFlex::Buffer* createBufferView(NvFlex::Buffer*,const NvFlex::BufferViewDesc*) override;
    void* map(NvFlex::Buffer*,NvFlex::MapType = NvFlex::eMapReadWrite,bool = true) override;
    void unmap(NvFlex::Buffer*) override;
    void upload(NvFlex::Buffer*) override;
    void upload(NvFlex::Buffer*,NvFlexUint,NvFlexUint) override;
    void download(NvFlex::Buffer*) override;
    void download(NvFlex::Buffer*,NvFlexUint,NvFlexUint) override;
    void copy(NvFlex::Buffer*,unsigned,NvFlex::Buffer*,NvFlexUint,NvFlexUint) override;
    void copyToNative(void*,unsigned,NvFlex::Buffer*,NvFlexUint,NvFlexUint) override;
    void copyToDevice(NvFlex::Buffer*,unsigned,NvFlex::Buffer*,NvFlexUint,NvFlexUint,NvFlex::BufferResourceTypes = NvFlex::eDownloadBuffer) override;
    void copyToHost(NvFlex::Buffer*,unsigned,NvFlex::Buffer*,NvFlexUint,NvFlexUint) override;
    void clearUnorderedAccessViewUint(NvFlex::Buffer*,const NvFlexUint*) override;
    void clearUnorderedAccessViewFloat(NvFlex::Buffer*,const NvFlexFloat*) override;
    void copyResourceState(NvFlex::Buffer*,NvFlex::Buffer*) override;
    NvFlex::Texture3D* createTexture3D(const NvFlex::Texture3DDesc*) override;
    NvFlex::MappedData map(NvFlex::Texture3D*) override;
    void unmap(NvFlex::Texture3D*) override;
    void download(NvFlex::Texture3D*) override;
    NvFlex::MappedData mapDownload(NvFlex::Texture3D*) override;
    void unmapDownload(NvFlex::Texture3D*) override;
    void copy(NvFlex::Texture3D*,NvFlex::Texture3D*) override;
    NvFlex::ComputeShader* createComputeShader(const NvFlex::ComputeShaderDesc*) override;
    void dispatch(const NvFlex::DispatchParams*) override;
    void dispatchIndirect(const NvFlex::DispatchParams*) override;
    NvFlex::TimerPool* createTimerPool() override;
    NvFlex::Fence* createFence() override;
    void fenceSet(NvFlex::Fence*) override;
    void fenceWait(NvFlex::Fence*) override;
    void startFrame() override;
    void flush() override;
    void clearState() override;
    void computeWaitForGraphics() override;
    void pixBeginEvent(const wchar_t*) override;
    void pixEndEvent() override;
    void eventMarker(const wchar_t*) override;
    void contextPush() override;
    void contextPop() override;
#if ENABLE_AFTERMATH_SUPPORT
    int setEventMarkerAftermath(void*,unsigned) override;
    int getDataAftermath(GFSDK_Aftermath_ContextData*,GFSDK_Aftermath_Status*) override;
#endif
};
class DeviceD3D12 final : public NvFlex::Device {
public:
    explicit DeviceD3D12(const NvFlexInitDesc&,NvFlexErrorCallback=nullptr);
    ~DeviceD3D12() override;
    NvFlexUint addRef() override{return ++refs;}
    NvFlexUint release() override{auto n=--refs;if(!n)delete this;return n;}
    NvFlex::Context* createContext() override;
    NvAPI_Status NvAPI_IsNvShaderExtnOpCodeSupported(NvU32,bool*) override;
    AGSReturnCode AGS_DriverExtensions_Init(AGSContext*,unsigned,unsigned*) override;
    void AGS_DeInit(AGSContext*) override;
    DXGI_ADAPTER_DESC1 getDXGIAdapter(void*,int&) override;
    void present() override;
    ComPtr<ID3D12Device> native;
    ComPtr<ID3D12CommandQueue> queue,graphics;
private:
    std::atomic_uint refs{1};
};
}
