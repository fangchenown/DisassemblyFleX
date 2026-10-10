#include "ShaderLibrary.hpp"
#include "NvFlexShaders.generated.hpp"
#include <stdexcept>
namespace df {
NvFlex::ComputeShader* GetShader(NvFlexLibrary* library,const char* name){
    auto found=library->shaders.find(name);if(found!=library->shaders.end())return found->second;
    auto code=FindShaderCode(name);if(!code)throw std::runtime_error(std::string("Unknown recovered shader: ")+name);
    if(code->vendorEncoding==1&&library->mDevice->mGpuVendorId!=VENDOR_ID_NVIDIA)
        throw std::runtime_error(std::string("NVIDIA shader selected on a different vendor: ")+name);
    if(code->vendorEncoding==2&&library->mDevice->mGpuVendorId!=VENDOR_ID_AMD)
        throw std::runtime_error(std::string("AMD shader selected on a different vendor: ")+name);
    NvFlex::ComputeShaderDesc desc{};desc.cs=code->bytes;desc.cs_length=code->size;desc.label=code->label;desc.NvAPI_Slot=code->nvSlot;
    auto shader=library->mContext->createComputeShader(&desc);library->shaders.emplace(name,shader);return shader;
}
void DestroyShaders(NvFlexLibrary* library){for(auto& item:library->shaders)delete item.second;library->shaders.clear();}
}
