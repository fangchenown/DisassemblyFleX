import ctypes as C,json,math,os,struct,sys
from pathlib import Path
from lifecycle_oracle import Init,Desc,Callback,bind
PROJECT=Path(__file__).resolve().parents[1];WS=PROJECT.parent;sys.path.insert(0,str(PROJECT/'tools'))
from ledger import write_json,event
class Detail(C.Structure):_fields_=[('name',C.c_char_p),('time',C.c_float)]
def run(path,nv):
    dll=C.CDLL(str(path));messages=[];callback=Callback(lambda s,t,f,l:messages.append([s,t.decode(),f.decode(),l]))
    lib=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)])(120,callback,C.byref(Init(-1,nv,None,None,None,True,1)))
    create=bind(dll,'NvFlexCreateSolver',C.c_void_p,[C.c_void_p,C.POINTER(Desc)]);solver=create(lib,C.byref(Desc(0,64,0,96,6)))
    alloc=bind(dll,'NvFlexAllocBuffer',C.c_void_p,[C.c_void_p,C.c_int,C.c_int,C.c_int]);free=bind(dll,'NvFlexFreeBuffer',None,[C.c_void_p]);mapbuf=bind(dll,'NvFlexMap',C.c_void_p,[C.c_void_p,C.c_int]);unmap=bind(dll,'NvFlexUnmap',None,[C.c_void_p]);buffers=[]
    timers=bind(dll,'NvFlexGetTimers',None,[C.c_void_p,C.c_void_p]);details=bind(dll,'NvFlexGetDetailTimers',C.c_int,[C.c_void_p,C.POINTER(C.POINTER(Detail))]);latency=bind(dll,'NvFlexGetDeviceLatency',C.c_float,[C.c_void_p]+[C.POINTER(C.c_ulonglong)]*3)
    try:
        sentinel=C.create_string_buffer(bytes([0xa5])*96,96);timers(solver,sentinel);assert bytes(sentinel)==bytes([0xa5])*96
        pointer=C.POINTER(Detail)();assert details(solver,C.byref(pointer))==0 and bool(pointer)
        begin,end,freq=C.c_ulonglong(11),C.c_ulonglong(22),C.c_ulonglong(33);assert latency(solver,C.byref(begin),C.byref(end),C.byref(freq))==0 and [begin.value,end.value,freq.value]==[11,22,33]
        params=C.create_string_buffer((WS/'Build/DisassemblyFleX-20261009/demo-runs/reference-scene47-30-v1/params.bin').read_bytes(),308);bind(dll,'NvFlexSetParams',None,[C.c_void_p,C.c_void_p])(solver,params)
        for name,stride,data in [('Particles',16,b''.join(struct.pack('<4f',.2+(i%8)*.08,1,.2+(i//8)*.08,1) for i in range(64))),('Phases',4,struct.pack('<64I',*([0x7f500000]*64)))]:
            b=alloc(lib,64,stride,0);buffers.append(b);p=mapbuf(b,0);C.memmove(p,data,len(data));unmap(b);bind(dll,'NvFlexSet'+name,None,[C.c_void_p]*3)(solver,b,None)
        bind(dll,'NvFlexSetActiveCount',None,[C.c_void_p,C.c_int])(solver,64)
        bind(dll,'NvFlexUpdateSolver',None,[C.c_void_p,C.c_float,C.c_int,C.c_bool])(solver,1/60,2,True);bind(dll,'NvFlexWait',None,[C.c_void_p])(lib)
        values=(C.c_float*24)();timers(solver,values);assert all(math.isfinite(x) and x>=0 for x in values);assert math.isclose(sum(values[:23]),values[23],rel_tol=1e-5,abs_tol=1e-6)
        count=details(solver,C.byref(pointer));names=[pointer[i].name.decode() for i in range(count)];assert names[-1]=='Total'
        elapsed=latency(solver,C.byref(begin),C.byref(end),C.byref(freq));assert freq.value>33 and end.value>=begin.value and elapsed>=0
        # Raw D3D buffer copy is checked with the actual particle output.
        gpu=alloc(lib,64,16,1);buffers.append(gpu);bind(dll,'NvFlexGetParticles',None,[C.c_void_p]*3)(solver,gpu,None);host=C.create_string_buffer(64*16);bind(dll,'NvFlexCopyDeviceToHost',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_int])(solver,gpu,host,64,16)
        expected=alloc(lib,64,16,0);buffers.append(expected);bind(dll,'NvFlexGetParticles',None,[C.c_void_p]*3)(solver,expected,None);ptr=mapbuf(expected,0);assert bytes(host)==C.string_at(ptr,64*16);unmap(expected)
        bvh=C.create_string_buffer(bytes([0xbd])*128,128);bind(dll,'NvFlexGetShapeBVH',None,[C.c_void_p,C.c_void_p])(solver,bvh);assert bytes(bvh)==bytes([0xbd])*128
        data=C.create_string_buffer(bytes([0x5a])*64,64);status=C.c_uint(0x12345678);bind(dll,'NvFlexGetDataAftermath',None,[C.c_void_p]*3)(lib,data,C.byref(status))
        assert not messages,messages
        return {'names':names,'timers_zero_mask':[x==0 for x in values],'numeric_times':list(values),'latency_ms':elapsed,'aftermath_data':bytes(data).hex(),'aftermath_status':status.value}
    finally:
        for p in buffers:free(p)
        bind(dll,'NvFlexDestroySolver',None,[C.c_void_p])(solver);bind(dll,'NvFlexShutdown',None,[C.c_void_p])(lib)
def main():
    directory=os.add_dll_directory(str(WS/'FleX/bin/win64'));rows=[]
    for nv in [False,True]:
        a=run(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll',nv);b=run(Path(sys.argv[1]),nv);keys=['names','timers_zero_mask','aftermath_data','aftermath_status'];rows.append({'extensions':nv,'equal':all(a[k]==b[k] for k in keys),'reference':a,'candidate':b})
    write_json(Path(sys.argv[2]),rows);event('diagnostic-api-oracle','计时名称/非负计时/未启用语义/延迟/读回/Aftermath对照',passed=all(r['equal'] for r in rows),evidence=sys.argv[2]);print(json.dumps(rows,indent=2));directory.close();assert all(r['equal'] for r in rows)
if __name__=='__main__':main()
