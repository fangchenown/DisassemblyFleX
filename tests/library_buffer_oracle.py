import ctypes as C
import hashlib,json,msvcrt,os,sys,time
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tools'))
from ledger import event,write_json
from locksafe_power import SystemRequired
WS=PROJECT.parent
class Desc(C.Structure):
    _fields_=[('deviceIndex',C.c_int),('enableExtensions',C.c_bool),('renderDevice',C.c_void_p),('renderContext',C.c_void_p),('computeContext',C.c_void_p),('runOnRenderContext',C.c_bool),('computeType',C.c_int)]
class BufferDesc(C.Structure):
    _fields_=[('ByteWidth',C.c_uint),('Usage',C.c_uint),('BindFlags',C.c_uint),('CPUAccessFlags',C.c_uint),('MiscFlags',C.c_uint),('StructureByteStride',C.c_uint)]
Callback=C.CFUNCTYPE(None,C.c_int,C.c_char_p,C.c_char_p,C.c_int)
def bind(dll,name,restype,args):f=getattr(dll,name);f.restype=restype;f.argtypes=args;return f
def test(path):
    directory=os.add_dll_directory(str(WS/'FleX/bin/win64'))
    dll=C.CDLL(str(path));messages=[]
    callback=Callback(lambda severity,message,file,line:messages.append({'severity':severity,'message':message.decode(errors='replace'),'file':file.decode(errors='replace'),'line':line}))
    init=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Desc)])
    shutdown=bind(dll,'NvFlexShutdown',None,[C.c_void_p]);alloc=bind(dll,'NvFlexAllocBuffer',C.c_void_p,[C.c_void_p,C.c_int,C.c_int,C.c_int])
    free=bind(dll,'NvFlexFreeBuffer',None,[C.c_void_p]);mapbuf=bind(dll,'NvFlexMap',C.c_void_p,[C.c_void_p,C.c_int]);unmap=bind(dll,'NvFlexUnmap',None,[C.c_void_p])
    getname=bind(dll,'NvFlexGetDeviceName',C.c_char_p,[C.c_void_p]);flush=bind(dll,'NvFlexFlush',None,[C.c_void_p]);wait=bind(dll,'NvFlexWait',None,[C.c_void_p])
    desc=Desc(-1,False,None,None,None,True,1)
    invalid=[]
    for version,compute in [(119,1),(121,1),(120,0)]:
        desc.computeType=compute;messages.clear();p=init(version,callback,C.byref(desc));assert not p
        invalid.append({'version':version,'compute':compute,'messages':list(messages)})
    desc.computeType=1;desc.deviceIndex=9999;messages.clear();p=init(120,callback,C.byref(desc));assert not p;invalid.append({'device_index':9999,'messages':list(messages)});desc.deviceIndex=-1
    desc.computeType=1;messages.clear();library=init(120,callback,C.byref(desc));assert library,messages
    rows=[]
    try:
        device=getname(library).decode()
        for count in [1,7,513]:
            for stride in [4,12,16,48]:
                p=alloc(library,count,stride,0);assert p
                pointer=mapbuf(p,0)
                if count:
                    assert pointer
                    data=bytes((i*17+count*3+stride)%256 for i in range(count*stride))
                    C.memmove(pointer,data,len(data));unmap(p);pointer=mapbuf(p,0);assert pointer
                    result=C.string_at(pointer,len(data));assert result==data
                    rows.append({'count':count,'stride':stride,'sha256':hashlib.sha256(result).hexdigest()})
                else:rows.append({'count':count,'stride':stride,'mapped':bool(pointer)})
                unmap(p);free(p)
        native=[]
        for stride in [4,12,16,48]:
            p=alloc(library,7,stride,1);assert p;native_buffer=mapbuf(p,0);assert native_buffer
            table=C.cast(native_buffer,C.POINTER(C.POINTER(C.c_void_p))).contents
            getdesc=C.WINFUNCTYPE(None,C.c_void_p,C.POINTER(BufferDesc))(table[10]);bd=BufferDesc();getdesc(native_buffer,C.byref(bd))
            native.append({name:getattr(bd,name) for name,_ in bd._fields_});unmap(p);free(p)
        assert mapbuf(None,0) is None;unmap(None);free(None);flush(library);wait(library)
        return {'device':device,'invalid_init':invalid,'host':rows,'native':native,'messages':messages}
    finally:shutdown(library);directory.close()
def main():
    candidate=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    with SystemRequired(),(WS/'Build/OpenFlexAlpha82c-20260928/gpu.lock').open('a+b') as lock:
        while True:
            try:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:time.sleep(.5)
        try:
            original=test(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll');recovered=test(candidate)
        finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    result={'original':original,'candidate':recovered,'equal':original==recovered,'candidate_path':str(candidate),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest()}
    write_json(out,result)
    event('library-buffer-oracle','D3D11通用初始化/设备名称/宿主缓冲区/设备映射描述对照。',equal=result['equal'],evidence=str(out))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    assert result['equal'],'Behavior difference; inspect saved result'
if __name__=='__main__':main()
