#include "NvFlex.h"
#include "dx/context/Context.h"
#include "recovered/FlexLayouts.hpp"
#include <windows.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <vector>
static void require(bool x,const char* why){if(!x)throw std::runtime_error(why);}
template<class T>static T api(HMODULE m,const char* name){auto p=GetProcAddress(m,name);require(p!=nullptr,name);return reinterpret_cast<T>(p);}
static std::vector<char> file(const wchar_t* path){std::ifstream in{std::filesystem::path(path),std::ios::binary};require(in.good(),"Shader file");return {std::istreambuf_iterator<char>(in),std::istreambuf_iterator<char>()};}
static std::vector<unsigned> read(NvFlex::Context* c,NvFlex::Buffer* b,unsigned words){c->download(b);auto p=static_cast<unsigned*>(c->map(b,NvFlex::eMapRead,true));require(p!=nullptr,"Read output");std::vector<unsigned> v(p,p+words);c->unmap(b);return v;}
int wmain(int argc,wchar_t** argv){
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);if(argc!=5)return 64;
    try{
        auto original=file(argv[2]),specialized=file(argv[3]);unsigned cases=0;
        auto module=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(module!=nullptr,"DLL");
        auto init=api<decltype(&NvFlexInit)>(module,"NvFlexInit");auto shutdown=api<decltype(&NvFlexShutdown)>(module,"NvFlexShutdown");auto getContext=api<decltype(&NvFlexGetDeviceAndContext)>(module,"NvFlexGetDeviceAndContext");
        for(int compute:{1,2}){
            NvFlexInitDesc setup{-1,false,nullptr,nullptr,nullptr,true,static_cast<NvFlexComputeType>(compute)};auto library=init(120,nullptr,&setup);require(library!=nullptr,"Init");void* device=nullptr;void* context=nullptr;getContext(library,&device,&context);auto c=static_cast<NvFlex::Context*>(context);
            NvFlex::ComputeShaderDesc sd{};sd.cs=original.data();sd.cs_length=original.size();sd.label=L"OriginalShapeKernel";sd.NvAPI_Slot=~0u;auto leftShader=c->createComputeShader(&sd);sd.cs=specialized.data();sd.cs_length=specialized.size();sd.label=L"PlaneSpecialization";auto rightShader=c->createComputeShader(&sd);
            NvFlex::ConstantBufferDesc cd{};cd.dim=1;cd.stride=512;cd.uploadAccess=true;auto constants=c->createConstantBuffer(&cd);
            const unsigned capacity=257;
            for(unsigned active:{0u,1u,127u,128u,129u,257u})for(unsigned planes:{0u,1u,3u,8u})for(unsigned maximum:{1u,6u,16u}){
                nvflex_recovered::KernelParams params{};params.kNumParticles=int(active);params.kMaxParticles=capacity;params.kNumPlanes=int(planes);params.kMaxContactsPerParticle=int(maximum);params.kNumShapes=0;params.kCollisionDistance=.125f;params.kCollisionThreshold=.03125f;
                const nvflex_recovered::float4 equations[8]={{0,1,0,0},{1,0,0,-.2f},{0,0,1,.1f},{0,-1,0,1},{-1,0,0,.25f},{0,0,-1,.3f},{.57735026f,.57735026f,.57735026f,-.3f},{-.57735026f,.57735026f,-.57735026f,.3f}};
                std::copy(std::begin(equations),std::end(equations),std::begin(params.kPlanes));auto cp=c->map(constants);require(cp!=nullptr,"Constant map");std::memcpy(cp,&params,sizeof(params));c->unmap(constants);
                std::vector<nvflex_recovered::float4> positions(capacity);std::vector<unsigned> counts(capacity),payload(capacity*maximum*4,0x3f123456u),speed(capacity*maximum*4,0x40123456u);
                for(unsigned i=0;i<capacity;++i){float boundary=.15625f;float y=i%3==0?boundary:i%3==1?std::nextafter(boundary,0.f):std::nextafter(boundary,1.f);positions[i]={float(int(i%11)-5)*.13f,y,float(int(i%13)-6)*.09f,1};counts[i]=i%3==0?0:i%3==1?maximum-1:maximum;}
                auto make=[&](unsigned count,unsigned stride,const void* data){NvFlex::BufferDesc d{};d.dim=count;d.stride=stride;d.bufferType=NvFlex::eBuffer|NvFlex::eUAV_SRV|NvFlex::eStage|NvFlex::eStructured;d.data=data;return c->createBuffer(&d);};
                auto position=make(capacity,16,positions.data());std::array<NvFlex::Buffer*,3> left={make(capacity,4,counts.data()),make(capacity*maximum,16,payload.data()),make(capacity*maximum,16,speed.data())},right={make(capacity,4,counts.data()),make(capacity*maximum,16,payload.data()),make(capacity*maximum,16,speed.data())};
                auto dispatch=[&](NvFlex::ComputeShader* shader,const auto& outputs){NvFlex::DispatchParams d{};d.shader=shader;d.rootConstantBuffer=constants;d.gridDim={3,1,1};d.readOnly[7]=position->getResource();for(unsigned i=0;i<3;++i)d.readWrite[i]=outputs[i]->getResourceRW();c->dispatch(&d);};dispatch(leftShader,left);dispatch(rightShader,right);
                for(unsigned i=0;i<3;++i){unsigned words=i?capacity*maximum*4:capacity;require(read(c,left[i],words)==read(c,right[i],words),"Original/specialized contact bytes differ");delete left[i];delete right[i];}delete position;++cases;
            }
            delete constants;delete leftShader;delete rightShader;shutdown(library);
        }
        FreeLibrary(module);std::ofstream out{std::filesystem::path(argv[4])};out<<"{\"status\":\"PASS\",\"cases\":"<<cases<<",\"counts_planes_velocities_bit_exact\":true,\"scope\":\"D3D11/D3D12; zero/partial/group-boundary active counts; 0/1/3/8 planes; contact capacities 1/6/16; pre-existing rows; near-threshold ULP positions; untouched-tail sentinels\"}\n";std::cout<<cases<<" kernel differential cases PASS\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
