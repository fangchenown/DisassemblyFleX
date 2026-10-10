#include "D3D12Context.hpp"
#include "NvApiInterop.hpp"
#include <cstdio>
namespace df {
// Device/queue selection recovered from RVA 0x5c920.
DeviceD3D12::DeviceD3D12(const NvFlexInitDesc& desc,NvFlexErrorCallback error){
    mD3D12Device=true;
    if(desc.renderDevice)native=static_cast<ID3D12Device*>(desc.renderDevice);
    else{ComPtr<IDXGIAdapter1> adapter;Check(m_pFactory->EnumAdapters1(desc.deviceIndex<0?0:unsigned(desc.deviceIndex),&adapter),"Select D3D12 adapter");Check(D3D12CreateDevice(adapter.Get(),D3D_FEATURE_LEVEL_11_0,IID_PPV_ARGS(&native)),"D3D12CreateDevice");}
    queryDeviceCapabilities(native.Get());bool async=false;
    if(!desc.runOnRenderContext){
        if(mGpuVendorId!=VENDOR_ID_NVIDIA)async=true;
        else{NvU32 version=0;NvAPI_ShortString branch{};NvAPI_SYS_GetDriverAndBranchVersion(&version,branch);char message[256]{};int line=0;
            if(version<38460){std::snprintf(message,sizeof(message),"Warning: D3D12 Async compute was requested, but driver lacks async compute features required by Flex (%s %d)",branch,version);line=0xa5;}
            else{unsigned hint=0;auto status=NvInterop(0x032650af,native.Get(),&hint);if(status==NVAPI_OK){async=hint==1;if(!async){std::snprintf(message,sizeof(message),"Warning: D3D12 Async compute was requested, but is not supported by GPU");line=0x9b;}}
                else{async=true;std::snprintf(message,sizeof(message),"Warning: D3D12 Async compute was requested, but NvAPI_D3D12_QueryAsyncComputeHint returned error %d",int(status));line=0xa0;}}
            if(line&&error)error(eNvFlexLogWarning,message,"..\\..\\dx\\contextD3D12\\DeviceD3D12.cpp",line);
        }
    }
    if(!async&&desc.renderContext)queue=static_cast<ID3D12CommandQueue*>(desc.renderContext);
    else{if(async&&desc.computeContext)queue=static_cast<ID3D12CommandQueue*>(desc.computeContext);
        else{D3D12_COMMAND_QUEUE_DESC q{};q.Type=async?D3D12_COMMAND_LIST_TYPE_COMPUTE:D3D12_COMMAND_LIST_TYPE_DIRECT;Check(native->CreateCommandQueue(&q,IID_PPV_ARGS(&queue)),"Create D3D12 queue");}
        if(async){graphics=static_cast<ID3D12CommandQueue*>(desc.renderContext);if(mGpuVendorId==VENDOR_ID_NVIDIA)NvInterop(0xc5f0365e,queue.Get(),4u,4u,true);}
    }
}
DeviceD3D12::~DeviceD3D12(){delete m_context;m_context=nullptr;}
NvFlex::Context* DeviceD3D12::createContext(){if(!m_context)m_context=new ContextD3D12(native.Get(),queue.Get(),graphics.Get());return m_context;}
NvAPI_Status DeviceD3D12::NvAPI_IsNvShaderExtnOpCodeSupported(NvU32 opcode,bool* supported){return NvAPI_D3D12_IsNvShaderExtnOpCodeSupported(native.Get(),opcode,supported);}
AGSReturnCode DeviceD3D12::AGS_DriverExtensions_Init(AGSContext* context,unsigned,unsigned* supported){return agsDriverExtensionsDX12_Init(context,native.Get(),supported);}
void DeviceD3D12::AGS_DeInit(AGSContext* context){agsDriverExtensionsDX12_DeInit(context);}
DXGI_ADAPTER_DESC1 DeviceD3D12::getDXGIAdapter(void* device,int& index){return getDeviceNumber(static_cast<ID3D12Device*>(device)->GetAdapterLuid(),index);}
void DeviceD3D12::present(){if(m_swapChain)m_swapChain->Present(0,0);}
}
