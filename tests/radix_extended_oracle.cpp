#include "NvFlex.h"
#include "solver/RadixSort.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
template<class T>T proc(HMODULE module,const char* name){auto p=GetProcAddress(module,name);if(!p)throw std::runtime_error(name);return reinterpret_cast<T>(p);}
static void require(bool v,const char* text){if(!v)throw std::runtime_error(text);}
static std::vector<unsigned> read(NvFlex::Context* c,NvFlex::Buffer* b,unsigned size){
    NvFlex::BufferDesc d{};d.dim=size;d.stride=4;d.bufferType=20;auto h=c->createBuffer(&d);c->copyToHost(h,0,b,0,size*4);
    auto p=static_cast<unsigned*>(c->map(h,NvFlex::eMapRead,true));require(p!=nullptr,"read map");std::vector<unsigned> out(p,p+size);c->unmap(h);delete h;return out;
}
static std::vector<std::vector<unsigned>> run(const wchar_t* path,int compute,unsigned capacity){
    auto m=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(m!=nullptr,"Load DLL");
    auto init=proc<decltype(&NvFlexInit)>(m,"NvFlexInit");auto shutdown=proc<decltype(&NvFlexShutdown)>(m,"NvFlexShutdown");
    auto create=proc<decltype(&NvFlexCreateSolver)>(m,"NvFlexCreateSolver");auto destroy=proc<decltype(&NvFlexDestroySolver)>(m,"NvFlexDestroySolver");
    auto get=proc<decltype(&NvFlexGetDeviceAndContext)>(m,"NvFlexGetDeviceAndContext");
    NvFlexInitDesc id{-1,false,nullptr,nullptr,nullptr,true,static_cast<NvFlexComputeType>(compute)};auto lib=init(120,nullptr,&id);require(lib!=nullptr,"Init");
    NvFlexSolverDesc desc{eNvFlexFeatureModeDefault,int(capacity),0,1,1};auto solver=create(lib,&desc);require(solver!=nullptr,"solver");
    void* device=nullptr;void* context=nullptr;get(lib,&device,&context);auto c=static_cast<NvFlex::Context*>(context);
    NvFlex::RadixSort* sorter=nullptr;std::memcpy(&sorter,reinterpret_cast<char*>(solver)+0xec0,8);require(sorter!=nullptr,"radix pointer");
    auto first=sorter->getInputBuffer();capacity=first.key->m_desc.dim;
    auto upload=[&](NvFlex::Buffer* b,const std::vector<unsigned>& data){NvFlex::BufferDesc d{};d.dim=capacity;d.stride=4;d.bufferType=20;d.data=data.data();auto h=c->createBuffer(&d);c->copyToDevice(b,0,h,0,capacity*4,NvFlex::eDownloadBuffer);delete h;};
    std::vector<unsigned> seed(capacity,0xffffffffu);upload(first.key,seed);upload(first.val,seed);
    NvFlex::RadixSortParams discover{1024,1,32};sorter->sort(c,&discover,nullptr);auto second=sorter->getInputBuffer();require(first.key!=second.key,"single-block swap");
    std::vector<std::pair<unsigned,unsigned>> cases;
    if(capacity<=131072){
        for(unsigned n:{0u,1u,1024u,1025u,2048u,3072u,8192u,8193u,32768u,65536u,131072u})
            for(unsigned bits:{0u,4u,16u,20u,24u,28u,32u})if(n<=capacity)cases.push_back({n,bits});
    }else cases={{capacity,24},{capacity,32},{2048,24},{capacity-1024,32}};
    std::vector<std::vector<unsigned>> result;std::mt19937 rng(0x82379);
    unsigned serial=0;
    for(auto item:cases){
        unsigned count=item.first,bits=item.second;auto input=sorter->getInputBuffer();auto other=input.key==first.key?second:first;
        std::vector<unsigned> keys(capacity,0xffffffffu),values(capacity,0xcafebabeu),backKeys(capacity,0xa5a5a5a5u),backValues(capacity,0x5a5a5a5au);
        std::vector<std::pair<unsigned,unsigned>> expected;expected.reserve(count);
        for(unsigned i=0;i<count;++i){keys[i]=(serial%3==0?unsigned(rng()):serial%3==1?unsigned(rng())&255u:0x80ffff55u);values[i]=i;expected.push_back({keys[i],i});}
        upload(input.key,keys);upload(input.val,values);upload(other.key,backKeys);upload(other.val,backValues);
        unsigned usedBits=count&&count<=1024?32:bits;unsigned mask=usedBits==32?~0u:usedBits==0?0u:(1u<<usedBits)-1;
        std::stable_sort(expected.begin(),expected.end(),[&](auto x,auto y){return (x.first&mask)<(y.first&mask);});
        NvFlex::RadixSortParams params{count,(count+1023)/1024,bits};sorter->sort(c,&params,nullptr);auto output=sorter->getOutputBuffer();auto outKeys=read(c,output.key,capacity),outValues=read(c,output.val,capacity);
        for(unsigned i=0;i<count;++i)require(outKeys[i]==expected[i].first&&outValues[i]==expected[i].second,"stable CPU ordering");
        std::vector<unsigned> snapshot{unsigned(output.key==first.key),count,bits};
        for(auto b:{first.key,first.val,second.key,second.val}){auto data=read(c,b,capacity);snapshot.insert(snapshot.end(),data.begin(),data.end());}
        result.push_back(std::move(snapshot));++serial;
    }
    destroy(solver);shutdown(lib);FreeLibrary(m);return result;
}
int wmain(int argc,wchar_t** argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);require(argc==4,"reference candidate output");unsigned cases=0,backendMask=0;
    for(int compute:{1,2})for(unsigned capacity:{131072u,1048576u}){
        const char* backend=std::getenv("DF_RADIX_ORACLE_BACKEND");if(backend&&std::atoi(backend)!=compute)continue;
        const char* limit=std::getenv("DF_RADIX_ORACLE_CAPACITY");if(limit&&unsigned(std::atoi(limit))!=capacity)continue;
        backendMask|=1u<<compute;
        std::cout<<"reference backend "<<compute<<" capacity "<<capacity<<" begin\n"<<std::flush;
        auto left=run(argv[1],compute,capacity);
        std::cout<<"candidate backend "<<compute<<" capacity "<<capacity<<" begin\n"<<std::flush;
        auto right=run(argv[2],compute,capacity);require(left==right,"full physical buffers/front ownership differ");cases+=unsigned(left.size());
        std::cout<<"backend "<<compute<<" capacity "<<capacity<<" cases "<<left.size()<<" PASS\n"<<std::flush;
    }
    require(cases>0,"No selected cases");
    std::ofstream out{std::filesystem::path(argv[3])};out<<"{\"status\":\"PASS\",\"cases\":"<<cases<<",\"both_backends\":"<<(backendMask==6?"true":"false")<<",\"backend_mask\":"<<backendMask<<",\"stable_cpu_order\":true,\"full_physical_front_back_and_tails_equal\":true}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
