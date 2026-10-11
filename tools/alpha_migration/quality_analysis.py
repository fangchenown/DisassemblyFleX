"""Finite/contract/state metrics. Cross-trajectory distance is not equivalence."""
import argparse,csv,collections,math,statistics
import numpy as np
from common import *
DTYPE=np.dtype([('id','<i4'),('position','<f4',(4,)),('velocity','<f4',(3,)),('phase','<i4')])
def statefile(path):
    data=path.read_bytes();n=int.from_bytes(data[:4],'little',signed=True);assert n>=0 and len(data)==4+n*DTYPE.itemsize
    return np.frombuffer(data[4:],dtype=DTYPE)
def describe(s):
    p=s['position'][:,:3].astype(float);v=s['velocity'].astype(float);okay=np.isfinite(s['position']).all(axis=1)&np.isfinite(v).all(axis=1);n=len(s)
    result=dict(particles=n,nonfinite=int((~okay).sum()),unique_ids=len(np.unique(s['id']))==n,fluid_count=int(((s['phase']&(1<<22))!=0).sum()))
    if okay.any():
        p=p[okay];v=v[okay];result.update(centroid=p.mean(axis=0).tolist(),extent=(p.max(axis=0)-p.min(axis=0)).tolist(),rms_radius=float(np.sqrt(np.mean(np.sum((p-p.mean(axis=0))**2,axis=1)))),speed_rms=float(np.sqrt(np.mean(np.sum(v*v,axis=1)))))
    return result
def distance(a,b):
    ids,ia,ib=np.intersect1d(a['id'],b['id'],assume_unique=False,return_indices=True);x=a['position'][ia,:3].astype(float);y=b['position'][ib,:3].astype(float);v=a['velocity'][ia].astype(float)-b['velocity'][ib].astype(float);okay=np.isfinite(x).all(axis=1)&np.isfinite(y).all(axis=1)&np.isfinite(v).all(axis=1)
    result=dict(common_ids=len(ids),same_id_order=bool(np.array_equal(a['id'],b['id'])),same_phases=bool(np.array_equal(a['phase'][ia],b['phase'][ib])),same_inverse_mass=bool(np.array_equal(a['position'][ia,3],b['position'][ib,3])),byte_identical=a.tobytes()==b.tobytes(),finite_pairs=int(okay.sum()))
    if okay.any():
        d=np.linalg.norm(x[okay]-y[okay],axis=1);result.update(position_rms=float(np.sqrt(np.mean(d*d))),position_p95=float(np.quantile(d,.95)),position_max=float(d.max()),velocity_rms=float(np.sqrt(np.mean(np.sum(v[okay]**2,axis=1)))))
    return result
def cloud_distance(a,b,limit=12000):
    # Spatial comparison per phase flags/group, deterministic subsampling. It
    # complements particle-ID error, never proves matching topology/trajectory.
    try:from scipy.spatial import cKDTree
    except ImportError:return dict(status='scipy unavailable; ID and distribution metrics retained')
    result=[]
    for phase in sorted(set(a['phase'].tolist())&set(b['phase'].tolist())):
        x=a['position'][a['phase']==phase,:3].astype(float);y=b['position'][b['phase']==phase,:3].astype(float)
        x=x[np.isfinite(x).all(axis=1)];y=y[np.isfinite(y).all(axis=1)]
        if not len(x) or not len(y):continue
        xs=x[np.linspace(0,len(x)-1,min(limit,len(x))).astype(int)];ys=y[np.linspace(0,len(y)-1,min(limit,len(y))).astype(int)]
        xy=cKDTree(y).query(xs,k=1,workers=1)[0];yx=cKDTree(x).query(ys,k=1,workers=1)[0];d=np.concatenate([xy,yx]);result.append(dict(phase=int(phase),left_count=len(x),right_count=len(y),sample_count=len(d),symmetric_nearest_mean=float(d.mean()),symmetric_nearest_p95=float(np.quantile(d,.95)),centroid_distance=float(np.linalg.norm(x.mean(axis=0)-y.mean(axis=0)))))
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--left',default='df');p.add_argument('--right',default='of');p.add_argument('--cloud',action='store_true');a=p.parse_args()
    receipts=[r for f in (ROOT/'runs').glob(a.suite+'-*/receipt.json') if (r:=read(f)).get('suite')==a.suite];assert receipts and all(r['status'] in ['PASS','FAIL'] for r in receipts);failed=[r['name'] for r in receipts if r['status']=='FAIL'];receipts=[r for r in receipts if r['status']=='PASS']
    groups=collections.defaultdict(dict)
    for r in receipts:groups[(r['scene'],r['emit'],r['repeat'])][r['variant']]=r
    rows=[];self_groups=collections.defaultdict(list)
    for key,arms in sorted(groups.items()):
        if a.left not in arms or a.right not in arms:continue
        dirs={k:ROOT/'runs'/arms[k]['name'] for k in [a.left,a.right]};files={k:{f.name:f for f in d.glob('state_*.bin')} for k,d in dirs.items()};snapshots=[]
        for name in sorted(set(files[a.left])&set(files[a.right])):
            frame=int(name.split('_')[1].split('.')[0]);left=statefile(files[a.left][name]);right=statefile(files[a.right][name]);row=dict(frame=frame,left=describe(left),right=describe(right),cross=distance(left,right))
            if a.cloud and frame>0:row['spatial_cloud']=cloud_distance(left,right)
            snapshots.append(row)
            for variant,data in [(a.left,left),(a.right,right)]:self_groups[(key[0],key[1],variant,frame)].append((key[2],files[variant][name]))
        equality=list(csv.DictReader((dirs[a.left]/'contract.csv').open()))==list(csv.DictReader((dirs[a.right]/'contract.csv').open()))
        rows.append(dict(scene=key[0],emit=key[1],repeat=key[2],left=a.left,right=a.right,contract_equal=equality,snapshots=snapshots,scope='Same-ID and spatial distribution distances; nonzero differences are retained, not silently accepted as equivalence.'))
    within=[]
    for (scene,emit,variant,frame),samples in self_groups.items():
        if len(samples)<2:continue
        samples.sort();base=statefile(samples[0][1])
        for rep,path in samples[1:]:within.append(dict(scene=scene,emit=emit,variant=variant,frame=frame,reference_repeat=samples[0][0],repeat=rep,metrics=distance(base,statefile(path))))
    summary=dict(suite=a.suite,pairs=len(rows),snapshot_pairs=sum(len(r['snapshots']) for r in rows),self_repeat_comparisons=len(within),all_contracts_equal=all(r['contract_equal'] for r in rows),nonfinite_state_particles=sum(s[k]['nonfinite'] for r in rows for s in r['snapshots'] for k in ['left','right']),scope='Finite checks + actual captured distributions/ID trajectories; no universal numerical equivalence claim.')
    summary['excluded_failed_runs']=failed
    label=a.suite if (a.left,a.right)==('df','of') else a.suite+'__'+a.left+'-vs-'+a.right
    write(ROOT/'analysis'/f'{label}-quality.json',rows);write(ROOT/'analysis'/f'{label}-self-repeat.json',within);write(ROOT/'analysis'/f'{label}-quality-summary.json',summary);event('quality-analyzed',summary=summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
