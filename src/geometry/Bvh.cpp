#include "Geometry.hpp"
#include "runtime/ShaderLibrary.hpp"
#include <algorithm>
#include <cstring>
namespace df {
void ReserveOwned(NvFlexLibrary* lib,std::vector<NvFlex::Buffer*>& owned,BufferSlot& slot,unsigned count,unsigned stride,unsigned flags,bool zero){
    if(slot.buffer&&slot.desc.dim>=count&&slot.desc.stride>=stride)return;
    if(slot.buffer){owned.erase(std::remove(owned.begin(),owned.end(),slot.buffer),owned.end());delete slot.buffer;}
    slot={};slot.desc.dim=count;slot.desc.stride=stride;slot.desc.bufferType=flags;
    std::vector<unsigned char> initial;if(zero){initial.resize(size_t(count)*stride);slot.desc.data=initial.data();}
    slot.buffer=lib->mContext->createBuffer(&slot.desc);slot.desc.data=nullptr;owned.push_back(slot.buffer);
}
void GeometryPass(NvFlexLibrary* lib,const char* name,unsigned blocks,NvFlex::ConstantBuffer* cb,std::initializer_list<GeometryBinding> reads,std::initializer_list<GeometryBinding> writes,SolverStorage::Timers* timers){
    NvFlex::DispatchParams p{};p.shader=GetShader(lib,name);p.gridDim={blocks,1,1};p.rootConstantBuffer=cb;
    for(auto b:reads)if(b.second)p.readOnly[b.first]=b.second->getResource();
    for(auto b:writes)if(b.second)p.readWrite[b.first]=b.second->getResourceRW();
    int timer=-1;if(timers&&timers->mEnabled){timer=timers->mTimerPool->begin();timers->mNameToTimerMapW.emplace(p.shader->m_desc.label,timer);}
    lib->mContext->dispatch(&p);if(timer>=0)timers->mTimerPool->end(timer);
}
BvhBuilder::BvhBuilder(NvFlexLibrary* l):library(l){
    NvFlex::ConstantBufferDesc desc{};desc.dim=1;desc.stride=4;desc.uploadAccess=true;constant=l->mContext->createConstantBuffer(&desc);
    ReserveOwned(l,owned,totalLower,1,12,23,true);ReserveOwned(l,owned,totalUpper,1,12,19,true);ReserveOwned(l,owned,inverseEdges,1,12,23,true);
}
BvhBuilder::~BvhBuilder(){for(auto p:owned)delete p;delete constant;}
void BvhBuilder::build(BVH& tree,std::vector<NvFlex::Buffer*>& treeOwned,NvFlex::Buffer* itemLower,NvFlex::Buffer* itemUpper,int count,const float* bounds,SolverStorage::Timers* timers){
    auto ctx=library->mContext;
    if(count*2>tree.maxNodes){tree.maxNodes=count*3;ReserveOwned(library,treeOwned,tree.lower,tree.maxNodes,16);ReserveOwned(library,treeOwned,tree.upper,tree.maxNodes,16);ReserveOwned(library,treeOwned,tree.root,1,4);}
    tree.numNodes=count*2;
    if(unsigned(count)>maxItems){maxItems=count*3/2;unsigned nodes=count*3;
        ReserveOwned(library,owned,deltas,maxItems,4);ReserveOwned(library,owned,lefts,nodes,4);ReserveOwned(library,owned,rights,nodes,4);ReserveOwned(library,owned,children,nodes,4,19,true);
        unsigned blocks=(maxItems+255)/256,groups=(blocks+255)/256;
        ReserveOwned(library,owned,lower,blocks,16,19,true);ReserveOwned(library,owned,upper,blocks,16,19,true);ReserveOwned(library,owned,groupLower,groups,16,19,true);ReserveOwned(library,owned,groupUpper,groups,16,19,true);
    }
    std::memcpy(ctx->map(constant),&count,4);ctx->unmap(constant);
    unsigned rounded=(unsigned(count)+1023)/1024*1024,blocks=rounded/256;
    auto pass=[&](const char* name,unsigned n,std::initializer_list<GeometryBinding> reads,std::initializer_list<GeometryBinding> writes){GeometryPass(library,name,n,constant,reads,writes,timers);};
    if(bounds){
        float inv[3];for(int j=0;j<3;++j)inv[j]=1.0f/((bounds[j+3]-bounds[j])+.0001f);
        auto upload=[&](NvFlex::Buffer* b,const float* data){std::memcpy(ctx->map(b,NvFlex::eMapWrite,true),data,12);ctx->unmap(b);ctx->upload(b,0,12);};
        upload(inverseEdges.buffer,inv);upload(totalLower.buffer,bounds);
    }else{
        std::string suffix=library->enableExtensions&&library->shflSupported?"NV":"";
        if(library->swizzleSupported)suffix="AMD";
        pass(("g_bvh_ComputeTotalBounds"+suffix).c_str(),blocks,{{0,itemLower},{1,itemUpper}},{{0,lower.buffer},{1,upper.buffer},{2,totalLower.buffer},{3,totalUpper.buffer}});
        pass(("g_bvh_ComputeTotalBoundsGroup"+suffix).c_str(),(blocks+255)/256,{{2,lower.buffer},{3,upper.buffer}},{{0,groupLower.buffer},{1,groupUpper.buffer},{2,totalLower.buffer},{3,totalUpper.buffer}});
        pass(("g_bvh_ComputeTotalBoundsFinalize"+suffix).c_str(),1,{{2,groupLower.buffer},{3,groupUpper.buffer}},{{2,totalLower.buffer},{3,totalUpper.buffer},{4,inverseEdges.buffer}});
    }
    if(!radix||radix->capacity()<unsigned(count))radix=std::make_unique<RadixSort>(library,(unsigned(count)+1023)/1024);
    pass("g_bvh_CalculateMortonCodes",blocks,{{0,itemLower},{1,itemUpper},{2,totalLower.buffer},{3,inverseEdges.buffer}},{{0,radix->front.value},{1,radix->front.key}});
    radix->sort(count,32,timers);
    pass("g_bvh_CalculateKeyDeltas",blocks,{{0,radix->front.key}},{{0,deltas.buffer}});
    pass("g_bvh_BuildLeaves",blocks,{{0,itemLower},{1,itemUpper},{2,radix->front.value}},{{0,lefts.buffer},{1,rights.buffer},{2,tree.lower.buffer},{3,tree.upper.buffer}});
    unsigned zero[4]{};ctx->clearUnorderedAccessViewUint(children.buffer,zero);
    pass("g_bvh_BuildHierarchy",blocks,{{0,itemLower},{1,itemUpper},{2,deltas.buffer}},{{0,lefts.buffer},{1,rights.buffer},{2,tree.lower.buffer},{3,tree.upper.buffer},{4,children.buffer},{5,tree.root.buffer}});
}
void RebuildGeometry(NvFlexSolver* solver){
    auto lib=SolverLibrary(solver);auto& geometry=*lib->geometry;
    if(geometry.rebuildTriangles){auto& timers=solver->storage.timerState;int timer=-1;if(timers.mEnabled){timer=timers.mTimerPool->begin();timers.mNameToTimerMapW.emplace(L"FlattenTriangleMeshes",timer);}FlattenTriangleMeshes(lib);geometry.rebuildTriangles=false;if(timer>=0)timers.mTimerPool->end(timer);}
    auto& shape=Shapes(solver);if(!shape.rebuild)return;
    auto cb=Constant(solver->state.mNumShapes).buffer;std::memcpy(lib->mContext->map(cb),&shape.count,4);lib->mContext->unmap(cb);
    GeometryPass(lib,"g_Flex_TransformShapeBounds",unsigned(shape.count+255)/256,cb,
        {{0,shape.positions.buffer},{1,shape.rotations.buffer},{2,shape.prevPositions.buffer},{3,shape.prevRotations.buffer},{4,shape.flags.buffer},{5,shape.geometry.buffer},{6,geometry.convexTable.buffer},{7,geometry.meshTable.buffer}},
        {{0,shape.lower.buffer},{1,shape.upper.buffer}},&solver->storage.timerState);
    lib->geometry->bvh.build(shape.bvh,solver->storage.ownedBuffers,shape.lower.buffer,shape.upper.buffer,shape.count,nullptr,&solver->storage.timerState);shape.rebuild=false;
}
}
