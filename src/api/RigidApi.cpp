#include "solver/SolverState.hpp"
// DF_IMPLEMENTED: NvFlexSetRigids
extern "C" void NvFlexSetRigids(NvFlexSolver* solver,NvFlexBuffer* offsets,NvFlexBuffer* indices,NvFlexBuffer* rest,NvFlexBuffer* normals,NvFlexBuffer* stiffness,NvFlexBuffer* thresholds,NvFlexBuffer* creeps,NvFlexBuffer* rotations,NvFlexBuffer* translations,int count,int indexCount){
    auto& s=solver->state;auto library=SolverLibrary(solver);auto context=library->mContext;
    if(!count){s.mNumRigids=0;s.mNumRigidIndices=0;return;}
    if(count>s.mMaxRigids){unsigned capacity=unsigned(count*3/2);df::ReserveBuffer(solver,s.mRigidOffsets,capacity+1,4);df::ReserveBuffer(solver,s.mRigidRotations,capacity,16);df::ReserveBuffer(solver,s.mRigidTranslations,capacity,12);df::ReserveBuffer(solver,s.mRigidCoefficients,capacity,4);s.mMaxRigids=capacity;}
    if(indexCount>s.mMaxRigidIndices){unsigned capacity=unsigned(indexCount*3/2);df::ReserveBuffer(solver,s.mRigidIndices,capacity,4);df::ReserveBuffer(solver,s.mRigidLocalPositions,capacity,12);df::ReserveBuffer(solver,s.mRigidLocalNormals,capacity,16);s.mMaxRigidIndices=capacity;}
    auto write=[&](void* field,NvFlexBuffer* source,unsigned bytes){df::WriteBytes(library,df::Slot(field).buffer,0,source,0,bytes);};
    write(s.mRigidRotations,rotations,count*16);write(s.mRigidTranslations,translations,count*12);write(s.mRigidOffsets,offsets,(count+1)*4);
    write(s.mRigidIndices,indices,indexCount*4);write(s.mRigidCoefficients,stiffness,count*4);write(s.mRigidLocalPositions,rest,indexCount*12);
    if(normals)write(s.mRigidLocalNormals,normals,indexCount*16);else {unsigned zero[4]{};context->clearUnorderedAccessViewUint(df::Slot(s.mRigidLocalNormals).buffer,zero);}
    s.mNumRigids=count;s.mNumRigidIndices=indexCount;
    if(!thresholds||!creeps){df::ReleaseBuffer(solver,s.mRigidPlasticThresholds);df::ReleaseBuffer(solver,s.mRigidPlasticCreeps);s.mMaxPlasticEntries=0;}
    else{
        if(count>s.mMaxPlasticEntries){df::ReserveBuffer(solver,s.mRigidPlasticThresholds,s.mMaxRigids,4);df::ReserveBuffer(solver,s.mRigidPlasticCreeps,s.mMaxRigids,4);s.mMaxPlasticEntries=s.mMaxRigids;}
        write(s.mRigidPlasticThresholds,thresholds,count*4);write(s.mRigidPlasticCreeps,creeps,count*4);
    }
}
// DF_IMPLEMENTED: NvFlexGetRigids
extern "C" void NvFlexGetRigids(NvFlexSolver* solver,NvFlexBuffer* offsets,NvFlexBuffer* indices,NvFlexBuffer* rest,NvFlexBuffer* normals,NvFlexBuffer* stiffness,NvFlexBuffer* thresholds,NvFlexBuffer* creeps,NvFlexBuffer* rotations,NvFlexBuffer* translations){
    auto& s=solver->state;if(!s.mNumRigids)return;auto library=SolverLibrary(solver);unsigned n=s.mNumRigids,k=s.mNumRigidIndices;
    auto read=[&](NvFlexBuffer* target,void* field,unsigned bytes){df::ReadBytes(library,target,0,df::Slot(field).buffer,0,bytes);};
    read(rotations,s.mRigidRotations,n*16);read(translations,s.mRigidTranslations,n*12);read(offsets,s.mRigidOffsets,(n+1)*4);read(indices,s.mRigidIndices,k*4);
    read(stiffness,s.mRigidCoefficients,n*4);read(rest,s.mRigidLocalPositions,k*12);read(normals,s.mRigidLocalNormals,k*16);
    if(df::Slot(s.mRigidPlasticThresholds).buffer)read(thresholds,s.mRigidPlasticThresholds,n*4);
    if(df::Slot(s.mRigidPlasticCreeps).buffer)read(creeps,s.mRigidPlasticCreeps,n*4);
}
