// New integer-only helper, not reconstructed NVIDIA shader source.
// The sorted endpoint keys remain intact here, immediately after SetSprings.
cbuffer Arguments : register(b0) { uint springCount; uint capacity; uint2 unused; };
Buffer<uint> endpointKeys : register(t0);
RWByteAddressBuffer dispatchArguments : register(u0);
[numthreads(1,1,1)]
void main() {
    uint extent=capacity;
    if(springCount!=0 && capacity!=0) {
        uint maximum=endpointKeys[springCount*2u-1u];
        // Keep the original full launch for out-of-range input; this helper
        // never tries to repair or reinterpret invalid spring endpoints.
        if(maximum<capacity)extent=maximum+1u;
    }
    dispatchArguments.Store3(0,uint3((extent+63u)/64u,1u,1u));
}
