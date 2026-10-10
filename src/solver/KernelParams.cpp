#include "KernelParams.hpp"
#include <cfloat>
#include <cstring>
namespace df {
// Recovered InitParams, RVA 0x34f40. Obsolete/padding fields that the reference
// never initializes are zeroed; all instruction-defined fields are compared.
nvflex_recovered::KernelParams BuildKernelParams(const nvflex_recovered::NvFlexSolver& s,float dt,int numSubsteps){
    nvflex_recovered::KernelParams p{};const auto& a=s.mParams;
    std::memcpy(p.kPlanes,a.planes,sizeof(p.kPlanes));p.kNumPlanes=a.numPlanes;
    p.kRadius=a.radius;p.kRadiusSq=a.radius*a.radius;p.kInvRadius=1.0f/a.radius;
    p.kPoly6=315.0f/(a.radius*201.06194f*a.radius*a.radius*a.radius*a.radius*a.radius*a.radius*a.radius*a.radius);
    float h3=a.radius*3.1415927f*a.radius*a.radius;
    p.kSpiky1=15.0f/h3;p.kSpiky2=30.0f/(h3*a.radius);
    float ratio=a.fluidRestDistance/a.radius;float inverseSquared=1.0f/(ratio*ratio);
    p.kCohesion1=-(inverseSquared*(ratio+1.0f));p.kCohesion2=((ratio+1.0f)*ratio+1.0f)*inverseSquared;
    p.kRestDensity=s.mFluidRestDensity;p.kInvRestDensity=1.0f/s.mFluidRestDensity;
    p.kFluidRestDistance=a.fluidRestDistance;p.kSolidRestDistance=a.solidRestDistance;p.kLambdaScale=1.0f/s.mFluidDensityConstraintScale;
    p.kCohesion=a.radius*a.cohesion;p.kSurfaceTension=(p.kInvRestDensity*a.surfaceTension)/s.mFluidSurfaceConstraintScale;
    p.kSolidPressure=a.solidPressure;p.kVorticityConfinement=a.vorticityConfinement;
    p.kAnisotropy=a.anisotropyScale;p.kAnisotropyMin=a.radius*a.anisotropyMin;p.kAnisotropyMax=a.radius*a.anisotropyMax;
    p.kSmoothing=a.smoothing;p.kViscosity=p.kInvRestDensity*a.viscosity;p.kFreeSurfaceDrag=a.freeSurfaceDrag;p.kBuoyancy=a.buoyancy;
    p.kDiffuseThreshold=s.mMaxDiffuseParticles?a.diffuseThreshold:0.0f;p.kDiffuseBuoyancy=a.diffuseBuoyancy;p.kDiffuseDrag=a.diffuseDrag;p.kDiffuseBallistic=a.diffuseBallistic;
    p.kGravity={a.gravity[0],a.gravity[1],a.gravity[2]};p.kDynamicFriction=a.dynamicFriction;p.kStaticFriction=a.staticFriction;p.kParticleFriction=a.particleFriction;
    p.kAdhesion=a.adhesion;p.kDissipation=a.dissipation;p.kDamping=a.damping;
    p.kCollisionDistance=a.collisionDistance;p.kCollisionThreshold=a.shapeCollisionMargin;p.kCollisionMargin=p.kCollisionThreshold+p.kCollisionDistance;p.kCollisionMarginSq=p.kCollisionMargin*p.kCollisionMargin;
    p.kDrag=a.drag*60.0f;p.kLift=a.lift*60.0f;p.kSleepThreshold=a.sleepThreshold;p.kSleepThresholdSq=a.sleepThreshold*a.sleepThreshold;
    p.kShockPropagation=a.shockPropagation;p.kRestitution=a.restitution;p.kSOR=1.0f/(a.relaxationFactor+1.0f);
    p.kNumParticles=s.mNumParticles;p.kNumParticlesAligned=s.mNumParticlesAligned;p.kDt=dt;p.kInvDt=1.0f/dt;p.kSubStepLength=1.0f/float(numSubsteps);p.kMaxSpeed=a.maxSpeed;
    float edge=a.radius+a.particleCollisionMargin;p.kInvCellEdge=1.0f/edge;p.kCollideParticlesRadiusSq=edge*edge;
    p.kMaxParticles=s.mMaxParticles;p.kRelaxationMode=a.relaxationMode;
    std::int64_t first=0,last=0;std::memcpy(&first,s.mSDFDeviceShapes,8);std::memcpy(&last,s.mSDFDeviceShapes+8,8);p.kShapesCount=int((last-first)>>3);
    std::memcpy(&p.kNumShapes,s.mShapes+0x170,4);p.kNumRigids=s.mNumRigids;p.kNumSprings=s.mNumSprings;p.kNumTriangles=s.mDynamicNumTris;
    p.kMaxDiffuseParticles=s.mMaxDiffuseParticles;p.kDiffuseDt=float(numSubsteps)*dt;p.kDiffuseMaxVelocity=FLT_MAX;
    p.kRelaxationFactor=a.relaxationFactor;p.kDiffuseLifetime=a.diffuseLifetime;p.kWind={a.wind[0],a.wind[1],a.wind[2]};
    p.kMaxNeighborsPerParticle=s.mMaxNeighborsPerParticle;p.kMaxAcceleration=a.maxAcceleration;p.kMaxVelocityDelta=a.maxAcceleration*dt;p.kMaxContactsPerParticle=s.mMaxContactsPerParticle;
    return p;
}
}
