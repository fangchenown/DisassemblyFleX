// Readable recovery of shader #75; resource bindings and reduction order from DXBC.
// The instruction-level version in ../recovered is the primary tracing reference.
#include "KernelParams.hlsli"
cbuffer consts : register(b0) { KernelParams gParams; };
StructuredBuffer<int> halfSpringOpposites : register(t1);
StructuredBuffer<float> halfSpringLengths : register(t2);
StructuredBuffer<float> halfSpringStiffness : register(t3);
StructuredBuffer<int> particleSpringBegin : register(t4);
StructuredBuffer<int> particleSpringEnd : register(t5);
StructuredBuffer<int> reverseLookup : register(t6);
StructuredBuffer<float4> sortedNewPositions : register(t7);
RWByteAddressBuffer deltas : register(u0);
groupshared float3 partialDelta[512];

[numthreads(512,1,1)]
void main(uint3 dispatchID : SV_DispatchThreadID,uint3 localID : SV_GroupThreadID)
{
    uint particle=dispatchID.x>>3;
    uint lane=dispatchID.x&7u;
    bool invalid=particle>=(uint)gParams.kMaxParticles;
    particle=invalid?0u:particle;
    uint begin=(uint)particleSpringBegin[particle];
    uint end=(uint)particleSpringEnd[particle];
    uint count=invalid?0u:end-begin;
    uint sortedIndex=(uint)reverseLookup[particle];
    float4 position=sortedNewPositions[sortedIndex];
    float3 correction=0.0f;
    if(count>0u && position.w>0.0f) {
        for(uint spring=begin+lane;spring<end;spring+=8u) {
            uint other=(uint)reverseLookup[halfSpringOpposites[spring]];
            float4 neighbor=sortedNewPositions[other];
            float3 separation=position.xyz-neighbor.xyz;
            float weight=position.w+neighbor.w;
            float lengthSquared=dot(separation,separation);
            float length=sqrt(lengthSquared);
            float error=halfSpringLengths[spring]-length;
            float stiffness=halfSpringStiffness[spring];
            if(stiffness<0.0f) { error=min(error,0.0f);stiffness=-stiffness; }
            float scale=error*((1.0f/weight)*stiffness);
            float3 candidate=mad(scale,separation/length,correction);
            if(weight>0.0f && lengthSquared>0.0f)correction=candidate;
        }
    }
    partialDelta[localID.x]=correction;
    GroupMemoryBarrierWithGroupSync();
    if(lane==0u && count>0u && position.w>0.0f) {
        float3 sum=partialDelta[localID.x+1]+correction;
        sum=sum+partialDelta[localID.x+2];
        sum=partialDelta[localID.x+3]+sum;
        sum=sum+partialDelta[localID.x+4];
        sum=sum+partialDelta[localID.x+5];
        sum=sum+partialDelta[localID.x+6];
        sum=sum+partialDelta[localID.x+7];
        float4 accumulated=asfloat(deltas.Load4(sortedIndex*16u));
        accumulated+=float4(position.w*sum,(float)count);
        deltas.Store4(sortedIndex*16u,asuint(accumulated));
    }
}
