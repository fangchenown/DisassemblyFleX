"""Compare captures against observed reference variability, without epsilon.

The original byte-equality results remain immutable. This separate diagnostic
requires identical inputs, discrete data and non-finite patterns, and compares
max-absolute/RMS distances to the maximum observed reference-reference distance.
It never invents a fixed tolerance or silently accepts an unexplained mismatch.
"""
import argparse,hashlib,itertools,json
from pathlib import Path
import numpy as np
from ledger import write_json
ROOT=Path(__file__).resolve().parents[2]/'Build/DisassemblyFleX-20261009'
FIXED=['params.bin','params_-001.bin','params_0000.bin','state_-001.bin','state_0000.bin','rigids_-001.bin','rigids_0000.bin','triangles.bin','triangles_-001.bin','triangles_0000.bin']
def fingerprint(job):return tuple(job.get('capture_files',{}).get(name) for name in FIXED)
def fields(path):
    raw=path.read_bytes();kind=path.name.split('_')[0];n=int(np.frombuffer(raw,dtype='<i4',count=1)[0]);words=np.frombuffer(raw,dtype='<u4',offset=4);floats=words.view(np.float32);discrete=[];groups={}
    if kind=='state':
        a=words.reshape(n,9);f=a.view(np.float32);discrete=[a[:,[0,4,8]].tobytes()];groups={'positions':f[:,1:4],'velocities':f[:,5:8]}
    elif kind=='render':
        f=floats.reshape(n,20);groups={'normals':f[:,:4],'smooth':f[:,4:8],'anisotropy':f[:,8:20]}
    elif kind=='rigids':
        f=floats.reshape(n,7);groups={'rotations':f[:,:4],'translations':f[:,4:]}
    elif kind=='triangles':discrete=[words[:n*3].tobytes()];groups={'normals':floats[n*3:]}
    elif kind=='diffuse':
        f=floats.reshape(n,8).astype(np.float64);groups={'population':np.array([n],dtype=np.float64)}
        if n:groups['distribution']=np.concatenate([f.min(axis=0),f.max(axis=0),f.mean(axis=0),np.mean(f*f,axis=0)])
        else:groups['distribution']=np.zeros(32,dtype=np.float64)
        # Pair positions/lifetimes and velocities before sorting; independent
        # sorting of the channels would hide broken particle associations.
        discrete=[np.sort(np.frombuffer(raw[4:],dtype='V32')).tobytes()]
    else:return raw,{},raw
    return (n,tuple(discrete)),groups,raw
def distance(a,b):
    if a.shape!=b.shape:return None
    fa=np.isfinite(a);fb=np.isfinite(b)
    if not np.array_equal(fa,fb) or not np.array_equal(np.isnan(a),np.isnan(b)) or not np.array_equal(np.isposinf(a),np.isposinf(b)):return None
    delta=a[fa].astype(np.float64)-b[fa].astype(np.float64)
    return (float(np.max(np.abs(delta))) if delta.size else 0,float(np.sqrt(np.mean(delta*delta))) if delta.size else 0)
def compare(cand_path,ref_paths):
    cd,cg,raw=fields(cand_path);refs=[fields(p) for p in ref_paths]
    if any(raw==r[2] for r in refs):return {'accepted':True,'classification':'exact_to_reference_repeat'}
    diffuse=cand_path.name.startswith('diffuse_')
    if diffuse and any(cd==r[0] for r in refs):return {'accepted':True,'classification':'exact_particle_tuple_multiset'}
    if not diffuse and not all(cd==r[0] for r in refs):return {'accepted':False,'classification':'discrete_mismatch'}
    if not cg:return {'accepted':False,'classification':'unclassified_binary_mismatch'}
    result={'accepted':True,'classification':'within_observed_reference_variation','fields':{}}
    for name,candidate in cg.items():
        values=[r[1][name] for r in refs];baseline=[distance(a,b) for a,b in itertools.combinations(values,2)];baseline=[d for d in baseline if d is not None];measured=[distance(candidate,v) for v in values]
        maximum=(max(d[0] for d in baseline),max(d[1] for d in baseline)) if baseline else (0,0)
        good=[i for i,d in enumerate(measured) if d is not None and d[0]<=maximum[0] and d[1]<=maximum[1]]
        result['fields'][name]={'accepted':bool(good),'reference_max_abs':maximum[0],'reference_max_rms':maximum[1],'candidate_distances':measured,'matching_reference_indices':good};result['accepted']&=bool(good)
    if not result['accepted']:result['classification']='exceeds_observed_reference_variation'
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('suite');p.add_argument('--output',required=True);args=p.parse_args();output=ROOT/'evidence'/args.output
    if output.exists():raise ValueError('Immutable report exists')
    references=[]
    for jobpath in sorted((ROOT/'demo-runs').glob('*/job.json')):
        job=json.loads(jobpath.read_text(encoding='utf-8'))
        if job.get('status')=='PASS' and job.get('implementation')=='reference':references.append((job,jobpath.parent))
    suite=json.loads((ROOT/'evidence'/args.suite/'results.json').read_text(encoding='utf-8'));rows=[]
    for row in suite:
        candidate=ROOT/'demo-runs'/row['runs']['candidate']['name'];job=json.loads((candidate/'job.json').read_text(encoding='utf-8'));matches=[root for j,root in references if (j['scene'],j['mode'],j['frames'],fingerprint(j))==(job['scene'],job['mode'],job['frames'],fingerprint(job))]
        current={'scene':row['scene'],'candidate':str(candidate),'references':[str(r) for r in matches],'files':{},'accepted':bool(matches)}
        if row.get('equal'):current['classification']='all_captures_byte_equal'
        else:
            for name in row.get('mismatches',[]):
                report=compare(candidate/name,[r/name for r in matches]);current['files'][name]=report;current['accepted']&=report['accepted']
            current['classification']='reference_variation' if current['accepted'] else 'investigate'
        rows.append(current);print(row['scene'],len(matches),current['accepted'],[n for n,r in current['files'].items() if not r['accepted']],flush=True)
    write_json(output,{'suite':args.suite,'rule':'No fixed epsilon: max-absolute and RMS distances must both fit observed reference-reference maxima; exact discrete values; diffuse complete tuple permutation or population/distribution comparison. This supplements, never replaces, byte-equality evidence.','accepted':all(r['accepted'] for r in rows),'rows':rows})
if __name__=='__main__':main()
