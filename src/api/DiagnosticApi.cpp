#include "solver/SolverState.hpp"
#include "runtime/ShaderLibrary.hpp"
#include <cstring>
#include <string>
namespace {
float get(df::SolverStorage::Timers& t,const wchar_t* key){float value=0;auto range=t.mNameToTimerMapW.equal_range(key);for(auto i=range.first;i!=range.second;++i)value+=t.mTimerPool->get(i->second);return value;}
float get(df::SolverStorage::Timers& t,const char* key){float value=0;auto range=t.mNameToTimerMap.equal_range(key);for(auto i=range.first;i!=range.second;++i)value+=t.mTimerPool->get(i->second);return value;}
}
// DF_IMPLEMENTED: NvFlexGetDataAftermath
extern "C" void NvFlexGetDataAftermath(NvFlexLibrary* lib,void* data,void* status){lib->mContext->getDataAftermath(static_cast<GFSDK_Aftermath_ContextData*>(data),static_cast<GFSDK_Aftermath_Status*>(status));}
// DF_IMPLEMENTED: NvFlexCopyDeviceToHost
extern "C" void NvFlexCopyDeviceToHost(NvFlexSolver* solver,NvFlexBuffer* device,void* host,int size,int stride){
    auto lib=SolverLibrary(solver);auto temporary=NvFlexAllocBuffer(lib,size,stride,eNvFlexBufferHost);if(size>0){lib->mContext->copyToHost(temporary->mBuffer,0,device->mBuffer,0,size*stride);auto data=NvFlexMap(temporary,eNvFlexMapWait);std::memcpy(host,data,size_t(size)*stride);NvFlexFreeBuffer(temporary);}
}
// DF_IMPLEMENTED: NvFlexGetDeviceLatency
extern "C" float NvFlexGetDeviceLatency(NvFlexSolver* solver,unsigned long long* begin,unsigned long long* end,unsigned long long* frequency){
    auto& s=solver->state;auto pool=solver->storage.timerState.mTimerPool;if(!s.mLatencyTimerEnable)s.mLatencyTimerEnable=true;
    else if(s.mLatencyTimerBeginRecorded&&s.mLatencyTimerEndRecorded){pool->sync();return pool->get(s.mLatencyTimerIndex,begin,end,frequency);}return 0;
}
// DF_IMPLEMENTED: NvFlexGetDetailTimers
extern "C" int NvFlexGetDetailTimers(NvFlexSolver* solver,NvFlexDetailTimer** output){
    auto& storage=solver->storage;auto& t=storage.timerState;int n=0;
    if(t.mEnabled){for(auto i=t.mNameToTimerMapW.begin();i!=t.mNameToTimerMapW.end();){auto name=i->first;auto& label=storage.detailNames[n];label.fill(0);WideCharToMultiByte(CP_ACP,0,name,-1,label.data(),int(label.size()),nullptr,nullptr);storage.details[n]={label.data(),get(t,name)};++n;do{++i;}while(i!=t.mNameToTimerMapW.end()&&i->first==name);}
        auto& label=storage.detailNames[n];label.fill(0);std::memcpy(label.data(),"Total",6);storage.details[n]={label.data(),NvFlexGetDeviceLatency(solver,nullptr,nullptr,nullptr)};++n;
    }*output=storage.details.data();return n;
}
// DF_IMPLEMENTED: NvFlexGetTimers
extern "C" void NvFlexGetTimers(NvFlexSolver* solver,NvFlexTimers* output){
    auto& t=solver->storage.timerState;if(!t.mEnabled)return;t.mTimerPool->sync();auto lib=SolverLibrary(solver);
    auto value=[&](const char* name){return get(t,df::GetShader(lib,name)->m_desc.label);};
    std::string bounds=lib->enableExtensions&&lib->shflSupported?"NV":"",atom=lib->enableExtensions&&lib->fp32AtomicSupported?"NV":"";
    if(lib->swizzleSupported)bounds="AMD";
    auto b=[&](const char* name){return value((std::string("g_Flex_")+name+bounds).c_str());};auto a=[&](const char* name){return value((std::string("g_Flex_")+name+atom).c_str());};
    output->predict=value("g_Flex_Predict");output->createCellIndices=value("g_Flex_CalculateParticleHash");output->sortCellIndices=get(t,"SortCellIndices");output->createGrid=value("g_Flex_CreateGrid");output->reorder=value("g_Flex_ReorderParticles");
    output->collideParticles=value("g_Flex_CollideParticles");output->collideShapes=value("g_Flex_CollideShapes");output->collideTriangles=value("g_Flex_CollideTriangles");output->collideFields=get(t,"CollideFields");
    output->calculateDensity=value("g_Flex_CalculateDensitySurfaceTension")+value("g_Flex_CalculateDensity");output->solveDensities=value("g_Flex_SolveDensitiesNonFluid")+value("g_Flex_SolveDensitiesSurfaceTension")+value("g_Flex_SolveDensities");
    output->solveVelocities=value("g_Flex_SolveVelocities")+value("g_Flex_CalculateVorticity")+value("g_Flex_UpdateVelocities");
    bool plastic=df::Slot(solver->state.mRigidPlasticThresholds).buffer&&df::Slot(solver->state.mRigidPlasticCreeps).buffer;std::string shape=plastic?"g_Flex_SolveShapesPlasticDeformation":"g_Flex_SolveShapes";
    if(!bounds.empty()&&!atom.empty())output->solveShapes=value((shape+"128NV").c_str())+value((shape+"32NV").c_str())+value((shape+"NV").c_str());else output->solveShapes=value(shape.c_str());
    output->solveSprings=a("SolveSprings");output->solveContacts=value("g_Flex_SolveContactsSequential");output->solveInflatables=a("SolveInflatableVolume")+b("CalculateInflatableVolume");output->applyDeltas=value("g_Flex_ApplyDeltas");
    output->calculateAnisotropy=value("g_Flex_CalculateAnisotropy")+value("g_Flex_SmoothPositions");output->updateDiffuse=value("g_Flex_CompactDiffuseParticles")+value("g_Flex_ClampDiffuseParticleCount")+value("g_Flex_UpdateDiffuseParticles")+value("g_Flex_CreateDiffuseParticles");
    output->updateTriangles=value("g_Flex_UpdateTrianglesInit")+a("UpdateTriangles");output->updateNormals=value("g_Flex_NormalizeVertexNormals")+a("UpdateVertexNormals")+value("g_Flex_UpdateVertexNormalsInit");output->finalize=value("g_Flex_Finalize");output->updateBounds=b("CalculateBoundsFinalize")+b("CalculateBoundsGroup")+b("CalculateBounds");
    float sum=0;for(unsigned i=0;i<23;++i)sum+=reinterpret_cast<float*>(output)[i];output->total=sum;
}
