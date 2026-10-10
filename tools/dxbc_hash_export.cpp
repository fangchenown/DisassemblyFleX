#include <windows.h>
#include <cstring>
void ComputeHashRetail(const BYTE*,UINT,BYTE*);
extern "C" __declspec(dllexport) int __cdecl RepairDxbc(void* data,unsigned length){
    if(length<32||std::memcmp(data,"DXBC",4)!=0)return 0;
    auto bytes=static_cast<BYTE*>(data);ComputeHashRetail(bytes+20,length-20,bytes+4);return 1;
}
