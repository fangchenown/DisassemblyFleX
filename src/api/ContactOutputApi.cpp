#include "solver/SolverState.hpp"
// DF_IMPLEMENTED: NvFlexGetBounds
extern "C" void NvFlexGetBounds(NvFlexSolver* solver,NvFlexBuffer* lower,NvFlexBuffer* upper){
    auto library=SolverLibrary(solver);auto source=df::Slot(solver->state.mParticleBounds).buffer;
    df::ReadBytes(library,lower,0,source,0,12);df::ReadBytes(library,upper,0,source,12,12);
}
// DF_IMPLEMENTED: NvFlexGetContacts
extern "C" void NvFlexGetContacts(NvFlexSolver* solver,NvFlexBuffer* planes,NvFlexBuffer* velocities,NvFlexBuffer* indices,NvFlexBuffer* counts){
    auto library=SolverLibrary(solver);auto& s=solver->state;unsigned n=s.mMaxParticles,contacts=n*s.mMaxContactsPerParticle;
    df::ReadBytes(library,planes,0,df::Slot(s.mStaticContactPlanes).buffer,0,contacts*16);
    df::ReadBytes(library,velocities,0,df::Slot(s.mStaticContactVelocities).buffer,0,contacts*16);
    df::ReadBytes(library,indices,0,df::Slot(s.mReverseLookup).buffer,0,n*4);
    df::ReadBytes(library,counts,0,df::Slot(s.mStaticContactCounts).buffer,0,n*4);
}
// DF_IMPLEMENTED: NvFlexGetNeighbors
extern "C" void NvFlexGetNeighbors(NvFlexSolver* solver,NvFlexBuffer* neighbors,NvFlexBuffer* counts,NvFlexBuffer* apiToInternal,NvFlexBuffer* internalToApi){
    auto library=SolverLibrary(solver);auto& s=solver->state;unsigned n=s.mMaxParticles;
    df::ReadBytes(library,neighbors,0,df::Slot(s.mParticleNeighbors).buffer,0,n*s.mMaxNeighborsPerParticle*4);
    df::ReadBytes(library,counts,0,df::Slot(s.mParticleNeighborCounts).buffer,0,n*4);
    df::ReadBytes(library,apiToInternal,0,df::Slot(s.mReverseLookup).buffer,0,n*4);
    df::ReadBytes(library,internalToApi,0,solver->storage.radix->front.value,0,n*4);
}
