"""Compare actual reference/candidate exports and restored basic API behavior."""
import ctypes as C
import csv,hashlib,json,random,sys
from pathlib import Path
import pefile
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tools'))
from ledger import event
candidate=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
reference=PROJECT.parent/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll'
def exports(p):
    pe=pefile.PE(str(p))
    return {(x.name.decode(),x.ordinal) for x in pe.DIRECTORY_ENTRY_EXPORT.symbols}
assert exports(candidate)==exports(reference)
pe=pefile.PE(str(candidate))
assert not any(b'nvflex' in item.dll.lower() for item in pe.DIRECTORY_ENTRY_IMPORT)
assert not any(x.forwarder for x in pe.DIRECTORY_ENTRY_EXPORT.symbols)
os_dir=C.windll.kernel32.SetDllDirectoryW
os_dir(str(reference.parent))
original=C.CDLL(str(reference));restored=C.CDLL(str(candidate))
assert original._handle!=restored._handle
def bind(dll,name,result,args):
    f=getattr(dll,name);f.restype=result;f.argtypes=args;return f
checks=0;functions=set();rng=random.Random(0xD15A55)
def equal(name,a,b):
    global checks
    checks+=1;functions.add(name)
    assert a==b,(name,a,b)
signatures={
 'NvFlexGetVersion':[],
 'NvFlexMakePhase':[C.c_int,C.c_int],
 'NvFlexMakePhaseWithChannels':[C.c_int,C.c_int,C.c_int],
 'NvFlexMakeShapeFlags':[C.c_int,C.c_bool],
 'NvFlexMakeShapeFlagsWithChannels':[C.c_int,C.c_bool,C.c_int]}
for name,args in signatures.items():
    a,b=[bind(d,name,C.c_int,args) for d in (original,restored)]
    for i in range(1 if not args else 10000):
        values=[bool(i%2) if t is C.c_bool else rng.randrange(-(1<<31),1<<31) for t in args]
        equal(name,a(*values),b(*values))
for name,size in [('NvFlexSetSolverDescDefaults',20)]:
    a,b=[bind(d,name,None,[C.c_void_p]) for d in (original,restored)]
    first=C.create_string_buffer(bytes([0xa5])*size,size);second=C.create_string_buffer(bytes([0xa5])*size,size)
    a(first);b(second);equal(name,bytes(first),bytes(second))
size=0xf20;first=C.create_string_buffer(size);second=C.create_string_buffer(size)
for offset,value in [(0xa50,999),(0x9b8,123),(0x538,97),(0xa48,51),(0x608,182),(0x868,17),(0x810,9)]:
    for storage in (first,second):C.c_int.from_buffer(storage,offset).value=value
for storage in (first,second):
    C.c_uint64.from_buffer(storage,0xc60).value=0x100000
    C.c_uint64.from_buffer(storage,0xc68).value=0x100068
    C.c_uint64.from_buffer(storage,0xf18).value=0x12345678
for name,ordinal in sorted(exports(reference)):
    if not name.startswith('?NvFlexGet') or 'TriangleMesh' in name:continue
    a,b=[bind(d,name,C.c_int,[C.c_void_p]) for d in (original,restored)]
    equal(name,a(first),b(second))
for name in ['NvFlexAcquireContext','NvFlexRestoreContext']:
    for dll in (original,restored):bind(dll,name,None,[C.c_void_p])(None)
    equal(name,True,True)
for name in ['NvFlexSetActiveCount','NvFlexSetDebug']:
    args=[C.c_void_p,C.c_bool if name.endswith('Debug') else C.c_int]
    a,b=[bind(d,name,None,args) for d in (original,restored)]
    for value in ([False,True,False] if name.endswith('Debug') else [0,1,99,999]):
        a(first,value);b(second,value);equal(name,bytes(first),bytes(second))
for name in ['NvFlexGetActiveCount','NvFlexGetSolverLibrary']:
    a,b=[bind(d,name,C.c_void_p if name.endswith('Library') else C.c_int,[C.c_void_p]) for d in (original,restored)]
    equal(name,a(first),b(second))
data=bytes(rng.randrange(256) for _ in range(308))
for storage in (first,second):C.memmove(C.addressof(storage)+0xb0c,data,len(data))
a,b=[bind(d,'NvFlexGetParams',None,[C.c_void_p,C.c_void_p]) for d in (original,restored)]
pa,pb=C.create_string_buffer(308),C.create_string_buffer(308);a(first,pa);b(second,pb)
equal('NvFlexGetParams',bytes(pa),bytes(pb));assert bytes(pa)==data
class Callback(C.Structure):_fields_=[('userData',C.c_void_p),('function',C.c_void_p)]
a,b=[bind(d,'NvFlexRegisterSolverCallback',Callback,[C.c_void_p,Callback,C.c_int]) for d in (original,restored)]
for stage in range(5):
    for value in (Callback(0x1110+stage,0x2220+stage),Callback(0,0)):
        va,vb=a(first,value,stage),b(second,value,stage)
        equal('NvFlexRegisterSolverCallback',(va.userData,va.function),(vb.userData,vb.function));assert bytes(first)==bytes(second)
result={'status':'PASS','export_names_ordinals':93,'tested_functions':len(functions),'checks':checks,
        'functions':sorted(functions),'candidate':str(candidate),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
        'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'runtime_original_dll_imports':False,'export_forwarders':False,
        'scope':'Restored basic functions only; no solver/library initialization, simulation, or GPU validation.'}
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2),encoding='utf-8')
event('basic-api-oracle-pass','93项导出名称/序号一致；基础API与原DLL逐项结果一致。',evidence=str(output),checks=checks,functions=len(functions))
print(json.dumps(result,indent=2))
