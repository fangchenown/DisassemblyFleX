// Stable rank is an integer population count of earlier lanes in this block.
cbuffer Params : register(b0) { uint Blocks1024, OneY, OneZ, Shift, OldHistogramSize, Count; };
Buffer<uint> Keys : register(t0);
Buffer<uint> Payload : register(t1);
Buffer<uint> Prefix : register(t2);
Buffer<uint> SumPrefix : register(t3);
RWBuffer<uint> OutKeys : register(u0);
RWBuffer<uint> OutPayload : register(u1);
groupshared uint laneMasks[2048];
[numthreads(256,1,1)]
void main(uint3 group : SV_GroupID, uint thread : SV_GroupIndex) {
    [unroll] for(uint k=0;k<8;++k) laneMasks[thread+256*k]=0;
    GroupMemoryBarrierWithGroupSync();
    uint index=group.x*256+thread,key=Keys[index],digit=(key>>Shift)&255;
    uint word=thread>>5,lane=thread&31,base=digit*8;
    InterlockedOr(laneMasks[base+word],1u<<lane);
    GroupMemoryBarrierWithGroupSync();
    uint rank=0;
    for(uint w=0;w<word;++w) rank+=countbits(laneMasks[base+w]);
    rank+=countbits(laneMasks[base+word]&((1u<<lane)-1u));
    uint hist=digit*(Blocks1024*4)+group.x;
    uint target=Prefix[hist]+SumPrefix[hist>>10]+rank;
    OutKeys[target]=key;OutPayload[target]=Payload[index];
}
