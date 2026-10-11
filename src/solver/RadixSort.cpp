#include "RadixSort.hpp"
#include "SolverState.hpp"
#include "runtime/ShaderLibrary.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <stdexcept>
namespace df {
RadixSort::RadixSort(NvFlexLibrary* owner,unsigned blocks):library(owner),maxBlocks(blocks){
    auto context=library->mContext;
    auto make=[&](unsigned count){NvFlex::BufferDesc d{};d.dim=count;d.stride=4;d.bufferType=3;d.format=eNvFlexFormat_r32_uint;auto b=context->createBuffer(&d);owned.push_back(b);return b;};
    auto view=[&](NvFlex::Buffer* source){NvFlex::BufferViewDesc d{eNvFlexFormat_r32g32b32a32_uint};auto b=context->createBufferView(source,&d);owned.push_back(b);return b;};
    front.key=make(capacity());front.value=make(capacity());back.key=make(capacity());back.value=make(capacity());
    front.key4=view(front.key);front.value4=view(front.value);back.key4=view(back.key);back.value4=view(back.value);
    countersFront.scalar=make(maxBlocks*32);countersBack.scalar=make(maxBlocks*32);
    countersFront.vector=view(countersFront.scalar);countersBack.vector=view(countersBack.scalar);
    NvFlex::ConstantBufferDesc cb{24,1,true};constants=context->createConstantBuffer(&cb);
    // Labels and bytecode come from the recovered HLSL registry.
    for(auto name:{"g_RadixSortBlockCS","g_RadixSort1CS","g_RadixSort2CS","g_RadixSort3CS"})GetShader(library,name);
}
RadixSort::~RadixSort(){for(auto p:wide)delete p;for(auto p:owned)delete p;delete constants;}
bool RadixSort::reserveWide(unsigned keys){
    if(wideCapacity>=keys)return true;
    NvFlex::Buffer* next[4]{};
    try{for(unsigned i=0;i<4;++i){NvFlex::BufferDesc d{};d.dim=i<2?keys:keys/1024;d.stride=4;d.bufferType=3;d.format=eNvFlexFormat_r32_uint;
        next[i]=library->mContext->createBuffer(&d);if(!next[i])throw std::bad_alloc();}}
    catch(...){for(auto p:next)delete p;return false;}
    for(unsigned i=0;i<4;++i){delete wide[i];wide[i]=next[i];}wideCapacity=keys;return true;
}
void RadixSort::upload(unsigned blocks,unsigned pass,unsigned keys){
    std::array<unsigned,6> words{blocks,1,1,pass,blocks*16,keys};auto ptr=library->mContext->map(constants);std::memcpy(ptr,words.data(),sizeof(words));library->mContext->unmap(constants);
}
void RadixSort::sort(unsigned keys,unsigned bits,void* timerControl){
    unsigned blocks=(keys+1023u)/1024u;if(!blocks)return;if(blocks>maxBlocks)throw std::runtime_error("Radix sort capacity exceeded");
    auto context=library->mContext;
    auto timers=static_cast<SolverStorage::Timers*>(timerControl);
    auto dispatch=[&](const NvFlex::DispatchParams* p){int index=-1;if(timers&&timers->mEnabled){index=timers->mTimerPool->begin();timers->mNameToTimerMapW.emplace(p->shader->m_desc.label,index);}context->dispatch(p);if(index>=0)timers->mTimerPool->end(index);};
    if(blocks==1){
        upload(1,0,keys);NvFlex::DispatchParams p{};p.shader=GetShader(library,"g_RadixSortBlockCS");p.gridDim={1,1,1};p.rootConstantBuffer=constants;
        p.readOnly[0]=front.key4->getResource();p.readOnly[1]=front.value4->getResource();p.readWrite[0]=back.key4->getResourceRW();p.readWrite[1]=back.value4->getResourceRW();dispatch(&p);std::swap(front,back);return;
    }
    unsigned firstPass=0;
    // Replace exactly four low-nibble passes by two stable byte passes.
    // The original remaining passes restore the same physical front/back data,
    // counter parity, final low-20/28-bit back side and untouched tail bytes.
    // Other lengths/bit counts retain the original kernels and dispatches.
    if(keys%1024==0 && keys<=1048576 && (bits==24 || bits==32) && reserveWide(keys)){
        for(unsigned shift:{0u,8u}){
            upload(blocks,shift,keys);NvFlex::DispatchParams p{};p.rootConstantBuffer=constants;
            p.shader=GetShader(library,"df_Radix8Histogram");p.gridDim={blocks*4,1,1};
            p.readOnly[0]=front.key->getResource();p.readWrite[0]=wide[0]->getResourceRW();dispatch(&p);
            p={};p.rootConstantBuffer=constants;p.shader=GetShader(library,"df_Radix8Scan");p.gridDim={blocks,1,1};
            p.readOnly[0]=wide[0]->getResource();p.readWrite[0]=wide[1]->getResourceRW();p.readWrite[1]=wide[2]->getResourceRW();dispatch(&p);
            p={};p.rootConstantBuffer=constants;p.shader=GetShader(library,"df_Radix8ScanSums");p.gridDim={1,1,1};
            p.readOnly[0]=wide[2]->getResource();p.readWrite[0]=wide[3]->getResourceRW();dispatch(&p);
            p={};p.rootConstantBuffer=constants;p.shader=GetShader(library,"df_Radix8Scatter");p.gridDim={blocks*4,1,1};
            p.readOnly[0]=front.key->getResource();p.readOnly[1]=front.value->getResource();p.readOnly[2]=wide[1]->getResource();p.readOnly[3]=wide[3]->getResource();
            p.readWrite[0]=back.key->getResourceRW();p.readWrite[1]=back.value->getResourceRW();dispatch(&p);std::swap(front,back);
        }
        firstPass=16;
    }
    for(unsigned pass=firstPass;pass<bits;pass+=4){
        upload(blocks,pass,keys);NvFlex::DispatchParams p{};p.shader=GetShader(library,"g_RadixSort1CS");p.gridDim={blocks,1,1};p.rootConstantBuffer=constants;
        p.readOnly[0]=front.key4->getResource();p.readWrite[0]=countersFront.scalar->getResourceRW();dispatch(&p);
        p={};p.shader=GetShader(library,"g_RadixSort2CS");p.gridDim={2,1,1};p.rootConstantBuffer=constants;
        p.readOnly[0]=countersFront.vector->getResource();p.readWrite[0]=countersBack.vector->getResourceRW();dispatch(&p);std::swap(countersFront,countersBack);
        p={};p.shader=GetShader(library,"g_RadixSort3CS");p.gridDim={blocks,1,1};p.rootConstantBuffer=constants;
        p.readOnly[0]=front.key4->getResource();p.readOnly[1]=front.value4->getResource();p.readOnly[2]=countersFront.scalar->getResource();
        p.readWrite[0]=back.key->getResourceRW();p.readWrite[1]=back.value->getResourceRW();dispatch(&p);std::swap(front,back);
    }
}
}
