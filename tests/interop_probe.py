import ctypes as C,json,os,sys
from pathlib import Path
from lifecycle_oracle import Init,Desc,Callback,bind
directory=os.add_dll_directory(str(Path(__file__).resolve().parents[2]/'FleX/bin/win64'))
native=C.WinDLL('d3d11.dll');create=native.D3D11CreateDevice;create.restype=C.c_long;create.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.c_void_p,C.POINTER(C.c_void_p)]
device,context=C.c_void_p(),C.c_void_p();hr=create(None,1,None,0,None,0,7,C.byref(device),None,C.byref(context));assert hr>=0
dll=C.CDLL(sys.argv[1]);errors=[];cb=Callback(lambda s,t,f,l:errors.append([s,t.decode(),f.decode(),l]));desc=Init(-1,True,device,context,None,False,1)
try:
    lib=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)])(120,cb,C.byref(desc));result={'initialized':bool(lib)}
    if lib:
        result['name']=bind(dll,'NvFlexGetDeviceName',C.c_char_p,[C.c_void_p])(lib).decode();solver=bind(dll,'NvFlexCreateSolver',C.c_void_p,[C.c_void_p,C.POINTER(Desc)])(lib,C.byref(Desc(0,64,0,96,6)));result['solver_created']=bool(solver)
        bind(dll,'NvFlexComputeWaitForGraphics',None,[C.c_void_p])(lib);bind(dll,'NvFlexDestroySolver',None,[C.c_void_p])(solver);bind(dll,'NvFlexShutdown',None,[C.c_void_p])(lib)
except Exception as e:result={'exception':str(e)}
result['errors']=errors;Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
