#pragma once
#include "Runtime.hpp"
namespace df {
NvFlex::ComputeShader* GetShader(NvFlexLibrary* library,const char* name);
void DestroyShaders(NvFlexLibrary* library);
}
