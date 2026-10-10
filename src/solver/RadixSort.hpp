#pragma once
#include "runtime/Runtime.hpp"
#include <vector>
namespace NvFlex {
struct RadixSortBuffer {Buffer* key;Buffer* val;};
struct RadixSortParams {unsigned numKeys,numSortBlocks,bits;};
// Recovered original virtual interface order (sort is slot 4).
struct RadixSort : NvFlexObject {
    virtual RadixSortBuffer getInputBuffer()=0;
    virtual RadixSortBuffer getOutputBuffer()=0;
    virtual void sort(Context*,const RadixSortParams*,void* timers)=0;
    virtual ~RadixSort()=default;
};
}
namespace df {
class RadixSort final : public NvFlex::RadixSort {
public:
    struct Side {NvFlex::Buffer* key=nullptr;NvFlex::Buffer* value=nullptr;NvFlex::Buffer* key4=nullptr;NvFlex::Buffer* value4=nullptr;};
    struct Counter {NvFlex::Buffer* scalar=nullptr;NvFlex::Buffer* vector=nullptr;};
    RadixSort(NvFlexLibrary*,unsigned maxBlocks);
    ~RadixSort() override;
    NvFlexUint addRef() override{return ++refs;}
    NvFlexUint release() override{auto n=--refs;if(!n)delete this;return n;}
    NvFlex::RadixSortBuffer getInputBuffer() override{return {front.key,front.value};}
    NvFlex::RadixSortBuffer getOutputBuffer() override{return {front.key,front.value};}
    void sort(NvFlex::Context*,const NvFlex::RadixSortParams* params,void* timers) override{sort(params->numKeys,params->bits,timers);}
    Side front,back;Counter countersFront,countersBack;
    unsigned capacity() const{return maxBlocks*1024u;}
    void sort(unsigned numKeys,unsigned bits,void* timers=nullptr);
private:
    std::atomic_uint refs{1};
    NvFlexLibrary* library;unsigned maxBlocks;NvFlex::ConstantBuffer* constants=nullptr;
    std::vector<NvFlex::Buffer*> owned;
    void upload(unsigned blocks,unsigned pass,unsigned keys);
};
}
