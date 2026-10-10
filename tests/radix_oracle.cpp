#include "NvFlex.h"
#include "solver/RadixSort.hpp"
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
template<class T>T proc(HMODULE module,const char* name){auto p=GetProcAddress(module,name);if(!p)throw std::runtime_error(name);return reinterpret_cast<T>(p);}
static void require(bool value,const char* name){if(!value)throw std::runtime_error(name);}
static void error(NvFlexErrorSeverity,const char* text,const char*,int){std::cerr<<text<<"\n";}
static std::vector<unsigned> read(NvFlex::Context* context,NvFlex::Buffer* buffer,unsigned count){
    NvFlex::BufferDesc d{};d.dim=count;d.stride=4;d.bufferType=20;auto host=context->createBuffer(&d);
    context->copyToHost(host,0,buffer,0,count*4);auto p=static_cast<unsigned*>(context->map(host,NvFlex::eMapRead,true));require(p!=nullptr,"Map output");
    std::vector<unsigned> result(p,p+count);context->unmap(host);delete host;return result;
}
static std::vector<unsigned> run(const wchar_t* path,unsigned count){
    HMODULE module=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(module!=nullptr,"Load DLL");
    auto init=proc<decltype(&NvFlexInit)>(module,"NvFlexInit");auto shutdown=proc<decltype(&NvFlexShutdown)>(module,"NvFlexShutdown");auto create=proc<decltype(&NvFlexCreateSolver)>(module,"NvFlexCreateSolver");auto destroy=proc<decltype(&NvFlexDestroySolver)>(module,"NvFlexDestroySolver");
    auto get=proc<decltype(&NvFlexGetDeviceAndContext)>(module,"NvFlexGetDeviceAndContext");NvFlexInitDesc id{-1,false,nullptr,nullptr,nullptr,true,eNvFlexD3D11};auto library=init(120,error,&id);require(library!=nullptr,"Init DLL");
    NvFlexSolverDesc sd{eNvFlexFeatureModeDefault,int(count),0,32,6};auto solver=create(library,&sd);require(solver!=nullptr,"Create solver");
    NvFlex::Device* device=nullptr;NvFlex::Context* context=nullptr;get(library,reinterpret_cast<void**>(&device),reinterpret_cast<void**>(&context));
    NvFlex::RadixSort* sort=nullptr;std::memcpy(&sort,reinterpret_cast<char*>(solver)+0xec0,8);require(sort!=nullptr,"Radix object");auto input=sort->getInputBuffer();
    unsigned capacity=input.key->m_desc.dim;std::vector<unsigned> keys(capacity,0xffffffff),values(capacity,0xffffffff);std::mt19937 random(0x240ac);
    std::vector<std::pair<unsigned,unsigned>> expected;for(unsigned i=0;i<count;++i){keys[i]=random()&0x7ffu;values[i]=i;expected.push_back({keys[i],i});}
    std::stable_sort(expected.begin(),expected.end(),[](auto a,auto b){return a.first<b.first;});
    auto upload=[&](NvFlex::Buffer* gpu,const std::vector<unsigned>& data){NvFlex::BufferDesc d{};d.dim=capacity;d.stride=4;d.bufferType=20;d.data=data.data();auto host=context->createBuffer(&d);context->copyToDevice(gpu,0,host,0,capacity*4,NvFlex::eDownloadBuffer);delete host;};
    upload(input.key,keys);upload(input.val,values);NvFlex::RadixSortParams params{count,(count+1023)/1024,24};sort->sort(context,&params,nullptr);auto output=sort->getOutputBuffer();auto outKeys=read(context,output.key,count),outValues=read(context,output.val,count);
    for(unsigned i=0;i<count;++i)require(outKeys[i]==expected[i].first&&outValues[i]==expected[i].second,"Stable radix output");
    // Repeat on the same object to check front/back ownership and counter swaps.
    input=sort->getInputBuffer();upload(input.key,keys);upload(input.val,values);sort->sort(context,&params,nullptr);output=sort->getOutputBuffer();require(read(context,output.key,count)==outKeys&&read(context,output.val,count)==outValues,"Repeated radix output");
    std::vector<unsigned> result=outKeys;result.insert(result.end(),outValues.begin(),outValues.end());destroy(solver);shutdown(library);FreeLibrary(module);return result;
}
int wmain(int argc,wchar_t** argv){try{
    if(argc!=4)throw std::runtime_error("reference candidate output.json");std::ofstream report{std::filesystem::path(argv[3])};report<<"{\"cases\":[";bool comma=false;
    for(unsigned n:{1u,4u,63u,1023u,1024u,1025u,2049u,8193u}){auto a=run(argv[1],n),b=run(argv[2],n);require(a==b,"Reference/candidate mismatch");
        report<<(comma?",":"")<<"{\"count\":"<<n<<",\"equal\":true,\"stable\":true,\"repeat\":true}";comma=true;report.flush();std::cout<<"radix "<<n<<" PASS\n"<<std::flush;}
    report<<"],\"status\":\"PASS\"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
