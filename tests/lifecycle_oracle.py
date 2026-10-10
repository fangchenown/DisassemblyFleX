import ctypes as C
import hashlib,json,os,struct,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'tools'))
from ledger import event,write_json
WS=PROJECT.parent
class Init(C.Structure):_fields_=[('device',C.c_int),('extensions',C.c_bool),('render',C.c_void_p),('renderContext',C.c_void_p),('computeContext',C.c_void_p),('onRender',C.c_bool),('computeType',C.c_int)]
class Desc(C.Structure):_fields_=[('mode',C.c_int),('particles',C.c_int),('diffuse',C.c_int),('neighbors',C.c_int),('contacts',C.c_int)]
class Copy(C.Structure):_fields_=[('src',C.c_int),('dst',C.c_int),('count',C.c_int)]
Callback=C.CFUNCTYPE(None,C.c_int,C.c_char_p,C.c_char_p,C.c_int)
def bind(dll,name,result,args):f=getattr(dll,name);f.restype=result;f.argtypes=args;return f
def run(path):
    dll=C.CDLL(str(path));messages=[];callback=Callback(lambda severity,text,file,line:messages.append([severity,text.decode(errors='replace'),file.decode(errors='replace'),line]))
    initialize=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)]);shutdown=bind(dll,'NvFlexShutdown',None,[C.c_void_p])
    create=bind(dll,'NvFlexCreateSolver',C.c_void_p,[C.c_void_p,C.POINTER(Desc)]);destroy=bind(dll,'NvFlexDestroySolver',None,[C.c_void_p])
    alloc=bind(dll,'NvFlexAllocBuffer',C.c_void_p,[C.c_void_p,C.c_int,C.c_int,C.c_int]);free=bind(dll,'NvFlexFreeBuffer',None,[C.c_void_p])
    mapbuf=bind(dll,'NvFlexMap',C.c_void_p,[C.c_void_p,C.c_int]);unmap=bind(dll,'NvFlexUnmap',None,[C.c_void_p])
    getdesc=bind(dll,'NvFlexGetSolverDesc',None,[C.c_void_p,C.POINTER(Desc)]);getparams=bind(dll,'NvFlexGetParams',None,[C.c_void_p,C.c_void_p])
    getsolvers=bind(dll,'NvFlexGetSolvers',C.c_int,[C.c_void_p,C.c_void_p,C.c_int]);setparams=bind(dll,'NvFlexSetParams',None,[C.c_void_p,C.c_void_p])
    desc=Init(-1,False,None,None,None,True,1);library=initialize(120,callback,C.byref(desc));assert library,messages
    results=[];active=[]
    def fill(buffer,data):
        pointer=mapbuf(buffer,0);assert pointer;C.memmove(pointer,data,len(data));unmap(buffer)
    def read(buffer,size):
        pointer=mapbuf(buffer,0);assert pointer;data=C.string_at(pointer,size);unmap(buffer);return data
    try:
        for n,mode,diffuse in [(64,0,0),(257,1,129),(65,2,0)]:
            sd=Desc(mode,n,diffuse,96,6);solver=create(library,C.byref(sd));assert solver;active.append(solver)
            output_desc=Desc();getdesc(solver,C.byref(output_desc));assert bytes(sd)==bytes(output_desc)
            params=C.create_string_buffer(308);getparams(solver,params)
            row={'n':n,'mode':mode,'diffuse':diffuse,'default_params':bytes(params).hex(),'channels':{}}
            assert getsolvers(library,None,0)==len(active)
            pointers=(C.c_void_p*8)();assert getsolvers(library,pointers,8)==len(active);assert list(pointers)[:len(active)]==active
            for channel,stride in [('Particles',16),('Velocities',12),('RestParticles',16),('Phases',4),('Normals',16),('Active',4)]:
                setter=bind(dll,'NvFlexSet'+channel,None,[C.c_void_p,C.c_void_p,C.POINTER(Copy)]);getter=bind(dll,'NvFlexGet'+channel,None,[C.c_void_p,C.c_void_p,C.POINTER(Copy)])
                src=alloc(library,n+4,stride,0);dst=alloc(library,n+4,stride,0)
                data=bytes((i*13+n+stride)%256 for i in range((n+4)*stride));sentinel=bytes([0xa5])*len(data)
                fill(src,data);fill(dst,sentinel);setter(solver,src,None);getter(solver,dst,None);full=read(dst,len(data));assert full[:n*stride]==data[:n*stride] and full[n*stride:]==sentinel[n*stride:]
                copy=Copy(2,5,7);setter(solver,src,C.byref(copy));expected=bytearray(data[:n*stride]);expected[5*stride:12*stride]=data[2*stride:9*stride]
                getter(solver,dst,None);after=read(dst,len(data));assert after[:n*stride]==expected
                fill(dst,sentinel);copy=Copy(5,1,7);getter(solver,dst,C.byref(copy));partial=read(dst,len(data));wanted=bytearray(sentinel);wanted[stride:8*stride]=expected[5*stride:12*stride];assert partial==wanted
                messages.clear();copy=Copy(0,n,2);setter(solver,src,C.byref(copy));copy=Copy(n,0,2);getter(solver,dst,C.byref(copy));errors=list(messages)
                row['channels'][channel]={'full':hashlib.sha256(full).hexdigest(),'partial':hashlib.sha256(partial).hexdigest(),'errors':errors}
                free(src);free(dst)
            # Use known actual Demo parameters; this also exercises the module RNG reset.
            blob=(WS/'Build/DisassemblyFleX-20261009/demo-runs/reference-scene47-30-v1/params.bin').read_bytes();p=C.create_string_buffer(blob,len(blob));setparams(solver,p);getparams(solver,params);assert bytes(params)==blob
            row['fluid_constants']=C.string_at(solver+0xe38,12).hex()
            results.append(row)
        destroy(active[1]);active.pop(1);pointers=(C.c_void_p*8)();assert getsolvers(library,pointers,8)==2;assert list(pointers)[:2]==active
    finally:
        for solver in active:destroy(solver)
        shutdown(library)
    return results
def main():
    candidate=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();directory=os.add_dll_directory(str(WS/'FleX/bin/win64'))
    original=run(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll');recovered=run(candidate)
    result={'status':'PASS' if original==recovered else 'FAIL','equal':original==recovered,'original':original,'candidate':recovered,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'scope':'3 live solvers, defaults/descriptors/list ordering, 6 set/get channels full/partial/range-error behavior, parameter copies and fluid constants. No UpdateSolver simulation yet.'}
    write_json(output,result);event('solver-lifecycle-oracle','求解器生命周期与粒子通道传输对照。',equal=result['equal'],evidence=str(output));print(result['status']);directory.close()
    assert result['equal']
if __name__=='__main__':main()
