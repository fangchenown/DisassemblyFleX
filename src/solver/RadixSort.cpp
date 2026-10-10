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
RadixSort::~RadixSort(){for(auto p:owned)delete p;delete constants;}
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
    for(unsigned pass=0;pass<bits;pass+=4){
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
