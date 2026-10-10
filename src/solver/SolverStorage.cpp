#include "SolverState.hpp"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <new>
namespace df {
BufferSlot& Slot(void* storage){return *static_cast<BufferSlot*>(storage);}
ConstantSlot& Constant(void* storage){return *static_cast<ConstantSlot*>(storage);}
void Allocate(NvFlexSolver* solver,void* address,unsigned count,unsigned stride,unsigned flags,NvFlexFormat format,const void* initial){
    NvFlex::BufferDesc desc{};desc.dim=count;desc.stride=stride;desc.bufferType=flags;desc.format=format;desc.data=initial;
    auto native=SolverLibrary(solver)->mContext->createBuffer(&desc);solver->storage.ownedBuffers.push_back(native);
    new(address)BufferSlot{native,desc};
}
void AllocateConstant(NvFlexSolver* solver,void* address,unsigned bytes){
    NvFlex::ConstantBufferDesc desc{};desc.stride=bytes;desc.dim=1;desc.uploadAccess=true;
    auto native=SolverLibrary(solver)->mContext->createConstantBuffer(&desc);solver->storage.ownedConstants.push_back(native);
    new(address)ConstantSlot{desc,native};
}
void ReserveBuffer(NvFlexSolver* solver,void* address,unsigned count,unsigned stride,unsigned flags,NvFlexFormat format){
    auto& slot=Slot(address);if(slot.buffer&&slot.desc.dim>=count&&slot.desc.stride>=stride)return;
    if(slot.buffer){auto& owned=solver->storage.ownedBuffers;owned.erase(std::remove(owned.begin(),owned.end(),slot.buffer),owned.end());delete slot.buffer;}
    Allocate(solver,address,count,stride,flags,format,nullptr);
}
void ReleaseBuffer(NvFlexSolver* solver,void* address){auto& slot=Slot(address);if(slot.buffer){auto& owned=solver->storage.ownedBuffers;owned.erase(std::remove(owned.begin(),owned.end(),slot.buffer),owned.end());delete slot.buffer;}new(address)BufferSlot{};}
void WriteBytes(NvFlexLibrary* library,NvFlex::Buffer* dst,unsigned dstByte,NvFlexBuffer* src,unsigned srcByte,unsigned bytes){
    if(!src||!dst||!bytes)return;
    if(src->type==eNvFlexBufferHost)library->mContext->copyToDevice(dst,dstByte,src->mBuffer,srcByte,bytes,NvFlex::eDownloadBuffer);
    else if(src->type==eNvFlexBufferDevice)library->mContext->copyToDevice(dst,dstByte,src->mBuffer,srcByte,bytes,NvFlex::eDefaultBuffer);
    else if(int(src->type)==3)library->mContext->copyToDevice(dst,dstByte,reinterpret_cast<NvFlex::Buffer*>(src->ptr),srcByte,bytes,NvFlex::eNativeBuffer);
}
void ReadBytes(NvFlexLibrary* library,NvFlexBuffer* dst,unsigned dstByte,NvFlex::Buffer* src,unsigned srcByte,unsigned bytes){
    if(!bytes||!dst)return;
    if(int(dst->type)==3)library->mContext->copyToNative(dst->ptr,dstByte,src,srcByte,bytes);
    else if(dst->type==eNvFlexBufferHost)library->mContext->copyToHost(dst->mBuffer,dstByte,src,srcByte,bytes);
    else if(dst->type==eNvFlexBufferDevice)library->mContext->copyToDevice(dst->mBuffer,dstByte,src,srcByte,bytes,NvFlex::eDefaultBuffer);
}
void ReadData(NvFlexLibrary* library,NvFlexBuffer* dst,NvFlex::Buffer* src,const NvFlexCopyDesc* range){
    if(!dst||!src)return;const unsigned stride=dst->elementByteStride;
    if(stride!=src->m_desc.stride){char text[256];std::snprintf(text,sizeof(text),"Call to an NvFlexGet*() method with incompatible buffer strides, source stride: %d dest stride: %d",src->m_desc.stride,stride);Report(library,eNvFlexLogError,text,"..\\..\\dx\\flex.cpp",198);return;}
    if(!range){ReadBytes(library,dst,0,src,0,unsigned(std::min(dst->elementCount,int(src->m_desc.dim)))*stride);return;}
    if(dst->elementCount<range->dstOffset+range->elementCount){Report(library,eNvFlexLogError,"Call to an NvFlexGet*() method with destination range outside of destination buffer","..\\..\\dx\\flex.cpp",208);return;}
    if(range->srcOffset+range->elementCount>int(src->m_desc.dim)){Report(library,eNvFlexLogError,"Call to an NvFlexGet*() method with source range outside of source buffer","..\\..\\dx\\flex.cpp",214);return;}
    ReadBytes(library,dst,range->dstOffset*stride,src,range->srcOffset*stride,range->elementCount*stride);
}
void WriteData(NvFlexLibrary* library,NvFlex::Buffer* dst,NvFlexBuffer* src,const NvFlexCopyDesc* range){
    if(!src||!dst)return;const unsigned stride=src->elementByteStride;
    if(stride!=dst->m_desc.stride){char text[256];std::snprintf(text,sizeof(text),"Call to an NvFlexSet*() method with incompatible buffer strides, source stride: %d dest stride: %d",stride,dst->m_desc.stride);Report(library,eNvFlexLogError,text,"..\\..\\dx\\flex.cpp",240);return;}
    int count=range?range->elementCount:std::min(src->elementCount,int(dst->m_desc.dim));int from=range?range->srcOffset:0,to=range?range->dstOffset:0;
    if(int(dst->m_desc.dim)<to+count){Report(library,eNvFlexLogError,"Call to an NvFlexSet*() method with destination range outside of destination buffer","..\\..\\dx\\flex.cpp",250);return;}
    if(from+count>src->elementCount){Report(library,eNvFlexLogError,"Call to an NvFlexSet*() method with source range outside of source buffer","..\\..\\dx\\flex.cpp",256);return;}
    if(!count)return;
    WriteBytes(library,dst,to*stride,src,from*stride,count*stride);
}
}
