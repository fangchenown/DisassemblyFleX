#include "solver/SolverState.hpp"
#include <cstring>
#include <vector>
// DF_IMPLEMENTED: NvFlexSetDynamicTriangles
extern "C" void NvFlexSetDynamicTriangles(NvFlexSolver* solver,NvFlexBuffer* triangles,NvFlexBuffer* normals,int count){
    auto& s=solver->state;if(!count){s.mDynamicNumTris=0;return;}auto library=SolverLibrary(solver);
    if(count>s.mDynamicMaxTris){unsigned capacity=unsigned(count*3/2);df::ReserveBuffer(solver,s.mDynamicTriangles,capacity*3,4);df::ReserveBuffer(solver,s.mDynamicTriangleNormals,capacity,12);s.mDynamicMaxTris=capacity;}
    df::WriteBytes(library,df::Slot(s.mDynamicTriangles).buffer,0,triangles,0,count*12);
    df::WriteBytes(library,df::Slot(s.mDynamicTriangleNormals).buffer,0,normals,0,count*12);s.mDynamicNumTris=count;
}
// DF_IMPLEMENTED: NvFlexGetDynamicTriangles
extern "C" void NvFlexGetDynamicTriangles(NvFlexSolver* solver,NvFlexBuffer* triangles,NvFlexBuffer* normals,int count){
    auto library=SolverLibrary(solver);df::ReadBytes(library,triangles,0,df::Slot(solver->state.mDynamicTriangles).buffer,0,count*12);df::ReadBytes(library,normals,0,df::Slot(solver->state.mDynamicTriangleNormals).buffer,0,count*12);
}
// DF_IMPLEMENTED: NvFlexSetInflatables
extern "C" void NvFlexSetInflatables(NvFlexSolver* solver,NvFlexBuffer* starts,NvFlexBuffer* counts,NvFlexBuffer* volumes,NvFlexBuffer* pressures,NvFlexBuffer* scales,int n){
    auto& s=solver->state;auto library=SolverLibrary(solver);auto context=library->mContext;
    if(n>s.mMaxInflatables){unsigned capacity=unsigned(n*3/2);df::ReserveBuffer(solver,s.mInflatables,capacity,16,23);df::ReserveBuffer(solver,s.mPressures,capacity,4);unsigned zero[4]{};context->clearUnorderedAccessViewUint(df::Slot(s.mPressures).buffer,zero);s.mMaxInflatables=capacity;}
    struct Inflatable {int start,count;float volume,scale;};static_assert(sizeof(Inflatable)==16);
    if(n>0){std::vector<Inflatable> data(n);
        for(int i=0;i<n;++i){auto a=static_cast<int*>(NvFlexMap(starts,0));auto b=static_cast<int*>(NvFlexMap(counts,0));auto c=static_cast<float*>(NvFlexMap(volumes,0));auto d=static_cast<float*>(NvFlexMap(pressures,0));auto e=static_cast<float*>(NvFlexMap(scales,0));
            data[i]={a[i],b[i],d[i]*c[i],e[i]};NvFlexUnmap(starts);NvFlexUnmap(counts);NvFlexUnmap(volumes);NvFlexUnmap(pressures);NvFlexUnmap(scales);}
        auto buffer=df::Slot(s.mInflatables).buffer;std::memcpy(context->map(buffer,NvFlex::eMapWrite,true),data.data(),n*sizeof(Inflatable));context->unmap(buffer);context->upload(buffer,0,n*sizeof(Inflatable));
    }
    s.mNumInflatables=n;
}
