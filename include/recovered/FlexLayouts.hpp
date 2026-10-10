// PDB-derived layout views. Opaque C++/D3D members retain byte storage.
// These views recover field offsets; they do not implement object construction or virtual methods.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
namespace nvflex_recovered {
struct float3 { float x,y,z; };
struct float4 { float x,y,z,w; };
#pragma pack(push, 1)
struct KernelParams {
    float4 kPlanes[8]; // +0x0
    std::int32_t kNumPlanes; // +0x80
    float kRadius; // +0x84
    float kRadiusSq; // +0x88
    float kInvRadius; // +0x8c
    float kPoly6; // +0x90
    float kSpiky1; // +0x94
    float kSpiky2; // +0x98
    float kAkinci1; // +0x9c
    float kAkinci2; // +0xa0
    float kCohesion1; // +0xa4
    float kCohesion2; // +0xa8
    float _pad0; // +0xac
    float kRestDensity; // +0xb0
    float kInvRestDensity; // +0xb4
    float kFluidRestDistance; // +0xb8
    float kSolidRestDistance; // +0xbc
    float kLambdaScale; // +0xc0
    float kCohesion; // +0xc4
    float kSurfaceTension; // +0xc8
    float kSolidPressure; // +0xcc
    float kVorticityConfinement; // +0xd0
    float kAnisotropy; // +0xd4
    float kAnisotropyMin; // +0xd8
    float kAnisotropyMax; // +0xdc
    float kSmoothing; // +0xe0
    float kViscosity; // +0xe4
    float kFreeSurfaceDrag; // +0xe8
    float kBuoyancy; // +0xec
    float kDiffuseThreshold; // +0xf0
    float kDiffuseBuoyancy; // +0xf4
    float kDiffuseDrag; // +0xf8
    std::int32_t kDiffuseBallistic; // +0xfc
    float3 kGravity; // +0x100
    float kDynamicFriction; // +0x10c
    float kStaticFriction; // +0x110
    float kParticleFriction; // +0x114
    float kAdhesion; // +0x118
    float kDissipation; // +0x11c
    float kDamping; // +0x120
    float kInertiaBias; // +0x124
    float kCollisionDistance; // +0x128
    float kCollisionThreshold; // +0x12c
    float kCollisionMargin; // +0x130
    float kCollisionMarginSq; // +0x134
    float _pad1; // +0x138
    float _pad2; // +0x13c
    float kDrag; // +0x140
    float kLift; // +0x144
    float kPlasticThreshold_deprecated; // +0x148
    float kPlasticCreep_deprecated; // +0x14c
    float kSleepThreshold; // +0x150
    float kSleepThresholdSq; // +0x154
    float kShockPropagation; // +0x158
    float kRestitution; // +0x15c
    float kSOR; // +0x160
    float3 _pad3; // +0x164
    std::int32_t kNumParticles; // +0x170
    std::int32_t kNumParticlesAligned; // +0x174
    float kDt; // +0x178
    float kInvDt; // +0x17c
    float kSubStepLength; // +0x180
    float kMaxSpeed; // +0x184
    float kInvCellEdge; // +0x188
    float kStaticTriGridInvCellEdge; // +0x18c
    float kCollideParticlesRadiusSq; // +0x190
    std::int32_t kMaxParticles; // +0x194
    std::int32_t kRelaxationMode; // +0x198
    std::int32_t kShapesCount; // +0x19c
    std::int32_t kNumShapes; // +0x1a0
    std::int32_t kNumRigids; // +0x1a4
    std::int32_t kNumSprings; // +0x1a8
    std::int32_t kNumTriangles; // +0x1ac
    std::int32_t kMaxDiffuseParticles; // +0x1b0
    std::int32_t kDiffuseRadixSortSize; // +0x1b4
    float kDiffuseDt; // +0x1b8
    float kDiffuseMaxVelocity; // +0x1bc
    float3 kDiffuseSortAxis; // +0x1c0
    float kRelaxationFactor; // +0x1cc
    float3 kStaticTriGridLower; // +0x1d0
    float kDiffuseLifetime; // +0x1dc
    float3 kWind; // +0x1e0
    std::int32_t kMaxNeighborsPerParticle; // +0x1ec
    std::int32_t kNumGeometryEntries; // +0x1f0
    float kMaxAcceleration; // +0x1f4
    float kMaxVelocityDelta; // +0x1f8
    std::int32_t kMaxContactsPerParticle; // +0x1fc
};
static_assert(sizeof(KernelParams) == 512);
static_assert(offsetof(KernelParams, kPlanes) == 0x0);
static_assert(offsetof(KernelParams, kNumPlanes) == 0x80);
static_assert(offsetof(KernelParams, kRadius) == 0x84);
static_assert(offsetof(KernelParams, kRadiusSq) == 0x88);
static_assert(offsetof(KernelParams, kInvRadius) == 0x8c);
static_assert(offsetof(KernelParams, kPoly6) == 0x90);
static_assert(offsetof(KernelParams, kSpiky1) == 0x94);
static_assert(offsetof(KernelParams, kSpiky2) == 0x98);
static_assert(offsetof(KernelParams, kAkinci1) == 0x9c);
static_assert(offsetof(KernelParams, kAkinci2) == 0xa0);
static_assert(offsetof(KernelParams, kCohesion1) == 0xa4);
static_assert(offsetof(KernelParams, kCohesion2) == 0xa8);
static_assert(offsetof(KernelParams, _pad0) == 0xac);
static_assert(offsetof(KernelParams, kRestDensity) == 0xb0);
static_assert(offsetof(KernelParams, kInvRestDensity) == 0xb4);
static_assert(offsetof(KernelParams, kFluidRestDistance) == 0xb8);
static_assert(offsetof(KernelParams, kSolidRestDistance) == 0xbc);
static_assert(offsetof(KernelParams, kLambdaScale) == 0xc0);
static_assert(offsetof(KernelParams, kCohesion) == 0xc4);
static_assert(offsetof(KernelParams, kSurfaceTension) == 0xc8);
static_assert(offsetof(KernelParams, kSolidPressure) == 0xcc);
static_assert(offsetof(KernelParams, kVorticityConfinement) == 0xd0);
static_assert(offsetof(KernelParams, kAnisotropy) == 0xd4);
static_assert(offsetof(KernelParams, kAnisotropyMin) == 0xd8);
static_assert(offsetof(KernelParams, kAnisotropyMax) == 0xdc);
static_assert(offsetof(KernelParams, kSmoothing) == 0xe0);
static_assert(offsetof(KernelParams, kViscosity) == 0xe4);
static_assert(offsetof(KernelParams, kFreeSurfaceDrag) == 0xe8);
static_assert(offsetof(KernelParams, kBuoyancy) == 0xec);
static_assert(offsetof(KernelParams, kDiffuseThreshold) == 0xf0);
static_assert(offsetof(KernelParams, kDiffuseBuoyancy) == 0xf4);
static_assert(offsetof(KernelParams, kDiffuseDrag) == 0xf8);
static_assert(offsetof(KernelParams, kDiffuseBallistic) == 0xfc);
static_assert(offsetof(KernelParams, kGravity) == 0x100);
static_assert(offsetof(KernelParams, kDynamicFriction) == 0x10c);
static_assert(offsetof(KernelParams, kStaticFriction) == 0x110);
static_assert(offsetof(KernelParams, kParticleFriction) == 0x114);
static_assert(offsetof(KernelParams, kAdhesion) == 0x118);
static_assert(offsetof(KernelParams, kDissipation) == 0x11c);
static_assert(offsetof(KernelParams, kDamping) == 0x120);
static_assert(offsetof(KernelParams, kInertiaBias) == 0x124);
static_assert(offsetof(KernelParams, kCollisionDistance) == 0x128);
static_assert(offsetof(KernelParams, kCollisionThreshold) == 0x12c);
static_assert(offsetof(KernelParams, kCollisionMargin) == 0x130);
static_assert(offsetof(KernelParams, kCollisionMarginSq) == 0x134);
static_assert(offsetof(KernelParams, _pad1) == 0x138);
static_assert(offsetof(KernelParams, _pad2) == 0x13c);
static_assert(offsetof(KernelParams, kDrag) == 0x140);
static_assert(offsetof(KernelParams, kLift) == 0x144);
static_assert(offsetof(KernelParams, kPlasticThreshold_deprecated) == 0x148);
static_assert(offsetof(KernelParams, kPlasticCreep_deprecated) == 0x14c);
static_assert(offsetof(KernelParams, kSleepThreshold) == 0x150);
static_assert(offsetof(KernelParams, kSleepThresholdSq) == 0x154);
static_assert(offsetof(KernelParams, kShockPropagation) == 0x158);
static_assert(offsetof(KernelParams, kRestitution) == 0x15c);
static_assert(offsetof(KernelParams, kSOR) == 0x160);
static_assert(offsetof(KernelParams, _pad3) == 0x164);
static_assert(offsetof(KernelParams, kNumParticles) == 0x170);
static_assert(offsetof(KernelParams, kNumParticlesAligned) == 0x174);
static_assert(offsetof(KernelParams, kDt) == 0x178);
static_assert(offsetof(KernelParams, kInvDt) == 0x17c);
static_assert(offsetof(KernelParams, kSubStepLength) == 0x180);
static_assert(offsetof(KernelParams, kMaxSpeed) == 0x184);
static_assert(offsetof(KernelParams, kInvCellEdge) == 0x188);
static_assert(offsetof(KernelParams, kStaticTriGridInvCellEdge) == 0x18c);
static_assert(offsetof(KernelParams, kCollideParticlesRadiusSq) == 0x190);
static_assert(offsetof(KernelParams, kMaxParticles) == 0x194);
static_assert(offsetof(KernelParams, kRelaxationMode) == 0x198);
static_assert(offsetof(KernelParams, kShapesCount) == 0x19c);
static_assert(offsetof(KernelParams, kNumShapes) == 0x1a0);
static_assert(offsetof(KernelParams, kNumRigids) == 0x1a4);
static_assert(offsetof(KernelParams, kNumSprings) == 0x1a8);
static_assert(offsetof(KernelParams, kNumTriangles) == 0x1ac);
static_assert(offsetof(KernelParams, kMaxDiffuseParticles) == 0x1b0);
static_assert(offsetof(KernelParams, kDiffuseRadixSortSize) == 0x1b4);
static_assert(offsetof(KernelParams, kDiffuseDt) == 0x1b8);
static_assert(offsetof(KernelParams, kDiffuseMaxVelocity) == 0x1bc);
static_assert(offsetof(KernelParams, kDiffuseSortAxis) == 0x1c0);
static_assert(offsetof(KernelParams, kRelaxationFactor) == 0x1cc);
static_assert(offsetof(KernelParams, kStaticTriGridLower) == 0x1d0);
static_assert(offsetof(KernelParams, kDiffuseLifetime) == 0x1dc);
static_assert(offsetof(KernelParams, kWind) == 0x1e0);
static_assert(offsetof(KernelParams, kMaxNeighborsPerParticle) == 0x1ec);
static_assert(offsetof(KernelParams, kNumGeometryEntries) == 0x1f0);
static_assert(offsetof(KernelParams, kMaxAcceleration) == 0x1f4);
static_assert(offsetof(KernelParams, kMaxVelocityDelta) == 0x1f8);
static_assert(offsetof(KernelParams, kMaxContactsPerParticle) == 0x1fc);
struct NvFlexSolverDesc {
    std::int32_t featureMode; // original enum: NvFlexFeatureMode // +0x0
    std::int32_t maxParticles; // +0x4
    std::int32_t maxDiffuseParticles; // +0x8
    std::int32_t maxNeighborsPerParticle; // +0xc
    std::int32_t maxContactsPerParticle; // +0x10
};
static_assert(sizeof(NvFlexSolverDesc) == 20);
static_assert(offsetof(NvFlexSolverDesc, featureMode) == 0x0);
static_assert(offsetof(NvFlexSolverDesc, maxParticles) == 0x4);
static_assert(offsetof(NvFlexSolverDesc, maxDiffuseParticles) == 0x8);
static_assert(offsetof(NvFlexSolverDesc, maxNeighborsPerParticle) == 0xc);
static_assert(offsetof(NvFlexSolverDesc, maxContactsPerParticle) == 0x10);
struct NvFlexParams {
    std::int32_t numIterations; // +0x0
    float gravity[3]; // +0x4
    float radius; // +0x10
    float solidRestDistance; // +0x14
    float fluidRestDistance; // +0x18
    float dynamicFriction; // +0x1c
    float staticFriction; // +0x20
    float particleFriction; // +0x24
    float restitution; // +0x28
    float adhesion; // +0x2c
    float sleepThreshold; // +0x30
    float maxSpeed; // +0x34
    float maxAcceleration; // +0x38
    float shockPropagation; // +0x3c
    float dissipation; // +0x40
    float damping; // +0x44
    float wind[3]; // +0x48
    float drag; // +0x54
    float lift; // +0x58
    float cohesion; // +0x5c
    float surfaceTension; // +0x60
    float viscosity; // +0x64
    float vorticityConfinement; // +0x68
    float anisotropyScale; // +0x6c
    float anisotropyMin; // +0x70
    float anisotropyMax; // +0x74
    float smoothing; // +0x78
    float solidPressure; // +0x7c
    float freeSurfaceDrag; // +0x80
    float buoyancy; // +0x84
    float diffuseThreshold; // +0x88
    float diffuseBuoyancy; // +0x8c
    float diffuseDrag; // +0x90
    std::int32_t diffuseBallistic; // +0x94
    float diffuseLifetime; // +0x98
    float collisionDistance; // +0x9c
    float particleCollisionMargin; // +0xa0
    float shapeCollisionMargin; // +0xa4
    float planes[8][4]; // +0xa8
    std::int32_t numPlanes; // +0x128
    std::int32_t relaxationMode; // original enum: NvFlexRelaxationMode // +0x12c
    float relaxationFactor; // +0x130
};
static_assert(sizeof(NvFlexParams) == 308);
static_assert(offsetof(NvFlexParams, numIterations) == 0x0);
static_assert(offsetof(NvFlexParams, gravity) == 0x4);
static_assert(offsetof(NvFlexParams, radius) == 0x10);
static_assert(offsetof(NvFlexParams, solidRestDistance) == 0x14);
static_assert(offsetof(NvFlexParams, fluidRestDistance) == 0x18);
static_assert(offsetof(NvFlexParams, dynamicFriction) == 0x1c);
static_assert(offsetof(NvFlexParams, staticFriction) == 0x20);
static_assert(offsetof(NvFlexParams, particleFriction) == 0x24);
static_assert(offsetof(NvFlexParams, restitution) == 0x28);
static_assert(offsetof(NvFlexParams, adhesion) == 0x2c);
static_assert(offsetof(NvFlexParams, sleepThreshold) == 0x30);
static_assert(offsetof(NvFlexParams, maxSpeed) == 0x34);
static_assert(offsetof(NvFlexParams, maxAcceleration) == 0x38);
static_assert(offsetof(NvFlexParams, shockPropagation) == 0x3c);
static_assert(offsetof(NvFlexParams, dissipation) == 0x40);
static_assert(offsetof(NvFlexParams, damping) == 0x44);
static_assert(offsetof(NvFlexParams, wind) == 0x48);
static_assert(offsetof(NvFlexParams, drag) == 0x54);
static_assert(offsetof(NvFlexParams, lift) == 0x58);
static_assert(offsetof(NvFlexParams, cohesion) == 0x5c);
static_assert(offsetof(NvFlexParams, surfaceTension) == 0x60);
static_assert(offsetof(NvFlexParams, viscosity) == 0x64);
static_assert(offsetof(NvFlexParams, vorticityConfinement) == 0x68);
static_assert(offsetof(NvFlexParams, anisotropyScale) == 0x6c);
static_assert(offsetof(NvFlexParams, anisotropyMin) == 0x70);
static_assert(offsetof(NvFlexParams, anisotropyMax) == 0x74);
static_assert(offsetof(NvFlexParams, smoothing) == 0x78);
static_assert(offsetof(NvFlexParams, solidPressure) == 0x7c);
static_assert(offsetof(NvFlexParams, freeSurfaceDrag) == 0x80);
static_assert(offsetof(NvFlexParams, buoyancy) == 0x84);
static_assert(offsetof(NvFlexParams, diffuseThreshold) == 0x88);
static_assert(offsetof(NvFlexParams, diffuseBuoyancy) == 0x8c);
static_assert(offsetof(NvFlexParams, diffuseDrag) == 0x90);
static_assert(offsetof(NvFlexParams, diffuseBallistic) == 0x94);
static_assert(offsetof(NvFlexParams, diffuseLifetime) == 0x98);
static_assert(offsetof(NvFlexParams, collisionDistance) == 0x9c);
static_assert(offsetof(NvFlexParams, particleCollisionMargin) == 0xa0);
static_assert(offsetof(NvFlexParams, shapeCollisionMargin) == 0xa4);
static_assert(offsetof(NvFlexParams, planes) == 0xa8);
static_assert(offsetof(NvFlexParams, numPlanes) == 0x128);
static_assert(offsetof(NvFlexParams, relaxationMode) == 0x12c);
static_assert(offsetof(NvFlexParams, relaxationFactor) == 0x130);
struct NvFlexSolver {
    KernelParams mKernelParamsHost; // +0x0
    std::byte mKernelParams[24]; // opaque original: DxConstantBuffer // +0x200
    std::byte mPositions[32]; // opaque original: DxBufferExt // +0x218
    std::byte mNewPositions[32]; // opaque original: DxBufferExt // +0x238
    std::byte mVelocities[32]; // opaque original: DxBufferExt // +0x258
    std::byte mRestPositions[32]; // opaque original: DxBufferExt // +0x278
    std::byte mDeltas[32]; // opaque original: DxBufferExt // +0x298
    std::byte mPhases[32]; // opaque original: DxBufferExt // +0x2b8
    std::byte mActiveIndices[32]; // opaque original: DxBufferExt // +0x2d8
    std::byte mDensities[32]; // opaque original: DxBufferExt // +0x2f8
    std::byte mPotentials[32]; // opaque original: DxBufferExt // +0x318
    std::byte mCurl[32]; // opaque original: DxBufferExt // +0x338
    std::byte mNormals[32]; // opaque original: DxBufferExt // +0x358
    std::byte mSortedNormals[32]; // opaque original: DxBufferExt // +0x378
    std::byte mNormalsTemp[32]; // opaque original: DxBufferExt // +0x398
    std::byte mAnisotropy1[32]; // opaque original: DxBufferExt // +0x3b8
    std::byte mAnisotropy2[32]; // opaque original: DxBufferExt // +0x3d8
    std::byte mAnisotropy3[32]; // opaque original: DxBufferExt // +0x3f8
    std::byte mSortedPositions[32]; // opaque original: DxBufferExt // +0x418
    std::byte mSortedVelocities[32]; // opaque original: DxBufferExt // +0x438
    std::byte mSortedNewPositions[32]; // opaque original: DxBufferExt // +0x458
    std::byte mSortedNewVelocities[32]; // opaque original: DxBufferExt // +0x478
    std::byte mSortedPhases[32]; // opaque original: DxBufferExt // +0x498
    std::byte mSortedDensities[32]; // opaque original: DxBufferExt // +0x4b8
    std::byte mStaticContactPlanes[32]; // opaque original: DxBufferExt // +0x4d8
    std::byte mStaticContactVelocities[32]; // opaque original: DxBufferExt // +0x4f8
    std::byte mStaticContactCounts[32]; // opaque original: DxBufferExt // +0x518
    std::int32_t mMaxNeighborsPerParticle; // +0x538
    std::byte padding_53c[4];
    std::byte mParticleNeighbors[32]; // opaque original: DxBufferExt // +0x540
    std::byte mParticleNeighborCounts[32]; // opaque original: DxBufferExt // +0x560
    std::int32_t mMaxContactsPerParticle; // +0x580
    std::byte padding_584[4];
    std::byte mPlanes[32]; // opaque original: DxBufferExt // +0x588
    std::byte mSpringIndices[32]; // opaque original: DxBufferExt // +0x5a8
    std::byte mSpringLengths[32]; // opaque original: DxBufferExt // +0x5c8
    std::byte mSpringStiffness[32]; // opaque original: DxBufferExt // +0x5e8
    std::int32_t mNumSprings; // +0x608
    std::int32_t mMaxSprings; // +0x60c
    std::byte mHalfSpringIndices[32]; // opaque original: DxBufferExt // +0x610
    std::byte mHalfSpringOpposites[32]; // opaque original: DxBufferExt // +0x630
    std::byte mHalfSpringLengths[32]; // opaque original: DxBufferExt // +0x650
    std::byte mHalfSpringStiffness[32]; // opaque original: DxBufferExt // +0x670
    std::byte mHalfSpringParticleBegin[32]; // opaque original: DxBufferExt // +0x690
    std::byte mHalfSpringParticleEnd[32]; // opaque original: DxBufferExt // +0x6b0
    std::byte mHalfSpringConstantBuffer[24]; // opaque original: DxConstantBuffer // +0x6d0
    std::int32_t mMaxHalfSprings; // +0x6e8
    std::byte padding_6ec[4];
    std::byte mRigidOffsets[32]; // opaque original: DxBufferExt // +0x6f0
    std::byte mRigidIndices[32]; // opaque original: DxBufferExt // +0x710
    std::byte mRigidLocalPositions[32]; // opaque original: DxBufferExt // +0x730
    std::byte mRigidLocalNormals[32]; // opaque original: DxBufferExt // +0x750
    std::byte mRigidCoefficients[32]; // opaque original: DxBufferExt // +0x770
    std::byte mRigidPlasticThresholds[32]; // opaque original: DxBufferExt // +0x790
    std::byte mRigidPlasticCreeps[32]; // opaque original: DxBufferExt // +0x7b0
    std::byte mRigidRotations[32]; // opaque original: DxBufferExt // +0x7d0
    std::byte mRigidTranslations[32]; // opaque original: DxBufferExt // +0x7f0
    std::int32_t mNumRigids; // +0x810
    std::int32_t mMaxRigids; // +0x814
    std::int32_t mNumRigidIndices; // +0x818
    std::int32_t mMaxRigidIndices; // +0x81c
    std::int32_t mMaxPlasticEntries; // +0x820
    std::byte padding_824[4];
    std::byte mDynamicTriangles[32]; // opaque original: DxBufferExt // +0x828
    std::byte mDynamicTriangleNormals[32]; // opaque original: DxBufferExt // +0x848
    std::int32_t mDynamicNumTris; // +0x868
    std::int32_t mDynamicMaxTris; // +0x86c
    std::byte mDynamicTriangleEdges[32]; // opaque original: DxBufferExt // +0x870
    std::byte mDynamicNumTriEdges[32]; // opaque original: DxBufferExt // +0x890
    std::byte mPressures[32]; // opaque original: DxBufferExt // +0x8b0
    std::byte mInflatables[32]; // opaque original: DxComputeBuffer // +0x8d0
    std::int32_t mNumInflatables; // +0x8f0
    std::int32_t mMaxInflatables; // +0x8f4
    std::byte mDiffusePositions[32]; // opaque original: DxBufferExt // +0x8f8
    std::byte mDiffuseVelocities[32]; // opaque original: DxBufferExt // +0x918
    std::byte mDiffusePositionsNew[32]; // opaque original: DxBufferExt // +0x938
    std::byte mDiffuseVelocitiesNew[32]; // opaque original: DxBufferExt // +0x958
    std::byte mNumDiffuseParticles[32]; // opaque original: DxComputeBuffer // +0x978
    std::byte mNumDiffuseParticlesNew[32]; // opaque original: DxComputeBuffer // +0x998
    std::int32_t mMaxDiffuseParticles; // +0x9b8
    std::int32_t mNumActiveDiffuseParticles; // +0x9bc
    std::byte mDiffuseSortSize[32]; // opaque original: DxBufferExt // +0x9c0
    std::byte mDiffuseLaunchArg[32]; // opaque original: DxBufferExt // +0x9e0
    float mDiffuseRate; // +0xa00
    float mDiffuseTimer; // +0xa04
    std::byte mCellIds[32]; // opaque original: DxBufferExt // +0xa08
    std::byte mReverseLookup[32]; // opaque original: DxBufferExt // +0xa28
    std::int32_t mNumParticles; // +0xa48
    std::int32_t mNumParticlesAligned; // +0xa4c
    std::int32_t mMaxParticles; // +0xa50
    std::byte padding_a54[4];
    std::byte mParticleBounds[32]; // opaque original: DxBufferExt // +0xa58
    std::byte mBoundsLower[32]; // opaque original: DxBufferExt // +0xa78
    std::byte mBoundsUpper[32]; // opaque original: DxBufferExt // +0xa98
    std::byte mGroupBoundsLower[32]; // opaque original: DxBufferExt // +0xab8
    std::byte mGroupBoundsUpper[32]; // opaque original: DxBufferExt // +0xad8
    NvFlexSolverDesc mDesc; // +0xaf8
    NvFlexParams mParams; // +0xb0c
    std::byte mSDFShapeDX[32]; // opaque original: DxBufferExt // +0xc40
    std::byte mSDFDeviceShapes[24]; // opaque original: std::vector<FlexSDFData *,std::allocator<FlexSDFData *> > // +0xc60
    std::byte mShapes[408]; // opaque original: FlexShapeData // +0xc78
    bool mDebug; // +0xe10
    std::byte padding_e11[7];
    std::byte mRandom[32]; // opaque original: DxBufferExt // +0xe18
    float mFluidRestDensity; // +0xe38
    float mFluidDensityConstraintScale; // +0xe3c
    float mFluidSurfaceConstraintScale; // +0xe40
    std::int32_t mStepCounter; // +0xe44
    std::byte mCallbacks[80]; // opaque original: NvFlexSolverCallback[5] // +0xe48
    std::byte mSmoothPositionsOriginal[32]; // opaque original: DxBufferExt // +0xe98
    std::int32_t mRadixSortSize; // +0xeb8
    std::byte padding_ebc[4];
    std::byte mRadixSort[8]; // opaque original: NvFlex::RadixSort* // +0xec0
    std::byte mSubstepParams[24]; // opaque original: DxConstantBuffer // +0xec8
    std::byte mNumShapes[24]; // opaque original: DxConstantBuffer // +0xee0
    std::byte mTimers[8]; // opaque original: `anonymous-namespace'::DxTimers* // +0xef8
    std::int32_t mNumDetailTimers; // +0xf00
    std::byte padding_f04[4];
    std::byte mDetailTimers[8]; // opaque original: NvFlexDetailTimer* // +0xf08
    bool mLatencyTimerBeginRecorded; // +0xf10
    bool mLatencyTimerEndRecorded; // +0xf11
    bool mLatencyTimerEnable; // +0xf12
    std::byte padding_f13[1];
    std::int32_t mLatencyTimerIndex; // +0xf14
    std::byte mLib[8]; // opaque original: NvFlexLibrary* // +0xf18
};
static_assert(sizeof(NvFlexSolver) == 3872);
static_assert(offsetof(NvFlexSolver, mKernelParamsHost) == 0x0);
static_assert(offsetof(NvFlexSolver, mKernelParams) == 0x200);
static_assert(offsetof(NvFlexSolver, mPositions) == 0x218);
static_assert(offsetof(NvFlexSolver, mNewPositions) == 0x238);
static_assert(offsetof(NvFlexSolver, mVelocities) == 0x258);
static_assert(offsetof(NvFlexSolver, mRestPositions) == 0x278);
static_assert(offsetof(NvFlexSolver, mDeltas) == 0x298);
static_assert(offsetof(NvFlexSolver, mPhases) == 0x2b8);
static_assert(offsetof(NvFlexSolver, mActiveIndices) == 0x2d8);
static_assert(offsetof(NvFlexSolver, mDensities) == 0x2f8);
static_assert(offsetof(NvFlexSolver, mPotentials) == 0x318);
static_assert(offsetof(NvFlexSolver, mCurl) == 0x338);
static_assert(offsetof(NvFlexSolver, mNormals) == 0x358);
static_assert(offsetof(NvFlexSolver, mSortedNormals) == 0x378);
static_assert(offsetof(NvFlexSolver, mNormalsTemp) == 0x398);
static_assert(offsetof(NvFlexSolver, mAnisotropy1) == 0x3b8);
static_assert(offsetof(NvFlexSolver, mAnisotropy2) == 0x3d8);
static_assert(offsetof(NvFlexSolver, mAnisotropy3) == 0x3f8);
static_assert(offsetof(NvFlexSolver, mSortedPositions) == 0x418);
static_assert(offsetof(NvFlexSolver, mSortedVelocities) == 0x438);
static_assert(offsetof(NvFlexSolver, mSortedNewPositions) == 0x458);
static_assert(offsetof(NvFlexSolver, mSortedNewVelocities) == 0x478);
static_assert(offsetof(NvFlexSolver, mSortedPhases) == 0x498);
static_assert(offsetof(NvFlexSolver, mSortedDensities) == 0x4b8);
static_assert(offsetof(NvFlexSolver, mStaticContactPlanes) == 0x4d8);
static_assert(offsetof(NvFlexSolver, mStaticContactVelocities) == 0x4f8);
static_assert(offsetof(NvFlexSolver, mStaticContactCounts) == 0x518);
static_assert(offsetof(NvFlexSolver, mMaxNeighborsPerParticle) == 0x538);
static_assert(offsetof(NvFlexSolver, mParticleNeighbors) == 0x540);
static_assert(offsetof(NvFlexSolver, mParticleNeighborCounts) == 0x560);
static_assert(offsetof(NvFlexSolver, mMaxContactsPerParticle) == 0x580);
static_assert(offsetof(NvFlexSolver, mPlanes) == 0x588);
static_assert(offsetof(NvFlexSolver, mSpringIndices) == 0x5a8);
static_assert(offsetof(NvFlexSolver, mSpringLengths) == 0x5c8);
static_assert(offsetof(NvFlexSolver, mSpringStiffness) == 0x5e8);
static_assert(offsetof(NvFlexSolver, mNumSprings) == 0x608);
static_assert(offsetof(NvFlexSolver, mMaxSprings) == 0x60c);
static_assert(offsetof(NvFlexSolver, mHalfSpringIndices) == 0x610);
static_assert(offsetof(NvFlexSolver, mHalfSpringOpposites) == 0x630);
static_assert(offsetof(NvFlexSolver, mHalfSpringLengths) == 0x650);
static_assert(offsetof(NvFlexSolver, mHalfSpringStiffness) == 0x670);
static_assert(offsetof(NvFlexSolver, mHalfSpringParticleBegin) == 0x690);
static_assert(offsetof(NvFlexSolver, mHalfSpringParticleEnd) == 0x6b0);
static_assert(offsetof(NvFlexSolver, mHalfSpringConstantBuffer) == 0x6d0);
static_assert(offsetof(NvFlexSolver, mMaxHalfSprings) == 0x6e8);
static_assert(offsetof(NvFlexSolver, mRigidOffsets) == 0x6f0);
static_assert(offsetof(NvFlexSolver, mRigidIndices) == 0x710);
static_assert(offsetof(NvFlexSolver, mRigidLocalPositions) == 0x730);
static_assert(offsetof(NvFlexSolver, mRigidLocalNormals) == 0x750);
static_assert(offsetof(NvFlexSolver, mRigidCoefficients) == 0x770);
static_assert(offsetof(NvFlexSolver, mRigidPlasticThresholds) == 0x790);
static_assert(offsetof(NvFlexSolver, mRigidPlasticCreeps) == 0x7b0);
static_assert(offsetof(NvFlexSolver, mRigidRotations) == 0x7d0);
static_assert(offsetof(NvFlexSolver, mRigidTranslations) == 0x7f0);
static_assert(offsetof(NvFlexSolver, mNumRigids) == 0x810);
static_assert(offsetof(NvFlexSolver, mMaxRigids) == 0x814);
static_assert(offsetof(NvFlexSolver, mNumRigidIndices) == 0x818);
static_assert(offsetof(NvFlexSolver, mMaxRigidIndices) == 0x81c);
static_assert(offsetof(NvFlexSolver, mMaxPlasticEntries) == 0x820);
static_assert(offsetof(NvFlexSolver, mDynamicTriangles) == 0x828);
static_assert(offsetof(NvFlexSolver, mDynamicTriangleNormals) == 0x848);
static_assert(offsetof(NvFlexSolver, mDynamicNumTris) == 0x868);
static_assert(offsetof(NvFlexSolver, mDynamicMaxTris) == 0x86c);
static_assert(offsetof(NvFlexSolver, mDynamicTriangleEdges) == 0x870);
static_assert(offsetof(NvFlexSolver, mDynamicNumTriEdges) == 0x890);
static_assert(offsetof(NvFlexSolver, mPressures) == 0x8b0);
static_assert(offsetof(NvFlexSolver, mInflatables) == 0x8d0);
static_assert(offsetof(NvFlexSolver, mNumInflatables) == 0x8f0);
static_assert(offsetof(NvFlexSolver, mMaxInflatables) == 0x8f4);
static_assert(offsetof(NvFlexSolver, mDiffusePositions) == 0x8f8);
static_assert(offsetof(NvFlexSolver, mDiffuseVelocities) == 0x918);
static_assert(offsetof(NvFlexSolver, mDiffusePositionsNew) == 0x938);
static_assert(offsetof(NvFlexSolver, mDiffuseVelocitiesNew) == 0x958);
static_assert(offsetof(NvFlexSolver, mNumDiffuseParticles) == 0x978);
static_assert(offsetof(NvFlexSolver, mNumDiffuseParticlesNew) == 0x998);
static_assert(offsetof(NvFlexSolver, mMaxDiffuseParticles) == 0x9b8);
static_assert(offsetof(NvFlexSolver, mNumActiveDiffuseParticles) == 0x9bc);
static_assert(offsetof(NvFlexSolver, mDiffuseSortSize) == 0x9c0);
static_assert(offsetof(NvFlexSolver, mDiffuseLaunchArg) == 0x9e0);
static_assert(offsetof(NvFlexSolver, mDiffuseRate) == 0xa00);
static_assert(offsetof(NvFlexSolver, mDiffuseTimer) == 0xa04);
static_assert(offsetof(NvFlexSolver, mCellIds) == 0xa08);
static_assert(offsetof(NvFlexSolver, mReverseLookup) == 0xa28);
static_assert(offsetof(NvFlexSolver, mNumParticles) == 0xa48);
static_assert(offsetof(NvFlexSolver, mNumParticlesAligned) == 0xa4c);
static_assert(offsetof(NvFlexSolver, mMaxParticles) == 0xa50);
static_assert(offsetof(NvFlexSolver, mParticleBounds) == 0xa58);
static_assert(offsetof(NvFlexSolver, mBoundsLower) == 0xa78);
static_assert(offsetof(NvFlexSolver, mBoundsUpper) == 0xa98);
static_assert(offsetof(NvFlexSolver, mGroupBoundsLower) == 0xab8);
static_assert(offsetof(NvFlexSolver, mGroupBoundsUpper) == 0xad8);
static_assert(offsetof(NvFlexSolver, mDesc) == 0xaf8);
static_assert(offsetof(NvFlexSolver, mParams) == 0xb0c);
static_assert(offsetof(NvFlexSolver, mSDFShapeDX) == 0xc40);
static_assert(offsetof(NvFlexSolver, mSDFDeviceShapes) == 0xc60);
static_assert(offsetof(NvFlexSolver, mShapes) == 0xc78);
static_assert(offsetof(NvFlexSolver, mDebug) == 0xe10);
static_assert(offsetof(NvFlexSolver, mRandom) == 0xe18);
static_assert(offsetof(NvFlexSolver, mFluidRestDensity) == 0xe38);
static_assert(offsetof(NvFlexSolver, mFluidDensityConstraintScale) == 0xe3c);
static_assert(offsetof(NvFlexSolver, mFluidSurfaceConstraintScale) == 0xe40);
static_assert(offsetof(NvFlexSolver, mStepCounter) == 0xe44);
static_assert(offsetof(NvFlexSolver, mCallbacks) == 0xe48);
static_assert(offsetof(NvFlexSolver, mSmoothPositionsOriginal) == 0xe98);
static_assert(offsetof(NvFlexSolver, mRadixSortSize) == 0xeb8);
static_assert(offsetof(NvFlexSolver, mRadixSort) == 0xec0);
static_assert(offsetof(NvFlexSolver, mSubstepParams) == 0xec8);
static_assert(offsetof(NvFlexSolver, mNumShapes) == 0xee0);
static_assert(offsetof(NvFlexSolver, mTimers) == 0xef8);
static_assert(offsetof(NvFlexSolver, mNumDetailTimers) == 0xf00);
static_assert(offsetof(NvFlexSolver, mDetailTimers) == 0xf08);
static_assert(offsetof(NvFlexSolver, mLatencyTimerBeginRecorded) == 0xf10);
static_assert(offsetof(NvFlexSolver, mLatencyTimerEndRecorded) == 0xf11);
static_assert(offsetof(NvFlexSolver, mLatencyTimerEnable) == 0xf12);
static_assert(offsetof(NvFlexSolver, mLatencyTimerIndex) == 0xf14);
static_assert(offsetof(NvFlexSolver, mLib) == 0xf18);
#pragma pack(pop)
} // namespace nvflex_recovered
