#include "NvFlex.h"
#include "recovered/FlexLayouts.hpp"
#include "solver/FluidConstants.hpp"
#include <cstring>
// DF_IMPLEMENTED: NvFlexSetParams
// Numeric fields/parameter copying are tested directly against the original;
// global RNG side effects remain tracked until all RNG consumers are restored.
extern "C" void NvFlexSetParams(NvFlexSolver* solver,const NvFlexParams* params){
    auto& state=*reinterpret_cast<nvflex_recovered::NvFlexSolver*>(solver);
    if(params->fluidRestDistance<=0.0f){state.mFluidRestDensity=0;state.mFluidDensityConstraintScale=0;state.mFluidSurfaceConstraintScale=0;}
    else if(params->radius!=state.mParams.radius||params->fluidRestDistance!=state.mParams.fluidRestDistance){
        df::CalculateRestDensity(params->fluidRestDistance,params->radius,state.mFluidRestDensity,state.mFluidDensityConstraintScale,state.mFluidSurfaceConstraintScale);
    }
    static_assert(sizeof(state.mParams)==sizeof(*params));std::memcpy(&state.mParams,params,sizeof(*params));
}
