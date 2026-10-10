#include "solver/SolverState.hpp"
#include <cstring>
// DF_IMPLEMENTED: NvFlexSetDiffuseParticles
extern "C" void NvFlexSetDiffuseParticles(NvFlexSolver* solver,NvFlexBuffer* positions,NvFlexBuffer* velocities,int count){
    auto& s=solver->state;auto lib=SolverLibrary(solver);df::WriteBytes(lib,df::Slot(s.mDiffusePositions).buffer,0,positions,0,count*16);df::WriteBytes(lib,df::Slot(s.mDiffuseVelocities).buffer,0,velocities,0,count*16);
    auto ctx=lib->mContext;auto b=df::Slot(s.mNumDiffuseParticles).buffer;std::memcpy(ctx->map(b,NvFlex::eMapWrite,true),&count,4);ctx->unmap(b);ctx->upload(b,0,4);
}
// DF_IMPLEMENTED: NvFlexGetDiffuseParticles
extern "C" void NvFlexGetDiffuseParticles(NvFlexSolver* solver,NvFlexBuffer* positions,NvFlexBuffer* velocities,NvFlexBuffer* count){
    auto& s=solver->state;if(!s.mMaxDiffuseParticles)return;auto lib=SolverLibrary(solver);
    df::ReadBytes(lib,positions,0,df::Slot(s.mDiffusePositions).buffer,0,s.mMaxDiffuseParticles*16);df::ReadBytes(lib,velocities,0,df::Slot(s.mDiffuseVelocities).buffer,0,s.mMaxDiffuseParticles*16);df::ReadBytes(lib,count,0,df::Slot(s.mNumDiffuseParticles).buffer,0,4);
}
