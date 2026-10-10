#include "NvFlex.h"
#include <windows.h>
#include <d3d12.h>
#include <wrl/client.h>
#include <filesystem>
#include <fstream>
#include <iostream>
using Microsoft::WRL::ComPtr;
using Get=decltype(&NvFlexGetParticles);
static unsigned invoke(Get get,NvFlexSolver* s,NvFlexBuffer* b){__try{get(s,b,nullptr);return 0;}__except(EXCEPTION_EXECUTE_HANDLER){return GetExceptionCode();}}
int wmain(int argc,wchar_t** argv){if(argc!=3)return 2;
    ComPtr<ID3D12Device> device;if(FAILED(D3D12CreateDevice(nullptr,D3D_FEATURE_LEVEL_11_0,IID_PPV_ARGS(&device))))return 3;
    D3D12_COMMAND_QUEUE_DESC q{};ComPtr<ID3D12CommandQueue> queue;if(FAILED(device->CreateCommandQueue(&q,IID_PPV_ARGS(&queue))))return 4;
    HMODULE module=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 5;
#define API(name) auto name=reinterpret_cast<decltype(&::name)>(GetProcAddress(module,#name))
    API(NvFlexInit);API(NvFlexCreateSolver);API(NvFlexRegisterD3DBuffer);API(NvFlexGetParticles);API(NvFlexFlush);API(NvFlexWait);
#undef API
    NvFlexInitDesc init{-1,false,device.Get(),queue.Get(),nullptr,true,eNvFlexD3D12};auto library=NvFlexInit(120,nullptr,&init);if(!library)return 6;NvFlexSolverDesc desc{eNvFlexFeatureModeDefault,64,0,96,6};auto solver=NvFlexCreateSolver(library,&desc);NvFlexFlush(library);NvFlexWait(library);
    D3D12_HEAP_PROPERTIES heap{};heap.Type=D3D12_HEAP_TYPE_DEFAULT;heap.CreationNodeMask=heap.VisibleNodeMask=1;D3D12_RESOURCE_DESC resource{};resource.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;resource.Width=64*16;resource.Height=1;resource.DepthOrArraySize=resource.MipLevels=1;resource.SampleDesc.Count=1;resource.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;ComPtr<ID3D12Resource> native;if(FAILED(device->CreateCommittedResource(&heap,D3D12_HEAP_FLAG_NONE,&resource,D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&native))))return 7;
    auto registered=NvFlexRegisterD3DBuffer(library,native.Get(),64,16);auto exception=invoke(NvFlexGetParticles,solver,registered);
    {std::ofstream out{std::filesystem::path(argv[2])};out<<"{\"external_device_queue_initialized\":true,\"native_get_exception\":"<<exception<<"}\n";}
    std::cout<<"external D3D12 initialized; native getter exception="<<exception<<std::endl;
    // Diagnostic isolation: do not submit a command list after a failing
    // native-resource path. Process exit releases its own driver objects.
    ExitProcess(0);
}
