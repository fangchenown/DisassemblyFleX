import ctypes as C

lib=C.WinDLL(r'C:\Windows\System32\d3dcompiler_47.dll')
def select_compiler(path):
    global lib
    lib=C.WinDLL(str(path))

def take_blob(blob):
    if not blob:
        return b''
    vtable=C.cast(blob,C.POINTER(C.POINTER(C.c_void_p))).contents
    pointer=C.WINFUNCTYPE(C.c_void_p,C.c_void_p)(vtable[3])
    size=C.WINFUNCTYPE(C.c_size_t,C.c_void_p)(vtable[4])
    release=C.WINFUNCTYPE(C.c_ulong,C.c_void_p)(vtable[2])
    try:
        return C.string_at(pointer(blob),size(blob))
    finally:
        release(blob)

def disassemble(data, flags=0x80):
    proc=lib.D3DDisassemble
    proc.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_char_p,C.POINTER(C.c_void_p)]
    proc.restype=C.c_long
    buffer=C.create_string_buffer(data)
    result=C.c_void_p()
    hr=proc(buffer,len(data),flags,None,C.byref(result))
    if hr<0: raise RuntimeError(f'D3DDisassemble {hr & 0xffffffff:08x}')
    return take_blob(result).rstrip(b'\0').decode('utf-8')

def compile_hlsl(text, name='recovered.hlsl', flags=1<<15):
    # D3DCOMPILE_OPTIMIZATION_LEVEL3; sources have no filesystem includes.
    proc=lib.D3DCompile
    proc.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)]
    proc.restype=C.c_long
    data=text.encode('utf-8')
    buffer=C.create_string_buffer(data)
    result,errors=C.c_void_p(),C.c_void_p()
    hr=proc(buffer,len(data),name.encode('utf-8'),None,None,b'main',b'cs_5_0',flags,0,C.byref(result),C.byref(errors))
    return hr,take_blob(result),take_blob(errors).rstrip(b'\0').decode('utf-8','replace')
