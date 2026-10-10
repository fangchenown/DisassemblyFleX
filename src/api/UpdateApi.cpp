#include "solver/ParticleStep.hpp"
#include "solver/KernelParams.hpp"
#include "geometry/Geometry.hpp"
#include <cstring>
#include <stdexcept>
// DF_IMPLEMENTED: NvFlexUpdateSolver
// Recovered frame preparation and substep dispatch sequence.
extern "C" void NvFlexUpdateSolver(NvFlexSolver* solver,float dt,int substeps,bool enableTimers){
    auto& s=solver->state;auto library=SolverLibrary(solver);auto& timers=solver->storage.timerState;
    timers.mEnabled=enableTimers;timers.mTimerPool->clear();timers.mNameToTimerMap.clear();timers.mNameToTimerMapW.clear();
    if(enableTimers)timers.mTimerPool->reserve(size_t((s.mParams.numIterations+5)*substeps*10));
    if(s.mLatencyTimerEnable){s.mLatencyTimerIndex=timers.mTimerPool->begin();s.mLatencyTimerBeginRecorded=true;}
    df::RebuildGeometry(solver);
    if(s.mNumParticles){float subdt=dt/float(substeps);s.mKernelParamsHost=df::BuildKernelParams(s,subdt,substeps);
        auto buffer=df::Constant(s.mKernelParams).buffer;std::memcpy(library->mContext->map(buffer),&s.mKernelParamsHost,sizeof(s.mKernelParamsHost));library->mContext->unmap(buffer);
        for(int i=0;i<substeps;++i)df::UpdateParticleSubstep(solver,subdt,i,substeps);
    }
    if(s.mLatencyTimerEnable){timers.mTimerPool->end(s.mLatencyTimerIndex);s.mLatencyTimerEndRecorded=true;}
    timers.mTimerPool->resolve();
}
