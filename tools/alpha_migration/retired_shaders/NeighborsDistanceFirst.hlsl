// Reconstructed from DXBC; not original HLSL source.
// uint temporaries preserve DXBC bits. All literals retain their original IEEE-754 encoding.
// Instruction comments map this source to the original shader.
// Derived from original shader058; ordered rows and capacity semantics retained.

cbuffer RecoveredConstants0 : register(b0) { uint4 cb0[31]; };
struct S_t0 { uint w[1]; }; StructuredBuffer<S_t0> t0_t0 : register(t0);
struct S_t1 { uint w[1]; }; StructuredBuffer<S_t1> t1_t1 : register(t1);
Buffer<uint4> t2_t2 : register(t2);
struct S_t3 { uint w[4]; }; StructuredBuffer<S_t3> t3_t3 : register(t3);
struct S_t4 { uint w[4]; }; StructuredBuffer<S_t4> t4_t4 : register(t4);
struct S_t5 { uint w[1]; }; StructuredBuffer<S_t5> t5_t5 : register(t5);
struct S_t6 { uint w[3]; }; StructuredBuffer<S_t6> t6_t6 : register(t6);
struct S_u0 { uint w[1]; }; RWStructuredBuffer<S_u0> u0_u0 : register(u0);
struct S_u1 { uint w[1]; }; RWStructuredBuffer<S_u1> u1_u1 : register(u1);

uint recovered_bfi(uint width, uint offset, uint value, uint baseValue) {
    width &= 31u; offset &= 31u;
    uint mask = ((1u << width) - 1u) << offset;
    return (baseValue & ~mask) | ((value << offset) & mask);
}

