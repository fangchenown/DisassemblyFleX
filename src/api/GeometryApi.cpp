#include "geometry/Geometry.hpp"
#include <algorithm>
#include <cstdio>
#include <cstring>
namespace {
void error(NvFlexLibrary* lib,const char* message,int line){df::Report(lib,eNvFlexLogError,message,"..\\..\\dx\\flex.cpp",line);}
void removeId(std::vector<unsigned>& ids,unsigned id){ids.erase(std::remove(ids.begin(),ids.end(),id),ids.end());}
int listIds(const std::vector<unsigned>& ids,unsigned* output,int n){int count=std::min(n,int(ids.size()));if(count>0)std::memcpy(output,ids.data(),count*4);return int(ids.size());}
}
// DF_IMPLEMENTED: NvFlexCreateTriangleMesh
extern "C" NvFlexTriangleMeshId NvFlexCreateTriangleMesh(NvFlexLibrary* lib){auto& g=*lib->geometry;unsigned i=0;for(;i<g.meshes.size();++i)if(!g.meshes[i])break;if(i==g.meshes.size())g.meshes.emplace_back();g.meshes[i]=std::make_unique<df::GeometryStorage::TriangleMesh>();g.triangleIds.push_back(i+1);return i+1;}
// DF_IMPLEMENTED: NvFlexDestroyTriangleMesh
extern "C" void NvFlexDestroyTriangleMesh(NvFlexLibrary* lib,NvFlexTriangleMeshId id){if(!id){error(lib,"Trying to destroy an invalid triangle mesh",0xa13);return;}auto& g=*lib->geometry;removeId(g.triangleIds,id);g.meshes[id-1].reset();}
// DF_IMPLEMENTED: NvFlexGetTriangleMeshes
extern "C" int NvFlexGetTriangleMeshes(NvFlexLibrary* lib,NvFlexTriangleMeshId* ids,int n){return listIds(lib->geometry->triangleIds,ids,n);}
// DF_IMPLEMENTED: NvFlexGetTriangleMeshNumTriangles
extern "C" int DF_NvFlexGetTriangleMeshNumTriangles(NvFlexLibrary* lib,unsigned id){return lib->geometry->meshes[id-1]->numTris;}
// DF_IMPLEMENTED: NvFlexGetTriangleMeshNumVertices
extern "C" int DF_NvFlexGetTriangleMeshNumVertices(NvFlexLibrary* lib,unsigned id){return lib->geometry->meshes[id-1]->numVertices;}
// DF_IMPLEMENTED: NvFlexGetShapeBVH
// The reference export is a three-byte no-op (RVA 0x42290).
extern "C" void NvFlexGetShapeBVH(NvFlexSolver*,void*){}
// DF_IMPLEMENTED: NvFlexGetTriangleMeshBounds
extern "C" void NvFlexGetTriangleMeshBounds(NvFlexLibrary* lib,NvFlexTriangleMeshId id,float* lower,float* upper){
    if(!id){error(lib,"Trying to query bounds of an invalid triangle mesh",0xa8b);return;}auto& m=lib->geometry->meshes[id-1];if(!m){error(lib,"Trying to query bounds of an invalid triangle mesh",0xa92);return;}
    std::memcpy(lower,m->lower,12);std::memcpy(upper,m->upper,12);
}
// DF_IMPLEMENTED: NvFlexUpdateTriangleMesh
extern "C" void NvFlexUpdateTriangleMesh(NvFlexLibrary* lib,NvFlexTriangleMeshId id,NvFlexBuffer* vertices,NvFlexBuffer* indices,int numVertices,int numTris,const float* lower,const float* upper){
    if(!id){error(lib,"Trying to update an invalid triangle mesh",0xa24);return;}auto& g=*lib->geometry;auto& ptr=g.meshes[id-1];if(!ptr){error(lib,"Trying to update an invalid triangle mesh",0xa2c);return;}
    if(!lower||!upper){error(lib,"Spatial bounds of mesh cannot be null",0xa32);return;}auto& m=*ptr;if(!numVertices||!numTris){m.numVertices=m.numTris=0;return;}
    if(numTris>m.maxTris){m.maxTris=numTris*3/2;df::ReserveOwned(lib,m.owned,m.indices,m.maxTris*3,4,23);}
    if(numVertices>m.maxVertices){m.maxVertices=numVertices*3/2;df::ReserveOwned(lib,m.owned,m.vertices,m.maxVertices,16,23);}
    m.numTris=numTris;m.numVertices=numVertices;m.numIndices=numTris*3;std::memcpy(m.lower,lower,12);std::memcpy(m.upper,upper,12);
    df::WriteBytes(lib,m.vertices.buffer,0,vertices,0,numVertices*16);df::WriteBytes(lib,m.indices.buffer,0,indices,0,numTris*12);
    auto ctx=lib->mContext;std::memcpy(ctx->map(g.triangleInfo),&numTris,4);ctx->unmap(g.triangleInfo);
    if(unsigned(numTris)>g.maxStaticTris){g.maxStaticTris=numTris*3/2;df::ReserveOwned(lib,g.owned,g.staticLower,g.maxStaticTris,16);df::ReserveOwned(lib,g.owned,g.staticUpper,g.maxStaticTris,16);}
    df::GeometryPass(lib,"g_Flex_ComputeTriangleBounds",unsigned(numTris+255)/256,g.triangleInfo,{{0,m.vertices.buffer},{1,m.indices.buffer}},{{0,g.staticLower.buffer},{1,g.staticUpper.buffer}});
    float bounds[6];std::memcpy(bounds,lower,12);std::memcpy(bounds+3,upper,12);g.bvh.build(m.bvh,m.owned,g.staticLower.buffer,g.staticUpper.buffer,numTris,bounds);g.rebuildTriangles=true;
}
// DF_IMPLEMENTED: NvFlexCreateConvexMesh
extern "C" NvFlexConvexMeshId NvFlexCreateConvexMesh(NvFlexLibrary* lib){auto& g=*lib->geometry;unsigned id=g.convexCount<4096?g.convexFree[g.convexCount++]+1:0;g.convexIds.push_back(id);return id;}
// DF_IMPLEMENTED: NvFlexDestroyConvexMesh
extern "C" void NvFlexDestroyConvexMesh(NvFlexLibrary* lib,NvFlexConvexMeshId id){if(!id){error(lib,"Trying to destroy an invalid convex mesh",0x9d6);return;}auto& g=*lib->geometry;removeId(g.convexIds,id);g.convexFree[--g.convexCount]=id-1;}
// DF_IMPLEMENTED: NvFlexGetConvexMeshes
extern "C" int NvFlexGetConvexMeshes(NvFlexLibrary* lib,NvFlexConvexMeshId* ids,int n){return listIds(lib->geometry->convexIds,ids,n);}
// DF_IMPLEMENTED: NvFlexUpdateConvexMesh
extern "C" void NvFlexUpdateConvexMesh(NvFlexLibrary* lib,NvFlexConvexMeshId id,NvFlexBuffer* planes,int count,const float* lower,const float* upper){
    if(!id){error(lib,"Trying to destroy an invalid convex mesh",0x9e7);return;}
    if(count>64){char message[128];std::snprintf(message,sizeof(message),"Trying to update a convex mesh with too many planes %d > %d",count,64);df::Report(lib,eNvFlexLogWarning,message,"..\\..\\dx\\flex.cpp",0x9ed);return;}
    auto& g=*lib->geometry;auto ctx=lib->mContext;unsigned first=(id-1)*64;if(count)ctx->copyToDevice(g.convexPlanes.buffer,first*16,planes->mBuffer,0,count*16,NvFlex::eDownloadBuffer);
    unsigned offset=(id-1)*48;auto data=static_cast<unsigned char*>(ctx->map(g.convexTable.buffer,NvFlex::eMapWrite,true))+offset;
    std::memset(data,0,48);std::memcpy(data,lower,12);std::memcpy(data+16,upper,12);std::memcpy(data+32,&first,4);std::memcpy(data+36,&count,4);ctx->unmap(g.convexTable.buffer);ctx->upload(g.convexTable.buffer,offset,48);
}
// DF_IMPLEMENTED: NvFlexGetConvexMeshBounds
extern "C" void NvFlexGetConvexMeshBounds(NvFlexLibrary* lib,NvFlexConvexMeshId id,float* lower,float* upper){
    if(!id){error(lib,"Trying to query bounds for an invalid convex mesh",0x9f8);return;}auto ctx=lib->mContext;auto b=lib->geometry->convexTable.buffer;unsigned offset=(id-1)*48;
    ctx->download(b,offset,48);auto data=static_cast<unsigned char*>(ctx->map(b,NvFlex::eMapRead,true))+offset;std::memcpy(lower,data,12);std::memcpy(upper,data+16,12);ctx->unmap(b);
}
// DF_IMPLEMENTED: NvFlexCreateDistanceField
extern "C" NvFlexDistanceFieldId NvFlexCreateDistanceField(NvFlexLibrary* lib){auto& g=*lib->geometry;unsigned id=g.sdfCount<16?g.sdfFree[g.sdfCount++]+1:0;g.sdfIds.push_back(id);return id;}
// DF_IMPLEMENTED: NvFlexDestroyDistanceField
extern "C" void NvFlexDestroyDistanceField(NvFlexLibrary* lib,NvFlexDistanceFieldId id){if(!id){error(lib,"Trying to update an invalid SDF",0x8fe);return;}auto& g=*lib->geometry;removeId(g.sdfIds,id);delete g.textures[id-1];g.textures[id-1]=nullptr;g.sdfFree[--g.sdfCount]=id-1;}
// DF_IMPLEMENTED: NvFlexGetDistanceFields
extern "C" int NvFlexGetDistanceFields(NvFlexLibrary* lib,NvFlexDistanceFieldId* ids,int n){return listIds(lib->geometry->sdfIds,ids,n);}
// DF_IMPLEMENTED: NvFlexUpdateDistanceField
extern "C" void NvFlexUpdateDistanceField(NvFlexLibrary* lib,NvFlexDistanceFieldId id,int x,int y,int z,NvFlexBuffer* field){
    if(!id){error(lib,"Trying to update an invalid SDF",0x911);return;}auto& g=*lib->geometry;auto ctx=lib->mContext;delete g.textures[id-1];g.textures[id-1]=nullptr;
    NvFlex::Texture3DDesc desc{};desc.format=static_cast<NvFlexFormat>(2);desc.dim={unsigned(x),unsigned(y),unsigned(z)};desc.uploadAccess=true;desc.data=ctx->map(field->mBuffer,NvFlex::eMapRead,true);
    g.textures[id-1]=ctx->createTexture3D(&desc);ctx->unmap(field->mBuffer);
    struct Record {int dims[4];float inverse[4];} record{{x,y,z,0},{1.0f/float(x),1.0f/float(y),1.0f/float(z),0}};
    unsigned offset=(id-1)*32;auto p=static_cast<unsigned char*>(ctx->map(g.sdfTable.buffer,NvFlex::eMapWrite,true));std::memcpy(p+offset,&record,32);ctx->unmap(g.sdfTable.buffer);ctx->upload(g.sdfTable.buffer,offset,32);
}
