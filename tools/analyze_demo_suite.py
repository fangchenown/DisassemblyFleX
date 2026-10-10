"""Numerical diagnostic only; does not relax or redefine an acceptance gate."""
import argparse,json,struct
from pathlib import Path
import numpy as np
from ledger import write_json
ROOT=Path(__file__).resolve().parents[2]/'Build/DisassemblyFleX-20261009'
def metrics(a,b):
    a=np.asarray(a,dtype=np.float32);b=np.asarray(b,dtype=np.float32);bits=a.view(np.uint32)!=b.view(np.uint32);valid=np.isfinite(a)&np.isfinite(b);d=np.abs(a[valid].astype(np.float64)-b[valid].astype(np.float64));changed=d[d!=0]
    return {'words':int(a.size),'different_bits':int(bits.sum()),'nonfinite_differences':int((bits&~valid).sum()),'max_abs':float(d.max()) if d.size else 0,'rms':float(np.sqrt(np.mean(d*d))) if d.size else 0,'p99_abs':float(np.quantile(changed,.99)) if changed.size else 0}
def compare(a,b):
    raw=a.read_bytes();other=b.read_bytes();r={'bytes_equal':raw==other,'bytes':[len(raw),len(other)]}
    if raw==other:return r
    if len(raw)<4 or len(other)<4:return r
    n,m=struct.unpack_from('<i',raw)[0],struct.unpack_from('<i',other)[0];r['counts']=[n,m]
    if n!=m:return r
    stem=a.name.split('_')[0];aw=np.frombuffer(raw,dtype='<u4',offset=4);bw=np.frombuffer(other,dtype='<u4',offset=4)
    if aw.size!=bw.size:return r
    af,bf=aw.view(np.float32),bw.view(np.float32)
    if stem=='state':
        aa=aw.reshape(n,9);bb=bw.reshape(n,9);fa=aa.view(np.float32);fb=bb.view(np.float32);r['ids_phases_equal']=bool(np.array_equal(aa[:,[0,8]],bb[:,[0,8]]));r['positions']=metrics(fa[:,1:4],fb[:,1:4]);r['inverse_mass']=metrics(fa[:,4],fb[:,4]);r['velocities']=metrics(fa[:,5:8],fb[:,5:8])
    elif stem=='render':
        aa=af.reshape(n,20);bb=bf.reshape(n,20)
        for name,x,y in [('normals',0,4),('smooth',4,8),('anisotropy',8,20)]:r[name]=metrics(aa[:,x:y],bb[:,x:y])
    elif stem=='rigids':r['rotations']=metrics(af.reshape(n,7)[:,:4],bf.reshape(n,7)[:,:4]);r['translations']=metrics(af.reshape(n,7)[:,4:],bf.reshape(n,7)[:,4:])
    elif stem=='triangles':r['indices_equal']=bool(np.array_equal(aw[:n*3],bw[:n*3]));r['normals']=metrics(af[n*3:],bf[n*3:])
    elif stem=='diffuse':
        left=sorted(raw[i:i+32] for i in range(4,len(raw),32));right=sorted(other[i:i+32] for i in range(4,len(other),32));r['active_tuple_multiset_equal']=left==right
        r['ordered_values']=metrics(af,bf)
    return r
def main():
    p=argparse.ArgumentParser();p.add_argument('suite');a=p.parse_args();out=ROOT/'evidence'/a.suite;rows=json.loads((out/'results.json').read_text());result=[]
    for row in rows:
        if not all(r['exit_code']==0 for r in row['runs'].values()):continue
        ref=ROOT/'demo-runs'/row['runs']['reference']['name'];cand=ROOT/'demo-runs'/row['runs']['candidate']['name'];r={'scene':row['scene'],'equal':row['equal'],'files':{name:compare(ref/name,cand/name) for name in row.get('mismatches',[])}};result.append(r)
    write_json(out/'numeric-diagnostics.json',result);print(json.dumps({'scenes':len(result),'exact':sum(r['equal'] for r in result),'output':str(out/'numeric-diagnostics.json')}))
if __name__=='__main__':main()
