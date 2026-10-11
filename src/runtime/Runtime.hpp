#pragma once
#include "D3D11Context.hpp"
#include "recovered/FlexLayouts.hpp"
#include <vector>
namespace df {struct GeometryStorage;}

struct NvFlexLibrary {
    NvFlexErrorCallback mErrorFunc=nullptr;
    NvFlex::Device* mDevice=nullptr;
    NvFlex::Context* mContext=nullptr;
    char mDeviceName[256]{};
    NvFlex::Fence* sync=nullptr;
    bool enableExtensions=false;
    bool shflSupported=false;
    bool fp32AtomicSupported=false;
    bool swizzleSupported=false;
    bool amdDriverWorkaround=false;
    AGSContext* agsContext=nullptr;
    std::vector<NvFlexSolver*> solvers;
    std::map<std::string,NvFlex::ComputeShader*,std::less<>> shaders;
    NvFlex::Buffer* cellBucketStarts=nullptr;
    NvFlex::Buffer* cellBucketEnds=nullptr;
    df::GeometryStorage* geometry=nullptr;
};
struct NvFlexBuffer {
    bool mapped=false;
    NvFlexBufferType type=eNvFlexBufferHost;
    NvFlex::Buffer* mBuffer=nullptr;
    void* ptr=nullptr;
    int elementCount=0,elementByteStride=0,mLastUsedFlag=0;
    NvFlex::Context* mContext=nullptr;
    NvFlexLibrary* mFlexLib=nullptr;
};
static_assert(sizeof(NvFlexBuffer)==56);
static_assert(offsetof(NvFlexBuffer,mBuffer)==8&&offsetof(NvFlexBuffer,mFlexLib)==48);
namespace df {
void Report(NvFlexLibrary*,NvFlexErrorSeverity,const char*,const char*,int);
}
