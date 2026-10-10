#pragma once
#include "D3D11Context.hpp"
#include <stdexcept>
#include <string>
namespace df {
// Driver interface IDs and signatures recovered from the original NvAPI
// wrappers at RVAs 0x16d40..0x17470. No original library code is forwarded.
template<class... Args> NvAPI_Status NvInterop(unsigned id,Args... args){
    using Query=void* (__cdecl*)(unsigned);static HMODULE module=LoadLibraryExW(L"nvapi64.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
    auto query=module?reinterpret_cast<Query>(GetProcAddress(module,"nvapi_QueryInterface")):nullptr;
    using Function=NvAPI_Status (__cdecl*)(Args...);auto fn=query?reinterpret_cast<Function>(query(id)):nullptr;
    return fn?fn(args...):NVAPI_NO_IMPLEMENTATION;
}
inline void NvCheck(NvAPI_Status status,const char* operation){if(status!=NVAPI_OK)throw std::runtime_error(std::string(operation)+" NvAPI="+std::to_string(status));}
}
