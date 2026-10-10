#pragma once
#include "solver/SolverState.hpp"
#include <initializer_list>
namespace df {
using GeometryBinding=std::pair<unsigned,NvFlex::Buffer*>;
struct BVH {
    BufferSlot lower,upper,root;
    int numNodes=0,maxNodes=0,maxDepth=0;
};
static_assert(sizeof(BVH)==112);
struct ShapeData {
    BufferSlot lower,upper,geometry,positions,rotations,prevPositions,prevRotations,flags;
    BVH bvh;
    int count=0,capacity=0;
    float boundsLower[3]{},boundsUpper[3]{};
    bool rebuild=false;
};
static_assert(sizeof(ShapeData)==408&&offsetof(ShapeData,count)==0x170);
inline ShapeData& Shapes(NvFlexSolver* s){return *reinterpret_cast<ShapeData*>(s->state.mShapes);}
void ReserveOwned(NvFlexLibrary*,std::vector<NvFlex::Buffer*>&,BufferSlot&,unsigned,unsigned,unsigned=19,bool=false);
void GeometryPass(NvFlexLibrary*,const char*,unsigned,NvFlex::ConstantBuffer*,std::initializer_list<GeometryBinding>,std::initializer_list<GeometryBinding>,SolverStorage::Timers* =nullptr);
class BvhBuilder {
public:
    explicit BvhBuilder(NvFlexLibrary*);
    ~BvhBuilder();
    void build(BVH&,std::vector<NvFlex::Buffer*>&,NvFlex::Buffer*,NvFlex::Buffer*,int,const float* bounds=nullptr,SolverStorage::Timers* timers=nullptr);
private:
    NvFlexLibrary* library;
    std::vector<NvFlex::Buffer*> owned;
    BufferSlot deltas,lefts,rights,children,totalLower,totalUpper,inverseEdges,lower,upper,groupLower,groupUpper;
    NvFlex::ConstantBuffer* constant=nullptr;
    std::unique_ptr<RadixSort> radix;
    unsigned maxItems=0;
};
struct GeometryStorage {
    explicit GeometryStorage(NvFlexLibrary*);
    ~GeometryStorage();
    BvhBuilder bvh;
    struct TriangleMesh {
        BufferSlot vertices,indices;BVH bvh;
        int numTris=0,numVertices=0,numIndices=0,maxTris=0,maxVertices=0;
        float lower[3]{},upper[3]{};
        std::vector<NvFlex::Buffer*> owned;
        ~TriangleMesh(){for(auto p:owned)delete p;}
    };
    std::vector<std::unique_ptr<TriangleMesh>> meshes;
    std::vector<unsigned> triangleIds,convexIds,sdfIds;
    std::vector<NvFlex::Buffer*> owned;
    BufferSlot meshTable,vertices,indices,nodeLower,nodeUpper,rootNodes,staticLower,staticUpper,convexTable,convexPlanes,sdfTable;
    NvFlex::ConstantBuffer* triangleInfo=nullptr;
    std::array<unsigned,4096> convexFree{};
    std::array<unsigned,16> sdfFree{};
    std::array<NvFlex::Texture3D*,16> textures{};
    unsigned convexCount=0,sdfCount=0,maxStaticTris=0,maxVertices=0,maxTriangles=0,maxMeshes=0;
    bool rebuildTriangles=false;
};
void FlattenTriangleMeshes(NvFlexLibrary*);
void RebuildGeometry(NvFlexSolver*);
}
