// Oracle-only executable. Forwards to the reference DLL to collect evidence.
// This file is deliberately excluded from NvFlexReconstructed sources.
#include "NvFlex.h"
#include "dx/context/Device.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <cstring>
#include <stdexcept>
using namespace NvFlex;
namespace fs=std::filesystem;
namespace NvFlex {Context::Context():mEnableTimers(false){} Context::~Context()=default;}
struct Trace {
    struct Mapping {void* pointer;size_t bytes;};
    fs::path root;std::ofstream output;std::string phase="setup";uintptr_t moduleBase;unsigned serial=0,nextId=1;
    std::map<const void*,unsigned> ids;std::map<const void*,size_t> sizes;std::map<const void*,Mapping> mappings;
    Trace(fs::path directory,uintptr_t base):root(directory),moduleBase(base){fs::create_directories(root);output.open(root/"context.jsonl");}
    unsigned id(const void* pointer){if(!pointer)return 0;auto p=ids.find(pointer);if(p!=ids.end())return p->second;auto value=nextId++;ids[pointer]=value;return value;}
    void line(const std::string& body){output<<"{\"sequence\":"<<serial++<<",\"phase\":"<<std::quoted(phase)<<","<<body<<"}\n";output.flush();}
    void operation(const char* name){line("\"op\":"+quoted(name));}
    static std::string quoted(const std::string& s){std::ostringstream out;out<<std::quoted(s);return out.str();}
    void adopt(Buffer* buffer,const char* label){if(!buffer)return;unsigned value=nextId++;ids[buffer]=value;ids[buffer->getResource()]=value;ids[buffer->getResourceRW()]=value;
        const auto& d=buffer->m_desc;sizes[buffer]=size_t(d.dim)*d.stride;
        line("\"op\":\"buffer\",\"id\":"+std::to_string(value)+",\"label\":"+quoted(label)+",\"dim\":"+std::to_string(d.dim)+",\"stride\":"+std::to_string(d.stride)+",\"flags\":"+std::to_string(d.bufferType)+",\"format\":"+std::to_string(d.format));}
    void adopt(ConstantBuffer* buffer,const char* label,const ConstantBufferDesc* creation=nullptr){if(!buffer)return;unsigned value=nextId++;ids[buffer]=value;const auto& d=creation?*creation:buffer->m_desc;sizes[buffer]=size_t(d.stride)*d.dim;
        line("\"op\":\"constant\",\"id\":"+std::to_string(value)+",\"label\":"+quoted(label)+",\"stride\":"+std::to_string(d.stride)+",\"dim\":"+std::to_string(d.dim)+",\"upload\":"+(d.uploadAccess?"true":"false"));}
    void mapped(Buffer* object,void* pointer){mappings[object]={pointer,sizes[object]};}
    void mapped(ConstantBuffer* object,void* pointer){mappings[object]={pointer,sizes[object]};}
    void initial(const void* object,const void* pointer,size_t bytes){mappings[object]={const_cast<void*>(pointer),bytes};capture(object);}
    void arguments(const char* name,std::initializer_list<unsigned long long> values){std::ostringstream text;text<<"\"op\":\"arguments\",\"method\":"<<quoted(name)<<",\"values\":[";bool first=true;for(auto value:values){text<<(first?"":",")<<value;first=false;}text<<"]";line(text.str());}
    void capture(const void* object){auto found=mappings.find(object);if(found==mappings.end()||!found->second.pointer)return;
        auto name="map_"+std::to_string(serial)+"_id"+std::to_string(id(object))+".bin";std::ofstream file(root/name,std::ios::binary);file.write(static_cast<const char*>(found->second.pointer),found->second.bytes);
        line("\"op\":\"mapped_bytes\",\"id\":"+std::to_string(id(object))+",\"bytes\":"+std::to_string(found->second.bytes)+",\"file\":"+quoted(name));mappings.erase(found);}
    void shader(ComputeShader* shader){if(!shader)return;std::string label;for(auto p=shader->m_desc.label;p&&*p;++p)label.push_back(static_cast<char>(*p));
        line("\"op\":\"shader\",\"id\":"+std::to_string(id(shader))+",\"label\":"+quoted(label)+",\"rva\":"+std::to_string(reinterpret_cast<uintptr_t>(shader->m_desc.cs)-moduleBase)+",\"bytes\":"+std::to_string(shader->m_desc.cs_length));}
    void dispatch(const char* operation,const DispatchParams* params){shader(params->shader);std::ostringstream text;text<<"\"op\":"<<quoted(operation)<<",\"shader\":"<<id(params->shader)<<",\"grid\":["<<params->gridDim.x<<","<<params->gridDim.y<<","<<params->gridDim.z<<"],\"cb\":["<<id(params->rootConstantBuffer)<<","<<id(params->secondConstantBuffer)<<"],\"reads\":[";
        for(unsigned i=0;i<32;++i)text<<(i?",":"")<<id(params->readOnly[i]);text<<"],\"writes\":[";for(unsigned i=0;i<8;++i)text<<(i?",":"")<<id(params->readWrite[i]);text<<"],\"indirect\":"<<id(params->IndirectLaunchArgs);line(text.str());}
    void field(const char* name,unsigned offset,void* pointer,const char* kind){line("\"op\":\"solver_field\",\"name\":"+quoted(name)+",\"offset\":"+std::to_string(offset)+",\"id\":"+std::to_string(id(pointer))+",\"kind\":"+quoted(kind));}
    void scalar(const char* name,unsigned offset,unsigned bits,const char* type){line("\"op\":\"solver_scalar\",\"name\":"+quoted(name)+",\"offset\":"+std::to_string(offset)+",\"bits\":"+std::to_string(bits)+",\"type\":"+quoted(type));}
};
#include "TraceContext.generated.hpp"
template<class T>T proc(HMODULE module,const char* name){auto p=GetProcAddress(module,name);if(!p)throw std::runtime_error(name);return reinterpret_cast<T>(p);}
static void error(NvFlexErrorSeverity severity,const char* text,const char*,int){std::cerr<<"Flex "<<severity<<": "<<text<<"\n";}
static void fields(Trace& trace,NvFlexSolver* solver){auto base=reinterpret_cast<const char*>(solver);
#include "TraceSolverFields.generated.hpp"
}
int wmain(int argc,wchar_t** argv){try{
    if(argc<3)throw std::runtime_error("reference.dll output_directory [capacity] [feature] [diffuse] [params.bin] [steps]");
    HMODULE module=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)throw std::runtime_error("Load reference");
    auto init=proc<decltype(&NvFlexInit)>(module,"NvFlexInit");auto shutdown=proc<decltype(&NvFlexShutdown)>(module,"NvFlexShutdown");
    auto create=proc<decltype(&NvFlexCreateSolver)>(module,"NvFlexCreateSolver");auto destroy=proc<decltype(&NvFlexDestroySolver)>(module,"NvFlexDestroySolver");
    auto defaults=proc<decltype(&NvFlexSetSolverDescDefaults)>(module,"NvFlexSetSolverDescDefaults");auto getParams=proc<decltype(&NvFlexGetParams)>(module,"NvFlexGetParams");
    NvFlexInitDesc desc{-1,false,nullptr,nullptr,nullptr,true,eNvFlexD3D11};auto library=init(120,error,&desc);if(!library)throw std::runtime_error("Initialize reference");
    auto contextAddress=reinterpret_cast<Context**>(reinterpret_cast<char*>(library)+0x10);auto original=*contextAddress;
    Trace trace(fs::path(argv[2]),reinterpret_cast<uintptr_t>(module));TracingContext proxy(original,trace);
    // Library-owned buffers are allocated before the proxy is attached.
    for(unsigned offset:{0x2e8u,0x308u,0x348u,0x368u}){Buffer* p=nullptr;std::memcpy(&p,reinterpret_cast<char*>(library)+offset,8);trace.adopt(p,("library+"+std::to_string(offset)).c_str());}
    for(unsigned offset:{0x158u,0x170u,0x330u}){ConstantBuffer* p=nullptr;std::memcpy(&p,reinterpret_cast<char*>(library)+offset+16,8);trace.adopt(p,("library+"+std::to_string(offset)).c_str(),reinterpret_cast<const ConstantBufferDesc*>(reinterpret_cast<char*>(library)+offset));}
    *contextAddress=&proxy;trace.phase="create_solver";NvFlexSolverDesc sd{};defaults(&sd);sd.maxParticles=argc>3?_wtoi(argv[3]):64;sd.featureMode=argc>4?NvFlexFeatureMode(_wtoi(argv[4])):eNvFlexFeatureModeDefault;sd.maxDiffuseParticles=argc>5?_wtoi(argv[5]):0;
    auto solver=create(library,&sd);if(!solver)throw std::runtime_error("Create reference solver");
    fields(trace,solver);NvFlexParams params{};getParams(solver,&params);std::ofstream(trace.root/"default_params.bin",std::ios::binary).write(reinterpret_cast<const char*>(&params),sizeof(params));
    if(argc>6){std::ifstream input(fs::path(argv[6]),std::ios::binary);input.read(reinterpret_cast<char*>(&params),sizeof(params));if(input.gcount()!=sizeof(params))throw std::runtime_error("Input parameter bytes");
        if(argc>7)params.numPlanes=0;
        trace.phase="set_params";proc<decltype(&NvFlexSetParams)>(module,"NvFlexSetParams")(solver,&params);fields(trace,solver);}
    if(argc>7){
        const int count=std::min(argc>8?_wtoi(argv[8]):4,sd.maxParticles);const int steps=_wtoi(argv[7]);
        std::ofstream(trace.root/"input_params.bin",std::ios::binary).write(reinterpret_cast<const char*>(&params),sizeof(params));
        auto alloc=proc<decltype(&NvFlexAllocBuffer)>(module,"NvFlexAllocBuffer");auto free=proc<decltype(&NvFlexFreeBuffer)>(module,"NvFlexFreeBuffer");
        auto map=proc<decltype(&NvFlexMap)>(module,"NvFlexMap");auto unmap=proc<decltype(&NvFlexUnmap)>(module,"NvFlexUnmap");
        trace.phase="input_upload";
        auto particles=alloc(library,count,16,eNvFlexBufferHost),velocities=alloc(library,count,12,eNvFlexBufferHost),phases=alloc(library,count,4,eNvFlexBufferHost);
        float* positions=static_cast<float*>(map(particles,0));for(int i=0;i<count;++i){positions[4*i]=0.2f+0.2f*i;positions[4*i+1]=1.0f;positions[4*i+2]=0.4f;positions[4*i+3]=1.0f;}unmap(particles);
        std::memset(map(velocities,0),0,count*12);unmap(velocities);std::memset(map(phases,0),0,count*4);unmap(phases);
        NvFlexCopyDesc range{0,0,count};proc<decltype(&NvFlexSetParticles)>(module,"NvFlexSetParticles")(solver,particles,&range);
        proc<decltype(&NvFlexSetVelocities)>(module,"NvFlexSetVelocities")(solver,velocities,&range);
        proc<decltype(&NvFlexSetPhases)>(module,"NvFlexSetPhases")(solver,phases,&range);
        proc<decltype(&NvFlexSetActiveCount)>(module,"NvFlexSetActiveCount")(solver,count);
        auto update=proc<decltype(&NvFlexUpdateSolver)>(module,"NvFlexUpdateSolver");
        for(int step=0;step<steps;++step){trace.phase="update_"+std::to_string(step);update(solver,1.0f/60.0f,2,false);fields(trace,solver);}
        trace.phase="outputs";proc<decltype(&NvFlexGetParticles)>(module,"NvFlexGetParticles")(solver,particles,&range);proc<decltype(&NvFlexGetVelocities)>(module,"NvFlexGetVelocities")(solver,velocities,&range);
        void* p=map(particles,0);std::ofstream(trace.root/"positions.bin",std::ios::binary).write(static_cast<const char*>(p),count*16);unmap(particles);
        p=map(velocities,0);std::ofstream(trace.root/"velocities.bin",std::ios::binary).write(static_cast<const char*>(p),count*12);unmap(velocities);
        free(particles);free(velocities);free(phases);
    }
    trace.phase="destroy_solver";destroy(solver);*contextAddress=original;shutdown(library);
    std::ofstream(trace.root/"complete.json")<<"{\"capacity\":"<<sd.maxParticles<<",\"feature\":"<<int(sd.featureMode)<<",\"diffuse\":"<<sd.maxDiffuseParticles<<",\"events\":"<<trace.serial<<"}\n";
    std::cout<<"Reference solver trace complete: "<<trace.serial<<" events\n";FreeLibrary(module);return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
