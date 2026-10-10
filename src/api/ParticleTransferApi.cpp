#include "solver/SolverState.hpp"
// These wrappers preserve the reference source buffer, stride and range rules.
// DF_IMPLEMENTED: NvFlexSetParticles
extern "C" void NvFlexSetParticles(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::WriteData(SolverLibrary(s),df::Slot(s->state.mPositions).buffer,p,d);}
// DF_IMPLEMENTED: NvFlexGetParticles
extern "C" void NvFlexGetParticles(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mPositions).buffer,d);}
// DF_IMPLEMENTED: NvFlexSetVelocities
extern "C" void NvFlexSetVelocities(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::WriteData(SolverLibrary(s),df::Slot(s->state.mVelocities).buffer,p,d);}
// DF_IMPLEMENTED: NvFlexGetVelocities
extern "C" void NvFlexGetVelocities(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mVelocities).buffer,d);}
// DF_IMPLEMENTED: NvFlexSetRestParticles
extern "C" void NvFlexSetRestParticles(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::WriteData(SolverLibrary(s),df::Slot(s->state.mRestPositions).buffer,p,d);}
// DF_IMPLEMENTED: NvFlexGetRestParticles
extern "C" void NvFlexGetRestParticles(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mRestPositions).buffer,d);}
// DF_IMPLEMENTED: NvFlexSetPhases
extern "C" void NvFlexSetPhases(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::WriteData(SolverLibrary(s),df::Slot(s->state.mPhases).buffer,p,d);}
// DF_IMPLEMENTED: NvFlexGetPhases
extern "C" void NvFlexGetPhases(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mPhases).buffer,d);}
// DF_IMPLEMENTED: NvFlexSetNormals
extern "C" void NvFlexSetNormals(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::WriteData(SolverLibrary(s),df::Slot(s->state.mNormals).buffer,p,d);}
// DF_IMPLEMENTED: NvFlexGetNormals
extern "C" void NvFlexGetNormals(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mNormals).buffer,d);}
// DF_IMPLEMENTED: NvFlexSetActive
extern "C" void NvFlexSetActive(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::WriteData(SolverLibrary(s),df::Slot(s->state.mActiveIndices).buffer,p,d);}
// DF_IMPLEMENTED: NvFlexGetActive
extern "C" void NvFlexGetActive(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mActiveIndices).buffer,d);}
// DF_IMPLEMENTED: NvFlexGetDensities
extern "C" void NvFlexGetDensities(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mDensities).buffer,d);}
// DF_IMPLEMENTED: NvFlexGetSmoothParticles
extern "C" void NvFlexGetSmoothParticles(NvFlexSolver* s,NvFlexBuffer* p,const NvFlexCopyDesc* d){df::ReadData(SolverLibrary(s),p,df::Slot(s->state.mSmoothPositionsOriginal).buffer,d);}
// DF_IMPLEMENTED: NvFlexGetAnisotropy
extern "C" void NvFlexGetAnisotropy(NvFlexSolver* s,NvFlexBuffer* a,NvFlexBuffer* b,NvFlexBuffer* c,const NvFlexCopyDesc* d){
    df::ReadData(SolverLibrary(s),a,df::Slot(s->state.mAnisotropy1).buffer,d);df::ReadData(SolverLibrary(s),b,df::Slot(s->state.mAnisotropy2).buffer,d);df::ReadData(SolverLibrary(s),c,df::Slot(s->state.mAnisotropy3).buffer,d);
}
