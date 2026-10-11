"""All-pair original baseline variability; independent of candidate tolerances."""
import argparse,csv,itertools,collections
import numpy as np
from common import *
from quality_analysis import statefile,distance
p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--variant',required=True);a=p.parse_args()
groups=collections.defaultdict(list)
for f in (ROOT/'runs').glob(a.suite+'-*/receipt.json'):
    r=read(f)
    if r.get('suite')!=a.suite:continue
    if r['variant']==a.variant:
        assert r['status']=='PASS' and r['capture'];groups[r['scene']].append((r,f.parent))
keys=['min_y','max_y','speed_rms','spring_rel_rms','spring_rel_max','plane_penetration_max'];out=[]
for scene,runs in sorted(groups.items()):
    runs.sort(key=lambda x:x[0]['repeat']);pairs=list(itertools.combinations(runs,2));frames={int(f.stem.split('_')[1]) for f in runs[0][1].glob('state_*.bin') if int(f.stem.split('_')[1])>0};snapshots=[]
    for frame in sorted(frames):
        loaded=[statefile(d/f'state_{frame:04d}.bin') for r,d in runs];ds=[]
        for i,j in itertools.combinations(range(len(loaded)),2):ds.append(dict(pair=[runs[i][0]['repeat'],runs[j][0]['repeat']],**distance(loaded[i],loaded[j])))
        snapshots.append(dict(frame=frame,pairs=ds,maxima={k:max(x.get(k,0) for x in ds) for k in ['position_rms','position_max','velocity_rms']},exact_pairs=sum(x['byte_identical'] for x in ds)))
    arrays=[]
    for r,d in runs:arrays.append(np.array([[float(x[k]) for k in keys] for x in csv.DictReader((d/'frames.csv').open())]))
    maxima=np.max([np.max(abs(x-y),axis=0) for x,y in itertools.combinations(arrays,2)],axis=0)
    out.append(dict(scene=scene,runs=len(runs),within_pairs=len(pairs),snapshots=snapshots,all_frame_maxima={k:float(maxima[i]) for i,k in enumerate(keys)},run_names=[r['name'] for r,d in runs]))
result=dict(suite=a.suite,variant=a.variant,scope='Independent original/no-change controls only. All within-variant repeat pairs; candidate samples do not set this envelope. Prior three-repeat metrics and failures remain preserved. Empirical envelope is not a universal bound.',scenes=out)
write(ROOT/'analysis'/f'{a.suite}__{a.variant}-independent-baseline.json',result);print(json.dumps([dict(scene=r['scene'],runs=r['runs'],position_rms_max=max(s['maxima']['position_rms'] for s in r['snapshots'])) for r in out]))
