// Exclusive scan of contiguous 1024-word tiles in digit-major histogram.
cbuffer Params : register(b0) { uint Blocks1024, OneY, OneZ, Shift, OldHistogramSize, Count; };
Buffer<uint> Input : register(t0);
RWBuffer<uint> Prefix : register(u0);
RWBuffer<uint> Sums : register(u1);
groupshared uint values[1024];
[numthreads(256,1,1)]
void main(uint3 group : SV_GroupID, uint thread : SV_GroupIndex) {
    [unroll] for(uint k=0;k<4;++k) values[thread+256*k]=Input[group.x*1024+thread+256*k];
    GroupMemoryBarrierWithGroupSync();
    for(uint stride=1;stride<1024;stride*=2) {
        for(uint node=thread;node<1024/(2*stride);node+=256) {
            uint i=(node+1)*2*stride-1;values[i]+=values[i-stride];
        }
        GroupMemoryBarrierWithGroupSync();
    }
    if(thread==0) { Sums[group.x]=values[1023];values[1023]=0; }
    GroupMemoryBarrierWithGroupSync();
    for(uint stride=512;stride>0;stride/=2) {
        for(uint node=thread;node<1024/(2*stride);node+=256) {
            uint i=(node+1)*2*stride-1;uint left=values[i-stride];values[i-stride]=values[i];values[i]+=left;
        }
        GroupMemoryBarrierWithGroupSync();
    }
    [unroll] for(uint k=0;k<4;++k) Prefix[group.x*1024+thread+256*k]=values[thread+256*k];
}
