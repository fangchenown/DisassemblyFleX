#include "solver/SolverState.hpp"
#include "solver/FluidConstants.hpp"
#include <algorithm>
#include <cfloat>
#include <cstring>
#include <numeric>
#include <stdexcept>

// DF_IMPLEMENTED: NvFlexCreateSolver
// Public state and persistent particle/output allocations are reconstructed.
// Radix/BVH/constraint growth and update behavior remain separate active gates.
extern "C" NvFlexSolver* NvFlexCreateSolver(NvFlexLibrary* library,const NvFlexSolverDesc* desc){
    if(!library||!desc||desc->maxParticles<0||desc->maxDiffuseParticles<0)return nullptr;
    auto solver=std::make_unique<NvFlexSolver>();auto& s=solver->state;
    std::memcpy(s.mLib,&library,8);std::memcpy(&s.mDesc,desc,sizeof(*desc));
    s.mMaxParticles=desc->maxParticles;s.mMaxNeighborsPerParticle=desc->maxNeighborsPerParticle;s.mMaxContactsPerParticle=desc->maxContactsPerParticle;
    const unsigned n=static_cast<unsigned>(desc->maxParticles);const unsigned aligned=(n+255u)&~255u;
    df::AllocateConstant(solver.get(),s.mKernelParams,512);
    auto zeros=[&](void* target,unsigned count,unsigned stride,unsigned flags=19,NvFlexFormat format=eNvFlexFormat_unknown){
        std::vector<std::byte> initial(size_t(count)*stride);df::Allocate(solver.get(),target,count,stride,flags,format,initial.data());
    };
    std::vector<unsigned> indices(n);std::iota(indices.begin(),indices.end(),0u);
    df::Allocate(solver.get(),s.mActiveIndices,n,4,19,eNvFlexFormat_unknown,indices.data());
    zeros(s.mPositions,n,16);zeros(s.mNewPositions,n,16);zeros(s.mRestPositions,n,16);zeros(s.mVelocities,n,12);
    zeros(s.mNormals,n,16);zeros(s.mSortedNormals,n,16);zeros(s.mNormalsTemp,n,16,11,eNvFlexFormat_r32_typeless);zeros(s.mDeltas,n,16,11,eNvFlexFormat_r32_typeless);
    zeros(s.mParticleNeighbors,aligned*desc->maxNeighborsPerParticle,4);zeros(s.mParticleNeighborCounts,n,4);
    zeros(s.mSortedPositions,n,16);zeros(s.mSortedNewPositions,n,16);zeros(s.mSortedNewVelocities,n,16);
    zeros(s.mStaticContactPlanes,n*desc->maxContactsPerParticle,16);zeros(s.mStaticContactVelocities,n*desc->maxContactsPerParticle,16);zeros(s.mStaticContactCounts,n,4);
    zeros(s.mDensities,n,4);zeros(s.mPhases,n,4);zeros(s.mSortedPhases,n,4);zeros(s.mPotentials,n,4);zeros(s.mCurl,n,16);
    std::vector<std::array<float,4>> axes(n);
    for(unsigned axis=0;axis<3;++axis){for(auto& value:axes){value={0,0,0,0.1f};value[axis]=1;}
        void* target=axis==0?static_cast<void*>(s.mAnisotropy1):axis==1?static_cast<void*>(s.mAnisotropy2):static_cast<void*>(s.mAnisotropy3);
        df::Allocate(solver.get(),target,n,16,19,eNvFlexFormat_unknown,axes.data());}
    zeros(s.mSortedDensities,n,4);zeros(s.mParticleBounds,2,12);
    unsigned boundGroups=(n+127u)/128u;unsigned groupGroups=(boundGroups+127u)/128u;
    zeros(s.mBoundsLower,boundGroups,16);zeros(s.mBoundsUpper,boundGroups,16);zeros(s.mGroupBoundsLower,groupGroups,16);zeros(s.mGroupBoundsUpper,groupGroups,16);
    s.mRadixSortSize=n;solver->storage.radix=std::make_unique<df::RadixSort>(library,(n+1023u)/1024u);
    auto radix=solver->storage.radix.get();std::memcpy(s.mRadixSort,&radix,8);
    zeros(s.mReverseLookup,n,4);
    std::array<float,256> random{};for(auto& value:random)value=df::RandomSigned();
    df::Allocate(solver.get(),s.mRandom,256,4,19,eNvFlexFormat_unknown,random.data());
    if(desc->maxDiffuseParticles){unsigned count=desc->maxDiffuseParticles;
        zeros(s.mDiffusePositions,count,16);zeros(s.mDiffuseVelocities,count,16);zeros(s.mDiffusePositionsNew,count,16);zeros(s.mDiffuseVelocitiesNew,count,16);
        zeros(s.mDiffuseSortSize,1,4);zeros(s.mDiffuseLaunchArg,3,4,35,eNvFlexFormat_r32_uint);
        zeros(s.mNumDiffuseParticles,1,4,23);zeros(s.mNumDiffuseParticlesNew,1,4,23);
        s.mMaxDiffuseParticles=count;s.mDiffuseRate=1.0f/60.0f;
    }
    s.mParams.numIterations=1;s.mParams.maxSpeed=FLT_MAX;s.mParams.maxAcceleration=FLT_MAX;
    s.mParams.relaxationMode=eNvFlexRelaxationLocal;s.mParams.relaxationFactor=1.0f;
    zeros(s.mSortedVelocities,n,16);zeros(s.mSmoothPositionsOriginal,n,16);
    df::AllocateConstant(solver.get(),s.mSubstepParams,8);df::AllocateConstant(solver.get(),s.mNumShapes,4);
    solver->storage.timers.reset(library->mContext->createTimerPool());solver->storage.timerState.mContext=library->mContext;solver->storage.timerState.mTimerPool=solver->storage.timers.get();
    auto timers=&solver->storage.timerState;std::memcpy(s.mTimers,&timers,8);
    s.mNumDetailTimers=256;for(size_t i=0;i<256;++i)solver->storage.details[i].name=solver->storage.detailNames[i].data();
    auto details=solver->storage.details.data();std::memcpy(s.mDetailTimers,&details,8);
    library->solvers.push_back(solver.get());return solver.release();
}
// DF_IMPLEMENTED: NvFlexDestroySolver
extern "C" void NvFlexDestroySolver(NvFlexSolver* solver){
    if(!solver)return;auto library=SolverLibrary(solver);auto& list=library->solvers;
    list.erase(std::remove(list.begin(),list.end(),solver),list.end());delete solver;
}
// DF_IMPLEMENTED: NvFlexGetSolvers
extern "C" int NvFlexGetSolvers(NvFlexLibrary* library,NvFlexSolver** output,int capacity){
    size_t count=std::min(static_cast<size_t>(std::max(0,capacity)),library->solvers.size());
    if(count)std::memcpy(output,library->solvers.data(),count*sizeof(NvFlexSolver*));return static_cast<int>(library->solvers.size());
}
// DF_IMPLEMENTED: NvFlexGetSolverDesc
extern "C" void NvFlexGetSolverDesc(NvFlexSolver* solver,NvFlexSolverDesc* output){std::memcpy(output,&solver->state.mDesc,sizeof(*output));}
