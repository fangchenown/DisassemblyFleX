// Compare real public solver outputs and inspect only the candidate's private
// integer dispatch bound. No benchmark timing is taken by this oracle.
#include "NvFlex.h"
#include "solver/SolverState.hpp"
#include <windows.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
static void require(bool value,const char* why){if(!value)throw std::runtime_error(why);}
template<class T>static T load(HMODULE m,const char* name){auto p=GetProcAddress(m,name);require(p!=nullptr,name);return reinterpret_cast<T>(p);}
static unsigned errors=0;
static void error(NvFlexErrorSeverity severity,const char* message,const char*,int){if(severity==eNvFlexLogError){++errors;std::cerr<<message<<"\n";}}
struct Result {std::vector<float> values;unsigned bounds=0;};
static Result run(const wchar_t* path,bool inspect,int compute,bool extensions,unsigned capacity,bool high,bool dense){
    errors=0;auto module=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(module!=nullptr,"Load DLL");
#define API(name) auto name=load<decltype(&::name)>(module,#name)
    API(NvFlexInit);API(NvFlexShutdown);API(NvFlexCreateSolver);API(NvFlexDestroySolver);API(NvFlexAllocBuffer);API(NvFlexFreeBuffer);API(NvFlexMap);API(NvFlexUnmap);API(NvFlexSetParticles);API(NvFlexSetVelocities);API(NvFlexSetPhases);API(NvFlexSetActive);API(NvFlexSetActiveCount);API(NvFlexSetParams);API(NvFlexSetSprings);API(NvFlexUpdateSolver);API(NvFlexGetParticles);API(NvFlexGetVelocities);API(NvFlexGetDeviceAndContext);
#undef API
    NvFlexInitDesc setup{-1,extensions,nullptr,nullptr,nullptr,true,static_cast<NvFlexComputeType>(compute)};
    auto library=NvFlexInit(120,error,&setup);require(library!=nullptr,"Init");
    void* device=nullptr;void* context=nullptr;NvFlexGetDeviceAndContext(library,&device,&context);auto c=static_cast<NvFlex::Context*>(context);
    NvFlexSolverDesc description{eNvFlexFeatureModeSimpleSolids,int(capacity),0,96,6};auto solver=NvFlexCreateSolver(library,&description);require(solver!=nullptr,"Solver");
    const unsigned activeCount=dense?capacity/2+1:64;std::vector<int> active(activeCount);for(unsigned i=0;i<activeCount;++i)active[i]=int(i);
    if(high){active.back()=int(capacity-1);std::swap(active[1],active.back());}
    std::vector<float> positions(capacity*4,0),velocities(capacity*3,0);std::vector<int> phases(capacity,0);
    for(unsigned i=0;i<activeCount;++i){auto id=unsigned(active[i]);positions[id*4]=float(i%32)*.21f;positions[id*4+1]=1+float(i/32)*.21f;positions[id*4+2]=.3f;positions[id*4+3]=i%17?1.f:0.f;}
    std::vector<NvFlexBuffer*> buffers;
    auto buffer=[&](unsigned count,unsigned stride,const void* data){auto b=NvFlexAllocBuffer(library,int(count),int(stride),eNvFlexBufferHost);require(b!=nullptr,"Allocate host");buffers.push_back(b);auto p=NvFlexMap(b,eNvFlexMapWait);require(p!=nullptr,"Map host");if(data)std::memcpy(p,data,size_t(count)*stride);else std::memset(p,0,size_t(count)*stride);NvFlexUnmap(b);return b;};
    auto position=buffer(capacity,16,positions.data()),velocity=buffer(capacity,12,velocities.data()),phase=buffer(capacity,4,phases.data()),indices=buffer(activeCount,4,active.data());
    NvFlexSetParticles(solver,position,nullptr);NvFlexSetVelocities(solver,velocity,nullptr);NvFlexSetPhases(solver,phase,nullptr);NvFlexSetActive(solver,indices,nullptr);NvFlexSetActiveCount(solver,int(activeCount));
    NvFlexParams params{};std::ifstream fixture("Build/DisassemblyFleX-AlphaMigration-20261010/runs/baseline-pilot-d11-v1-s47-e0-r0-nv/params.bin",std::ios::binary);fixture.read(reinterpret_cast<char*>(&params),sizeof(params));require(fixture.gcount()==sizeof(params),"Parameter fixture");
    params.numPlanes=0;params.numIterations=4;params.fluidRestDistance=0;params.gravity[0]=params.gravity[1]=params.gravity[2]=0;params.wind[0]=params.wind[1]=params.wind[2]=0;params.drag=params.lift=0;NvFlexSetParams(solver,&params);
    std::vector<int> springs(128);std::vector<float> lengths(64,.21f),stiffness(64,.5f);
    for(unsigned i=0;i<64;++i){springs[2*i]=active[i%activeCount];springs[2*i+1]=active[(i+1)%activeCount];}
    auto springIndices=buffer(128,4,springs.data()),springLengths=buffer(64,4,lengths.data()),springStiffness=buffer(64,4,stiffness.data());Result result;
    auto set=[&](unsigned count){
        NvFlexSetSprings(solver,springIndices,springLengths,springStiffness,int(count));
        if(!inspect)return;
        auto& storage=solver->storage;const bool expected=count && capacity>=16384 && activeCount<=capacity/2;
        require(storage.springDispatchReady==expected,"Eligibility/clear invalidation");
        if(!expected)return;
        unsigned maximum=0;for(unsigned i=0;i<count*2;++i)maximum=std::max(maximum,unsigned(springs[i]));unsigned expectedX=(maximum+1u+63u)/64u;
        NvFlex::BufferDesc desc{};desc.dim=3;desc.stride=4;desc.bufferType=NvFlex::eBuffer|NvFlex::eUAV_SRV|NvFlex::eStage;desc.format=eNvFlexFormat_r32_uint;
        auto target=c->createBuffer(&desc);c->copyToHost(target,0,storage.springDispatchArgs.buffer,0,12);auto values=static_cast<unsigned*>(c->map(target,NvFlex::eMapRead,true));require(values!=nullptr,"Read indirect args");
        require(values[0]==expectedX&&values[1]==1&&values[2]==1,"GPU maximum endpoint bound");c->unmap(target);delete target;++result.bounds;
    };
    for(unsigned frame=0;frame<12;++frame){
        if(frame==0)set(16);if(frame==3)set(64);if(frame==6)set(0);if(frame==8)set(32);if(frame==10)set(64);
        NvFlexUpdateSolver(solver,1.f/60.f,2,false);
        if(frame==2||frame==5||frame==7||frame==9||frame==11){
            NvFlexGetParticles(solver,position,nullptr);NvFlexGetVelocities(solver,velocity,nullptr);
            for(auto pair:{std::make_pair(position,capacity*4),std::make_pair(velocity,capacity*3)}){
                auto values=static_cast<float*>(NvFlexMap(pair.first,eNvFlexMapWait));require(values!=nullptr,"Read result");
                for(unsigned i=0;i<pair.second;++i)require(std::isfinite(values[i]),"Nonfinite solver state");
                result.values.insert(result.values.end(),values,values+pair.second);NvFlexUnmap(pair.first);
            }
        }
    }
    require(errors==0,"Runtime error callback");for(auto b:buffers)NvFlexFreeBuffer(b);NvFlexDestroySolver(solver);NvFlexShutdown(library);FreeLibrary(module);return result;
}
int wmain(int argc,wchar_t** argv){
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);if(argc!=4)return 64;
    try{
        unsigned cases=0,bounds=0;
        for(int compute:{1,2})for(bool extension:{false,true})for(int scenario=0;scenario<4;++scenario){
            unsigned capacity=scenario==2?4096:scenario==3?16384:65536;bool high=scenario==1,dense=scenario==3;
            auto control=run(argv[1],false,compute,extension,capacity,high,dense);auto candidate=run(argv[2],true,compute,extension,capacity,high,dense);
            require(control.values.size()==candidate.values.size(),"Output length");require(std::memcmp(control.values.data(),candidate.values.data(),control.values.size()*sizeof(float))==0,"Output bytes differ");
            ++cases;bounds+=candidate.bounds;std::cout<<compute<<" "<<extension<<" "<<scenario<<" PASS\n";
        }
        std::ofstream file{std::filesystem::path(argv[3])};file<<"{\"status\":\"PASS\",\"cases\":"<<cases<<",\"gpu_bound_checks\":"<<bounds<<",\"whole_capacity_position_velocity_bytes_equal\":true}\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
