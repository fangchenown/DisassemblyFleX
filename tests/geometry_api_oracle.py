"""Reference/candidate geometry lifetime, IDs, bounds and diagnostic contract."""
import ctypes as C
import json,os,struct,sys
from pathlib import Path
from lifecycle_oracle import Init,Callback,bind
PROJECT=Path(__file__).resolve().parents[1];WS=PROJECT.parent
sys.path.insert(0,str(PROJECT/'tools'))
from ledger import write_json,event
def run(path):
    dll=C.CDLL(str(path));errors=[];callback=Callback(lambda s,t,f,l:errors.append([s,t.decode(),f.decode(),l]))
    library=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)])(120,callback,C.byref(Init(-1,False,None,None,None,True,1)))
    alloc=bind(dll,'NvFlexAllocBuffer',C.c_void_p,[C.c_void_p,C.c_int,C.c_int,C.c_int]);free=bind(dll,'NvFlexFreeBuffer',None,[C.c_void_p]);mapbuf=bind(dll,'NvFlexMap',C.c_void_p,[C.c_void_p,C.c_int]);unmap=bind(dll,'NvFlexUnmap',None,[C.c_void_p])
    result={};buffers=[]
    def buf(data,stride):
        p=alloc(library,len(data)//stride,stride,0);buffers.append(p);q=mapbuf(p,0);C.memmove(q,data,len(data));unmap(p);return p
    try:
        for kind,plural,capacity in [('TriangleMesh','TriangleMeshes',0),('ConvexMesh','ConvexMeshes',4096),('DistanceField','DistanceFields',16)]:
            create=bind(dll,'NvFlexCreate'+kind,C.c_uint,[C.c_void_p]);destroy=bind(dll,'NvFlexDestroy'+kind,None,[C.c_void_p,C.c_uint]);get=bind(dll,'NvFlexGet'+plural,C.c_int,[C.c_void_p,C.c_void_p,C.c_int])
            ids=[create(library) for _ in range(5)];snapshots=[]
            def snap():
                a=(C.c_uint*12)(*([0xfadebeef]*12));n=get(library,a,12);b=(C.c_uint*2)(0xfadebeef,0xfadebeef);m=get(library,b,2);return [n,list(a),m,list(b),get(library,None,0)]
            snapshots.append(snap());destroy(library,ids[1]);destroy(library,ids[3]);snapshots.append(snap());ids=[ids[0],ids[2],ids[4],create(library),create(library)];snapshots.append(snap())
            for id in ids:destroy(library,id)
            snapshots.append(snap());destroy(library,0)
            if capacity:
                # Overflow is isolated in a separate process: the original
                # tracks ID 0 and loops forever during Shutdown cleanup.
                full=[create(library) for _ in range(capacity)];snapshots.append([full[:8],full[-3:],get(library,None,0)])
                for id in full:
                    if id:destroy(library,id)
                snapshots.append(get(library,None,0))
            result[kind]=snapshots
        for kind in ['ConvexMesh','TriangleMesh']:
            id=bind(dll,'NvFlexCreate'+kind,C.c_uint,[C.c_void_p])(library);lower=(C.c_float*3)(-1,-2,-3);upper=(C.c_float*3)(4,5,6)
            bounds=bind(dll,'NvFlexGet'+kind+'Bounds',None,[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]);outlo=(C.c_float*3)();outhi=(C.c_float*3)()
            if kind=='ConvexMesh':
                update=bind(dll,'NvFlexUpdateConvexMesh',None,[C.c_void_p,C.c_uint,C.c_void_p,C.c_int,C.c_void_p,C.c_void_p]);p=buf(struct.pack('<4f',1,0,0,-1)*6,16);update(library,id,p,6,lower,upper);bounds(library,id,outlo,outhi);result['convexBounds']=[list(outlo),list(outhi)];update(library,id,p,65,lower,upper);update(library,0,p,6,lower,upper)
            else:
                update=bind(dll,'NvFlexUpdateTriangleMesh',None,[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_int,C.c_int,C.c_void_p,C.c_void_p]);p=buf(struct.pack('<12f',0,0,0,0,1,0,0,0,0,1,0,0),16);q=buf(struct.pack('<3i',0,1,2),4)
                update(library,id,p,q,3,1,lower,upper);bounds(library,id,outlo,outhi);result['triangleBounds']=[list(outlo),list(outhi)];update(library,id,p,q,3,0,lower,upper);bounds(library,id,outlo,outhi);result['triangleZeroBounds']=[list(outlo),list(outhi)];update(library,id,p,q,3,1,None,upper);update(library,0,p,q,3,1,lower,upper)
            bounds(library,0,outlo,outhi);bind(dll,'NvFlexDestroy'+kind,None,[C.c_void_p,C.c_uint])(library,id)
        bind(dll,'NvFlexUpdateDistanceField',None,[C.c_void_p,C.c_uint,C.c_int,C.c_int,C.c_int,C.c_void_p])(library,0,2,2,2,None)
        result['errors']=errors;return result
    finally:
        for p in buffers:free(p)
        bind(dll,'NvFlexShutdown',None,[C.c_void_p])(library)
def main():
    directory=os.add_dll_directory(str(WS/'FleX/bin/win64'));a=run(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll');b=run(Path(sys.argv[1]));report={'equal':a==b,'reference':a,'candidate':b};write_json(Path(sys.argv[2]),report);event('geometry-api-oracle','几何资源ID顺序/复用/容量/空间界/错误诊断对照',equal=a==b,evidence=sys.argv[2]);print(json.dumps(report,ensure_ascii=False));directory.close();assert a==b
if __name__=='__main__':main()
