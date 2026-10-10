#pragma once
#include <cstdint>
#include <vector>
#include <cstring>
#include <nvtx3/nvToolsExt.h>

static bool probeCpu=false,probeNvtx=false,probePrewait=false;
static bool probeNoUpload=false,probeResident=false,probeCopies=false;
static const char* probeExperiment="default";
static std::ofstream probeOutput;
struct ProbeStamp {double wall=0;uint64_t cycles=0,thread=0,process=0;};
struct ProbeRow {const char* name;ProbeStamp a,b;};
static std::vector<ProbeRow> probeRows;
static uint64_t FileTicks(FILETIME f){return (uint64_t(f.dwHighDateTime)<<32)|f.dwLowDateTime;}
uint64_t ApiCpuCycles(){ULONG64 x=0;QueryThreadCycleTime(GetCurrentThread(),&x);return x;}
static ProbeStamp ProbeNow(){
    ProbeStamp s;
    if(probeCpu){
        FILETIME create,exit,kernel,user;
        GetThreadTimes(GetCurrentThread(),&create,&exit,&kernel,&user);s.thread=FileTicks(kernel)+FileTicks(user);
        GetProcessTimes(GetCurrentProcess(),&create,&exit,&kernel,&user);s.process=FileTicks(kernel)+FileTicks(user);
        s.cycles=ApiCpuCycles();
    }
    s.wall=Ms();return s;
}
struct ProbeScope {
    const char* name;ProbeStamp a;bool enabled;
    explicit ProbeScope(const char* n):name(n),enabled(probeCpu||probeNvtx){
        if(enabled){if(probeNvtx)nvtxRangePushA(n);a=ProbeNow();}
    }
    ~ProbeScope(){if(enabled){auto b=ProbeNow();if(probeNvtx)nvtxRangePop();if(probeCpu)probeRows.push_back({name,a,b});}}
};
static void InitProbes(int mode,const std::string& root,int scene){
    probeCpu=(mode&4)!=0;probeNvtx=getenv("DEMO_NVTX")!=nullptr;
    const char* experiment=getenv("DEMO_EXPERIMENT");if(experiment)probeExperiment=experiment;
    probePrewait=false;
    probeNoUpload=false;
    probeResident=false;
    probeCopies=false;
    if((probeNoUpload||probeResident)&&scene!=47&&scene!=52){fprintf(stderr,"resident diagnostic restricted to reviewed scenes47/52\n");exit(81);}
    if(strcmp(probeExperiment,"default")&& !probePrewait&&!probeNoUpload&&!probeResident){fprintf(stderr,"unknown diagnostic experiment\n");exit(82);}
    probeRows.reserve(24);
    probeOutput.open(root+"/cpu-phases.csv");probeOutput<<"frame,phase,wall_ms,thread_ms,process_ms,cycles\n";
}
static void WriteProbeRow(int frame,const char* name,const ProbeStamp&a,const ProbeStamp&b){
    probeOutput<<frame<<','<<name<<','<<std::setprecision(12)<<b.wall-a.wall<<','<<double(b.thread-a.thread)/10000.0<<','<<double(b.process-a.process)/10000.0<<','<<b.cycles-a.cycles<<'\n';
}
static void FlushProbeFrame(int frame,const ProbeStamp&a,const ProbeStamp&b){
    if(probeCpu){for(const auto&r:probeRows)WriteProbeRow(frame,r.name,r.a,r.b);WriteProbeRow(frame,"WholeFrame",a,b);}
}
static void RunCopyProbe(){
    if(!probeCopies)return;
    // Called after normal frames with buffers unmapped and output complete.
    // This measures the API transfer/completion protocol, not PCIe link bandwidth.
    NvFlexFlush(g_flexLib);NvFlexWait(g_flexLib);
    const int capacity=g_buffers->positions.size();
    std::vector<NvFlexBuffer*> buffers;
    for(int i=0;i<16;++i){auto*b=NvFlexAllocBuffer(g_flexLib,capacity,16,eNvFlexBufferHost);if(!b)exit(83);buffers.push_back(b);}
    std::ofstream out(outputRoot+"/copy-probe.csv");out<<"elements,batch,repeat,request_ms,map_ms,total_ms,thread_ms,process_ms,cycles,logical_bytes,checksum\n";
    const int sizes[]={1,256,4096,capacity};
    for(int count:sizes){if(count>capacity)continue;for(int batch:{1,4,16}){
      for(int r=0;r<110;++r){
        if(getenv("DEMO_COPY_FRESH")){NvFlexUpdateSolver(g_solver,g_dt,g_numSubsteps,false);NvFlexFlush(g_flexLib);NvFlexWait(g_flexLib);}
        NvFlexCopyDesc region={0,0,count};ProbeStamp a=ProbeNow();
        for(int j=0;j<batch;++j)NvFlexGetParticles(g_solver,buffers[j],&region);
        double submitted=Ms();double checksum=0;
        for(int j=0;j<batch;++j){float* p=(float*)NvFlexMap(buffers[j],eNvFlexMapWait);if(!p)exit(84);checksum+=p[0]+p[(count-1)*4];NvFlexUnmap(buffers[j]);}
        ProbeStamp b=ProbeNow();
        out<<count<<','<<batch<<','<<r<<','<<std::setprecision(12)<<submitted-a.wall<<','<<b.wall-submitted<<','<<b.wall-a.wall<<','<<double(b.thread-a.thread)/10000.0<<','<<double(b.process-a.process)/10000.0<<','<<b.cycles-a.cycles<<','<<uint64_t(count)*16*batch<<','<<checksum<<'\n';
      }
    }}
    for(auto*b:buffers)NvFlexFreeBuffer(b);
}
