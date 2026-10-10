#include "NvFlex.h"
#include "solver/KernelParams.hpp"
#include <windows.h>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
template<class T>T proc(HMODULE m,const char* name){auto p=GetProcAddress(m,name);if(!p)throw std::runtime_error(name);return reinterpret_cast<T>(p);}
static void error(NvFlexErrorSeverity,const char* text,const char*,int){std::cerr<<text<<"\n";}
int wmain(int argc,wchar_t** argv){try{
    if(argc!=4)throw std::runtime_error("reference.dll params.bin result.json");
    HMODULE module=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)throw std::runtime_error("Load DLL");
    auto init=proc<decltype(&NvFlexInit)>(module,"NvFlexInit");auto shutdown=proc<decltype(&NvFlexShutdown)>(module,"NvFlexShutdown");auto create=proc<decltype(&NvFlexCreateSolver)>(module,"NvFlexCreateSolver");auto destroy=proc<decltype(&NvFlexDestroySolver)>(module,"NvFlexDestroySolver");
    auto setParams=proc<decltype(&NvFlexSetParams)>(module,"NvFlexSetParams");auto active=proc<decltype(&NvFlexSetActiveCount)>(module,"NvFlexSetActiveCount");
    auto reference=reinterpret_cast<void(*)(NvFlexSolver*,float,int)>(reinterpret_cast<char*>(module)+0x34f40);
    NvFlexInitDesc id{-1,false,nullptr,nullptr,nullptr,true,eNvFlexD3D11};auto library=init(120,error,&id);if(!library)throw std::runtime_error("Init library");
    NvFlexSolverDesc sd{eNvFlexFeatureModeDefault,64,32,96,6};auto solver=create(library,&sd);if(!solver)throw std::runtime_error("Create solver");active(solver,7);
    NvFlexParams base{};std::ifstream input(std::filesystem::path(argv[2]),std::ios::binary);input.read(reinterpret_cast<char*>(&base),sizeof(base));if(input.gcount()!=sizeof(base))throw std::runtime_error("Input params");
    // Explicit stores in InitParams define these byte ranges. The gaps are
    // obsolete fields/padding copied uninitialized by the original routine.
    std::vector<std::pair<unsigned,unsigned>> defined={{0,156},{164,172},{176,292},{296,312},{320,328},{336,356},{368,396},{400,436},{440,448},{460,464},{476,496},{500,512}};
    unsigned cases=0,failures=0;std::ofstream report{std::filesystem::path(argv[3])};report<<"{\"cases\":[";bool comma=false;
    for(float radius:{0.01f,0.05f,0.1f,0.5f})for(float ratio:{0.0f,0.5f,0.65f,1.0f})for(int substeps:{1,2,3,5}){
        auto params=base;params.radius=radius;params.fluidRestDistance=radius*ratio;params.solidRestDistance=radius*ratio;setParams(solver,&params);
        float dt=(1.0f/60.0f)/float(substeps);reference(solver,dt,substeps);
        const auto& state=*reinterpret_cast<const nvflex_recovered::NvFlexSolver*>(solver);auto actual=df::BuildKernelParams(state,dt,substeps);
        auto expected=reinterpret_cast<const unsigned char*>(&state.mKernelParamsHost);auto bytes=reinterpret_cast<const unsigned char*>(&actual);std::vector<unsigned> wrong;
        for(auto range:defined)for(unsigned offset=range.first;offset<range.second;++offset)if(expected[offset]!=bytes[offset])wrong.push_back(offset);
        failures+=!wrong.empty();++cases;report<<(comma?",":"")<<"{\"radius\":"<<radius<<",\"ratio\":"<<ratio<<",\"substeps\":"<<substeps<<",\"wrong_bytes\":[";
        for(size_t i=0;i<wrong.size();++i)report<<(i?",":"")<<wrong[i];report<<"]}";comma=true;
        if(!wrong.empty())std::cout<<"mismatch radius="<<radius<<" ratio="<<ratio<<" substeps="<<substeps<<" first="<<wrong.front()<<"\n";
    }
    report<<"],\"total\":"<<cases<<",\"mismatches\":"<<failures<<"}\n";destroy(solver);shutdown(library);FreeLibrary(module);
    std::cout<<"Kernel parameter cases="<<cases<<" mismatches="<<failures<<"\n";return failures?1:0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
