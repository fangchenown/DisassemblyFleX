#pragma once
#include "SolverState.hpp"
namespace df {
void UpdateParticleSubstep(NvFlexSolver*,float substepDt,int substep,int numSubsteps);
void ExecuteCallback(NvFlexSolver*,NvFlexSolverCallbackStage,float dt);
}
