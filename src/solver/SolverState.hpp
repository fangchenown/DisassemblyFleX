#pragma once
#include "runtime/Runtime.hpp"
#include "RadixSort.hpp"
#include <array>
#include <memory>
#include <vector>
namespace df {
struct BufferSlot {NvFlex::Buffer* buffer=nullptr;NvFlex::BufferDesc desc{};};
struct ConstantSlot {NvFlex::ConstantBufferDesc desc{};NvFlex::ConstantBuffer* buffer=nullptr;};
static_assert(sizeof(BufferSlot)==32&&sizeof(ConstantSlot)==24);
struct SolverStorage {
    struct Timers {
        bool mEnabled=false;
        NvFlex::NameToTimerMap mNameToTimerMap;
        NvFlex::NameToTimerMapW mNameToTimerMapW;
        NvFlex::Context* mContext=nullptr;
        NvFlex::TimerPool* mTimerPool=nullptr;
    } timerState;
    std::vector<NvFlex::Buffer*> ownedBuffers;
    std::vector<NvFlex::ConstantBuffer*> ownedConstants;
    std::unique_ptr<NvFlex::TimerPool> timers;
    std::unique_ptr<RadixSort> radix;
    BufferSlot springDispatchArgs;
    ConstantSlot springDispatchParams;
    bool springDispatchReady=false;
    unsigned springDispatchCapacity=0;
    int springDispatchCount=0;
    std::array<NvFlexDetailTimer,256> details{};
    std::array<std::array<char,256>,256> detailNames{};
    ~SolverStorage(){for(auto p:ownedBuffers)delete p;for(auto p:ownedConstants)delete p;}
};
static_assert(sizeof(SolverStorage::Timers)==56);
BufferSlot& Slot(void* storage);
ConstantSlot& Constant(void* storage);
void Allocate(NvFlexSolver*,void* storage,unsigned count,unsigned stride,unsigned flags=19,NvFlexFormat format=eNvFlexFormat_unknown,const void* initial=nullptr);
void AllocateConstant(NvFlexSolver*,void* storage,unsigned bytes);
void ReserveBuffer(NvFlexSolver*,void* storage,unsigned count,unsigned stride,unsigned flags=19,NvFlexFormat format=eNvFlexFormat_unknown);
void ReleaseBuffer(NvFlexSolver*,void* storage);
void WriteBytes(NvFlexLibrary*,NvFlex::Buffer*,unsigned dstOffset,NvFlexBuffer*,unsigned srcOffset,unsigned bytes);
void ReadBytes(NvFlexLibrary*,NvFlexBuffer*,unsigned dstOffset,NvFlex::Buffer*,unsigned srcOffset,unsigned bytes);
void ReadData(NvFlexLibrary*,NvFlexBuffer*,NvFlex::Buffer*,const NvFlexCopyDesc*);
void WriteData(NvFlexLibrary*,NvFlex::Buffer*,NvFlexBuffer*,const NvFlexCopyDesc*);
}
struct NvFlexSolver {
    nvflex_recovered::NvFlexSolver state{};
    df::SolverStorage storage;
};
static_assert(offsetof(NvFlexSolver,state)==0);
inline NvFlexLibrary* SolverLibrary(NvFlexSolver* solver){NvFlexLibrary* library=nullptr;std::memcpy(&library,solver->state.mLib,8);return library;}