[numthreads(256, 1, 1)]
void main(uint3 vThreadID : SV_DispatchThreadID, uint3 vThreadIDInGroup : SV_GroupThreadID, uint3 vThreadGroupID : SV_GroupID, uint vThreadIDInGroupFlattened : SV_GroupIndex)
{
    uint4 r0;
    uint4 r1;
    uint4 r2;
    uint4 r3;
    uint4 r4;
    uint4 r5;
    uint4 r6;
    uint4 r7;
    uint4 r8;
    uint4 r9;
    // ilt r0.x, vThreadID.x, cb0[23].x
    r0.x = (asint(vThreadID.x) < asint(cb0[23].x) ? 0xffffffffu : 0u);
    // if_nz r0.x
    if (r0.x != 0u) {
        // ld_structured_indexable(structured_buffer, stride=16)(mixed,mixed,mixed,mixed) r0.xyz, vThreadID.x, l(0x00000000), t3.xyzx
        r0.xyz = uint3(t3_t3[vThreadID.x].w[(0x00000000u) / 4u + 0u], t3_t3[vThreadID.x].w[(0x00000000u) / 4u + 1u], t3_t3[vThreadID.x].w[(0x00000000u) / 4u + 2u]);
        // ld_structured_indexable(structured_buffer, stride=12)(mixed,mixed,mixed,mixed) r1.xyz, l(0x00000000), l(0x00000000), t6.xyzx
        r1.xyz = uint3(t6_t6[0x00000000u].w[(0x00000000u) / 4u + 0u], t6_t6[0x00000000u].w[(0x00000000u) / 4u + 1u], t6_t6[0x00000000u].w[(0x00000000u) / 4u + 2u]);
        // add r1.xyz, r0.xyzx, -r1.xyzx
        r1.xyz = uint3(asuint((asfloat(r0.x) + (-(asfloat(r1.x))))), asuint((asfloat(r0.y) + (-(asfloat(r1.y))))), asuint((asfloat(r0.z) + (-(asfloat(r1.z))))));
        // mul r1.xyz, r1.xyzx, cb0[24].zzzz
        r1.xyz = uint3(asuint((asfloat(r1.x) * asfloat(cb0[24].z))), asuint((asfloat(r1.y) * asfloat(cb0[24].z))), asuint((asfloat(r1.z) * asfloat(cb0[24].z))));
        // ftoi r1.xyz, r1.xyzx
        r1.xyz = uint3(asuint((int)asfloat(r1.x)), asuint((int)asfloat(r1.y)), asuint((int)asfloat(r1.z)));
        // iadd r2.xyzw, r1.xxyy, l(0xffffffff, 0x00000001, 0xffffffff, 0x00000001)
        r2.xyzw = uint4((r1.x + 0xffffffffu), (r1.x + 0x00000001u), (r1.y + 0xffffffffu), (r1.y + 0x00000001u));
        // iadd r1.xy, r1.zzzz, l(0xffffffff, 0x00000001, 0x00000000, 0x00000000)
        r1.xy = uint2((r1.z + 0xffffffffu), (r1.z + 0x00000001u));
        // ld_structured_indexable(structured_buffer, stride=4)(mixed,mixed,mixed,mixed) r0.w, vThreadID.x, l(0x00000000), t5.xxxx
        r0.w = t5_t5[vThreadID.x].w[(0x00000000u) / 4u + 0u];
        // and r3.xyz, r0.wwww, l(0x00200000, 0x000fffff, 0x00100000, 0x00000000)
        r3.xyz = uint3((r0.w & 0x00200000u), (r0.w & 0x000fffffu), (r0.w & 0x00100000u));
        // if_nz r3.x
        if (r3.x != 0u) {
            // ld_indexable(buffer)(uint,uint,uint,uint) r0.w, vThreadID.xxxx, t2.yzwx
            r0.w = t2_t2[vThreadID.x].x;
            // ld_structured_indexable(structured_buffer, stride=16)(mixed,mixed,mixed,mixed) r4.xyz, r0.w, l(0x00000000), t4.xyzx
            r4.xyz = uint3(t4_t4[r0.w].w[(0x00000000u) / 4u + 0u], t4_t4[r0.w].w[(0x00000000u) / 4u + 1u], t4_t4[r0.w].w[(0x00000000u) / 4u + 2u]);
            // endif
        }
        // iadd r5.z, vThreadID.x, l(0x00000001)
        r5.z = (vThreadID.x + 0x00000001u);
        // ine r1.zw, r3.xxxz, l(0x00000000, 0x00000000, 0x00000000, 0x00000000)
        r1.zw = uint2((r3.x != 0x00000000u ? 0xffffffffu : 0u), (r3.z != 0x00000000u ? 0xffffffffu : 0u));
        // mov r3.z, vThreadID.x
        r3.z = vThreadID.x;
        // mov r3.x, l(0x00000000)
        r3.x = 0x00000000u;
        // mov r0.w, r1.x
        r0.w = r1.x;
        // loop
        [loop] while (true) {
            // ilt r3.w, r1.y, r0.w
            r3.w = (asint(r1.y) < asint(r0.w) ? 0xffffffffu : 0u);
            // breakc_nz r3.w
            if (r3.w != 0u) break;
            // bfi r3.w, l(0x00000007), l(0x0000000e), r0.w, l(0x00000000)
            r3.w = recovered_bfi(0x00000007u, 0x0000000eu, r0.w, 0x00000000u);
            // mov r6.xy, r3.zxzz
            r6.xy = uint2(r3.z, r3.x);
            // mov r4.w, r2.z
            r4.w = r2.z;
            // loop
            [loop] while (true) {
                // ilt r5.w, r2.w, r4.w
                r5.w = (asint(r2.w) < asint(r4.w) ? 0xffffffffu : 0u);
                // breakc_nz r5.w
                if (r5.w != 0u) break;
                // bfi r5.w, l(0x00000007), l(0x00000007), r4.w, l(0x00000000)
                r5.w = recovered_bfi(0x00000007u, 0x00000007u, r4.w, 0x00000000u);
                // iadd r5.w, r3.w, r5.w
                r5.w = (r3.w + r5.w);
                // mov r6.zw, r6.xxxy
                r6.zw = uint2(r6.x, r6.y);
                // mov r7.x, r2.x
                r7.x = r2.x;
                // loop
                [loop] while (true) {
                    // ilt r7.y, r2.y, r7.x
                    r7.y = (asint(r2.y) < asint(r7.x) ? 0xffffffffu : 0u);
                    // breakc_nz r7.y
                    if (r7.y != 0u) break;
                    // bfi r7.y, l(0x00000007), l(0x00000000), r7.x, r5.w
                    r7.y = recovered_bfi(0x00000007u, 0x00000000u, r7.x, r5.w);
                    // ld_structured_indexable(structured_buffer, stride=4)(mixed,mixed,mixed,mixed) r7.z, r7.y, l(0x00000000), t0.xxxx
                    r7.z = t0_t0[r7.y].w[(0x00000000u) / 4u + 0u];
                    // ld_structured_indexable(structured_buffer, stride=4)(mixed,mixed,mixed,mixed) r7.y, r7.y, l(0x00000000), t1.xxxx
                    r7.y = t1_t1[r7.y].w[(0x00000000u) / 4u + 0u];
                    // mov r8.yz, r6.zzwz
                    r8.yz = uint2(r6.z, r6.w);
                    // mov r8.x, r7.z
                    r8.x = r7.z;
                    // loop
                    [loop] while (true) {
                        // ige r7.w, r8.x, r7.y
                        r7.w = (asint(r8.x) >= asint(r7.y) ? 0xffffffffu : 0u);
                        // breakc_nz r7.w
                        if (r7.w != 0u) break;
                        // ieq r7.w, r8.x, vThreadID.x
                        r7.w = (r8.x == vThreadID.x ? 0xffffffffu : 0u);
                        // if_nz r7.w
                        if (r7.w != 0u) {
                            // mov r5.xy, r8.yzyy
                            r5.xy = uint2(r8.y, r8.z);
                            // mov r8.xyz, r5.zxyz
                            r8.xyz = uint3(r5.z, r5.x, r5.y);
                            // continue
                            continue;
                            // endif
                        }
                        // ld_structured_indexable(structured_buffer, stride=4)(mixed,mixed,mixed,mixed) r5.x, r8.x, l(0x00000000), t5.xxxx
                        r5.x = t5_t5[r8.x].w[(0x00000000u) / 4u + 0u];
                        // and r5.x, r5.x, l(0x000fffff)
                        r5.x = (r5.x & 0x000fffffu);
                        // ieq r5.x, r3.y, r5.x
                        r5.x = (r3.y == r5.x ? 0xffffffffu : 0u);
                        // not r5.y, r5.x
                        r5.y = (~r5.x);
                        // or r5.y, r1.w, r5.y
                        r5.y = (r1.w | r5.y);
                        // if_nz r5.y
                        if (r5.y != 0u) {
                            // and r5.y, r1.z, r5.x
                            r5.y = (r1.z & r5.x);
                            // ld_structured_indexable(structured_buffer, stride=16)(mixed,mixed,mixed,mixed) r9.xyz, r8.x, l(0x00000000), t3.xyzx
                            r9.xyz = uint3(t3_t3[r8.x].w[(0x00000000u) / 4u + 0u], t3_t3[r8.x].w[(0x00000000u) / 4u + 1u], t3_t3[r8.x].w[(0x00000000u) / 4u + 2u]);
                            // add r9.xyz, r0.xyzx, -r9.xyzx
                            r9.xyz = uint3(asuint((asfloat(r0.x) + (-(asfloat(r9.x))))), asuint((asfloat(r0.y) + (-(asfloat(r9.y))))), asuint((asfloat(r0.z) + (-(asfloat(r9.z))))));
                            // dp3 r5.x, r9.xyzx, r9.xyzx
                            r5.x = asuint(dot(float3(asfloat(r9.x), asfloat(r9.y), asfloat(r9.z)), float3(asfloat(r9.x), asfloat(r9.y), asfloat(r9.z))));
                            // lt r5.x, r5.x, cb0[25].x
                            r5.x = (asfloat(r5.x) < asfloat(cb0[25].x) ? 0xffffffffu : 0u);
                            // if_nz r5.x
                            if (r5.x != 0u) {
                                // if_nz r5.y
                                if (r5.y != 0u) {
                                    // ld_indexable(buffer)(uint,uint,uint,uint) r5.x, r8.xxxx, t2.xyzw
                                    r5.x = t2_t2[r8.x].x;
                                    // ld_structured_indexable(structured_buffer, stride=16)(mixed,mixed,mixed,mixed) r9.xyz, r5.x, l(0x00000000), t4.xyzx
                                    r9.xyz = uint3(t4_t4[r5.x].w[(0x00000000u) / 4u + 0u], t4_t4[r5.x].w[(0x00000000u) / 4u + 1u], t4_t4[r5.x].w[(0x00000000u) / 4u + 2u]);
                                    // add r9.xyz, r4.xyzx, -r9.xyzx
                                    r9.xyz = uint3(asuint((asfloat(r4.x) + (-(asfloat(r9.x))))), asuint((asfloat(r4.y) + (-(asfloat(r9.y))))), asuint((asfloat(r4.z) + (-(asfloat(r9.z))))));
                                    // dp3 r5.x, r9.xyzx, r9.xyzx
                                    r5.x = asuint(dot(float3(asfloat(r9.x), asfloat(r9.y), asfloat(r9.z)), float3(asfloat(r9.x), asfloat(r9.y), asfloat(r9.z))));
                                    // lt r5.x, r5.x, cb0[8].z
                                    r5.x = (asfloat(r5.x) < asfloat(cb0[8].z) ? 0xffffffffu : 0u);
                                    // if_nz r5.x
                                    if (r5.x != 0u) {
                                        // iadd r9.z, r8.x, l(0x00000001)
                                        r9.z = (r8.x + 0x00000001u);
                                        // mov r9.xy, r8.yzyy
                                        r9.xy = uint2(r8.y, r8.z);
                                        // mov r8.xyz, r9.zxyz
                                        r8.xyz = uint3(r9.z, r9.x, r9.y);
                                        // continue
                                        continue;
                                        // endif
                                    }
                                    // endif
                                }
                                // ilt r5.x, r8.z, cb0[30].w
                                r5.x = (asint(r8.z) < asint(cb0[30].w) ? 0xffffffffu : 0u);
                                // if_nz r5.x
                                if (r5.x != 0u) {
                                    // store_structured u0.x, r8.y, l(0x00000000), r8.x
                                    u0_u0[r8.y].w[(0x00000000u) / 4u + 0u] = r8.x;
                                    // iadd r8.y, r8.y, cb0[23].y
                                    r8.y = (r8.y + cb0[23].y);
                                    // iadd r8.z, r8.z, l(0x00000001)
                                    r8.z = (r8.z + 0x00000001u);
                                    // endif
                                }
                                // endif
                            }
                            // endif
                        }
                        // iadd r8.x, r8.x, l(0x00000001)
                        r8.x = (r8.x + 0x00000001u);
                        // endloop
                    }
                    // mov r6.zw, r8.yyyz
                    r6.zw = uint2(r8.y, r8.z);
                    // iadd r7.x, r7.x, l(0x00000001)
                    r7.x = (r7.x + 0x00000001u);
                    // endloop
                }
                // mov r6.xy, r6.zwzz
                r6.xy = uint2(r6.z, r6.w);
                // iadd r4.w, r4.w, l(0x00000001)
                r4.w = (r4.w + 0x00000001u);
                // endloop
            }
            // mov r3.xz, r6.yyxy
            r3.xz = uint2(r6.y, r6.x);
            // iadd r0.w, r0.w, l(0x00000001)
            r0.w = (r0.w + 0x00000001u);
            // endloop
        }
        // store_structured u1.x, vThreadID.x, l(0x00000000), r3.x
        u1_u1[vThreadID.x].w[(0x00000000u) / 4u + 0u] = r3.x;
        // endif
    }
    // ret
    return;
}
