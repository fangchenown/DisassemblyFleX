// Manually normalized from the corresponding original DLL instructions.
#pragma once
#include "FlexLayouts.hpp"
#include <cstring>
namespace nvflex_recovered {
inline int NvFlexGetVersion() { return 120; } // RVA 0x37c30
inline int NvFlexMakePhaseWithChannels(int group,int flags,int channels) { // RVA 0x29e10
    return (group & 0x000fffff) | (flags & 0x00f00000) | (channels & 0x7f000000);
}
inline int NvFlexMakePhase(int group,int flags) { // RVA 0x29e30
    return NvFlexMakePhaseWithChannels(group,flags,0x7f000000);
}
inline int NvFlexMakeShapeFlagsWithChannels(int type,bool dynamic,int channels) { // RVA 0x29e50
    return type | (dynamic?8:0) | channels;
}
inline int NvFlexMakeShapeFlags(int type,bool dynamic) { // RVA 0x29e60
    return NvFlexMakeShapeFlagsWithChannels(type,dynamic,0x7f000000);
}
inline void NvFlexSetSolverDescDefaults(NvFlexSolverDesc* desc) { // RVA 0x37f60
    desc->featureMode=0;desc->maxParticles=16384;desc->maxDiffuseParticles=0;
    desc->maxNeighborsPerParticle=96;desc->maxContactsPerParticle=6;
}
inline int NvFlexGetMaxNumParticles(const NvFlexSolver* s) { return s->mMaxParticles; } // RVA 0x421f0
inline int NvFlexGetMaxDiffuseParticles(const NvFlexSolver* s) { return s->mMaxDiffuseParticles; } // RVA 0x42200
inline int NvFlexGetMaxNeighborsPerParticle(const NvFlexSolver* s) { return s->mMaxNeighborsPerParticle; } // RVA 0x42210
inline int NvFlexGetNumParticles(const NvFlexSolver* s) { return s->mNumParticles; } // RVA 0x42220
inline int NvFlexGetNumSprings(const NvFlexSolver* s) { return s->mNumSprings; } // RVA 0x42230
inline int NvFlexGetNumDynamicTriangles(const NvFlexSolver* s) { return s->mDynamicNumTris; } // RVA 0x42240
inline int NvFlexGetNumRigids(const NvFlexSolver* s) { return s->mNumRigids; } // RVA 0x42250
inline int NvFlexGetNumShapes(const NvFlexSolver* s) { // RVA 0x42260: actual DLL reads the SDF pointer vector.
    std::int64_t begin,end;std::memcpy(&begin,s->mSDFDeviceShapes,8);std::memcpy(&end,s->mSDFDeviceShapes+8,8);
    return static_cast<int>((end-begin)>>3);
}
} // namespace nvflex_recovered
