#include "geometry/Geometry.hpp"
// DF_IMPLEMENTED: NvFlexSetShapes
extern "C" void NvFlexSetShapes(NvFlexSolver* solver,NvFlexBuffer* geometry,NvFlexBuffer* positions,NvFlexBuffer* rotations,NvFlexBuffer* previousPositions,NvFlexBuffer* previousRotations,NvFlexBuffer* flags,int count){
    auto& shape=df::Shapes(solver);if(!count){shape.count=0;return;}auto lib=SolverLibrary(solver);
    if(count>shape.capacity){unsigned capacity=unsigned(count*3/2);auto& owner=solver->storage.ownedBuffers;
        for(auto slot:{&shape.lower,&shape.upper,&shape.positions,&shape.rotations,&shape.prevPositions,&shape.prevRotations,&shape.geometry})df::ReserveOwned(lib,owner,*slot,capacity,16);
        df::ReserveOwned(lib,owner,shape.flags,capacity,4);shape.capacity=capacity;
    }
    for(auto pair:{std::make_pair(&shape.geometry,geometry),{&shape.positions,positions},{&shape.rotations,rotations},{&shape.prevPositions,previousPositions},{&shape.prevRotations,previousRotations}})
        df::WriteBytes(lib,pair.first->buffer,0,pair.second,0,count*16);
    df::WriteBytes(lib,shape.flags.buffer,0,flags,0,count*4);shape.count=count;shape.rebuild=true;
}
