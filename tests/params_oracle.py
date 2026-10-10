import ctypes as C
import hashlib,json,os,struct,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'tools'))
from ledger import write_json,event
WS=PROJECT.parent
def main():
    reference=WS/'FleX/bin/win64/NvFlexReleaseD3D_x64.dll';candidate=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
    directory=os.add_dll_directory(str(reference.parent));libraries=[C.CDLL(str(p)) for p in (reference,candidate)]
    funcs=[]
    for dll in libraries:
        f=dll.NvFlexSetParams;f.restype=None;f.argtypes=[C.c_void_p,C.c_void_p];funcs.append(f)
    records=[]
    for radius in [0.01,0.025,0.05,0.1,0.5,1.0]:
        for ratio in [0.1,0.25,0.5,0.55,0.65,0.75,1.0]:
            params=bytearray(308);struct.pack_into('<i',params,0,3);struct.pack_into('<f',params,16,radius);struct.pack_into('<f',params,20,radius*ratio);struct.pack_into('<f',params,24,radius*ratio)
            p=C.create_string_buffer(bytes(params),308);outputs=[]
            for f in funcs:
                solver=C.create_string_buffer(3872);f(solver,p)
                assert C.string_at(C.addressof(solver)+0xb0c,308)==bytes(params)
                values=C.string_at(C.addressof(solver)+0xe38,12);f(solver,p);assert C.string_at(C.addressof(solver)+0xe38,12)==values
                outputs.append(values)
            a,b=outputs;records.append({'radius':radius,'ratio':ratio,'reference_bits':a.hex(),'candidate_bits':b.hex(),'equal':a==b,'reference_values':struct.unpack('<fff',a),'candidate_values':struct.unpack('<fff',b)})
    failures=[r for r in records if not r['equal']]
    result={'status':'PASS' if not failures else 'FAIL','cases':records,'mismatches':len(failures),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'scope':'SetParams copying, fluid normalization constants, cached repeat behavior; no GPU simulation or RNG-consumer equivalence claimed.'}
    write_json(out,result);event('params-oracle','流体参数CPU系数与原版逐位对照。',mismatches=len(failures),evidence=str(out))
    print('Cases',len(records),'mismatches',len(failures));print(json.dumps(failures[:4],indent=2))
    directory.close()
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
