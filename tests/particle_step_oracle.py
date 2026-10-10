import ctypes as C
import hashlib,json,math,os,struct,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'tools'))
from ledger import write_json,event
from lifecycle_oracle import Init,Desc,Copy,Callback,bind
WS=PROJECT.parent
def run(path,case):
    dll=C.CDLL(str(path));messages=[];callback=Callback(lambda severity,text,file,line:messages.append([severity,text.decode(errors='replace'),file.decode(errors='replace'),line]))
    initialize=bind(dll,'NvFlexInit',C.c_void_p,[C.c_int,Callback,C.POINTER(Init)]);shutdown=bind(dll,'NvFlexShutdown',None,[C.c_void_p])
    create=bind(dll,'NvFlexCreateSolver',C.c_void_p,[C.c_void_p,C.POINTER(Desc)]);destroy=bind(dll,'NvFlexDestroySolver',None,[C.c_void_p])
    alloc=bind(dll,'NvFlexAllocBuffer',C.c_void_p,[C.c_void_p,C.c_int,C.c_int,C.c_int]);free=bind(dll,'NvFlexFreeBuffer',None,[C.c_void_p])
    mapbuf=bind(dll,'NvFlexMap',C.c_void_p,[C.c_void_p,C.c_int]);unmap=bind(dll,'NvFlexUnmap',None,[C.c_void_p]);update=bind(dll,'NvFlexUpdateSolver',None,[C.c_void_p,C.c_float,C.c_int,C.c_bool])
    external_device,external_context=C.c_void_p(),C.c_void_p()
    if case.get('external'):
        native=C.WinDLL('d3d11.dll');make=native.D3D11CreateDevice;make.restype=C.c_long;make.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.c_void_p,C.POINTER(C.c_void_p)]
        assert make(None,1,None,0,None,0,7,C.byref(external_device),None,C.byref(external_context))>=0
    idesc=Init(-1,case.get('extensions',False),external_device,external_context,None,case.get('external')!='async',case.get('compute',1));library=initialize(120,callback,C.byref(idesc));assert library,messages
    n=case['count'];capacity=max(64,n);sd=Desc(case.get('feature',0),capacity,case.get('diffuse',0),96,6);solver=create(library,C.byref(sd));assert solver
    buffers={};pointers=[]
    def buffer(name,stride):
        p=alloc(library,n,stride,0);pointers.append(p);buffers[name]=(p,stride);return p
    def fill(p,data):
        ptr=mapbuf(p,0);assert ptr;C.memmove(ptr,data,len(data));unmap(p)
    def read(p,size):
        ptr=mapbuf(p,0);assert ptr;data=C.string_at(ptr,size);unmap(p);return data
    try:
        params=bytearray((WS/'Build/DisassemblyFleX-20261009/demo-runs/reference-scene47-30-v1/params.bin').read_bytes())
        struct.pack_into('<i',params,296,1 if case.get('plane') else 0)
        if case.get('plane'):struct.pack_into('<4f',params,168,0,1,0,0)
        if case.get('aero'):
            struct.pack_into('<3f',params,72,1.0,.5,.2);struct.pack_into('<f',params,84,.02);struct.pack_into('<f',params,88,.05)
        param_buffer=C.create_string_buffer(bytes(params),308);bind(dll,'NvFlexSetParams',None,[C.c_void_p,C.c_void_p])(solver,param_buffer)
        positions=b''.join(struct.pack('<4f',.3+(i%16)*case['spacing'],case.get('height',1.0)+(i//256)*case['spacing'],.3+((i//16)%16)*case['spacing'],0.0 if i%17==16 else 1.0) for i in range(n))
        if case.get('tetra'):positions=b''.join(struct.pack('<4f',*p,1) for p in [(.4,1,.4),(.6,1,.4),(.4,1.2,.4),(.4,1,.6)])
        if case.get('rigid'):
            side=1
            while side**3<n:side+=1
            positions=b''.join(struct.pack('<4f',.3+(i%side)*case['spacing'],1+((i//side)%side)*case['spacing'],.3+(i//(side*side))*case['spacing'],1) for i in range(n))
        velocities=b''.join(struct.pack('<3f',0.02*(i%3),0,-0.01*(i%5)) for i in range(n));phases=struct.pack('<'+'i'*n,*([case['phase']]*n))
        for name,stride,data in [('Particles',16,positions),('Velocities',12,velocities),('Phases',4,phases)]:
            p=buffer(name,stride);fill(p,data);bind(dll,'NvFlexSet'+name,None,[C.c_void_p,C.c_void_p,C.c_void_p])(solver,p,None)
        bind(dll,'NvFlexSetActiveCount',None,[C.c_void_p,C.c_int])(solver,n)
        diffuse_outputs=None
        if case.get('diffuse'):
            maximum=case['diffuse'];p=alloc(library,maximum,16,0);v=alloc(library,maximum,16,0);c=alloc(library,1,4,0);pointers.extend([p,v,c]);diffuse_outputs=(p,v,c,maximum)
            seed=min(maximum,case.get('diffuse_seed',0));data=b''.join(struct.pack('<4f',.3+(i%16)*.04,.95,.3+(i//16)*.04,.025 if i%3==0 else 1.5) for i in range(seed));speeds=b''.join(struct.pack('<4f',.05*(i%4),-.1,0,0) for i in range(seed))
            fill(p,data+bytes((maximum-seed)*16));fill(v,speeds+bytes((maximum-seed)*16));fill(c,bytes(4));bind(dll,'NvFlexSetDiffuseParticles',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int])(solver,p,v,seed)
        shape_uploads=[];mesh_id=None
        if case.get('shape') in (3,4,5):
            kind=case['shape'];api={3:'ConvexMesh',4:'TriangleMesh',5:'DistanceField'}[kind]
            mesh_id=bind(dll,'NvFlexCreate'+api,C.c_uint,[C.c_void_p])(library)
            lower=(C.c_float*3)(-.5,-.1,-.5);upper=(C.c_float*3)(.5,.1,.5)
            if kind==3:
                planes=b''.join(struct.pack('<4f',*p) for p in [(1,0,0,-.5),(-1,0,0,-.5),(0,1,0,-.1),(0,-1,0,-.1),(0,0,1,-.5),(0,0,-1,-.5)])
                p=alloc(library,6,16,0);pointers.append(p);fill(p,planes)
                bind(dll,'NvFlexUpdateConvexMesh',None,[C.c_void_p,C.c_uint,C.c_void_p,C.c_int,C.c_void_p,C.c_void_p])(library,mesh_id,p,6,lower,upper)
            elif kind==4:
                side=case.get('mesh_side',2);vertices=b''.join(struct.pack('<4f',x/(side-1)-.5,.03*math.sin(x+z),z/(side-1)-.5,0) for z in range(side) for x in range(side));indices=[]
                for z in range(side-1):
                    for x in range(side-1):
                        a=z*side+x;indices.extend([a,a+side,a+1,a+1,a+side,a+side+1])
                p=alloc(library,side*side,16,0);q=alloc(library,len(indices),4,0);pointers.extend([p,q]);fill(p,vertices);fill(q,struct.pack('<'+'I'*len(indices),*indices))
                bind(dll,'NvFlexUpdateTriangleMesh',None,[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_int,C.c_int,C.c_void_p,C.c_void_p])(library,mesh_id,p,q,side*side,len(indices)//3,lower,upper)
            else:
                side=24;field=b''.join(struct.pack('<f',math.sqrt((x/(side-1)-.5)**2+(y/(side-1)-.5)**2+(z/(side-1)-.5)**2)-.35) for z in range(side) for y in range(side) for x in range(side))
                p=alloc(library,side**3,4,0);pointers.append(p);fill(p,field)
                bind(dll,'NvFlexUpdateDistanceField',None,[C.c_void_p,C.c_uint,C.c_int,C.c_int,C.c_int,C.c_void_p])(library,mesh_id,side,side,side,p)
        def set_shapes(frame):
            kind=case.get('shape',0);count=case.get('shape_count',1)
            if kind<3:geometry=struct.pack('<4f',*[(.3,0,0,0),(.2,.3,0,0),(.3,.18,.3,0)][kind])
            elif kind<5:geometry=struct.pack('<3fI',1,1,1,mesh_id)
            else:geometry=struct.pack('<fI2f',1,mesh_id,0,0)
            shape_positions=b''.join(struct.pack('<4f',.65+frame*.003+i*2,.8,.4,0) for i in range(count))
            previous=b''.join(struct.pack('<4f',.65+(frame-1)*.003+i*2,.8,.4,0) for i in range(count))
            blobs=[geometry*count,shape_positions,struct.pack('<4f',0,0,.38268343,.92387953)*count,previous,struct.pack('<4f',0,0,.38268343,.92387953)*count,struct.pack('<i',kind|0x7f000000|8)*count]
            if kind==5:
                blobs[1]=struct.pack('<4f',.15+frame*.003,.35,-.15,0)*count;blobs[3]=struct.pack('<4f',.15+(frame-1)*.003,.35,-.15,0)*count
                blobs[2]=blobs[4]=struct.pack('<4f',0,0,0,1)*count
            if not shape_uploads:
                for i,blob in enumerate(blobs):
                    p=alloc(library,count,4 if i==5 else 16,0);pointers.append(p);shape_uploads.append(p)
            for p,blob in zip(shape_uploads,blobs):fill(p,blob)
            bind(dll,'NvFlexSetShapes',None,[C.c_void_p]*7+[C.c_int])(solver,*shape_uploads,count)
        spring_buffers=[]
        def set_springs(multiplier=1):
            setter=bind(dll,'NvFlexSetSprings',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_int])
            if not multiplier:setter(solver,None,None,None,0);return
            edges=[(i,i+1) for i in range(n-1)]*multiplier;count=len(edges)
            values=[struct.pack('<'+'i'*(count*2),*(x for pair in edges for x in pair)),
                    struct.pack('<'+'f'*count,*([case['spacing']*.8]*count)),
                    struct.pack('<'+'f'*count,*[(-.7 if i%11==0 else .8) for i in range(count)])]
            handles=[]
            for payload,elements in zip(values,[count*2,count,count]):
                handle=alloc(library,elements,4,0);pointers.append(handle);spring_buffers.append(handle);fill(handle,payload);handles.append(handle)
            setter(solver,*handles,count)
            # GetSprings in this reference D3D binary is a no-op; preserve the
            # observed contract instead of inventing a readback implementation.
            before=[read(handle,len(payload)) for handle,payload in zip(handles,values)]
            bind(dll,'NvFlexGetSprings',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_int])(solver,*handles,count)
            assert before==[read(handle,len(payload)) for handle,payload in zip(handles,values)]
        if case.get('springs'):set_springs()
        rigid_outputs=None
        if case.get('rigid'):
            coords=[struct.unpack_from('<4f',positions,i*16)[:3] for i in range(n)];center=[sum(p[j] for p in coords)/n for j in range(3)]
            rest=b''.join(struct.pack('<3f',*[p[j]-center[j] for j in range(3)]) for p in coords)
            blobs=[struct.pack('<2i',0,n),struct.pack('<'+'i'*n,*range(n)),rest,bytes(n*16),struct.pack('<f',.8),struct.pack('<f',.001),struct.pack('<f',.2),struct.pack('<4f',0,0,0,1),struct.pack('<3f',*center)]
            counts=[2,n,n,n,1,1,1,1,1];strides=[4,4,12,16,4,4,4,16,12];handles=[]
            for blob,count,stride in zip(blobs,counts,strides):
                p=alloc(library,count,stride,0);pointers.append(p);fill(p,blob);handles.append(p)
            upload_handles=list(handles);upload_handles[3]=None
            if not case.get('plastic'):upload_handles[5]=None;upload_handles[6]=None
            bind(dll,'NvFlexSetRigids',None,[C.c_void_p]*10+[C.c_int,C.c_int])(solver,*upload_handles,1,n)
            rigid_outputs=(handles,counts,strides)
        triangle_outputs=None
        if case.get('triangles') or case.get('tetra'):
            if case.get('tetra'):triangles=[0,2,1,0,1,3,0,3,2,1,2,3]
            else:
                triangles=[]
                for z in range(n//16-1):
                    for x in range(15):
                        a=z*16+x;triangles.extend([a,a+16,a+1,a+1,a+16,a+17])
            tri_count=len(triangles)//3;tri=alloc(library,len(triangles),4,0);normal=alloc(library,tri_count,12,0);pointers.extend([tri,normal])
            fill(tri,struct.pack('<'+'i'*len(triangles),*triangles));fill(normal,bytes(tri_count*12))
            bind(dll,'NvFlexSetDynamicTriangles',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int])(solver,tri,normal,tri_count);triangle_outputs=(tri,normal,tri_count)
            if case.get('tetra'):
                fields=[struct.pack('<i',0),struct.pack('<i',4),struct.pack('<f',.2**3/6),struct.pack('<f',1.2),struct.pack('<f',.25)];handles=[]
                for payload in fields:
                    p=alloc(library,1,4,0);pointers.append(p);fill(p,payload);handles.append(p)
                bind(dll,'NvFlexSetInflatables',None,[C.c_void_p]+[C.c_void_p]*5+[C.c_int])(solver,*handles,1)
        for name,stride in [('Normals',16),('Densities',4),('SmoothParticles',16),('Anisotropy1',16),('Anisotropy2',16),('Anisotropy3',16)]:buffer(name,stride)
        extra_outputs={}
        if case.get('extra_outputs'):
            for name,count,stride in [('BoundsLower',1,12),('BoundsUpper',1,12),('ContactPlanes',capacity*6,16),('ContactVelocities',capacity*6,16),('ContactIndices',capacity,4),('ContactCounts',capacity,4),('Neighbors',capacity*96,4),('NeighborCounts',capacity,4),('ApiToInternal',capacity,4),('InternalToApi',capacity,4)]:
                p=alloc(library,count+1,stride,0);pointers.append(p);fill(p,bytes([0xa5])*((count+1)*stride));extra_outputs[name]=(p,count,stride)
        snapshots=[]
        for frame in range(case['frames']):
            if 'shape' in case:set_shapes(frame)
            if case.get('topology_changes') and frame in (2,4):set_springs(0 if frame==2 else 2)
            update(solver,1.0/60.0,case['substeps'],False)
            if frame in (0,case['frames']-1):
                result={'frame':frame+1,'data':{}}
                for name in ['Particles','Velocities','Normals','Densities','SmoothParticles']:
                    p,stride=buffers[name];bind(dll,'NvFlexGet'+name,None,[C.c_void_p,C.c_void_p,C.c_void_p])(solver,p,None)
                bind(dll,'NvFlexGetAnisotropy',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p])(solver,buffers['Anisotropy1'][0],buffers['Anisotropy2'][0],buffers['Anisotropy3'][0],None)
                for name,(p,stride) in buffers.items():
                    if name=='Phases':continue
                    result['data'][name]=read(p,n*stride)
                if triangle_outputs:
                    tri,normal,count=triangle_outputs;bind(dll,'NvFlexGetDynamicTriangles',None,[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int])(solver,tri,normal,count)
                    result['data']['Triangles']=read(tri,count*12);result['data']['TriangleNormals']=read(normal,count*12)
                    if case.get('diagnostic_normals'):
                        device,context=C.c_void_p(),C.c_void_p();bind(dll,'NvFlexGetDeviceAndContext',None,[C.c_void_p,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)])(library,C.byref(device),C.byref(context))
                        source=C.c_void_p.from_address(solver+0x398).value
                        destination=alloc(library,capacity,16,0);pointers.append(destination);native_dst=C.c_void_p.from_address(destination+8).value
                        table=C.cast(context,C.POINTER(C.POINTER(C.c_void_p))).contents
                        copy_to_host=C.WINFUNCTYPE(None,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint)(table[20])
                        copy_to_host(context,native_dst,0,source,0,capacity*16);result['data']['NormalsTempDiagnostic']=read(destination,capacity*16)
                if rigid_outputs:
                    handles,counts,strides=rigid_outputs;bind(dll,'NvFlexGetRigids',None,[C.c_void_p]*10)(solver,*handles)
                    for name,p,count,stride in zip(['RigidOffsets','RigidIndices','RigidRest','RigidLocalNormals','RigidStiffness','RigidThresholds','RigidCreeps','RigidRotations','RigidTranslations'],handles,counts,strides):result['data'][name]=read(p,count*stride)
                if diffuse_outputs:
                    p,v,c,maximum=diffuse_outputs;bind(dll,'NvFlexGetDiffuseParticles',None,[C.c_void_p]*4)(solver,p,v,c)
                    result['data']['DiffuseCount']=read(c,4);result['data']['DiffusePositions']=read(p,maximum*16);result['data']['DiffuseVelocities']=read(v,maximum*16)
                if extra_outputs:
                    handles=lambda names:[extra_outputs[name][0] for name in names.split(',')]
                    bind(dll,'NvFlexGetBounds',None,[C.c_void_p]*3)(solver,*handles('BoundsLower,BoundsUpper'))
                    bind(dll,'NvFlexGetContacts',None,[C.c_void_p]*5)(solver,*handles('ContactPlanes,ContactVelocities,ContactIndices,ContactCounts'))
                    bind(dll,'NvFlexGetNeighbors',None,[C.c_void_p]*5)(solver,*handles('Neighbors,NeighborCounts,ApiToInternal,InternalToApi'))
                    for name,(p,count,stride) in extra_outputs.items():
                        data=read(p,(count+1)*stride);assert data[-stride:]==bytes([0xa5])*stride,(name,'output overwritten past contract');result['data'][name]=data
                snapshots.append(result)
        assert not messages,messages
        return snapshots
    finally:
        for p in pointers:free(p)
        destroy(solver);shutdown(library)
        for pointer in [external_context,external_device]:
            if pointer:
                table=C.cast(pointer,C.POINTER(C.POINTER(C.c_void_p))).contents;C.WINFUNCTYPE(C.c_ulong,C.c_void_p)(table[2])(pointer)
def main():
    candidate=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False);directory=os.add_dll_directory(str(WS/'FleX/bin/win64'))
    cases=[{'name':'separated4','count':4,'spacing':.2,'phase':0,'frames':4,'substeps':2},
           {'name':'solid64','count':64,'spacing':.04,'phase':1<<20,'frames':10,'substeps':2},
           {'name':'fluid64','count':64,'spacing':.06,'phase':(1<<20)|(1<<22),'frames':10,'substeps':2},
           {'name':'plane16','count':16,'spacing':.08,'phase':1<<20,'height':.04,'plane':True,'frames':10,'substeps':3},
           {'name':'large1025','count':1025,'spacing':.2,'phase':0,'frames':2,'substeps':1},
           {'name':'fluid64_nv','count':64,'spacing':.06,'phase':(1<<20)|(1<<22),'frames':10,'substeps':2,'extensions':True},
           {'name':'solid64_nv','count':64,'spacing':.04,'phase':1<<20,'frames':10,'substeps':2,'extensions':True}]
    cases.extend([{'name':'springs32','count':32,'spacing':.08,'phase':0,'frames':10,'substeps':2,'springs':True,'topology_changes':True},
                  {'name':'springs80_nv','count':80,'spacing':.06,'phase':1<<20,'frames':10,'substeps':3,'springs':True,'extensions':True},
                  {'name':'springs1025','count':1025,'spacing':.1,'phase':0,'frames':3,'substeps':2,'springs':True}])
    cases.extend([{'name':'triangles64','count':64,'spacing':.08,'phase':0,'frames':10,'substeps':2,'springs':True,'triangles':True,'aero':True},
                  {'name':'triangles64_nv','count':64,'spacing':.08,'phase':0,'frames':10,'substeps':2,'springs':True,'triangles':True,'aero':True,'extensions':True},
                  {'name':'inflatable4','count':4,'spacing':.2,'phase':0,'frames':10,'substeps':2,'tetra':True},
                  {'name':'inflatable4_nv','count':4,'spacing':.2,'phase':0,'frames':10,'substeps':2,'tetra':True,'extensions':True}])
    cases.extend([{'name':'rigid8','count':8,'spacing':.08,'phase':0,'frames':10,'substeps':2,'rigid':True},
                  {'name':'rigid8_nv','count':8,'spacing':.08,'phase':0,'frames':10,'substeps':2,'rigid':True,'extensions':True},
                  {'name':'rigid64_nv','count':64,'spacing':.08,'phase':0,'frames':10,'substeps':2,'rigid':True,'extensions':True},
                  {'name':'rigid160_nv','count':160,'spacing':.08,'phase':0,'frames':5,'substeps':2,'rigid':True,'extensions':True},
                  {'name':'plastic64','count':64,'spacing':.08,'phase':0,'frames':10,'substeps':2,'rigid':True,'plastic':True},
                  {'name':'plastic64_nv','count':64,'spacing':.08,'phase':0,'frames':10,'substeps':2,'rigid':True,'plastic':True,'extensions':True}])
    cases.extend([dict(name=name,count=64,spacing=.04,phase=0x7f100000,frames=10,substeps=3,shape=kind,extensions=nv,shape_count=count)
                  for name,kind,nv,count in [('sphere64',0,False,1),('capsule64',1,False,1),('box64_nv',2,True,1),('spheres1300_nv',0,True,1300)]])
    cases.extend([dict(name=name,count=64,spacing=.04,phase=0x7f100000,frames=10,substeps=3,shape=kind,extensions=nv,mesh_side=side)
                  for name,kind,nv,side in [('convex64',3,False,2),('mesh64',4,False,2),('mesh1800_nv',4,True,31),('sdf64',5,False,2),('sdf64_nv',5,True,2)]])
    cases.extend([dict(name=name,count=64,spacing=.06,phase=0x7f500000,frames=10,substeps=3,diffuse=maximum,diffuse_seed=seed,extensions=nv)
                  for name,maximum,seed,nv in [('diffuse64',64,24,False),('diffuse64_nv',64,24,True),('diffuse1025_nv',1025,600,True)]])
    cases.extend([dict(name='external_'+mode,count=64,spacing=.06,phase=0x7f500000,frames=10,substeps=3,external=mode,extensions=True) for mode in ['render','async']])
    cases.extend([dict(name=name,count=64,spacing=.06,phase=0x7f500000,frames=10,substeps=3,compute=2,extensions=nv) for name,nv in [('d3d12_fluid64',False),('d3d12_fluid64_nv',True)]])
    cases.extend([dict(name='outputs_'+str(compute),count=64,spacing=.04,phase=0x7f100000,frames=4,substeps=3,compute=compute,shape=2,extra_outputs=True,extensions=True) for compute in [1,2]])
    if len(sys.argv)>3:cases=[case for case in cases if case['name'] in sys.argv[3].split(',')]
    if len(sys.argv)>4 and sys.argv[4]=='diagnostic-normals':
        for case in cases:case['diagnostic_normals']=True
    results=[]
    for case in cases:
        print('case',case['name'],flush=True);a=run(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll',case);b=run(candidate,case);diffs=[]
        if 'shape' in case:
            baseline=dict(case);baseline.pop('shape');without_shape=run(WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll',baseline)
            assert any(x['data']['Particles']!=y['data']['Particles'] for x,y in zip(a,without_shape)), 'fixture did not exercise shape collision'
        for x,y in zip(a,b):
            for name,original in x['data'].items():
                reconstructed=y['data'][name];stem=case['name']+'-'+str(x['frame'])+'-'+name
                (out/(stem+'-reference.bin')).write_bytes(original);(out/(stem+'-candidate.bin')).write_bytes(reconstructed)
                if original!=reconstructed:
                    aw=struct.unpack('<'+'I'*(len(original)//4),original);bw=struct.unpack('<'+'I'*(len(reconstructed)//4),reconstructed);bad=[i for i,(u,v) in enumerate(zip(aw,bw)) if u!=v]
                    diffs.append({'frame':x['frame'],'channel':name,'mismatch_words':len(bad),'first':bad[:10]})
        results.append({'case':case,'equal':not diffs,'differences':diffs});write_json(out/'results.json',results)
        print('equal',not diffs,json.dumps(diffs[:4]),flush=True)
    event('particle-step-oracle','粒子/密度/速度/法线/平滑/各向异性多帧对照。',passed=sum(r['equal'] for r in results),total=len(results),evidence=str(out/'results.json'))
    directory.close()
    if not all(r['equal'] for r in results):raise SystemExit(1)
if __name__=='__main__':main()
