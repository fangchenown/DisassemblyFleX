#include "ParticleStep.hpp"
#include "runtime/ShaderLibrary.hpp"
#include "geometry/Geometry.hpp"
#include <cstring>
#include <cmath>
#include <initializer_list>
#include <string>
namespace df {
using Binding=std::pair<unsigned,NvFlex::Buffer*>;
static NvFlex::Buffer* B(void* field){return Slot(field).buffer;}
static void Pass(NvFlexSolver* solver,const char* shader,unsigned groups,std::initializer_list<Binding> reads,std::initializer_list<Binding> writes,bool root=true,NvFlex::ConstantBuffer* second=nullptr){
    auto library=SolverLibrary(solver);auto& state=solver->state;auto& timers=solver->storage.timerState;
    NvFlex::DispatchParams p{};p.shader=GetShader(library,shader);p.gridDim={groups,1,1};
    if(root)p.rootConstantBuffer=Constant(state.mKernelParams).buffer;p.secondConstantBuffer=second;
    for(auto binding:reads)if(binding.second)p.readOnly[binding.first]=binding.second->getResource();
    for(auto binding:writes)if(binding.second)p.readWrite[binding.first]=binding.second->getResourceRW();
    if(std::strcmp(shader,"g_Flex_CollideShapes")==0&&library->geometry->sdfCount){for(unsigned i=0;i<16;++i)if(auto texture=library->geometry->textures[i])p.readOnly[15+i]=texture->getResource();}
    int timer=-1;if(timers.mEnabled){timer=timers.mTimerPool->begin();timers.mNameToTimerMapW.emplace(p.shader->m_desc.label,timer);}
    library->mContext->dispatch(&p);
    if(library->amdDriverWorkaround&&std::strcmp(shader,"g_Flex_Predict")==0){library->mContext->flush();NvFlexWait(library);}
    if(timers.mEnabled)timers.mTimerPool->end(timer);
}
void ExecuteCallback(NvFlexSolver* solver,NvFlexSolverCallbackStage stage,float dt){
    auto& s=solver->state;NvFlexSolverCallback callback{};std::memcpy(&callback,s.mCallbacks+sizeof(callback)*int(stage),sizeof(callback));
    if(!callback.function)return;
    // The reference does not write the solver member at RVA 0x30bb0. Keep that
    // indeterminate field out of equivalence checks; do not invent its value.
    NvFlexSolverCallbackParams params;
    params.userData=callback.userData;params.particles=reinterpret_cast<float*>(B(s.mSortedNewPositions));params.velocities=reinterpret_cast<float*>(B(s.mSortedNewVelocities));
    params.phases=reinterpret_cast<int*>(B(s.mSortedPhases));params.numActive=s.mNumParticles;params.dt=dt;
    params.originalToSortedMap=reinterpret_cast<int*>(B(s.mReverseLookup));params.sortedToOriginalMap=reinterpret_cast<int*>(solver->storage.radix->front.value);
    callback.function(params);
}
void UpdateParticleSubstep(NvFlexSolver* solver,float dt,int substep,int numSubsteps){
    auto& s=solver->state;auto library=SolverLibrary(solver);auto context=library->mContext;auto& radix=*solver->storage.radix;
    unsigned blocks=(unsigned(s.mNumParticles)+255u)/256u,boundsBlocks=(unsigned(s.mNumParticles)+127u)/128u;
    Pass(solver,"g_Flex_Predict",blocks,{{0,B(s.mActiveIndices)},{1,B(s.mPositions)},{2,B(s.mPhases)}},{{0,B(s.mNewPositions)},{1,B(s.mVelocities)}});
    std::string suffix=library->enableExtensions&&library->shflSupported?"NV":"";
    if(library->swizzleSupported)suffix="AMD";
    std::string bounds="g_Flex_CalculateBounds"+suffix,group="g_Flex_CalculateBoundsGroup"+suffix,finalize="g_Flex_CalculateBoundsFinalize"+suffix;
    Pass(solver,bounds.c_str(),boundsBlocks,{{0,B(s.mActiveIndices)},{1,B(s.mNewPositions)}},{{0,B(s.mBoundsLower)},{1,B(s.mBoundsUpper)},{2,B(s.mParticleBounds)}});
    Pass(solver,group.c_str(),(boundsBlocks+127u)/128u,{{2,B(s.mBoundsLower)},{3,B(s.mBoundsUpper)}},{{0,B(s.mGroupBoundsLower)},{1,B(s.mGroupBoundsUpper)},{2,B(s.mParticleBounds)}});
    Pass(solver,finalize.c_str(),1,{{2,B(s.mGroupBoundsLower)},{3,B(s.mGroupBoundsUpper)}},{{2,B(s.mParticleBounds)}});
    Pass(solver,"g_Flex_CalculateParticleHash",radix.capacity()/256u,{{0,B(s.mActiveIndices)},{1,B(s.mNewPositions)},{2,B(s.mParticleBounds)}},{{0,radix.front.key},{1,radix.front.value}});
    if(s.mNumParticles){auto& timers=solver->storage.timerState;int timer=-1;if(timers.mEnabled){timer=timers.mTimerPool->begin();timers.mNameToTimerMapW.emplace(L"SortCellIndices",timer);}radix.sort(unsigned(s.mNumParticles),24,&timers);if(timer>=0)timers.mTimerPool->end(timer);}
    Pass(solver,"g_Flex_CreateGrid",blocks,{{0,radix.front.key}},{{0,library->cellBucketStarts},{1,library->cellBucketEnds}});
    Pass(solver,"g_Flex_ReorderParticles",blocks,{{0,B(s.mPositions)},{1,B(s.mNewPositions)},{2,B(s.mVelocities)},{3,B(s.mPhases)},{4,radix.front.value},{5,B(s.mNormals)}},{{0,B(s.mSortedPositions)},{1,B(s.mSortedNewPositions)},{2,B(s.mSortedVelocities)},{3,B(s.mSortedPhases)},{4,B(s.mReverseLookup)},{5,B(s.mSortedNormals)}});
    Pass(solver,"g_Flex_CollideParticles",blocks,{{0,library->cellBucketStarts},{1,library->cellBucketEnds},{2,radix.front.value},{3,B(s.mSortedNewPositions)},{4,B(s.mRestPositions)},{5,B(s.mSortedPhases)},{6,B(s.mParticleBounds)}},{{0,B(s.mParticleNeighbors)},{1,B(s.mParticleNeighborCounts)}});
    ExecuteCallback(solver,eNvFlexStageSubstepBegin,dt);
    // The clear has the same text as the collision shader but a distinct label
    // address in the original. DetailTimers groups adjacent equal pointers.
    static wchar_t clearContactsLabel[]=L"CollideTriangles";auto& frameTimers=solver->storage.timerState;int clearTimer=-1;
    if(frameTimers.mEnabled){clearTimer=frameTimers.mTimerPool->begin();frameTimers.mNameToTimerMapW.emplace(clearContactsLabel,clearTimer);}
    unsigned clear[4]{};context->clearUnorderedAccessViewUint(B(s.mStaticContactCounts),clear);if(clearTimer>=0)frameTimers.mTimerPool->end(clearTimer);
    auto second=Constant(s.mSubstepParams).buffer;float fraction=1.0f/float(numSubsteps);float values[2]={float(substep)*fraction,float(substep+1)*fraction};auto& shape=Shapes(solver);auto& geometry=*library->geometry;
    auto uploadSubstep=[&](){std::memcpy(context->map(second),values,sizeof(values));context->unmap(second);};
    uploadSubstep();
    Pass(solver,"g_Flex_CollideTriangles",blocks,{{0,geometry.vertices.buffer},{1,geometry.indices.buffer},{2,geometry.nodeLower.buffer},{3,geometry.nodeUpper.buffer},{4,geometry.rootNodes.buffer},{17,geometry.vertices.buffer?geometry.meshTable.buffer:nullptr},{5,B(s.mSortedPositions)},{6,B(s.mSortedNewPositions)},{7,B(s.mSortedPhases)},{8,shape.count?shape.prevPositions.buffer:nullptr},{9,shape.count?shape.prevRotations.buffer:nullptr},{10,shape.count?shape.flags.buffer:nullptr},{11,shape.count?shape.positions.buffer:nullptr},{12,shape.count?shape.rotations.buffer:nullptr},{13,shape.count?shape.geometry.buffer:nullptr},{14,shape.count?shape.bvh.root.buffer:nullptr},{15,shape.count?shape.bvh.lower.buffer:nullptr},{16,shape.count?shape.bvh.upper.buffer:nullptr}},{{0,B(s.mStaticContactCounts)},{1,B(s.mStaticContactPlanes)},{2,B(s.mStaticContactVelocities)}},true,second);
    uploadSubstep();
    Pass(solver,"g_Flex_CollideShapes",boundsBlocks,{{12,geometry.convexCount?geometry.convexTable.buffer:nullptr},{13,geometry.convexCount?geometry.convexPlanes.buffer:nullptr},{14,geometry.sdfCount?geometry.sdfTable.buffer:nullptr},{0,shape.count?shape.geometry.buffer:nullptr},{1,shape.count?shape.positions.buffer:nullptr},{2,shape.count?shape.rotations.buffer:nullptr},{3,shape.count?shape.prevPositions.buffer:nullptr},{4,shape.count?shape.prevRotations.buffer:nullptr},{5,shape.count?shape.flags.buffer:nullptr},{6,B(s.mSortedPositions)},{7,B(s.mSortedNewPositions)},{8,B(s.mSortedPhases)},{9,shape.count?shape.bvh.root.buffer:nullptr},{10,shape.count?shape.bvh.lower.buffer:nullptr},{11,shape.count?shape.bvh.upper.buffer:nullptr}},{{0,B(s.mStaticContactCounts)},{1,B(s.mStaticContactPlanes)},{2,B(s.mStaticContactVelocities)}},true,second);
    if(s.mParams.shockPropagation>0)Pass(solver,"g_Flex_ContinuousShockPropagation",blocks,{{0,B(s.mParticleBounds)}},{{0,B(s.mSortedNewPositions)}});
    for(int iteration=0;iteration<s.mParams.numIterations;++iteration){
        ExecuteCallback(solver,eNvFlexStageIterationStart,dt);
        if(s.mParams.fluidRestDistance>0){const char* name=s.mParams.surfaceTension<=0?"g_Flex_CalculateDensity":"g_Flex_CalculateDensitySurfaceTension";
            Pass(solver,name,blocks,{{0,B(s.mParticleNeighbors)},{1,B(s.mParticleNeighborCounts)},{2,B(s.mSortedNewPositions)},{3,B(s.mSortedPhases)},{4,radix.front.value}},{{0,B(s.mDensities)},{1,B(s.mNormals)},{2,B(s.mSortedNormals)}},false);}
        const char* density=s.mDesc.featureMode==eNvFlexFeatureModeSimpleSolids?"g_Flex_SolveDensitiesNonFluid":s.mParams.surfaceTension<=0?"g_Flex_SolveDensities":"g_Flex_SolveDensitiesSurfaceTension";
        Pass(solver,density,blocks,{{0,B(s.mParticleNeighbors)},{1,B(s.mParticleNeighborCounts)},{2,B(s.mSortedNewPositions)},{3,B(s.mSortedPhases)},{4,B(s.mDensities)},{5,B(s.mNormals)},{6,B(s.mSortedPositions)},{7,B(s.mSortedNormals)}},{{0,B(s.mDeltas)}});
        if(s.mNumSprings){const char* spring=library->enableExtensions&&library->fp32AtomicSupported?"g_Flex_SolveSpringsNV":"g_Flex_SolveSprings";
            Pass(solver,spring,unsigned(s.mMaxParticles*8+511)/512,{{0,B(s.mHalfSpringIndices)},{1,B(s.mHalfSpringOpposites)},{2,B(s.mHalfSpringLengths)},{3,B(s.mHalfSpringStiffness)},{4,B(s.mHalfSpringParticleBegin)},{5,B(s.mHalfSpringParticleEnd)},{6,B(s.mReverseLookup)},{7,B(s.mSortedNewPositions)}},{{0,B(s.mDeltas)}});}
        if(s.mNumInflatables){
            const char* volume=library->enableExtensions&&library->shflSupported?"g_Flex_CalculateInflatableVolumeNV":library->swizzleSupported?"g_Flex_CalculateInflatableVolumeAMD":"g_Flex_CalculateInflatableVolume";
            const char* solve=library->enableExtensions&&library->fp32AtomicSupported?"g_Flex_SolveInflatableVolumeNV":"g_Flex_SolveInflatableVolume";
            Pass(solver,volume,unsigned(s.mNumInflatables),{{0,B(s.mInflatables)},{1,B(s.mSortedNewPositions)},{2,B(s.mReverseLookup)},{3,B(s.mDynamicTriangles)}},{{0,B(s.mPressures)}});
            Pass(solver,solve,unsigned(s.mNumInflatables),{{0,B(s.mInflatables)},{1,B(s.mSortedNewPositions)},{2,B(s.mReverseLookup)},{3,B(s.mDynamicTriangles)},{4,B(s.mPressures)}},{{0,B(s.mDeltas)}});
            if(library->amdDriverWorkaround){context->flush();NvFlexWait(library);}
        }
        if(s.mNumRigids){
            bool plastic=B(s.mRigidPlasticThresholds)&&B(s.mRigidPlasticCreeps);std::string name=plastic?"g_Flex_SolveShapesPlasticDeformation":"g_Flex_SolveShapes";
            if(library->enableExtensions&&library->shflSupported&&library->fp32AtomicSupported){int average=s.mNumRigidIndices/s.mNumRigids;if(average<=32)name+="32NV";else if(average>127)name+="128NV";else name+="NV";}
            Pass(solver,name.c_str(),unsigned(s.mNumRigids),{{0,B(s.mRigidOffsets)},{1,B(s.mRigidIndices)},{2,B(s.mRigidCoefficients)},{3,plastic?B(s.mRigidPlasticThresholds):nullptr},{4,plastic?B(s.mRigidPlasticCreeps):nullptr},{5,B(s.mReverseLookup)},{6,B(s.mSortedPositions)},{7,B(s.mRigidLocalNormals)}},{{0,B(s.mDeltas)},{1,B(s.mRigidLocalPositions)},{2,B(s.mSortedNewPositions)},{3,B(s.mRigidRotations)},{4,B(s.mRigidTranslations)},{5,B(s.mNormals)}});
        }
        Pass(solver,"g_Flex_ApplyDeltas",blocks,{{0,B(s.mDeltas)}},{{0,B(s.mSortedNewPositions)}});
        Pass(solver,"g_Flex_SolveContactsSequential",blocks,{{0,B(s.mStaticContactCounts)},{1,B(s.mStaticContactPlanes)},{2,B(s.mSortedPositions)},{3,B(s.mStaticContactVelocities)}},{{0,B(s.mSortedNewPositions)}});
        ExecuteCallback(solver,eNvFlexStageIterationEnd,dt);
    }
    Pass(solver,"g_Flex_UpdateVelocities",blocks,{{0,B(s.mSortedPositions)},{1,B(s.mSortedNewPositions)}},{{0,B(s.mSortedNewVelocities)}});
    ExecuteCallback(solver,eNvFlexStageSubstepEnd,dt);if(substep==numSubsteps-1)ExecuteCallback(solver,eNvFlexStageUpdateEnd,float(numSubsteps)*dt);
    if(s.mParams.vorticityConfinement>0)Pass(solver,"g_Flex_CalculateVorticity",blocks,{{0,B(s.mSortedNewPositions)},{1,B(s.mSortedNewVelocities)},{2,B(s.mSortedPhases)},{3,B(s.mParticleNeighbors)},{4,B(s.mParticleNeighborCounts)},{5,B(s.mStaticContactPlanes)},{6,B(s.mStaticContactCounts)}},{{0,B(s.mCurl)}});
    Pass(solver,"g_Flex_SolveVelocities",blocks,{{0,B(s.mParticleNeighbors)},{1,B(s.mParticleNeighborCounts)},{2,B(s.mStaticContactPlanes)},{3,B(s.mStaticContactCounts)},{4,B(s.mSortedPositions)},{5,B(s.mSortedVelocities)},{6,B(s.mSortedNewVelocities)},{7,B(s.mSortedPhases)},{8,B(s.mCurl)}},{{0,B(s.mSortedNewPositions)},{1,B(s.mDeltas)},{2,B(s.mSortedDensities)},{3,B(s.mPotentials)}});
    if(s.mDynamicNumTris){
        unsigned triangleBlocks=unsigned(s.mDynamicNumTris+255)/256;
        const char* triangle=library->enableExtensions&&library->fp32AtomicSupported?"g_Flex_UpdateTrianglesNV":"g_Flex_UpdateTriangles";
        Pass(solver,triangle,triangleBlocks,{{0,B(s.mSortedNewPositions)},{1,B(s.mSortedNewVelocities)},{2,B(s.mReverseLookup)},{3,B(s.mDynamicTriangles)}},{{0,B(s.mDeltas)},{1,B(s.mDynamicTriangleNormals)}});
        if(substep==numSubsteps-1){
            Pass(solver,"g_Flex_UpdateVertexNormalsInit",unsigned(s.mMaxParticles+255)/256,{{0,B(s.mReverseLookup)},{1,B(s.mDynamicTriangles)},{2,B(s.mDynamicTriangleNormals)}},{{0,B(s.mNormalsTemp)}});
            const char* normals=library->enableExtensions&&library->fp32AtomicSupported?"g_Flex_UpdateVertexNormalsNV":"g_Flex_UpdateVertexNormals";
            Pass(solver,normals,triangleBlocks,{{0,B(s.mReverseLookup)},{1,B(s.mDynamicTriangles)},{2,B(s.mDynamicTriangleNormals)}},{{0,B(s.mNormalsTemp)}});
            Pass(solver,"g_Flex_NormalizeVertexNormals",blocks,{{0,radix.front.value},{1,B(s.mNormalsTemp)}},{{0,B(s.mNormals)}});
        }
    }
    Pass(solver,"g_Flex_Finalize",blocks,{{0,B(s.mSortedNewPositions)},{1,B(s.mSortedNewVelocities)},{2,B(s.mSortedDensities)},{3,B(s.mDeltas)},{4,radix.front.value}},{{0,B(s.mPositions)},{1,B(s.mVelocities)},{2,B(s.mDensities)}});
    s.mDiffuseTimer+=dt;
    if(substep==numSubsteps-1){
        if(s.mMaxDiffuseParticles){
            unsigned diffuseBlocks=unsigned(s.mMaxDiffuseParticles+255)/256;
            if(s.mDiffuseRate<=s.mDiffuseTimer){s.mDiffuseTimer=std::fmod(s.mDiffuseTimer,s.mDiffuseRate);
                Pass(solver,"g_Flex_CreateDiffuseParticles",blocks,{{0,B(s.mPotentials)},{1,B(s.mSortedNewPositions)},{2,B(s.mSortedNewVelocities)},{3,B(s.mRandom)}},{{0,B(s.mNumDiffuseParticles)},{1,B(s.mDiffusePositions)},{2,B(s.mDiffuseVelocities)}});
            }
            Pass(solver,"g_Flex_UpdateDiffuseParticles",diffuseBlocks,{{0,B(s.mNumDiffuseParticles)},{1,library->cellBucketStarts},{2,library->cellBucketEnds},{3,B(s.mParticleNeighborCounts)},{4,B(s.mSortedNewPositions)},{5,B(s.mSortedNewVelocities)},{6,B(s.mSortedPhases)},{7,B(s.mParticleBounds)}},{{0,B(s.mDiffusePositions)},{1,B(s.mDiffuseVelocities)}});
            Pass(solver,"g_Flex_ClampDiffuseParticleCount",1,{},{{0,B(s.mNumDiffuseParticles)},{1,B(s.mNumDiffuseParticlesNew)}});
            Pass(solver,"g_Flex_CompactDiffuseParticles",diffuseBlocks,{{0,B(s.mNumDiffuseParticles)},{1,B(s.mDiffusePositions)},{2,B(s.mDiffuseVelocities)}},{{0,B(s.mNumDiffuseParticlesNew)},{1,B(s.mDiffusePositionsNew)},{2,B(s.mDiffuseVelocitiesNew)}});
            std::swap(Slot(s.mDiffusePositions),Slot(s.mDiffusePositionsNew));std::swap(Slot(s.mDiffuseVelocities),Slot(s.mDiffuseVelocitiesNew));std::swap(Slot(s.mNumDiffuseParticles),Slot(s.mNumDiffuseParticlesNew));
        }
        if(s.mParams.anisotropyScale>0||s.mParams.smoothing>0)Pass(solver,"g_Flex_SmoothPositions",blocks,{{0,B(s.mParticleNeighbors)},{1,B(s.mParticleNeighborCounts)},{2,B(s.mSortedPhases)},{3,B(s.mSortedNewPositions)},{4,radix.front.value}},{{0,B(s.mSortedPositions)},{1,B(s.mSmoothPositionsOriginal)}});
        if(s.mParams.anisotropyScale>0)Pass(solver,"g_Flex_CalculateAnisotropy",blocks,{{0,B(s.mParticleNeighbors)},{1,B(s.mParticleNeighborCounts)},{2,radix.front.value},{3,B(s.mSortedPhases)},{4,B(s.mSortedPositions)}},{{0,B(s.mAnisotropy1)},{1,B(s.mAnisotropy2)},{2,B(s.mAnisotropy3)}});
    }
    Pass(solver,"g_Flex_ClearCellBuckets",blocks,{{0,B(s.mActiveIndices)},{1,B(s.mNewPositions)},{2,B(s.mParticleBounds)}},{{0,library->cellBucketStarts},{1,library->cellBucketEnds}});
    if(library->mDevice->mGpuVendorId==VENDOR_ID_NVIDIA)context->clearState();++s.mStepCounter;
}
}
