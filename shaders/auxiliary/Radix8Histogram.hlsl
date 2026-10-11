// Authored integer helper inspired by OF alpha8.2 stable eight-bit radix.
// DF typed buffers, ordering and physical front/back contract are retained.
cbuffer Params : register(b0) { uint Blocks1024, OneY, OneZ, Shift, OldHistogramSize, Count; };
Buffer<uint> Keys : register(t0);
RWBuffer<uint> Histogram : register(u0);
groupshared uint bins[256];
[numthreads(256,1,1)]
void main(uint3 group : SV_GroupID, uint thread : SV_GroupIndex) {
    bins[thread]=0;
    GroupMemoryBarrierWithGroupSync();
    uint digit=(Keys[group.x*256+thread]>>Shift)&255;
    InterlockedAdd(bins[digit],1);
    GroupMemoryBarrierWithGroupSync();
    Histogram[thread*(Blocks1024*4)+group.x]=bins[thread];
}
