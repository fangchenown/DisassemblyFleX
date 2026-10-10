#pragma once
#include "recovered/FlexLayouts.hpp"
namespace df {
nvflex_recovered::KernelParams BuildKernelParams(const nvflex_recovered::NvFlexSolver&,float substepDt,int numSubsteps);
}
