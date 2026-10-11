#include "solver/SolverState.hpp"
#include "runtime/ShaderLibrary.hpp"
#include <cstring>
// DF_IMPLEMENTED: NvFlexSetSprings
extern "C" void NvFlexSetSprings(NvFlexSolver* solver,NvFlexBuffer* indices,NvFlexBuffer* lengths,NvFlexBuffer* stiffness,int count){
    auto& s=solver->state;auto library=SolverLibrary(solver);auto context=library->mContext;
    solver->storage.springDispatchReady=false;
    if(count>s.mMaxSprings){unsigned capacity=unsigned(count*3/2);df::ReserveBuffer(solver,s.mSpringIndices,capacity*2,4);df::ReserveBuffer(solver,s.mSpringLengths,capacity,4);df::ReserveBuffer(solver,s.mSpringStiffness,capacity,4);s.mMaxSprings=capacity;}
    if(count){df::WriteBytes(library,df::Slot(s.mSpringIndices).buffer,0,indices,0,count*8);df::WriteBytes(library,df::Slot(s.mSpringLengths).buffer,0,lengths,0,count*4);df::WriteBytes(library,df::Slot(s.mSpringStiffness).buffer,0,stiffness,0,count*4);}
    if(count*2>s.mMaxHalfSprings){
        unsigned capacity=unsigned(count*3);df::ReserveBuffer(solver,s.mHalfSpringOpposites,capacity,4);
        df::ReserveBuffer(solver,s.mHalfSpringLengths,capacity,4);df::ReserveBuffer(solver,s.mHalfSpringStiffness,capacity,4);
        df::ReserveBuffer(solver,s.mHalfSpringParticleBegin,s.mMaxParticles,4);df::ReserveBuffer(solver,s.mHalfSpringParticleEnd,s.mMaxParticles,4);
        if(!df::Constant(s.mHalfSpringConstantBuffer).buffer)df::AllocateConstant(solver,s.mHalfSpringConstantBuffer,4);
        s.mMaxHalfSprings=capacity;
    }
    if(count){
        if(s.mRadixSortSize<count*2){solver->storage.radix=std::make_unique<df::RadixSort>(library,unsigned(count*2+1023)/1024);s.mRadixSortSize=count*2;auto pointer=solver->storage.radix.get();std::memcpy(s.mRadixSort,&pointer,8);}
        auto& radix=*solver->storage.radix;auto cb=df::Constant(s.mHalfSpringConstantBuffer).buffer;
        std::memcpy(context->map(cb),&count,4);context->unmap(cb);
        // The original copies the caller's host staging indices into the radix keys.
        context->copyToDevice(radix.front.key,0,indices->mBuffer,0,count*8,NvFlex::eDownloadBuffer);
        unsigned groups=unsigned(count*2+255)/256;NvFlex::DispatchParams p{};p.rootConstantBuffer=cb;p.gridDim={groups,1,1};
        p.shader=df::GetShader(library,"g_Flex_SpringsGenerateIndices");p.readWrite[0]=radix.front.value->getResourceRW();context->dispatch(&p);
        radix.sort(unsigned(count*2),32);
        // Prepare a bound without any CPU readback. Only large spare-capacity
        // solvers can amortize indirect-launch overhead; sparse high IDs are
        // still included because the actual maximum endpoint comes from GPU.
        if(s.mMaxParticles>=16384 && (s.mNumParticles==0 ||
                unsigned(s.mMaxParticles)/2u>=unsigned(s.mNumParticles))){
            auto& storage=solver->storage;
            if(!storage.springDispatchArgs.buffer){
                df::Allocate(solver,&storage.springDispatchArgs,3,4,
                    NvFlex::eBuffer|NvFlex::eUAV_SRV|NvFlex::eRaw|NvFlex::eIndirect);
                df::AllocateConstant(solver,&storage.springDispatchParams,16);
            }
            unsigned values[4]={unsigned(count),unsigned(s.mMaxParticles),0,0};
            auto constant=storage.springDispatchParams.buffer;
            std::memcpy(context->map(constant),values,sizeof(values));context->unmap(constant);
            NvFlex::DispatchParams args{};args.shader=df::GetShader(library,"df_BuildSpringDispatchArgs");
            args.rootConstantBuffer=constant;args.gridDim={1,1,1};
            args.readOnly[0]=radix.front.key->getResource();
            args.readWrite[0]=storage.springDispatchArgs.buffer->getResourceRW();
            context->dispatch(&args);
            storage.springDispatchCapacity=unsigned(s.mMaxParticles);
            storage.springDispatchCount=count;storage.springDispatchReady=true;
        }
        unsigned zeros[4]{};context->clearUnorderedAccessViewUint(df::Slot(s.mHalfSpringParticleBegin).buffer,zeros);context->clearUnorderedAccessViewUint(df::Slot(s.mHalfSpringParticleEnd).buffer,zeros);
        p={};p.rootConstantBuffer=cb;p.gridDim={groups,1,1};p.shader=df::GetShader(library,"g_Flex_SpringsParticleRange");
        p.readOnly[0]=radix.front.key->getResource();p.readWrite[0]=df::Slot(s.mHalfSpringParticleBegin).buffer->getResourceRW();p.readWrite[1]=df::Slot(s.mHalfSpringParticleEnd).buffer->getResourceRW();context->dispatch(&p);
        p={};p.rootConstantBuffer=cb;p.gridDim={groups,1,1};p.shader=df::GetShader(library,"g_Flex_SpringsReorder");
        p.readOnly[0]=radix.front.value->getResource();p.readOnly[1]=df::Slot(s.mSpringIndices).buffer->getResource();p.readOnly[2]=df::Slot(s.mSpringLengths).buffer->getResource();p.readOnly[3]=df::Slot(s.mSpringStiffness).buffer->getResource();
        p.readWrite[0]=df::Slot(s.mHalfSpringOpposites).buffer->getResourceRW();p.readWrite[1]=df::Slot(s.mHalfSpringLengths).buffer->getResourceRW();p.readWrite[2]=df::Slot(s.mHalfSpringStiffness).buffer->getResourceRW();context->dispatch(&p);
    }
    s.mNumSprings=count;
}
// DF_RESTORED: NvFlexGetSprings
// The target D3D DLL's RVA 0x3d330 contains only profiling push/pop and returns;
// it does not write the supplied buffers. Preserve that observed behavior.
extern "C" void NvFlexGetSprings(NvFlexSolver*,NvFlexBuffer*,NvFlexBuffer*,NvFlexBuffer*,int){}
