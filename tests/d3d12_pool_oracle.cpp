// Allocation-lifetime regression. GPU output checks exercise the real DLL;
// candidate-only pool sizes verify bounded reuse, not just successful dispatch.
#include "NvFlex.h"
#include "runtime/D3D12Resources.hpp"
#include <d3dcompiler.h>
#include <d3d12sdklayers.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <cstring>
using Microsoft::WRL::ComPtr;
using namespace NvFlex;
static void require(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
static void check(HRESULT hr,const char* text){require(SUCCEEDED(hr),text);}
template<class T>static T api(HMODULE m,const char* n){auto p=GetProcAddress(m,n);require(p!=nullptr,n);return reinterpret_cast<T>(p);}
struct Engine {
    HMODULE module;NvFlexLibrary* library;Context* context;
    decltype(&NvFlexShutdown) shutdown;
    ComPtr<ID3D12Device> device;ComPtr<ID3D12CommandQueue> queue;
    Engine(const wchar_t* path,D3D12_COMMAND_LIST_TYPE type=D3D12_COMMAND_LIST_TYPE_DIRECT){
        check(D3D12CreateDevice(nullptr,D3D_FEATURE_LEVEL_11_0,IID_PPV_ARGS(&device)),"Create device");
        D3D12_COMMAND_QUEUE_DESC desc{};desc.Type=type;check(device->CreateCommandQueue(&desc,IID_PPV_ARGS(&queue)),"Create queue");
        module=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(module!=nullptr,"Load DLL");
        auto init=api<decltype(&NvFlexInit)>(module,"NvFlexInit");shutdown=api<decltype(&NvFlexShutdown)>(module,"NvFlexShutdown");
        NvFlexInitDesc setup{-1,false,device.Get(),queue.Get(),nullptr,true,eNvFlexD3D12};library=init(120,nullptr,&setup);require(library!=nullptr,"Initialize");
        void* d=nullptr;void* c=nullptr;api<decltype(&NvFlexGetDeviceAndContext)>(module,"NvFlexGetDeviceAndContext")(library,&d,&c);context=static_cast<Context*>(c);
    }
    ~Engine(){shutdown(library);FreeLibrary(module);}
};
static ComPtr<ID3DBlob> program(){
    const char* source="cbuffer C0:register(b0){uint index,value,pad0,pad1;} cbuffer C1:register(b1){uint salt;uint3 pad2;} RWStructuredBuffer<uint> o:register(u0); [numthreads(1,1,1)] void main(){o[index]=value^salt;}";
    ComPtr<ID3DBlob> code,errors;check(D3DCompile(source,std::strlen(source),"pool_oracle",nullptr,nullptr,"main","cs_5_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&code,&errors),"Compile");return code;
}
static Buffer* buffer(Context* c){BufferDesc d{};d.dim=512;d.stride=4;d.bufferType=eBuffer|eUAV_SRV|eStage|eStructured;return c->createBuffer(&d);}
static ConstantBuffer* constant(Context* c){ConstantBufferDesc d{};d.dim=64;d.stride=4;d.uploadAccess=true;return c->createConstantBuffer(&d);}
static void fill(Context* c,ConstantBuffer* b,unsigned a,unsigned z){auto p=static_cast<unsigned*>(c->map(b));require(p!=nullptr,"Map CB");std::memset(p,0,256);p[0]=a;p[1]=z;c->unmap(b);}
static std::vector<unsigned> read(Context* c,Buffer* b,unsigned count){c->download(b);auto p=static_cast<unsigned*>(c->map(b,eMapRead,true));require(p!=nullptr,"Readback");std::vector<unsigned> data(p,p+count);c->unmap(b);return data;}
static void submit(Context* c,ComputeShader* shader,Buffer* output,ConstantBuffer* a,ConstantBuffer* z){DispatchParams p{};p.shader=shader;p.gridDim={1,1,1};p.rootConstantBuffer=a;p.secondConstantBuffer=z;p.readWrite[0]=output->getResourceRW();c->dispatch(&p);}
struct Stats {unsigned batches=0,dispatches=0;size_t constants=0,heaps=0;};
static Stats normal(const wchar_t* path,bool inspect){
    Engine e(path);auto c=e.context;auto code=program();ComputeShaderDesc sd{};sd.cs=code->GetBufferPointer();sd.cs_length=code->GetBufferSize();sd.label=L"PoolLifetime";
    auto shader=c->createComputeShader(&sd);auto out=buffer(c);auto a=constant(c),z=constant(c);Stats result;
    for(unsigned batch=0;batch<32;++batch){
        for(unsigned i=0;i<256;++i){fill(c,a,i,batch*10000+i);fill(c,z,0x12340000u+batch,0);submit(c,shader,out,a,z);}
        auto values=read(c,out,256);for(unsigned i=0;i<256;++i)require(values[i]==((batch*10000+i)^(0x12340000u+batch)),"Queued CB data overwritten");
        if(inspect){auto actual=static_cast<df::Constant12*>(a);auto state=static_cast<df::ContextD3D12*>(c)->state.get();
            if(batch==0){result.constants=actual->versions.size();result.heaps=state->gpuHeaps.size();}
            else require(actual->versions.size()==result.constants&&state->gpuHeaps.size()==result.heaps,"Pool keeps growing after high-water warmup");
        }
        ++result.batches;result.dispatches+=256;
    }
    // Reuse a current CB without another map after the first submission, then
    // map twice while its second use is still unsubmitted. A map-only fence
    // stamp incorrectly treats that first resource as already completed.
    fill(c,a,0,111);fill(c,z,9,0);submit(c,shader,out,a,z);c->flush();
    submit(c,shader,out,a,z);
    fill(c,a,1,222);fill(c,z,9,0);submit(c,shader,out,a,z);
    fill(c,a,2,333);fill(c,z,9,0);submit(c,shader,out,a,z);
    auto values=read(c,out,3);require(values[0]==(111^9)&&values[1]==(222^9)&&values[2]==(333^9),"Last use must be updated at bind");
    if(inspect){
        fill(c,a,0,444);fill(c,z,9,0);submit(c,shader,out,a,z);
        delete a;delete z;a=z=nullptr;values=read(c,out,1);require(values[0]==(444^9),"Released CB not retained through submission");
    }
    delete a;delete z;delete shader;delete out;return result;
}
struct NativeList {
    ComPtr<ID3D12CommandQueue> queue;ComPtr<ID3D12CommandAllocator> allocator;ComPtr<ID3D12GraphicsCommandList> list;ComPtr<ID3D12Fence> fence;
    NativeList(ID3D12Device* d,D3D12_COMMAND_LIST_TYPE type,UINT64 initial){D3D12_COMMAND_QUEUE_DESC q{};q.Type=type;check(d->CreateCommandQueue(&q,IID_PPV_ARGS(&queue)),"External queue");check(d->CreateCommandAllocator(type,IID_PPV_ARGS(&allocator)),"External allocator");check(d->CreateCommandList(0,type,allocator.Get(),nullptr,IID_PPV_ARGS(&list)),"External list");check(d->CreateFence(initial,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&fence)),"External fence");}
    void execute(UINT64 value){check(list->Close(),"Close external");ID3D12CommandList* lists[]={list.Get()};queue->ExecuteCommandLists(1,lists);check(queue->Signal(fence.Get(),value),"Signal external");}
};
struct ExternalDesc {ID3D12Device* device;ID3D12CommandQueue* queue;ID3D12CommandQueue* graphics;ID3D12CommandAllocator* allocator;ID3D12Fence* fence;ID3D12GraphicsCommandList* list;UINT64 completed,next;void** event;};
static_assert(sizeof(ExternalDesc)==72);
static void adopt(Engine& e,NativeList& n,UINT64 next){ExternalDesc d{e.device.Get(),n.queue.Get(),nullptr,n.allocator.Get(),n.fence.Get(),n.list.Get(),n.fence->GetCompletedValue(),next,nullptr};e.context->updateContext(reinterpret_cast<const NvFlexContextDesc*>(&d));}
static void wait(ID3D12Fence* f,UINT64 value){HANDLE event=CreateEventW(nullptr,FALSE,FALSE,nullptr);require(event!=nullptr,"Wait event");check(f->SetEventOnCompletion(value,event),"Arm wait");DWORD status=WaitForSingleObject(event,30000);CloseHandle(event);require(status==WAIT_OBJECT_0,"External completion timeout");}
struct Gate {ComPtr<ID3D12Fence> fence;~Gate(){if(fence)fence->Signal(1);}};
static void external(const wchar_t* path,D3D12_COMMAND_LIST_TYPE type){
    Engine e(path);auto c=e.context;auto code=program();ComputeShaderDesc sd{};sd.cs=code->GetBufferPointer();sd.cs_length=code->GetBufferSize();sd.label=L"ExternalFencePool";
    auto shader=c->createComputeShader(&sd);auto outA=buffer(c),outB=buffer(c);auto a=constant(c),z=constant(c);c->flush();
    NativeList first(e.device.Get(),type,0),second(e.device.Get(),type,1000);Gate gate;check(e.device->CreateFence(0,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&gate.fence)),"Gate fence");
    check(first.queue->Wait(gate.fence.Get(),1),"Block first queue");adopt(e,first,2);
    for(unsigned i=0;i<256;++i){fill(c,a,i,0x1000+i);fill(c,z,0x71,0);submit(c,shader,outA,a,z);}
    first.execute(2); // Deliberately pending behind the host-controlled gate.
    adopt(e,second,1001);
    for(unsigned i=0;i<256;++i){fill(c,a,i,0x2000+i);fill(c,z,0x82,0);submit(c,shader,outB,a,z);}
    auto b=read(c,outB,256);for(unsigned i=0;i<256;++i)require(b[i]==((0x2000+i)^0x82),"Second timeline output");
    for(unsigned i=0;i<256;++i){fill(c,a,i,0x3000+i);fill(c,z,0x93,0);submit(c,shader,outB,a,z);}
    // The old first queue still references CB versions and descriptor heaps.
    // Deleting wrappers must leave retained native objects alive for it.
    delete a;delete z;b=read(c,outB,256);for(unsigned i=0;i<256;++i)require(b[i]==((0x3000+i)^0x93),"Third submission output");
    check(gate.fence->Signal(1),"Unblock first queue");wait(first.fence.Get(),2);
    auto old=read(c,outA,256);for(unsigned i=0;i<256;++i)require(old[i]==((0x1000+i)^0x71),"Different fence reused pending descriptors/constants");
    delete shader;delete outA;delete outB;
}
static std::vector<unsigned> multipleSolvers(const wchar_t* path,D3D12_COMMAND_LIST_TYPE type){
    Engine e(path,type);
#define API(name) auto name=api<decltype(&::name)>(e.module,#name)
    API(NvFlexCreateSolver);API(NvFlexDestroySolver);API(NvFlexAllocBuffer);API(NvFlexFreeBuffer);API(NvFlexMap);API(NvFlexUnmap);API(NvFlexSetParticles);API(NvFlexSetVelocities);API(NvFlexSetPhases);API(NvFlexSetActiveCount);API(NvFlexSetParams);API(NvFlexUpdateSolver);API(NvFlexGetParticles);API(NvFlexGetVelocities);API(NvFlexGetSolvers);
#undef API
    NvFlexParams params{};std::ifstream file("Build/DisassemblyFleX-20261009/demo-runs/reference-scene47-30-v1/params.bin",std::ios::binary);file.read(reinterpret_cast<char*>(&params),sizeof(params));require(file.gcount()==sizeof(params),"Multi-solver parameter fixture");params.numPlanes=0;
    struct Sim {NvFlexSolver* solver=nullptr;NvFlexBuffer* position=nullptr;NvFlexBuffer* velocity=nullptr;NvFlexBuffer* phase=nullptr;int count=0;};
    std::array<Sim,3> sims;
    auto create=[&](Sim& s,int count){
        s.count=count;NvFlexSolverDesc d{eNvFlexFeatureModeDefault,count,0,96,6};s.solver=NvFlexCreateSolver(e.library,&d);require(s.solver!=nullptr,"Create solver");
        s.position=NvFlexAllocBuffer(e.library,count,16,eNvFlexBufferHost);s.velocity=NvFlexAllocBuffer(e.library,count,12,eNvFlexBufferHost);s.phase=NvFlexAllocBuffer(e.library,count,4,eNvFlexBufferHost);
        auto p=static_cast<float*>(NvFlexMap(s.position,eNvFlexMapWait));for(int i=0;i<count;++i){p[i*4]=float(i%16)*.2f;p[i*4+1]=2.0f+float(i/16)*.2f;p[i*4+2]=.4f;p[i*4+3]=1;}NvFlexUnmap(s.position);
        p=static_cast<float*>(NvFlexMap(s.velocity,eNvFlexMapWait));for(int i=0;i<count*3;++i)p[i]=float(i%7)*.01f;NvFlexUnmap(s.velocity);
        auto q=static_cast<int*>(NvFlexMap(s.phase,eNvFlexMapWait));for(int i=0;i<count;++i)q[i]=NvFlexMakePhase(i,0);NvFlexUnmap(s.phase);
        NvFlexSetParticles(s.solver,s.position,nullptr);NvFlexSetVelocities(s.solver,s.velocity,nullptr);NvFlexSetPhases(s.solver,s.phase,nullptr);NvFlexSetActiveCount(s.solver,count);NvFlexSetParams(s.solver,&params);
    };
    auto destroy=[&](Sim& s){NvFlexDestroySolver(s.solver);NvFlexFreeBuffer(s.position);NvFlexFreeBuffer(s.velocity);NvFlexFreeBuffer(s.phase);s={};};
    create(sims[0],64);create(sims[1],129);create(sims[2],257);std::vector<unsigned> data;
    for(unsigned frame=0;frame<120;++frame){
        for(auto&s:sims)NvFlexUpdateSolver(s.solver,1.0f/60,2,false);
        // Destroy/recreate while other solver work is queued in the same lib.
        if(frame==30){destroy(sims[1]);create(sims[1],193);}
        if(frame==70){destroy(sims[0]);create(sims[0],65);}
        require(NvFlexGetSolvers(e.library,nullptr,0)==3,"Three live solvers");
        for(auto&s:sims){NvFlexGetParticles(s.solver,s.position,nullptr);NvFlexGetVelocities(s.solver,s.velocity,nullptr);}
        for(auto&s:sims){
            auto p=static_cast<unsigned*>(NvFlexMap(s.position,eNvFlexMapWait));require(p!=nullptr,"Multi-solver particles");data.insert(data.end(),p,p+s.count*4);NvFlexUnmap(s.position);
            p=static_cast<unsigned*>(NvFlexMap(s.velocity,eNvFlexMapWait));require(p!=nullptr,"Multi-solver velocities");data.insert(data.end(),p,p+s.count*3);NvFlexUnmap(s.velocity);
        }
    }
    for(auto&s:sims)destroy(s);return data;
}
int wmain(int argc,wchar_t** argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);require(argc==4,"reference candidate output.json");
    auto r=normal(argv[1],false),n=normal(argv[2],true);external(argv[2],D3D12_COMMAND_LIST_TYPE_DIRECT);external(argv[2],D3D12_COMMAND_LIST_TYPE_COMPUTE);
    size_t words=0;for(auto type:{D3D12_COMMAND_LIST_TYPE_DIRECT,D3D12_COMMAND_LIST_TYPE_COMPUTE}){auto reference=multipleSolvers(argv[1],type),candidate=multipleSolvers(argv[2],type);require(reference==candidate,"Multi-solver outputs differ");words+=reference.size();}
    std::ofstream out{std::filesystem::path(argv[3])};out<<"{\"status\":\"PASS\",\"reference_batches\":"<<r.batches<<",\"candidate_batches\":"<<n.batches<<",\"dispatches_per_implementation\":"<<n.dispatches<<",\"constant_versions_after_warmup\":"<<n.constants<<",\"descriptor_heaps_after_warmup\":"<<n.heaps<<",\"pool_growth_after_warmup\":false,\"cross_submission_last_use\":true,\"release_before_flush\":true,\"independent_fence_timelines\":true,\"external_direct_queue\":true,\"external_compute_queue\":true,\"three_solver_120_frame_direct_and_compute_exact_words\":"<<words<<"}\n";
    std::cout<<"D3D12 pool lifetime tests PASS\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
