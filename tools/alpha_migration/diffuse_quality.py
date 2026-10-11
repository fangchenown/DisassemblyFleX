"""Diffuse output has no persistent public particle IDs: compare permutations/distributions."""
import argparse,collections,itertools
import numpy as np
from scipy.spatial import cKDTree
from common import *
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',required=True);p.add_argument('--right',required=True);a=p.parse_args()
def read_diffuse(path):
    data=path.read_bytes();count=int.from_bytes(data[:4],'little',signed=True);v=np.frombuffer(data,dtype='<f4',offset=4).reshape(-1,8);return count,v
def compare(lp,rp):
    ln,x=read_diffuse(lp);rn,y=read_diffuse(rp);r=dict(left_count=ln,right_count=rn,count_equal=ln==rn,left_stored=len(x),right_stored=len(y),left_nonfinite=int((~np.isfinite(x)).sum()),right_nonfinite=int((~np.isfinite(y)).sum()),ordered_exact=x.tobytes()==y.tobytes())
    if x.shape==y.shape:
        def canonical(z):
            u=z.view('<u4');order=np.lexsort(tuple(u[:,i] for i in reversed(range(8))));return u[order].tobytes()
        r['exact_multiset']=canonical(x)==canonical(y)
    if len(x) and len(y) and not r['left_nonfinite'] and not r['right_nonfinite']:
        # Fixed evenly spaced samples, both directions, after sorting positions
        # to prevent GPU append order from selecting a different region.
        x=x[np.lexsort((x[:,2],x[:,1],x[:,0]))].astype(float);y=y[np.lexsort((y[:,2],y[:,1],y[:,0]))].astype(float)
        xs=x[np.linspace(0,len(x)-1,min(4096,len(x))).astype(int)];ys=y[np.linspace(0,len(y)-1,min(4096,len(y))).astype(int)]
        d=np.concatenate((cKDTree(y[:,:3]).query(xs[:,:3])[0],cKDTree(x[:,:3]).query(ys[:,:3])[0]))
        r.update(nearest_mean=float(d.mean()),nearest_p95=float(np.quantile(d,.95)),centroid_distance=float(np.linalg.norm(x[:,:3].mean(axis=0)-y[:,:3].mean(axis=0))),mean_lifetime_delta=float(abs(x[:,3].mean()-y[:,3].mean())),rms_speed_delta=float(abs(np.sqrt(np.mean(np.sum(x[:,4:7]**2,axis=1)))-np.sqrt(np.mean(np.sum(y[:,4:7]**2,axis=1))))))
    return r
groups=collections.defaultdict(dict);within=collections.defaultdict(list)
for f in (ROOT/'runs').glob(a.suite+'-*/receipt.json'):
    r=read(f)
    if r.get('suite')!=a.suite:continue
    if r['status']=='PASS' and r['variant'] in [a.left,a.right]:groups[(r['scene'],r['repeat'])][r['variant']]=f.parent
cross=[]
for (scene,repeat),arms in sorted(groups.items()):
    if not all(v in arms for v in [a.left,a.right]):continue
    for lp in sorted(arms[a.left].glob('diffuse_*.bin')):
        rp=arms[a.right]/lp.name;assert rp.exists();cross.append(dict(scene=scene,repeat=repeat,frame=lp.name,**compare(lp,rp)))
        for v,path in [(a.left,lp),(a.right,rp)]:within[(scene,v,lp.name)].append((repeat,path))
selfs=[]
for (scene,variant,frame),samples in within.items():
    for x,y in itertools.combinations(samples,2):selfs.append(dict(scene=scene,variant=variant,frame=frame,repeats=[x[0],y[0]],**compare(x[1],y[1])))
summary=[]
for scene in sorted(set(r['scene'] for r in cross)):
    xs=[r for r in cross if r['scene']==scene];row=dict(scene=scene,count_equal=all(r['count_equal'] for r in xs),pairs=len(xs),exact_multiset_pairs=sum(r.get('exact_multiset',False) for r in xs),nonfinite=sum(r['left_nonfinite']+r['right_nonfinite'] for r in xs))
    for key in ['nearest_mean','nearest_p95','centroid_distance','mean_lifetime_delta','rms_speed_delta']:
        row[key]=dict(cross_max=max([r.get(key,0) for r in xs] or [0]))
        for v in [a.left,a.right]:row[key][v+'_self_max']=max([r.get(key,0) for r in selfs if r['scene']==scene and r['variant']==v] or [0])
    summary.append(row)
label=a.suite+'__'+a.left+'-vs-'+a.right;write(ROOT/'analysis'/f'{label}-diffuse-quality.json',dict(cross=cross,self=selfs,summary=summary));print(json.dumps(summary,ensure_ascii=False,indent=2))
