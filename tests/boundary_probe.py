"""Isolate reference defects; expected failure is recorded, never hidden."""
import ctypes as C,json,os,sys
from pathlib import Path
from lifecycle_oracle import Init,Callback,bind
directory=os.add_dll_directory(str(Path(__file__).resolve().parents[2]/'FleX/bin/win64'))
dll=C.CDLL(sys.argv[1]);case=sys.argv[2];output=Path(sys.argv[3]);messages=[];shutdown_phase=False
def save(value):output.write_text(json.dumps(value,indent=2),encoding='utf-8');print(json.dumps(value),flush=True)
def log(severity,text,file,line):
    messages.append([severity,text.decode(),file.decode(),line])
    if shutdown_phase and len(messages)==3:
        save({'case':case,'observed':'repeated_invalid_id_shutdown_loop','messages':messages});os._exit(0)
callback=Callback(log);initialize=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)])
try:
    if case=='invalid-compute-enum':
        pointer=initialize(120,callback,C.byref(Init(-1,False,None,None,None,True,99)));save({'case':case,'returned_null':not pointer,'messages':messages});os._exit(0)
    library=initialize(120,callback,C.byref(Init(-1,False,None,None,None,True,1)));assert library
    if case=='zero-buffer':
        b=bind(dll,'NvFlexAllocBuffer',C.c_void_p,[C.c_void_p,C.c_int,C.c_int,C.c_int])(library,0,4,0);p=bind(dll,'NvFlexMap',C.c_void_p,[C.c_void_p,C.c_int])(b,0);save({'case':case,'mapped':bool(p),'messages':messages})
    elif case=='sdf-overflow':
        create=bind(dll,'NvFlexCreateDistanceField',C.c_uint,[C.c_void_p]);ids=[create(library) for _ in range(17)];assert ids==list(range(1,17))+[0];shutdown_phase=True;messages.clear();bind(dll,'NvFlexShutdown',None,[C.c_void_p])(library);save({'case':case,'observed':'shutdown_returned','ids':ids})
    else:raise ValueError(case)
except OSError as error:save({'case':case,'observed':'native_exception','exception':str(error),'messages':messages})
os._exit(0)
