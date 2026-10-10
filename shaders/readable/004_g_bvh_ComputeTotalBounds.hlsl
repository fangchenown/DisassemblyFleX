// Readable recovery of shader #4; two separate group reductions, 256 items/group.
cbuffer constBVH : register(b0) { int itemCount; int3 padding; };
StructuredBuffer<float4> itemLowers : register(t0);
StructuredBuffer<float4> itemUppers : register(t1);
RWStructuredBuffer<float4> writeBoundsLower : register(u0);
RWStructuredBuffer<float4> writeBoundsUpper : register(u1);
groupshared float3 sharedBounds[256];
[numthreads(256,1,1)]
void main(uint3 id:SV_DispatchThreadID,uint3 localID:SV_GroupThreadID,uint3 group:SV_GroupID) {
    float maxFinite=asfloat(0x7f7fffffu);
    sharedBounds[localID.x]=(int)id.x<itemCount?itemLowers[id.x].xyz:float3(maxFinite,maxFinite,maxFinite);
    for(uint width=128u;width>0u;width>>=1u) {
        GroupMemoryBarrierWithGroupSync();
        if(localID.x<width)sharedBounds[localID.x]=min(sharedBounds[localID.x],sharedBounds[localID.x+width]);
    }
    GroupMemoryBarrierWithGroupSync();
    float3 lower=sharedBounds[0];
    GroupMemoryBarrierWithGroupSync();
    sharedBounds[localID.x]=(int)id.x<itemCount?itemUppers[id.x].xyz:float3(-maxFinite,-maxFinite,-maxFinite);
    for(uint upperWidth=128u;upperWidth>0u;upperWidth>>=1u) {
        GroupMemoryBarrierWithGroupSync();
        if(localID.x<upperWidth)sharedBounds[localID.x]=max(sharedBounds[localID.x],sharedBounds[localID.x+upperWidth]);
    }
    GroupMemoryBarrierWithGroupSync();
    if(localID.x==0u) {
        writeBoundsLower[group.x]=float4(lower,0.0f);
        writeBoundsUpper[group.x]=float4(sharedBounds[0],0.0f);
    }
}
