// Readable recovery of shader #66; per-particle correction and relaxation.
#include "KernelParams.hlsli"
cbuffer consts : register(b0) { KernelParams gParams; };
ByteAddressBuffer deltas : register(t0);
RWStructuredBuffer<float4> newPositions : register(u0);
[numthreads(256,1,1)]
void main(uint3 id : SV_DispatchThreadID) {
    if((int)id.x<gParams.kNumParticles) {
        float4 correction=asfloat(deltas.Load4(id.x*16u));
        float factor=gParams.kRelaxationMode!=0
            ?1.0f/max(correction.w*gParams.kSOR,1.0f):gParams.kRelaxationFactor;
        newPositions[id.x].xyz=mad(correction.xyz,factor,newPositions[id.x].xyz);
    }
}
