#include "runtime/Runtime.hpp"
#include "runtime/ShaderLibrary.hpp"
#include "geometry/Geometry.hpp"
#include "runtime/D3D12Context.hpp"
#include <cstdio>
#include <cstring>
#include <memory>
#include <stdexcept>

namespace df {
void Report(NvFlexLibrary* library,NvFlexErrorSeverity severity,const char* message,const char* file,int line){if(library&&library->mErrorFunc)library->mErrorFunc(severity,message,file,line);}
}
// DF_IMPLEMENTED: NvFlexInit
// Device and extension selection reconstructed from RVA 0x35ba0.
extern "C" NvFlexLibrary* NvFlexInit(int version,NvFlexErrorCallback error,NvFlexInitDesc* input){
    if(version!=NV_FLEX_VERSION){if(error){char message[256];std::snprintf(message,sizeof(message),"Could not initialize Flex, header/NvFlexLibrary mismatch, provided: %d, expected: %d",version,NV_FLEX_VERSION);error(eNvFlexLogError,message,"..\\..\\dx\\flex.cpp",699);}return nullptr;}
    NvFlexInitDesc defaults{-1,true,nullptr,nullptr,nullptr,true,eNvFlexD3D11};const auto& desc=input?*input:defaults;
    if(desc.computeType==eNvFlexCUDA){if(error)error(eNvFlexLogError,"Trying to initialize D3D Flex with a CUDA compute type.","..\\..\\dx\\flex.cpp",705);return nullptr;}
    if(desc.computeType!=eNvFlexD3D11&&desc.computeType!=eNvFlexD3D12){if(error)error(eNvFlexLogError,"Could not initialize Flex, error querying devices.","..\\..\\dx\\flex.cpp",0x2ca);return nullptr;}
    auto library=std::make_unique<NvFlexLibrary>();library->mErrorFunc=error;bool deviceReady=false;
    try{
        NvAPI_Initialize();std::unique_ptr<NvFlex::Device> device;
        if(desc.computeType==eNvFlexD3D12)device=std::make_unique<df::DeviceD3D12>(desc,error);else device=std::make_unique<df::DeviceD3D11>(desc,error);
        library->mContext=device->createContext();library->mDevice=device.release();deviceReady=true;
        std::strncpy(library->mDeviceName,library->mDevice->mDeviceName.c_str(),sizeof(library->mDeviceName)-1);
        library->enableExtensions=desc.enableExtensions;
        if(library->mDevice->mGpuVendorId==VENDOR_ID_NVIDIA&&library->mDevice->mSMCount==~0u)library->enableExtensions=false;
        if(library->mDevice->mGpuVendorId==VENDOR_ID_AMD&&library->enableExtensions){
            AGSGPUInfo info{};agsInit(&library->agsContext,nullptr,&info);bool compatible=false;
            if(info.architectureVersion==AGSGPUInfo::ArchitectureVersion_GCN){int major=0,minor=0,patch=0;if(info.radeonSoftwareVersion)std::sscanf(info.radeonSoftwareVersion,"%d.%d.%d",&major,&minor,&patch);compatible=major>15&&(major!=16||(minor>8&&(minor!=9||patch>0)));library->amdDriverWorkaround=!compatible;}
            library->enableExtensions=compatible;
            if(compatible){unsigned supported=0;if(library->mDevice->AGS_DriverExtensions_Init(library->agsContext,7,&supported)==AGS_SUCCESS&&((supported&(1<<10))||(supported&8)))library->swizzleSupported=true;}
        }
        if(library->mDevice->mGpuVendorId==VENDOR_ID_OTHERS)library->enableExtensions=false;
        if(desc.enableExtensions&&library->mDevice->mGpuVendorId==VENDOR_ID_NVIDIA&&library->mDevice->mSMCount!=~0u){
            library->mDevice->NvAPI_IsNvShaderExtnOpCodeSupported(1,&library->shflSupported);
            library->mDevice->NvAPI_IsNvShaderExtnOpCodeSupported(13,&library->fp32AtomicSupported);
        }
        library->sync=library->mContext->createFence();
        std::vector<unsigned> emptyBuckets(1u<<21,0u);NvFlex::BufferDesc grid{};grid.dim=1u<<21;grid.stride=4;grid.bufferType=19;grid.data=emptyBuckets.data();
        library->cellBucketStarts=library->mContext->createBuffer(&grid);library->cellBucketEnds=library->mContext->createBuffer(&grid);
        library->geometry=new df::GeometryStorage(library.get());
        return library.release();
    }catch(const std::exception& exception){
        if(error){if(deviceReady)error(eNvFlexLogError,exception.what(),__FILE__,__LINE__);else error(eNvFlexLogError,"Could not initialize Flex, error querying devices.","..\\..\\dx\\flex.cpp",0x2ca);}
        delete library->mDevice;return nullptr;
    }
}
// DF_IMPLEMENTED: NvFlexShutdown
extern "C" void NvFlexShutdown(NvFlexLibrary* library){
    if(!library)return;
    // Same tracked-resource cleanup order as RVA 0x30a50. A failed allocation
    // tracked as ID 0 also retains the reference's non-terminating error path;
    // boundary diagnostics isolate that behavior in a bounded subprocess.
    while(!library->solvers.empty())NvFlexDestroySolver(library->solvers.front());
    while(!library->geometry->triangleIds.empty())NvFlexDestroyTriangleMesh(library,library->geometry->triangleIds.front());
    while(!library->geometry->sdfIds.empty())NvFlexDestroyDistanceField(library,library->geometry->sdfIds.front());
    while(!library->geometry->convexIds.empty())NvFlexDestroyConvexMesh(library,library->geometry->convexIds.front());
    delete library->geometry;
    df::DestroyShaders(library);
    delete library->cellBucketStarts;delete library->cellBucketEnds;
    if(library->mDevice->mGpuVendorId==VENDOR_ID_AMD)library->mDevice->AGS_DeInit(library->agsContext);
    delete library->sync;library->sync=nullptr;delete library->mDevice;library->mDevice=nullptr;library->mContext=nullptr;delete library;
}
// DF_IMPLEMENTED: NvFlexGetDeviceName
extern "C" const char* NvFlexGetDeviceName(NvFlexLibrary* library){return library->mDeviceName;}
// DF_IMPLEMENTED: NvFlexGetDeviceAndContext
extern "C" void NvFlexGetDeviceAndContext(NvFlexLibrary* library,void** device,void** context){*device=library->mDevice;*context=library->mContext;}
// DF_IMPLEMENTED: NvFlexFlush
extern "C" void NvFlexFlush(NvFlexLibrary* library){library->mContext->flush();}
// DF_IMPLEMENTED: NvFlexWait
extern "C" void NvFlexWait(NvFlexLibrary* library){library->mContext->fenceSet(library->sync);library->mContext->fenceWait(library->sync);}
// DF_IMPLEMENTED: NvFlexComputeWaitForGraphics
extern "C" void NvFlexComputeWaitForGraphics(NvFlexLibrary* library){library->mContext->computeWaitForGraphics();}
// DF_IMPLEMENTED: NvFlexAllocBuffer
extern "C" NvFlexBuffer* NvFlexAllocBuffer(NvFlexLibrary* library,int count,int stride,NvFlexBufferType type){
    auto out=std::make_unique<NvFlexBuffer>();out->mFlexLib=library;out->mContext=library->mContext;out->elementCount=count;out->elementByteStride=stride;out->type=type;
    NvFlex::BufferDesc desc{};desc.dim=static_cast<unsigned>(count);desc.stride=static_cast<unsigned>(stride);desc.format=eNvFlexFormat_unknown;
    desc.bufferType=type==eNvFlexBufferHost?0x14u:(type==eNvFlexBufferDevice?0x11u:0x90u);
    out->mBuffer=out->mContext->createBuffer(&desc);return out.release();
}
// DF_IMPLEMENTED: NvFlexFreeBuffer
extern "C" void NvFlexFreeBuffer(NvFlexBuffer* buffer){if(buffer){delete buffer->mBuffer;buffer->mBuffer=nullptr;buffer->mContext=nullptr;buffer->ptr=nullptr;delete buffer;}}
// DF_IMPLEMENTED: NvFlexMap
extern "C" void* NvFlexMap(NvFlexBuffer* buffer,int flags){
    if(!buffer)return nullptr;
    if(buffer->ptr)df::Report(buffer->mFlexLib,eNvFlexLogWarning,"Mapping a buffer that was already mapped","..\\..\\dx\\utils.cpp",62);
    if(!buffer->mBuffer)return buffer->ptr=nullptr;
    if(buffer->type==eNvFlexBufferHost)buffer->ptr=buffer->mContext->map(buffer->mBuffer,NvFlex::eMapReadWrite,(flags&1)==0);
    else if(buffer->type==eNvFlexBufferDevice)buffer->ptr=buffer->mBuffer->getResource(NvFlex::eDefaultBuffer);
    else if(static_cast<int>(buffer->type)==2)buffer->ptr=buffer->mContext->map(buffer->mBuffer,NvFlex::eMapWriteDiscard,true);
    return buffer->ptr;
}
// DF_IMPLEMENTED: NvFlexUnmap
extern "C" void NvFlexUnmap(NvFlexBuffer* buffer){
    if(!buffer)return;
    if(!buffer->ptr)df::Report(buffer->mFlexLib,eNvFlexLogWarning,"Unmapping a buffer that was not mapped","..\\..\\dx\\utils.cpp",98);
    if(buffer->mBuffer&&(static_cast<int>(buffer->type)&~2)==0)buffer->mContext->unmap(buffer->mBuffer);
    buffer->ptr=nullptr;
}
// DF_IMPLEMENTED: NvFlexRegisterD3DBuffer
extern "C" NvFlexBuffer* NvFlexRegisterD3DBuffer(NvFlexLibrary* library,void* native,int count,int stride){
    auto out=std::make_unique<NvFlexBuffer>();out->mFlexLib=library;out->mContext=library->mContext;out->elementCount=count;out->elementByteStride=stride;out->type=static_cast<NvFlexBufferType>(3);out->ptr=native;return out.release();
}
// DF_IMPLEMENTED: NvFlexUnregisterD3DBuffer
extern "C" void NvFlexUnregisterD3DBuffer(NvFlexBuffer* buffer){NvFlexFreeBuffer(buffer);}
// DF_IMPLEMENTED: NvFlexUnregisterOGLBuffer
extern "C" void NvFlexUnregisterOGLBuffer(NvFlexBuffer* buffer){NvFlexFreeBuffer(buffer);}
