#include "FluidConstants.hpp"
#include <array>
#include <cmath>
#include <cstdint>
namespace df {
namespace { struct Vec3 {float x,y,z;};std::uint32_t seed1=0,seed2=0; }
std::uint32_t RandomUint(){seed1=((seed1<<5)|(seed1>>27))^(seed2*seed1)^seed2;seed2=((seed2<<12)|(seed2>>20))^seed1;return seed1;}
float RandomSigned(){float t=float(RandomUint())*0x1p-32f;return t-(1.0f-t);}
// RVA 0x2e520 and SDK core/maths.h TightPack3D agree on packing/order.
static int TightPack(float radius,float separation,Vec3* points,int maxPoints){
    const int dim=static_cast<int>(std::ceil(radius/separation));int count=0;
    for(int z=-dim;z<=dim;++z)for(int y=-dim;y<=dim;++y)for(int x=-dim;x<=dim;++x){
        float px=float(x)*separation+(((y+z)&1)?separation*0.5f:0.0f);
        float py=float(y)*0.8660254f*separation;
        float pz=float(z)*0.8660254f*separation;
        float lengthSquared=px*px+py*py+pz*pz;
        if(lengthSquared!=0.0f&&count<maxPoints&&std::sqrt(lengthSquared)<=radius)points[count++]={px,py,pz};
    }
    return count;
}
// RVA 0x34ba0: 2048-point storage, quadratic spiky kernel, scalar accumulation.
// The reference resets its module-local RNG seeds here. TightPack itself is
// deterministic and does not consume the RNG; CreateSolver does consume it.
void CalculateRestDensity(float separation,float radius,float& density,float& constraintScale,float& surfaceScale){
    seed1=0x258f4aa;seed2=0x7583f;
    std::array<Vec3,2048> points{};int count=TightPack(radius,separation,points.data(),int(points.size()));
    density=0.0f;constraintScale=0.0f;float normalSum=0.0f,depthSum=0.0f;
    float inverseRadius=1.0f/radius;
    float coefficient=15.0f/(radius*3.1415927f*radius*radius);
    for(int i=0;i<count;++i){
        const auto& p=points[i];float squared=p.x*p.x+p.y*p.y+p.z*p.z;
        float distance=squared==0.0f?0.0f:std::sqrt(squared);
        float q=1.0f-inverseRadius*distance;
        float gradient=coefficient*-2.0f*q*inverseRadius;
        density=q*q*coefficient+density;
        constraintScale=gradient*gradient+constraintScale;
        if(p.y<=0.0f){
            float ny=p.y/distance;
            normalSum=normalSum+coefficient*-2.0f*q*inverseRadius*ny;
            depthSum=depthSum-distance*ny;
        }
    }
    surfaceScale=normalSum/depthSum;
}
}
