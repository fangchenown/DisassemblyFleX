#include "D3D11Context.hpp"
#include <cstring>
#include <stdexcept>
#include <cstdio>
#include <VersionHelpers.h>
#include "NvApiInterop.hpp"

namespace NvFlex {
Device::Device():mWindowDesc{},mWinRect{},m_hWnd(nullptr),m_swapChain(nullptr),m_pFactory(nullptr),
 mSMCount(~0u),mGpuVendorId(VENDOR_ID_OTHERS),mD3D12Device(false),m_context(nullptr){
    df::Check(CreateDXGIFactory1(__uuidof(IDXGIFactory1),reinterpret_cast<void**>(&m_pFactory)),"CreateDXGIFactory1");
}
Device::~Device(){if(m_swapChain)m_swapChain->Release();if(m_pFactory)m_pFactory->Release();}
static LRESULT CALLBACK RecoveredWindowProc(HWND window,UINT message,WPARAM wparam,LPARAM lparam){return DefWindowProcA(window,message,wparam,lparam);}
void Device::createWindow(){
    // Original private presentation helper, RVA 0x4f180. Public NvFlexInit
    // always disables presentation, so normal library/tests create no window.
    HMODULE module=nullptr;GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS,reinterpret_cast<LPCSTR>(&RecoveredWindowProc),&module);
    WNDCLASSEXA desc{};desc.cbSize=sizeof(desc);desc.style=CS_HREDRAW|CS_VREDRAW;desc.lpfnWndProc=RecoveredWindowProc;desc.hInstance=module;
    desc.hIcon=LoadIconA(nullptr,MAKEINTRESOURCEA(32512));desc.hCursor=LoadCursorA(nullptr,MAKEINTRESOURCEA(32512));desc.hbrBackground=reinterpret_cast<HBRUSH>(6);desc.lpszClassName="MyWin";desc.hIconSm=LoadIconA(nullptr,MAKEINTRESOURCEA(32512));RegisterClassExA(&desc);std::memcpy(&mWindowDesc,&desc,sizeof(desc));
    mWinRect={0,0,640,480};AdjustWindowRect(&mWinRect,WS_OVERLAPPEDWINDOW,FALSE);m_hWnd=CreateWindowExA(0,desc.lpszClassName,"",0xa0cf0000u,50,50,mWinRect.right-mWinRect.left,mWinRect.bottom-mWinRect.top,nullptr,nullptr,nullptr,nullptr);
}
std::vector<IDXGIAdapter1*> Device::enumerateDXGIAdapters(){
    std::vector<IDXGIAdapter1*> adapters;IDXGIAdapter1* item=nullptr;
    for(unsigned i=0;m_pFactory->EnumAdapters1(i,&item)==S_OK;++i)adapters.push_back(item);
    return adapters;
}
DXGI_ADAPTER_DESC1 Device::getDeviceNumber(const LUID id,int& index){
    DXGI_ADAPTER_DESC1 desc{};index=-1;
    for(unsigned i=0;;++i){df::ComPtr<IDXGIAdapter1> a;if(m_pFactory->EnumAdapters1(i,&a)!=S_OK)break;
        a->GetDesc1(&desc);if(desc.AdapterLuid.HighPart==id.HighPart&&desc.AdapterLuid.LowPart==id.LowPart){index=int(i);return desc;}}
    return {};
}
void Device::queryDeviceCapabilities(void* d3ddevice){
    int index=-1;DXGI_ADAPTER_DESC1 desc=getDXGIAdapter(d3ddevice,index);mSMCount=~0u;
    if(index<0)return;
    mDeviceName.clear();for(auto c:desc.Description){if(!c)break;mDeviceName.push_back(static_cast<char>(c));}
    auto end=mDeviceName.find_last_not_of(" \t\r\n");if(end!=std::string::npos)mDeviceName.resize(end+1);
    if(desc.VendorId==VENDOR_ID_NVIDIA){
        mGpuVendorId=VENDOR_ID_NVIDIA;NvAPI_Initialize();NvPhysicalGpuHandle handles[NVAPI_MAX_PHYSICAL_GPUS]{};NvU32 count=0;
        if(NvAPI_EnumPhysicalGPUs(handles,&count)==NVAPI_OK)for(NvU32 i=0;i<count;++i){
            NvU32 deviceId=0,subsystem=0,revision=0,externalId=0;
            if(NvAPI_GPU_GetPCIIdentifiers(handles[i],&deviceId,&subsystem,&revision,&externalId)==NVAPI_OK
              && desc.DeviceId==externalId&&desc.SubSysId==subsystem&&desc.Revision==revision){NvU32 count=~0ul;NvAPI_GPU_GetShaderSubPipeCount(handles[i],&count);mSMCount=static_cast<NvFlexUint>(count);break;}
        }
    }else mGpuVendorId=((desc.VendorId-0x1002u)&0xffffffdfu)==0?VENDOR_ID_AMD:VENDOR_ID_OTHERS;
}
}
namespace df {
DeviceD3D11::DeviceD3D11(const NvFlexInitDesc& desc,NvFlexErrorCallback error){
    if(desc.renderDevice){
        auto render=static_cast<ID3D11Device*>(desc.renderDevice);queryDeviceCapabilities(render);bool async=false;
        auto warn=[&](const char* message,int line){if(error)error(eNvFlexLogWarning,message,"..\\..\\dx\\contextD3D11\\DeviceD3D11.cpp",line);};
        if(!desc.runOnRenderContext){
            if(mGpuVendorId!=VENDOR_ID_NVIDIA){char text[180];std::snprintf(text,sizeof(text),"Warning: D3D11 Async compute was requested, but is not supported by this vendor %d",int(mGpuVendorId));warn(text,0xb2);}
            else if(!IsWindows10OrGreater())warn("Warning: D3D11 Async compute was requested, but is not supported prior to Windows 10",0xad);
            else{NvU32 version=0;NvAPI_ShortString branch{};NvAPI_SYS_GetDriverAndBranchVersion(&version,branch);
                if(version<38460){char text[240];std::snprintf(text,sizeof(text),"Warning: D3D11 Async compute was requested, but is not supported by driver %s %d",branch,version);warn(text,0xa8);}
                else{unsigned hint=0;auto status=NvInterop(0x09f22adf,render,&hint);if(status==NVAPI_OK){async=hint==1;if(!async)warn("Warning: D3D11 Async compute was requested, but is not supported by GPU",0x9e);}
                    else{async=true;char text[200];std::snprintf(text,sizeof(text),"Warning: D3D11 Async compute was requested, but NvAPI_D3D11_QueryAsyncComputeHint returned error %d",int(status));warn(text,0xa3);}}
            }
        }
        if(async){ID3D11Device* compute=nullptr;NvCheck(NvInterop(0x07b86467,render,0u,7u,&compute,static_cast<void*>(nullptr),static_cast<void*>(nullptr)),"Create compute-only D3D11 device");native.Attach(compute);native->GetImmediateContext(&immediate);NvInterop(0xc663b7b3,immediate.Get(),4u,4u,true);renderDevice=render;render->GetImmediateContext(&renderContext);mSMCount=~0u;}
        else{native=render;native->GetImmediateContext(&immediate);}
    }else{
        ComPtr<IDXGIAdapter1> adapter;unsigned index=desc.deviceIndex<0?0u:unsigned(desc.deviceIndex);
        Check(m_pFactory->EnumAdapters1(index,&adapter),"EnumAdapters1");
        Check(D3D11CreateDevice(adapter.Get(),D3D_DRIVER_TYPE_UNKNOWN,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&native,nullptr,&immediate),"D3D11CreateDevice");
    }
    if(!desc.renderDevice)queryDeviceCapabilities(native.Get());
}
DeviceD3D11::~DeviceD3D11(){delete m_context;m_context=nullptr;}
NvFlexUint DeviceD3D11::addRef(){return ++refs;}
NvFlexUint DeviceD3D11::release(){auto n=--refs;if(!n)delete this;return n;}
NvFlex::Context* DeviceD3D11::createContext(){if(!m_context)m_context=new ContextD3D11(native.Get(),immediate.Get(),renderDevice.Get(),renderContext.Get());return m_context;}
NvAPI_Status DeviceD3D11::NvAPI_IsNvShaderExtnOpCodeSupported(NvU32 opcode,bool* supported){return NvAPI_D3D11_IsNvShaderExtnOpCodeSupported(native.Get(),opcode,supported);}
AGSReturnCode DeviceD3D11::AGS_DriverExtensions_Init(AGSContext* context,unsigned slot,unsigned* supported){return agsDriverExtensionsDX11_Init(context,native.Get(),slot,supported);}
void DeviceD3D11::AGS_DeInit(AGSContext* context){agsDriverExtensionsDX11_DeInit(context);}
DXGI_ADAPTER_DESC1 DeviceD3D11::getDXGIAdapter(void* device,int& index){
    ComPtr<IDXGIDevice> dxgi;Check(static_cast<ID3D11Device*>(device)->QueryInterface(IID_PPV_ARGS(&dxgi)),"Get IDXGIDevice");
    ComPtr<IDXGIAdapter> adapter;Check(dxgi->GetAdapter(&adapter),"GetAdapter");DXGI_ADAPTER_DESC desc{};adapter->GetDesc(&desc);
    return getDeviceNumber(desc.AdapterLuid,index);
}
void DeviceD3D11::present(){if(m_swapChain)m_swapChain->Present(0,0);}
}
