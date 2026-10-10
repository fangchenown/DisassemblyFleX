#include "NvFlex.h"
#include "dx/context/Context.h"
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
static void check(bool okay,const char* text){if(!okay)throw std::runtime_error(text);}
struct Result {std::vector<unsigned> calls,particles,velocities;};
struct User {NvFlex::Context* context;NvFlex::ComputeShader* shader;NvFlex::ConstantBuffer* constants;Result* result;unsigned stage;};
static void callback(NvFlexSolverCallbackParams params){
    auto& user=*static_cast<User*>(params.userData);unsigned dt=0;std::memcpy(&dt,&params.dt,4);unsigned pointers=!!params.particles|((!!params.velocities)<<1)|((!!params.phases)<<2)|((!!params.originalToSortedMap)<<3)|((!!params.sortedToOriginalMap)<<4);
    user.result->calls.insert(user.result->calls.end(),{user.stage,unsigned(params.numActive),dt,pointers});
    // The reference does not initialize params.solver. Exclude only that
    // indeterminate field, and inspect all usable callback payload fields.
    if(user.stage==eNvFlexStageSubstepEnd){auto context=user.context;context->contextPush();NvFlex::DispatchParams p{};p.shader=user.shader;p.gridDim={1,1,1};p.rootConstantBuffer=user.constants;p.readWrite[0]=reinterpret_cast<NvFlex::Buffer*>(params.velocities)->getResourceRW();context->dispatch(&p);context->contextPop();}
}
static Result run(const wchar_t* path,NvFlexComputeType type){
    HMODULE module=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);check(module!=nullptr,"Load DLL");
#define API(name) auto name=reinterpret_cast<decltype(&::name)>(GetProcAddress(module,#name));check(name!=nullptr,#name)
    API(NvFlexInit);API(NvFlexShutdown);API(NvFlexCreateSolver);API(NvFlexDestroySolver);API(NvFlexGetDeviceAndContext);API(NvFlexAllocBuffer);API(NvFlexFreeBuffer);API(NvFlexMap);API(NvFlexUnmap);API(NvFlexSetParticles);API(NvFlexGetParticles);API(NvFlexGetVelocities);API(NvFlexSetActiveCount);API(NvFlexSetParams);API(NvFlexUpdateSolver);API(NvFlexRegisterSolverCallback);
#undef API
    NvFlexInitDesc init{-1,false,nullptr,nullptr,nullptr,true,type};auto library=NvFlexInit(120,nullptr,&init);check(library!=nullptr,"Initialize");NvFlexSolverDesc desc{eNvFlexFeatureModeDefault,64,0,96,6};auto solver=NvFlexCreateSolver(library,&desc);
    NvFlexParams params{};params.numIterations=3;params.radius=.1f;params.solidRestDistance=.1f;params.fluidRestDistance=.06f;params.gravity[1]=-9.8f;params.maxSpeed=params.maxAcceleration=1.0e10f;params.relaxationMode=eNvFlexRelaxationLocal;params.relaxationFactor=1;NvFlexSetParams(solver,&params);
    auto particles=NvFlexAllocBuffer(library,64,16,eNvFlexBufferHost);auto velocities=NvFlexAllocBuffer(library,64,12,eNvFlexBufferHost);auto values=static_cast<float*>(NvFlexMap(particles,eNvFlexMapWait));std::memset(values,0,64*16);for(unsigned i=0;i<8;++i){values[i*4]=i*.2f;values[i*4+1]=1;values[i*4+3]=1;}NvFlexUnmap(particles);NvFlexSetParticles(solver,particles,nullptr);NvFlexSetActiveCount(solver,8);
    void* device=nullptr;NvFlex::Context* context=nullptr;NvFlexGetDeviceAndContext(library,&device,reinterpret_cast<void**>(&context));
    const char* hlsl="cbuffer C:register(b0){uint n;float delta;float2 padding;}RWStructuredBuffer<float4> velocity:register(u0);[numthreads(64,1,1)]void main(uint3 id:SV_DispatchThreadID){if(id.x<n)velocity[id.x].y+=delta;}";ComPtr<ID3DBlob> code,errors;check(SUCCEEDED(D3DCompile(hlsl,std::strlen(hlsl),nullptr,nullptr,nullptr,"main","cs_5_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&code,&errors)),"Compile callback shader");NvFlex::ComputeShaderDesc shaderDesc{code->GetBufferPointer(),code->GetBufferSize(),L"CallbackProbe"};auto shader=context->createComputeShader(&shaderDesc);
    NvFlex::ConstantBufferDesc cbDesc{16,1,true};auto constants=context->createConstantBuffer(&cbDesc);struct Constants {unsigned count;float delta;unsigned padding[2];} cb{8,.025f,{}};std::memcpy(context->map(constants),&cb,sizeof(cb));context->unmap(constants);
    Result result;std::array<User,5> users;
    for(unsigned stage=0;stage<5;++stage){users[stage]={context,shader,constants,&result,stage};NvFlexSolverCallback item{&users[stage],callback};auto old=NvFlexRegisterSolverCallback(solver,item,NvFlexSolverCallbackStage(stage));check(!old.function&&!old.userData,"Initial callback slot");old=NvFlexRegisterSolverCallback(solver,item,NvFlexSolverCallbackStage(stage));check(old.function==callback&&old.userData==&users[stage],"Previous callback return");}
    for(unsigned frame=0;frame<3;++frame)NvFlexUpdateSolver(solver,1.0f/60.0f,2,false);
    check(result.calls.size()==51*4,"Callback invocation count");for(size_t i=0;i<result.calls.size();i+=4)check(result.calls[i+1]==8&&result.calls[i+3]==31,"Callback fields");
    NvFlexGetParticles(solver,particles,nullptr);NvFlexGetVelocities(solver,velocities,nullptr);auto p=static_cast<unsigned*>(NvFlexMap(particles,eNvFlexMapWait));result.particles.assign(p,p+64*4);NvFlexUnmap(particles);p=static_cast<unsigned*>(NvFlexMap(velocities,eNvFlexMapWait));result.velocities.assign(p,p+64*3);NvFlexUnmap(velocities);
    for(unsigned stage=0;stage<5;++stage)NvFlexRegisterSolverCallback(solver,NvFlexSolverCallback{},NvFlexSolverCallbackStage(stage));delete shader;delete constants;NvFlexFreeBuffer(particles);NvFlexFreeBuffer(velocities);NvFlexDestroySolver(solver);NvFlexShutdown(library);FreeLibrary(module);return result;
}
int wmain(int argc,wchar_t** argv){try{check(argc==4,"reference candidate output.json");std::ofstream out{std::filesystem::path(argv[3])};out<<"[";bool all=true;for(unsigned mode=1;mode<=2;++mode){auto a=run(argv[1],NvFlexComputeType(mode)),b=run(argv[2],NvFlexComputeType(mode));bool equal=a.calls==b.calls&&a.particles==b.particles&&a.velocities==b.velocities;all&=equal;out<<(mode==2?",":"")<<"{\"compute_type\":"<<mode<<",\"equal\":"<<(equal?"true":"false")<<",\"callbacks\":51,\"gpu_outputs_equal\":"<<(a.particles==b.particles&&a.velocities==b.velocities?"true":"false")<<"}";std::cout<<"callback mode="<<mode<<" equal="<<equal<<std::endl;}out<<"]\n";return all?0:1;}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 2;}}
