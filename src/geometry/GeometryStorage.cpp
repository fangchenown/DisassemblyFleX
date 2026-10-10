#include "Geometry.hpp"
#include <cstring>
#include <numeric>
namespace df {
GeometryStorage::GeometryStorage(NvFlexLibrary* l):bvh(l){
    std::iota(convexFree.begin(),convexFree.end(),0u);std::iota(sdfFree.begin(),sdfFree.end(),0u);
    ReserveOwned(l,owned,convexPlanes,4096*64,16,23);ReserveOwned(l,owned,convexTable,4096,48,23);ReserveOwned(l,owned,sdfTable,16,32,23);
    NvFlex::ConstantBufferDesc desc{};desc.dim=1;desc.stride=4;desc.uploadAccess=true;triangleInfo=l->mContext->createConstantBuffer(&desc);
}
GeometryStorage::~GeometryStorage(){for(auto p:owned)delete p;for(auto t:textures)delete t;delete triangleInfo;}
void FlattenTriangleMeshes(NvFlexLibrary* lib){
    auto& g=*lib->geometry;auto ctx=lib->mContext;unsigned vertices=0,triangles=0,meshes=unsigned(g.meshes.size());
    for(auto& m:g.meshes)if(m){vertices+=m->numVertices;triangles+=m->numTris;}
    if(vertices>g.maxVertices){g.maxVertices=vertices*3/2;ReserveOwned(lib,g.owned,g.vertices,g.maxVertices,16);}
    if(triangles>g.maxTriangles){g.maxTriangles=triangles*3/2;ReserveOwned(lib,g.owned,g.indices,g.maxTriangles*3,4);ReserveOwned(lib,g.owned,g.nodeLower,g.maxTriangles*2,16);ReserveOwned(lib,g.owned,g.nodeUpper,g.maxTriangles*2,16);}
    if(meshes>g.maxMeshes){g.maxMeshes=meshes*3/2;ReserveOwned(lib,g.owned,g.rootNodes,g.maxMeshes,4);ReserveOwned(lib,g.owned,g.meshTable,g.maxMeshes,48,23);}
    struct Record {float lower[4],upper[4];unsigned indexOffset,vertexOffset,nodeOffset,padding;};static_assert(sizeof(Record)==48);
    std::vector<Record> table(meshes);unsigned vertexOffset=0,indexOffset=0,nodeOffset=0;
    for(unsigned i=0;i<meshes;++i)if(auto& mesh=g.meshes[i]){
        auto& m=*mesh;auto copy=[&](BufferSlot& dst,unsigned offset,BufferSlot& src,unsigned bytes){if(bytes)ctx->copy(dst.buffer,offset,src.buffer,0,bytes);};
        copy(g.vertices,vertexOffset*16,m.vertices,m.numVertices*16);copy(g.indices,indexOffset*4,m.indices,m.numIndices*4);
        copy(g.nodeLower,nodeOffset*16,m.bvh.lower,m.bvh.numNodes*16);copy(g.nodeUpper,nodeOffset*16,m.bvh.upper,m.bvh.numNodes*16);copy(g.rootNodes,i*4,m.bvh.root,4);
        auto& r=table[i];std::memcpy(r.lower,m.lower,12);std::memcpy(r.upper,m.upper,12);r.indexOffset=indexOffset;r.vertexOffset=vertexOffset;r.nodeOffset=nodeOffset;
        indexOffset+=m.numIndices;vertexOffset+=m.numVertices;nodeOffset+=m.bvh.numNodes;
    }
    if(meshes){std::memcpy(ctx->map(g.meshTable.buffer,NvFlex::eMapWrite,true),table.data(),meshes*48);ctx->unmap(g.meshTable.buffer);ctx->upload(g.meshTable.buffer,0,meshes*48);}
}
}
