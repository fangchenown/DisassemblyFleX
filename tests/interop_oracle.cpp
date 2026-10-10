#include "NvFlex.h"
#include "dx/context/Context.h"
#include "dx/context/Device.h"
#include <d3d11.h>
#include <d3dcompiler.h>
#include <wrl/client.h>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
using Microsoft::WRL::ComPtr;
static void check(bool okay,const char* message){if(!okay)throw std::runtime_error(message);}
static void error(NvFlexErrorSeverity severity,const char* message,const char*,int){if(severity==eNvFlexLogError)throw std::runtime_error(message);}
struct Result {std::vector<unsigned> native;bool matchesInput=true;};
static Result run(const wchar_t* path,bool async){
    Result result;
    std::wcout<<L"interop "<<path<<L" async="<<async<<std::endl;
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> immediate;check(SUCCEEDED(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&device,nullptr,&immediate)),"D3D11CreateDevice");
    HMODULE module=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);check(module!=nullptr,"Load DLL");
#define API(name) auto name=reinterpret_cast<decltype(&::name)>(GetProcAddress(module,#name));check(name!=nullptr,#name)
    API(NvFlexInit);API(NvFlexShutdown);API(NvFlexCreateSolver);API(NvFlexDestroySolver);API(NvFlexRegisterD3DBuffer);API(NvFlexUnregisterD3DBuffer);API(NvFlexSetParticles);API(NvFlexGetParticles);API(NvFlexAllocBuffer);API(NvFlexFreeBuffer);API(NvFlexMap);API(NvFlexUnmap);API(NvFlexWait);API(NvFlexFlush);API(NvFlexComputeWaitForGraphics);API(NvFlexGetDeviceAndContext);
