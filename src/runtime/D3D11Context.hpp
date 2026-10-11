#pragma once
#include "NvFlex.h"
#include "dx/context/Device.h"
#include <wrl/client.h>
#include <memory>

namespace df {
using Microsoft::WRL::ComPtr;
class ContextD3D11 final : public NvFlex::Context {
public:
    ContextD3D11(ID3D11Device*,ID3D11DeviceContext*,ID3D11Device* renderDevice=nullptr,ID3D11DeviceContext* renderContext=nullptr);
    ~ContextD3D11() override;
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> immediate;
    ComPtr<ID3D11SamplerState> linearSampler;
    ComPtr<ID3D11Device> renderDevice;
    ComPtr<ID3D11DeviceContext> renderContext;
    ComPtr<ID3D11Query> renderCompletion,computeCompletion;
    void* computeFinished=nullptr;void* graphicsFinished=nullptr;
    unsigned long long computeCount=0,graphicsCount=0;
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
    // Internal, nested-safe submission scope. Public Context calls outside it
    // keep the original full binding policy. No COM object is cached/owned.
    void beginSolverBatch();
    void endSolverBatch();
#if ENABLE_AFTERMATH_SUPPORT
    int setEventMarkerAftermath(void*,unsigned) override;
    int getDataAftermath(GFSDK_Aftermath_ContextData*,GFSDK_Aftermath_Status*) override;
#endif
private:
    struct SavedState;
    std::vector<std::unique_ptr<SavedState>> saved;
    void bind(const NvFlex::DispatchParams*);
    void unbindResources();
    unsigned solverBatchDepth=0,lastReadSpan=32;
    bool resourcesKnownClear=false,samplerKnown=false,constantKnown[2]{};
    ID3D11Buffer* boundConstants[2]{};
    void invalidateBindings();
    void invalidateConstant(ID3D11Buffer*);
};
class DeviceD3D11 final : public NvFlex::Device {
public:
    explicit DeviceD3D11(const NvFlexInitDesc&,NvFlexErrorCallback=nullptr);
    ~DeviceD3D11() override;
    NvFlexUint addRef() override;
    NvFlexUint release() override;
    NvFlex::Context* createContext() override;
    NvAPI_Status NvAPI_IsNvShaderExtnOpCodeSupported(NvU32,bool*) override;
    AGSReturnCode AGS_DriverExtensions_Init(AGSContext*,unsigned,unsigned*) override;
    void AGS_DeInit(AGSContext*) override;
    DXGI_ADAPTER_DESC1 getDXGIAdapter(void*,int&) override;
    void present() override;
    ComPtr<ID3D11Device> native;
    ComPtr<ID3D11DeviceContext> immediate;
    ComPtr<ID3D11Device> renderDevice;
    ComPtr<ID3D11DeviceContext> renderContext;
private:
    std::atomic_uint refs{1};
};
void Check(HRESULT,const char*);
}
