import ctypes as C,json,os,sys
from pathlib import Path
from lifecycle_oracle import Init,Desc,Callback,bind
directory=os.add_dll_directory(str(Path(__file__).resolve().parents[2]/'FleX/bin/win64'))
dll=C.CDLL(sys.argv[1]);errors=[];cb=Callback(lambda s,t,f,l:errors.append([s,t.decode(),l]));lib=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)])(120,cb,C.byref(Init(-1,False,None,None,None,True,1)))
create=bind(dll,'NvFlexCreateSolver',C.c_void_p,[C.c_void_p,C.POINTER(Desc)]);desc=Desc(0,64,0,96,6);src=create(lib,C.byref(desc));dst=create(lib,C.byref(desc))
try:
    bind(dll,'NvFlexCopySolver',None,[C.c_void_p,C.c_void_p])(dst,src);result={'returned':True}
except Exception as e:result={'returned':False,'exception':str(e)}
result['errors']=errors;Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
