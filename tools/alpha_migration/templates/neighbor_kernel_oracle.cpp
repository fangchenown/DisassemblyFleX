#include "NvFlex.h"
#include "dx/context/Context.h"
#include "recovered/FlexLayouts.hpp"
#include <windows.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <numeric>
#include <stdexcept>
#include <vector>
static void require(bool x,const char* why){if(!x)throw std::runtime_error(why);}
template<class T>static T api(HMODULE m,const char* name){auto p=GetProcAddress(m,name);require(p!=nullptr,name);return reinterpret_cast<T>(p);}
static std::vector<char> file(const wchar_t* p){std::ifstream in{std::filesystem::path(p),std::ios::binary};require(in.good(),"Shader file");return {std::istreambuf_iterator<char>(in),std::istreambuf_iterator<char>()};}
static std::vector<unsigned> read(NvFlex::Context* c,NvFlex::Buffer* b,unsigned words){c->download(b);auto p=static_cast<unsigned*>(c->map(b,NvFlex::eMapRead,true));require(p!=nullptr,"Output map");std::vector<unsigned> result(p,p+words);c->unmap(b);return result;}
int wmain(int argc,wchar_t** argv){
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);if(argc!=5)return 64;
    try{
        auto original=file(argv[2]),candidate=file(argv[3]);auto module=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(module!=nullptr,"DLL");auto init=api<decltype(&NvFlexInit)>(module,"NvFlexInit");auto shutdown=api<decltype(&NvFlexShutdown)>(module,"NvFlexShutdown");auto get=api<decltype(&NvFlexGetDeviceAndContext)>(module,"NvFlexGetDeviceAndContext");unsigned cases=0,saturatedChecks=0;
        for(int compute:{1,2}){
            NvFlexInitDesc setup{-1,false,nullptr,nullptr,nullptr,true,static_cast<NvFlexComputeType>(compute)};auto lib=init(120,nullptr,&setup);require(lib!=nullptr,"Initialize");void* device=nullptr;void* context=nullptr;get(lib,&device,&context);auto c=static_cast<NvFlex::Context*>(context);
            NvFlex::ComputeShaderDesc sd{};sd.cs=original.data();sd.cs_length=original.size();sd.label=L"OriginalNeighbors";sd.NvAPI_Slot=~0u;auto leftShader=c->createComputeShader(&sd);sd.cs=candidate.data();sd.cs_length=candidate.size();sd.label=L"DerivedNeighbors";auto rightShader=c->createComputeShader(&sd);
            NvFlex::ConstantBufferDesc cd{};cd.dim=1;cd.stride=512;cd.uploadAccess=true;auto constant=c->createConstantBuffer(&cd);
            auto make=[&](unsigned count,unsigned stride,const void* data,bool typed=false){NvFlex::BufferDesc d{};d.dim=count;d.stride=stride;d.data=data;d.bufferType=NvFlex::eBuffer|NvFlex::eUAV_SRV|NvFlex::eStage|(typed?0:NvFlex::eStructured);if(typed)d.format=eNvFlexFormat_r32_uint;return c->createBuffer(&d);};
            const unsigned restCapacity=1024,cells=1u<<21;std::vector<nvflex_recovered::float4> rest(restCapacity);
            for(unsigned i=0;i<restCapacity;++i)rest[i]={float(i%17)*.1f,float(i/17%7)*.04f,float(i%5)*.11f,1};
            auto restBuffer=make(restCapacity,16,rest.data());nvflex_recovered::float3 bounds[2]={{-1,-1,-1},{130,3,3}};auto boundsBuffer=make(2,12,bounds);
            for(unsigned n:{0u,1u,17u,129u,257u})for(unsigned layout=0;layout<3;++layout){
                unsigned size=std::max(1u,n),stride=std::max(256u,(n+255u)&~255u);std::vector<nvflex_recovered::float4> positions(size),sorted(size);std::vector<unsigned> keys(size),order(size),mapping(size),starts(cells,0),ends(cells,0);
                for(unsigned i=0;i<n;++i){
                    if(layout==0)positions[i]={.125f,.125f,.125f,1};
                    else if(layout==1)positions[i]={float(i%3==0?128:i%3==1?0:1)+.125f,float(i%5)*.17f,float(i%4)*.2f,1};
                    else {const float x[6]={0,.5f,std::nextafter(.5f,0.f),std::nextafter(.5f,1.f),-0.f,128.5f};positions[i]={x[i%6],float(i%3)*.1f,0,1};}
                    int x=int(positions[i].x+1),y=int(positions[i].y+1),z=int(positions[i].z+1);keys[i]=(unsigned(x)&127u)|((unsigned(y)&127u)<<7)|((unsigned(z)&127u)<<14);order[i]=i;
                }
                std::stable_sort(order.begin(),order.begin()+n,[&](unsigned x,unsigned y){return keys[x]<keys[y];});
                for(unsigned i=0;i<n;++i){sorted[i]=positions[order[i]];mapping[i]=(order[i]*37u)%restCapacity;unsigned key=keys[order[i]];if(i==0||key!=keys[order[i-1]])starts[key]=i;ends[key]=i+1;}
                auto positionBuffer=make(size,16,sorted.data()),mapBuffer=make(size,4,mapping.data(),true),startBuffer=make(cells,4,starts.data()),endBuffer=make(cells,4,ends.data());
                for(unsigned phaseKind=0;phaseKind<3;++phaseKind){
                    std::vector<unsigned> phases(size,0);for(unsigned i=0;i<n;++i){unsigned source=order[i];phases[i]=phaseKind==0?0x00100000u:phaseKind==1?0x00300000u:(source%3u)|(source%2u?0u:0x00100000u)|(source%5u?0u:0x00200000u)|(source%7u?0u:0x00400000u);}
                    auto phaseBuffer=make(size,4,phases.data());
                    for(unsigned maximum:{0u,1u,4u,32u,96u}){
                        nvflex_recovered::KernelParams params{};params.kNumParticles=int(n);params.kNumParticlesAligned=int(stride);params.kRadiusSq=.25f;params.kInvCellEdge=1;params.kCollideParticlesRadiusSq=.25f;params.kMaxNeighborsPerParticle=int(maximum);auto p=c->map(constant);std::memcpy(p,&params,sizeof(params));c->unmap(constant);
                        unsigned words=stride*std::max(1u,maximum);std::vector<unsigned> initial(words,0x7b7b7b7bu),initialCounts(stride,0x72727272u);auto leftRows=make(words,4,initial.data()),rightRows=make(words,4,initial.data()),leftCounts=make(stride,4,initialCounts.data()),rightCounts=make(stride,4,initialCounts.data());
                        auto dispatch=[&](NvFlex::ComputeShader* shader,NvFlex::Buffer* rows,NvFlex::Buffer* counts){NvFlex::DispatchParams d{};d.shader=shader;d.rootConstantBuffer=constant;d.gridDim={std::max(1u,(n+255u)/256u),1,1};NvFlex::Buffer* inputs[]={startBuffer,endBuffer,mapBuffer,positionBuffer,restBuffer,phaseBuffer,boundsBuffer};for(unsigned i=0;i<7;++i)d.readOnly[i]=inputs[i]->getResource();d.readWrite[0]=rows->getResourceRW();d.readWrite[1]=counts->getResourceRW();c->dispatch(&d);};
                        dispatch(leftShader,leftRows,leftCounts);dispatch(rightShader,rightRows,rightCounts);auto lc=read(c,leftCounts,stride),rc=read(c,rightCounts,stride);require(lc==rc,"Neighbor counts differ");require(read(c,leftRows,words)==read(c,rightRows,words),"Neighbor row ordering/payload/sentinel differs");
                        if(layout==0&&phaseKind==0)for(unsigned i=0;i<n;++i){require(lc[i]==std::min(n-1,maximum),"Original count is not the bounded contract");++saturatedChecks;}
                        delete leftRows;delete rightRows;delete leftCounts;delete rightCounts;++cases;
                    }
                    delete phaseBuffer;
                }
                delete positionBuffer;delete mapBuffer;delete startBuffer;delete endBuffer;
            }
            delete restBuffer;delete boundsBuffer;delete constant;delete leftShader;delete rightShader;shutdown(lib);
        }
        FreeLibrary(module);std::ofstream out{std::filesystem::path(argv[4])};out<<"{\"status\":\"PASS\",\"cases\":"<<cases<<",\"bounded_original_count_checks\":"<<saturatedChecks<<",\"full_neighbor_rows_counts_and_sentinels_bit_exact\":true,\"scope\":\"D3D11/D3D12; phase/self/rest/current predicates; near-radius ULPs; hash aliases; nonidentity original map; zero/partial/overflow rows\"}\n";std::cout<<cases<<" neighbor cases PASS\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
