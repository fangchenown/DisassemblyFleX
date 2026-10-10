#include "NvFlex.h"
#include "recovered/FlexLayouts.hpp"
#include <cstring>
namespace R=nvflex_recovered;
static R::NvFlexSolver& view(NvFlexSolver* s){return *reinterpret_cast<R::NvFlexSolver*>(s);}
static const R::NvFlexSolver& view(const NvFlexSolver* s){return *reinterpret_cast<const R::NvFlexSolver*>(s);}

// DF_RESTORED: NvFlexGetVersion
extern "C" int NvFlexGetVersion(){return 120;}
// DF_RESTORED: NvFlexSetSolverDescDefaults
extern "C" void NvFlexSetSolverDescDefaults(NvFlexSolverDesc* d){
    d->featureMode=eNvFlexFeatureModeDefault;d->maxParticles=16384;d->maxDiffuseParticles=0;
    d->maxNeighborsPerParticle=96;d->maxContactsPerParticle=6;
}
// DF_RESTORED: NvFlexMakePhaseWithChannels
extern "C" int DF_NvFlexMakePhaseWithChannels(int group,int flags,int channels){return (group&0xfffff)|(flags&0xf00000)|(channels&0x7f000000);}
// DF_RESTORED: NvFlexMakePhase
extern "C" int DF_NvFlexMakePhase(int group,int flags){return DF_NvFlexMakePhaseWithChannels(group,flags,0x7f000000);}
// DF_RESTORED: NvFlexMakeShapeFlagsWithChannels
extern "C" int DF_NvFlexMakeShapeFlagsWithChannels(int type,bool dynamic,int channels){return type|(dynamic?8:0)|channels;}
// DF_RESTORED: NvFlexMakeShapeFlags
extern "C" int DF_NvFlexMakeShapeFlags(int type,bool dynamic){return DF_NvFlexMakeShapeFlagsWithChannels(type,dynamic,0x7f000000);}
// DF_RESTORED: NvFlexGetMaxNumParticles
extern "C" int DF_NvFlexGetMaxNumParticles(const NvFlexSolver* s){return view(s).mMaxParticles;}
// DF_RESTORED: NvFlexGetMaxDiffuseParticles
extern "C" int DF_NvFlexGetMaxDiffuseParticles(const NvFlexSolver* s){return view(s).mMaxDiffuseParticles;}
// DF_RESTORED: NvFlexGetMaxNeighborsPerParticle
extern "C" int DF_NvFlexGetMaxNeighborsPerParticle(const NvFlexSolver* s){return view(s).mMaxNeighborsPerParticle;}
// DF_RESTORED: NvFlexGetNumParticles
extern "C" int DF_NvFlexGetNumParticles(const NvFlexSolver* s){return view(s).mNumParticles;}
// DF_RESTORED: NvFlexGetNumSprings
extern "C" int DF_NvFlexGetNumSprings(const NvFlexSolver* s){return view(s).mNumSprings;}
// DF_RESTORED: NvFlexGetNumDynamicTriangles
extern "C" int DF_NvFlexGetNumDynamicTriangles(const NvFlexSolver* s){return view(s).mDynamicNumTris;}
// DF_RESTORED: NvFlexGetNumRigids
extern "C" int DF_NvFlexGetNumRigids(const NvFlexSolver* s){return view(s).mNumRigids;}
// DF_RESTORED: NvFlexGetNumShapes
extern "C" int DF_NvFlexGetNumShapes(const NvFlexSolver* s){
    std::int64_t first,last;std::memcpy(&first,view(s).mSDFDeviceShapes,8);std::memcpy(&last,view(s).mSDFDeviceShapes+8,8);
    return static_cast<int>((last-first)>>3);
}
// DF_RESTORED: NvFlexAcquireContext
extern "C" void NvFlexAcquireContext(NvFlexLibrary*){}
// DF_RESTORED: NvFlexRestoreContext
extern "C" void NvFlexRestoreContext(NvFlexLibrary*){}
// DF_RESTORED: NvFlexSetActiveCount
extern "C" void NvFlexSetActiveCount(NvFlexSolver* s,int n){view(s).mNumParticles=n;view(s).mNumParticlesAligned=n;}
// DF_RESTORED: NvFlexGetActiveCount
extern "C" int NvFlexGetActiveCount(NvFlexSolver* s){return view(s).mNumParticles;}
// DF_RESTORED: NvFlexSetDebug
extern "C" void NvFlexSetDebug(NvFlexSolver* s,bool enabled){view(s).mDebug=enabled;}
// DF_RESTORED: NvFlexGetSolverLibrary
extern "C" NvFlexLibrary* NvFlexGetSolverLibrary(NvFlexSolver* s){NvFlexLibrary* p;std::memcpy(&p,view(s).mLib,8);return p;}
// DF_RESTORED: NvFlexGetParams
extern "C" void NvFlexGetParams(NvFlexSolver* s,NvFlexParams* p){static_assert(sizeof(*p)==sizeof(view(s).mParams));std::memcpy(p,&view(s).mParams,sizeof(*p));}
// DF_RESTORED: NvFlexRegisterSolverCallback
extern "C" NvFlexSolverCallback NvFlexRegisterSolverCallback(NvFlexSolver* s,NvFlexSolverCallback callback,NvFlexSolverCallbackStage stage){
    NvFlexSolverCallback previous;auto p=view(s).mCallbacks+sizeof(callback)*static_cast<int>(stage);
    std::memcpy(&previous,p,sizeof(previous));std::memcpy(p,&callback,sizeof(callback));return previous;
}
