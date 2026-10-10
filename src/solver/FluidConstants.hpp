#pragma once
#include <cstdint>
namespace df {
void CalculateRestDensity(float separation,float radius,float& density,float& constraintScale,float& surfaceScale);
std::uint32_t RandomUint();
float RandomSigned();
}
