#include "geometry/Geometry.hpp"
#include <cstring>
namespace {
// These helpers deliberately retain the reference's staging-only copy and
// map-discard constant-buffer behavior. This undocumented debugging export
// faults on ordinary newly created D3D11 solvers; it is not a GPU clone API.
void copyBuffer(NvFlexSolver* dst,void* target,NvFlexSolver* src,void* source){
    auto& a=df::Slot(target);auto& b=df::Slot(source);unsigned bytes=b.desc.dim*b.desc.stride;
    if(a.desc.dim*a.desc.stride<bytes){unsigned stride=a.desc.stride;df::ReleaseBuffer(dst,target);std::vector<unsigned char> zeros(size_t(b.desc.dim)*stride);df::Allocate(dst,target,b.desc.dim,stride,7,eNvFlexFormat_unknown,zeros.data());}
    auto from=SolverLibrary(src)->mContext,to=SolverLibrary(dst)->mContext;
    auto input=from->map(b.buffer,NvFlex::eMapReadWrite,true);auto output=to->map(a.buffer,NvFlex::eMapReadWrite,true);
    std::memcpy(output,input,bytes);to->unmap(a.buffer);from->unmap(b.buffer);
}
void copyConstant(NvFlexSolver* dst,void* target,NvFlexSolver* src,void* source){
    auto& a=df::Constant(target);auto& b=df::Constant(source);auto from=SolverLibrary(src)->mContext,to=SolverLibrary(dst)->mContext;
    auto input=from->map(b.buffer);auto output=to->map(a.buffer);std::memcpy(output,input,b.desc.dim*b.desc.stride);to->unmap(a.buffer);from->unmap(b.buffer);
}
}
// DF_IMPLEMENTED: NvFlexCopySolver
extern "C" void NvFlexCopySolver(NvFlexSolver* destination,NvFlexSolver* source){
    destination->storage.springDispatchReady=false;
    auto& dst=destination->state;auto& src=source->state;
    copyConstant(destination,dst.mKernelParams,source,src.mKernelParams);
#define BUFFER(field) copyBuffer(destination,dst.field,source,src.field)
#define VALUE(field) dst.field=src.field
    BUFFER(mPositions);BUFFER(mVelocities);BUFFER(mRestPositions);BUFFER(mPhases);BUFFER(mActiveIndices);BUFFER(mDensities);BUFFER(mCurl);BUFFER(mNormals);
    BUFFER(mAnisotropy1);BUFFER(mAnisotropy2);BUFFER(mAnisotropy3);BUFFER(mStaticContactPlanes);BUFFER(mStaticContactVelocities);BUFFER(mStaticContactCounts);VALUE(mMaxNeighborsPerParticle);
    BUFFER(mRigidOffsets);BUFFER(mRigidIndices);BUFFER(mRigidLocalPositions);BUFFER(mRigidLocalNormals);BUFFER(mRigidCoefficients);BUFFER(mRigidPlasticThresholds);BUFFER(mRigidPlasticCreeps);BUFFER(mRigidRotations);BUFFER(mRigidTranslations);
    VALUE(mNumRigids);VALUE(mMaxRigids);VALUE(mNumRigidIndices);VALUE(mMaxRigidIndices);VALUE(mMaxPlasticEntries);
    BUFFER(mDynamicTriangles);BUFFER(mDynamicTriangleNormals);VALUE(mDynamicNumTris);VALUE(mDynamicMaxTris);BUFFER(mInflatables);VALUE(mNumInflatables);VALUE(mMaxInflatables);
    BUFFER(mDiffusePositions);BUFFER(mDiffuseVelocities);BUFFER(mNumDiffuseParticles);VALUE(mMaxDiffuseParticles);VALUE(mDiffuseRate);VALUE(mDiffuseTimer);VALUE(mNumParticles);VALUE(mNumParticlesAligned);VALUE(mMaxParticles);BUFFER(mParticleBounds);VALUE(mParams);
    auto& a=df::Shapes(destination);auto& b=df::Shapes(source);
    for(unsigned offset=0;offset<0x100;offset+=32)copyBuffer(destination,dst.mShapes+offset,source,src.mShapes+offset);
    a.count=b.count;a.capacity=b.capacity;std::memcpy(a.boundsLower,b.boundsLower,12);std::memcpy(a.boundsUpper,b.boundsUpper,12);
    VALUE(mFluidRestDensity);VALUE(mFluidDensityConstraintScale);VALUE(mFluidSurfaceConstraintScale);VALUE(mStepCounter);std::memcpy(dst.mCallbacks,src.mCallbacks,sizeof(dst.mCallbacks));VALUE(mRadixSortSize);BUFFER(mSmoothPositionsOriginal);
    copyConstant(destination,dst.mSubstepParams,source,src.mSubstepParams);
#undef BUFFER
#undef VALUE
}