#undef API
    NvFlexInitDesc init{-1,true,device.Get(),immediate.Get(),nullptr,!async,eNvFlexD3D11};auto lib=NvFlexInit(120,error,&init);check(lib!=nullptr,"Initialize interop");NvFlexSolverDesc desc{eNvFlexFeatureModeDefault,64,0,96,6};auto solver=NvFlexCreateSolver(lib,&desc);
    std::array<float,256> values;for(unsigned i=0;i<values.size();++i)values[i]=float(i)*.03125f;
    D3D11_BUFFER_DESC bd{};bd.ByteWidth=sizeof(values);bd.Usage=D3D11_USAGE_DEFAULT;bd.BindFlags=D3D11_BIND_SHADER_RESOURCE|D3D11_BIND_UNORDERED_ACCESS;bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED|D3D11_RESOURCE_MISC_SHARED;bd.StructureByteStride=16;D3D11_SUBRESOURCE_DATA initial{values.data(),0,0};ComPtr<ID3D11Buffer> input,output;
    check(SUCCEEDED(device->CreateBuffer(&bd,&initial,&input)),"Create shared input");std::array<unsigned,256> sentinel;sentinel.fill(0x3fa00000);D3D11_SUBRESOURCE_DATA sentinelData{sentinel.data(),0,0};check(SUCCEEDED(device->CreateBuffer(&bd,&sentinelData,&output)),"Create shared output");
    auto registeredIn=NvFlexRegisterD3DBuffer(lib,input.Get(),64,16),registeredOut=NvFlexRegisterD3DBuffer(lib,output.Get(),64,16);
    check(*reinterpret_cast<int*>(reinterpret_cast<char*>(registeredOut)+4)==3,"Registered native buffer type");check(*reinterpret_cast<void**>(reinterpret_cast<char*>(registeredOut)+16)==output.Get(),"Registered native pointer");
    NvFlexComputeWaitForGraphics(lib);NvFlexBuffer* upload=nullptr;
    if(async){upload=NvFlexAllocBuffer(lib,64,16,eNvFlexBufferHost);auto data=NvFlexMap(upload,eNvFlexMapWait);std::memcpy(data,values.data(),sizeof(values));NvFlexUnmap(upload);}
    // A render-device buffer cannot be used as a CopySubresourceRegion source
    // on the separate compute device. Test that input path in render mode;
    // async outputs exercise the reference's NV synchronization protocol.
    NvFlexSetParticles(solver,async?upload:registeredIn,nullptr);NvFlexFlush(lib);NvFlexWait(lib);NvFlexGetParticles(solver,registeredOut,nullptr);std::cout<<"shared copy queued"<<std::endl;NvFlexFlush(lib);immediate->Flush();NvFlexWait(lib);std::cout<<"shared copy completed"<<std::endl;if(upload)NvFlexFreeBuffer(upload);
    auto host=NvFlexAllocBuffer(lib,64,16,eNvFlexBufferHost);NvFlexGetParticles(solver,host,nullptr);auto p=NvFlexMap(host,eNvFlexMapWait);check(std::memcmp(p,values.data(),sizeof(values))==0,"Shared input to solver");NvFlexUnmap(host);
    bd.Usage=D3D11_USAGE_STAGING;bd.BindFlags=0;bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;bd.CPUAccessFlags=D3D11_CPU_ACCESS_READ|D3D11_CPU_ACCESS_WRITE;ComPtr<ID3D11Buffer> staging;check(SUCCEEDED(device->CreateBuffer(&bd,nullptr,&staging)),"Create staging");
    // The original currently returns a different native output in compute-only
    // mode on this driver. Preserve every word for reference/candidate
    // comparison instead of assuming a stronger contract than the binary.
    auto verify=[&](){immediate->CopyResource(staging.Get(),output.Get());D3D11_MAPPED_SUBRESOURCE map{};check(SUCCEEDED(immediate->Map(staging.Get(),0,D3D11_MAP_READ,0,&map)),"Read native buffer");auto words=static_cast<unsigned*>(map.pData);result.native.insert(result.native.end(),words,words+256);result.matchesInput&=std::memcmp(map.pData,values.data(),sizeof(values))==0;std::cout<<"native input match="<<result.matchesInput<<" first="<<words[0]<<","<<words[1]<<","<<words[2]<<std::endl;immediate->Unmap(staging.Get(),0);};verify();
    void* abstractDevice=nullptr;NvFlex::Context* context=nullptr;NvFlexGetDeviceAndContext(lib,&abstractDevice,reinterpret_cast<void**>(&context));
    if(async)check(static_cast<NvFlex::Device*>(abstractDevice)->mSMCount==~0u,"Async mode did not create the compute-only device");
    auto source=*reinterpret_cast<NvFlex::Buffer**>(reinterpret_cast<char*>(solver)+0x218);context->copyToNative(output.Get(),0,source,0,sizeof(values));NvFlexFlush(lib);immediate->Flush();NvFlexWait(lib);verify();
    // Original push/pop preserves CS slots, while clearing graphics state.
    const char* sourceText="float4 main():SV_POSITION{return float4(0,0,0,1);}";ComPtr<ID3DBlob> code,messages;check(SUCCEEDED(D3DCompile(sourceText,std::strlen(sourceText),nullptr,nullptr,nullptr,"main","vs_5_0",0,0,&code,&messages)),"Compile vertex shader");ComPtr<ID3D11VertexShader> vertex;check(SUCCEEDED(device->CreateVertexShader(code->GetBufferPointer(),code->GetBufferSize(),nullptr,&vertex)),"Create vertex shader");
    if(!async){immediate->VSSetShader(vertex.Get(),nullptr,0);D3D11_RASTERIZER_DESC raster{};raster.FillMode=D3D11_FILL_SOLID;raster.CullMode=D3D11_CULL_NONE;ComPtr<ID3D11RasterizerState> state;device->CreateRasterizerState(&raster,&state);immediate->RSSetState(state.Get());context->contextPush();context->contextPop();ComPtr<ID3D11VertexShader> after;immediate->VSGetShader(&after,nullptr,nullptr);ComPtr<ID3D11RasterizerState> afterRaster;immediate->RSGetState(&afterRaster);check(!after&&!afterRaster,"Graphics state must remain cleared by contextPush");}
    NvFlexFreeBuffer(host);NvFlexUnregisterD3DBuffer(registeredIn);NvFlexUnregisterD3DBuffer(registeredOut);NvFlexDestroySolver(solver);NvFlexShutdown(lib);FreeLibrary(module);
    return result;
}
int wmain(int argc,wchar_t** argv){try{check(argc==4,"reference candidate output.json");std::array<Result,4> results;unsigned index=0;for(auto path:{argv[1],argv[2]})for(bool async:{false,true})results[index++]=run(path,async);bool equal=results[0].native==results[2].native&&results[1].native==results[3].native;
    auto output=std::filesystem::path(argv[3]);for(unsigned i=0;i<4;++i){auto file=output;file.replace_extension(std::to_string(i)+".bin");std::ofstream stream(file,std::ios::binary);stream.write(reinterpret_cast<const char*>(results[i].native.data()),results[i].native.size()*4);}
    std::ofstream report(output);report<<"{\"equal\":"<<(equal?"true":"false")<<",\"modes\":[\"reference-render\",\"reference-compute-only\",\"candidate-render\",\"candidate-compute-only\"],\"native_matches_input\":[";for(unsigned i=0;i<4;++i)report<<(i?",":"")<<(results[i].matchesInput?"true":"false");report<<"],\"graphics_state_contract\":true}\n";std::cout<<"Interop equivalent="<<equal<<std::endl;return equal?0:1;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
