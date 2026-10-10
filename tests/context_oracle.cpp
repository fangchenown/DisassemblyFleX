#include "NvFlex.h"
#include "dx/context/Device.h"
#include <d3dcompiler.h>
#include <wrl/client.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
using Microsoft::WRL::ComPtr;
static bool useD3D12=false;
static void check(bool okay,const char* text){if(!okay)throw std::runtime_error(text);}
static void hrcheck(HRESULT hr,const char* text){check(SUCCEEDED(hr),text);}
static_assert(sizeof(NvFlex::DispatchParams)==368);
template<class T> T proc(HMODULE module,const char* name){auto p=GetProcAddress(module,name);check(p!=nullptr,name);return reinterpret_cast<T>(p);}
static void error(NvFlexErrorSeverity severity,const char* message,const char*,int){std::cerr<<"Flex "<<severity<<": "<<message<<"\n";}
static ComPtr<ID3DBlob> compile(const char* source){ComPtr<ID3DBlob> code,errors;HRESULT hr=D3DCompile(source,std::strlen(source),"context_oracle",nullptr,nullptr,"main","cs_5_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&code,&errors);if(errors)std::cerr<<static_cast<const char*>(errors->GetBufferPointer());hrcheck(hr,"Compile shader");return code;}
struct Result {std::vector<unsigned> arithmetic,copy,texture;bool nativeDevice=false,stateRestored=false,timerValid=false;};
static std::vector<unsigned> readback(NvFlex::Context* context,NvFlex::Buffer* buffer,unsigned count){context->download(buffer);auto p=static_cast<unsigned*>(context->map(buffer,NvFlex::eMapRead,true));check(p!=nullptr,"Readback map");std::vector<unsigned> result(p,p+count);context->unmap(buffer);return result;}
static Result run(const wchar_t* path){
    HMODULE module=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);check(module!=nullptr,"Load library");
    auto init=proc<NvFlexLibrary*(*)(int,NvFlexErrorCallback,NvFlexInitDesc*)>(module,"NvFlexInit");
    auto shutdown=proc<void(*)(NvFlexLibrary*)>(module,"NvFlexShutdown");
    auto get=proc<void(*)(NvFlexLibrary*,void**,void**)>(module,"NvFlexGetDeviceAndContext");
    NvFlexInitDesc desc{};desc.deviceIndex=0;desc.enableExtensions=false;desc.runOnRenderContext=true;desc.computeType=useD3D12?eNvFlexD3D12:eNvFlexD3D11;
    NvFlexLibrary* library=init(120,error,&desc);check(library!=nullptr,"Initialize library");
    NvFlex::Device* device=nullptr;NvFlex::Context* context=nullptr;get(library,reinterpret_cast<void**>(&device),reinterpret_cast<void**>(&context));check(device&&context,"Get internal interfaces");
    NvFlex::BufferDesc bufferDesc{};bufferDesc.dim=96;bufferDesc.stride=4;bufferDesc.bufferType=NvFlex::eBuffer|NvFlex::eUAV_SRV|NvFlex::eStage|NvFlex::eStructured;
    auto input=context->createBuffer(&bufferDesc);auto output=context->createBuffer(&bufferDesc);auto copied=context->createBuffer(&bufferDesc);
    auto fill=[&](NvFlex::Buffer* buffer,bool sequence){auto p=static_cast<unsigned*>(context->map(buffer,NvFlex::eMapWrite,true));check(p!=nullptr,"Upload map");for(unsigned i=0;i<96;++i)p[i]=sequence?i*17u+3u:0xdeadbeefu;context->unmap(buffer);context->upload(buffer);};
    fill(input,true);fill(output,false);fill(copied,false);
    NvFlex::ConstantBufferDesc cbDesc{};cbDesc.dim=4;cbDesc.stride=4;cbDesc.uploadAccess=true;
    auto cb=context->createConstantBuffer(&cbDesc);auto constants=static_cast<unsigned*>(context->map(cb));check(constants!=nullptr,"Map constant buffer");constants[0]=123;constants[1]=0;constants[2]=0;constants[3]=0;context->unmap(cb);
    auto code=compile("cbuffer C:register(b0){uint4 c;} StructuredBuffer<uint> a:register(t0); RWStructuredBuffer<uint> b:register(u0); [numthreads(64,1,1)] void main(uint3 id:SV_DispatchThreadID){b[id.x]=(a[id.x]^c.x)+id.x;}");
    NvFlex::ComputeShaderDesc shaderDesc{};shaderDesc.cs=code->GetBufferPointer();shaderDesc.cs_length=code->GetBufferSize();shaderDesc.label=L"ContextOracle";
    auto shader=context->createComputeShader(&shaderDesc);check(shader!=nullptr,"Create compute shader");
    NvFlex::DispatchParams dispatch{};dispatch.shader=shader;dispatch.gridDim={1,1,1};dispatch.rootConstantBuffer=cb;dispatch.readOnly[0]=input->getResource();dispatch.readWrite[0]=output->getResourceRW();
    auto timers=context->createTimerPool();int timer=timers->begin();context->dispatch(&dispatch);timers->end(timer);timers->resolve();if(useD3D12)context->flush();timers->sync();
    auto timerFence=context->createFence();context->fenceSet(timerFence);context->fenceWait(timerFence);delete timerFence;
    unsigned long long first=0,last=0,frequency=0;float seconds=timers->get(timer,&first,&last,&frequency);
    Result result;result.timerValid=frequency>0&&last>=first&&std::isfinite(seconds)&&seconds>=0;check(result.timerValid,"Timestamp contract");
    result.arithmetic=readback(context,output,96);for(unsigned i=0;i<96;++i)check(result.arithmetic[i]==(i<64?((i*17u+3u)^123u)+i:0xdeadbeefu),"Arithmetic result");
    context->copy(copied,7*4,output,5*4,13*4);result.copy=readback(context,copied,96);
    for(unsigned i=0;i<96;++i)check(result.copy[i]==(i>=7&&i<20?result.arithmetic[i-2]:0xdeadbeefu),"Partial copy result");
    auto fence=context->createFence();context->fenceSet(fence);context->fenceWait(fence);
    if(useD3D12){auto native=reinterpret_cast<ID3D12Resource*>(input->getResource(NvFlex::eDefaultBuffer));ComPtr<ID3D12Device> nativeDevice;hrcheck(native->GetDevice(IID_PPV_ARGS(&nativeDevice)),"Native D3D12 device");result.nativeDevice=bool(nativeDevice)&&device->mD3D12Device;context->contextPush();context->contextPop();context->dispatch(&dispatch);check(readback(context,output,96)==result.arithmetic,"D3D12 context no-op contract");result.stateRestored=true;}
    else{auto native=reinterpret_cast<ID3D11Buffer*>(input->getResource(NvFlex::eDefaultBuffer));ComPtr<ID3D11Device> nativeDevice;native->GetDevice(&nativeDevice);result.nativeDevice=nativeDevice!=nullptr;
    ComPtr<ID3D11DeviceContext> nativeContext;nativeDevice->GetImmediateContext(&nativeContext);
    ComPtr<ID3D11ComputeShader> before,after;nativeContext->CSGetShader(&before,nullptr,nullptr);context->contextPush();nativeContext->CSSetShader(nullptr,nullptr,0);context->contextPop();nativeContext->CSGetShader(&after,nullptr,nullptr);result.stateRestored=before.Get()==after.Get();check(result.stateRestored,"Context preservation");}
    NvFlex::Texture3DDesc textureDesc{};textureDesc.dim={4,3,2};textureDesc.format=eNvFlexFormat_r32_float;textureDesc.uploadAccess=true;textureDesc.downloadAccess=true;
    auto texture=context->createTexture3D(&textureDesc);auto mapped=context->map(texture);check(mapped.data!=nullptr,"Texture upload map");
    for(unsigned z=0;z<2;++z)for(unsigned y=0;y<3;++y)for(unsigned x=0;x<4;++x){float value=float(x+y*10+z*100)+0.125f;std::memcpy(static_cast<char*>(mapped.data)+z*mapped.depthPitch+y*mapped.rowPitch+x*4,&value,4);}context->unmap(texture);
    auto textureCode=compile("Texture3D<float> a:register(t0);SamplerState s:register(s0);RWStructuredBuffer<float> b:register(u0);[numthreads(64,1,1)]void main(uint3 id:SV_DispatchThreadID){b[id.x]=a.SampleLevel(s,float3(float(id.x)/42.0-0.25,0.5,0.5),0);}");
    shaderDesc.cs=textureCode->GetBufferPointer();shaderDesc.cs_length=textureCode->GetBufferSize();auto textureShader=context->createComputeShader(&shaderDesc);
    dispatch={};dispatch.shader=textureShader;dispatch.gridDim={1,1,1};dispatch.readOnly[0]=texture->getResource();dispatch.readWrite[0]=output->getResourceRW();context->dispatch(&dispatch);result.texture=readback(context,output,64);
    delete textureShader;delete texture;delete fence;delete timers;delete shader;delete cb;delete copied;delete output;delete input;shutdown(library);FreeLibrary(module);return result;
}
int wmain(int argc,wchar_t** argv){try{
    if(argc!=4&&argc!=5)throw std::runtime_error("reference candidate output.json [d3d12]");useD3D12=argc==5&&std::wstring(argv[4])==L"d3d12";
    auto a=run(argv[1]),b=run(argv[2]);unsigned differences=0;for(size_t i=0;i<a.texture.size();++i)differences+=a.texture[i]!=b.texture[i];
    bool okay=a.arithmetic==b.arithmetic&&a.copy==b.copy&&differences==0&&a.nativeDevice&&b.nativeDevice&&a.stateRestored&&b.stateRestored&&a.timerValid&&b.timerValid;
    std::ofstream output{std::filesystem::path(argv[3])};output<<"{\"equal\":"<<(okay?"true":"false")<<",\"arithmetic_words\":"<<a.arithmetic.size()<<",\"copy_words\":"<<a.copy.size()<<",\"texture_words\":"<<a.texture.size()<<",\"texture_differences\":"<<differences<<",\"state_roundtrip\":true,\"timers_valid\":true,\"reference_texture\":[";
    for(size_t i=0;i<a.texture.size();++i)output<<(i?",":"")<<a.texture[i];output<<"],\"candidate_texture\":[";for(size_t i=0;i<b.texture.size();++i)output<<(i?",":"")<<b.texture[i];output<<"]}\n";
    std::cout<<"Context virtual interface compare="<<okay<<" texture bit differences="<<differences<<"\n";return okay?0:1;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
