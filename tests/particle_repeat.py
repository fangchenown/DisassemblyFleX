import hashlib,json,os,sys
from pathlib import Path
from particle_step_oracle import run
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'tools'))
from ledger import write_json
WS=PROJECT.parent
case={'name':'fluid64','count':64,'spacing':.06,'phase':(1<<20)|(1<<22),'frames':10,'substeps':2}
if len(sys.argv)>2 and sys.argv[2].startswith('triangles'):
    case={'name':sys.argv[2],'count':64,'spacing':.08,'phase':0,'frames':10,'substeps':2,'springs':True,'triangles':True,'aero':True,'extensions':sys.argv[2].endswith('_nv')}
directory=os.add_dll_directory(str(WS/'FleX/bin/win64'))
reference=WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll'
first=run(reference,case);differences=[];repeats=int(sys.argv[3]) if len(sys.argv)>3 else 2
for repeat in range(1,repeats):
    second=run(reference,case)
    for a,b in zip(first,second):
        for name,data in a['data'].items():
            if data!=b['data'][name]:differences.append({'repeat':repeat+1,'frame':a['frame'],'channel':name})
result={'equal':not differences,'differences':differences,'repeats':repeats,'case':case,'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}
write_json(Path(sys.argv[1]),result);print(json.dumps(result,indent=2));directory.close()
